import decimal
import logging
from collections import deque

from insurrector import MFCR_DATE_FORMAT
from insurrector.calculators.utils import adjust_stock_data, get_stock_sales

logger = logging.getLogger("calculations")

decimal.getcontext().rounding = decimal.ROUND_HALF_UP


class SalesCalculator(object):
    def __init__(self, statements):
        self.statements = statements

        self.statement = None
        self.stock_symbol = None

        self.purchases = {}
        self.sales = []
        self.ssp_surrendered_data = {}

    def _calculate_buy(self):
        activity_quantity = abs(self.statement.get("quantity", 0))

        logger.debug(
            f"[BUY] [{self.stock_symbol}] td:[{self.statement['trade_date']}] qt:[{activity_quantity}] pr:[{self.statement['price']}] ex:[{self.statement['exchange_rate']}]"
        )
        stock_queue = self.purchases.get(self.stock_symbol, deque())
        stock_queue.append(
            {
                "price": self.statement["price"],
                "exchange_rate": self.statement["exchange_rate"],
                "quantity": activity_quantity,
                "trade_date": self.statement["trade_date"],
            }
        )
        self.purchases[self.stock_symbol] = stock_queue

    def _calculate_sell(self):
        raise NotImplementedError("Generic sale calculations are not implemented")

    def _calculate_sso(self):
        activity_quantity = abs(self.statement.get("quantity", 0))

        logger.debug(
            f"[SSO] [{self.stock_symbol}] td:[{self.statement['trade_date']}] qt:[{activity_quantity}] pr:[{self.statement['price']}] ex:[{self.statement['exchange_rate']}]"
        )

        stock_queue = self.purchases.get(self.stock_symbol, deque())
        stock_queue.append(
            {
                "price": decimal.Decimal(0),
                "exchange_rate": decimal.Decimal(0),
                "quantity": activity_quantity,
                "trade_date": self.statement["trade_date"],
            }
        )
        self.purchases[self.stock_symbol] = stock_queue

    def _calculate_ssp_mas(self):
        activity_type = self.statement["activity_type"]
        activity_quantity = self.statement["quantity"]
        stock_symbol = self.stock_symbol.replace(".OLD", "")

        logger.debug(
            f"[{activity_type}] [{self.stock_symbol}] td:[{self.statement['trade_date']}] qt:[{activity_quantity}] pr:[{self.statement['price']}] ex:[{self.statement['exchange_rate']}]"
        )

        if activity_quantity < 0:
            self.ssp_surrendered_data[stock_symbol] = {
                "quantity": abs(activity_quantity),
                "price": self.statement["price"],
            }
            return

        stock_queue = self.purchases.get(stock_symbol, deque())
        logger.debug(f"Before addition: {stock_queue}")

        if stock_symbol not in self.ssp_surrendered_data:
            logging.warn(f"No SSP surrender information found for: [{stock_symbol}].")
            return

        surrendered_data = self.ssp_surrendered_data[stock_symbol]
        ssp_quantity_ratio = abs(activity_quantity) / surrendered_data["quantity"]
        ssp_price_ratio = self.statement["price"] / surrendered_data["price"]

        logger.debug(
            f"SSP quantity ratio: [{ssp_quantity_ratio}], price ratio: [{ssp_price_ratio}]."
        )
        adjust_stock_data(stock_queue, ssp_quantity_ratio, ssp_price_ratio)
        logger.debug(f"After addition: {stock_queue}")
        del self.ssp_surrendered_data[stock_symbol]

    def calculate_sales(self):
        for statement in self.statements:
            self.statement = statement
            self.stock_symbol = statement.get("symbol", None)

            if statement["activity_type"] == "BUY":
                self._calculate_buy()

            if statement["activity_type"] == "SELL":
                self._calculate_sell()

            if statement["activity_type"] == "SSO":
                self._calculate_sso()

            if (
                statement["activity_type"] == "SSP"
                or statement["activity_type"] == "MAS"
            ):
                self._calculate_ssp_mas()


class SalesCalculatorCzechia(SalesCalculator):
    def __init__(self, statements):
        super().__init__(statements)

    def _calculate_sell(self):
        activity_quantity = abs(self.statement.get("quantity", 0))

        logger.debug(
            f"[SELL] [{self.stock_symbol}] td:[{self.statement['trade_date']}] qt:[{activity_quantity}] pr:[{self.statement['price']}] ex:[{self.statement['exchange_rate']}]"
        )

        if (
            self.stock_symbol not in self.purchases
            or len(self.purchases[self.stock_symbol]) == 0
        ):
            logging.warn(f"No purchase information found for: [{self.stock_symbol}].")
            return

        stock_queue = self.purchases[self.stock_symbol]

        for sale_item in get_stock_sales(stock_queue, activity_quantity):
            purchase_price_in_currency = sale_item["price"] * sale_item["quantity"]
            purchase_price = purchase_price_in_currency * sale_item["exchange_rate"]

            sell_price_in_currency = self.statement["price"] * sale_item["quantity"]
            sell_price = sell_price_in_currency * self.statement["exchange_rate"]

            sale = {
                "symbol": self.stock_symbol,
                "quantity": sale_item["quantity"],
                "purchase_date": sale_item["trade_date"].strftime(MFCR_DATE_FORMAT),
                "trade_date": self.statement["trade_date"].strftime(MFCR_DATE_FORMAT),
                "purchase_item_price_in_currency": sale_item["price"],
                "purchase_price": purchase_price,
                "purchase_price_in_currency": purchase_price_in_currency,
                "purchase_exchange_rate": sale_item["exchange_rate"],
                "sell_price": sell_price,
                "sell_exchange_rate": self.statement["exchange_rate"],
                "sell_price_in_currency": sell_price_in_currency,
                "sell_item_price_in_currency": self.statement["price"],
                "profit": decimal.Decimal(0),
                "loss": decimal.Decimal(0),
                "profit_in_currency": decimal.Decimal(0),
                "loss_in_currency": decimal.Decimal(0),
            }

            profit_loss = sale["sell_price"] - sale["purchase_price"]
            if profit_loss > 0:
                sale["profit"] = profit_loss
            else:
                sale["loss"] = profit_loss

            profit_loss = sell_price_in_currency - purchase_price_in_currency
            if profit_loss > 0:
                sale["profit_in_currency"] = profit_loss
            else:
                sale["loss_in_currency"] = profit_loss

            self.sales.append(sale)


def calculate_sales_czk(statements):
    sales_calculator = SalesCalculatorCzechia(statements)
    sales_calculator.calculate_sales()
    return sales_calculator.sales, sales_calculator.purchases
