import csv
import decimal

from insurrector import MFCR_DIGIT_PRECISION
from insurrector.utils import humanize_date

decimal.getcontext().rounding = decimal.ROUND_HALF_UP


def export_to_csv(list_object, csv_file, fieldnames):

    csv_list_object = humanize_date(list_object)

    with open(csv_file, "w") as fd:
        writer = csv.DictWriter(
            fd,
            fieldnames=fieldnames,
            quotechar='"',
            quoting=csv.QUOTE_ALL,
        )

        header = {
            fieldname: fieldname.replace("_", " ").title() for fieldname in fieldnames
        }
        writer.writerow(header)
        for elements in csv_list_object:
            writer.writerow(elements)


def export_statements(file_path, statements):
    export_to_csv(
        statements,
        file_path,
        [
            "trade_date",
            "settle_date",
            "currency",
            "activity_type",
            "company",
            "symbol_description",
            "symbol",
            "quantity",
            "price",
            "amount",
        ],
    )


def export_sales_in_currency_czk(file_path, sales):
    sales = [
        {
            **{
                k: v
                for k, v in sale.items()
                if k
                not in [
                    "purchase_exchange_rate",
                    "purchase_price",
                    "sell_exchange_rate",
                    "sell_price",
                    "profit",
                    "loss",
                    "purchase_price_in_currency",
                    "sell_price_in_currency",
                ]
            },
            **{
                "profit_in_currency": sale["profit_in_currency"].quantize(
                    decimal.Decimal(MFCR_DIGIT_PRECISION)
                ),
                "loss_in_currency": sale["loss_in_currency"].quantize(
                    decimal.Decimal(MFCR_DIGIT_PRECISION)
                ),
                "purchase_item_price_in_currency": sale[
                    "purchase_item_price_in_currency"
                ].quantize(decimal.Decimal(MFCR_DIGIT_PRECISION)),
                "sell_item_price_in_currency": sale[
                    "sell_item_price_in_currency"
                ].quantize(decimal.Decimal(MFCR_DIGIT_PRECISION)),
            },
            **{"currency": "USD"},
        }
        for sale in sales
    ]
    export_to_csv(
        sales,
        file_path,
        [
            "symbol",
            "quantity",
            "sell_item_price_in_currency",
            "currency",
            "trade_date",
            "purchase_item_price_in_currency",
            "purchase_date",
            "profit_in_currency",
            "loss_in_currency",
        ],
    )


def export_sales_czk(file_path, sales):
    sales = [
        {
            **{
                k: v
                for k, v in sale.items()
                if k
                not in [
                    "purchase_price",
                    "purchase_exchange_rate",
                    "sell_exchange_rate",
                    "sell_price",
                    "profit_in_currency",
                    "loss_in_currency",
                    "purchase_price_in_currency",
                    "purchase_item_price_in_currency",
                    "sell_price_in_currency",
                    "sell_item_price_in_currency",
                ]
            },
            **{
                "profit": sale["profit"].quantize(
                    decimal.Decimal(MFCR_DIGIT_PRECISION)
                ),
                "loss": sale["loss"].quantize(decimal.Decimal(MFCR_DIGIT_PRECISION)),
                "purchase_item_price": sale["purchase_item_price_in_currency"]
                * sale["purchase_exchange_rate"].quantize(
                    decimal.Decimal(MFCR_DIGIT_PRECISION)
                ),
                "sell_item_price": sale["sell_item_price_in_currency"]
                * sale["sell_exchange_rate"].quantize(
                    decimal.Decimal(MFCR_DIGIT_PRECISION)
                ),
            },
            **{"currency": "CZK"},
        }
        for sale in sales
    ]
    export_to_csv(
        sales,
        file_path,
        [
            "symbol",
            "quantity",
            "sell_item_price",
            "currency",
            "trade_date",
            "purchase_item_price",
            "purchase_date",
            "profit",
            "loss",
        ],
    )
