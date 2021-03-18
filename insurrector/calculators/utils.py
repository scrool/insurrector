import copy
import decimal
from collections import deque

decimal.getcontext().rounding = decimal.ROUND_HALF_UP


def adjust_stock_data(stock_queue, ssp_quantity_ratio, ssp_price_ratio):
    for data in stock_queue:
        data["quantity"] *= ssp_quantity_ratio
        data["price"] *= ssp_price_ratio


def adjust_quantity(stock_queue, sold_quantity):
    quantity_to_adjust = sold_quantity

    for data in list(stock_queue):
        quantity_after_abj = data["quantity"] - quantity_to_adjust

        if quantity_after_abj > 0:
            data["quantity"] = quantity_after_abj
            break

        stock_queue.popleft()
        quantity_to_adjust -= data["quantity"]


def get_stock_sales(stock_queue, sold_quantity):
    quantity_to_adjust = sold_quantity

    sold_queue = deque()
    local_stock_queue = copy.deepcopy(stock_queue)
    for item in list(local_stock_queue):
        quantity_after_abj = item["quantity"] - quantity_to_adjust

        if quantity_after_abj > 0:
            item["quantity"] = item["quantity"] - quantity_after_abj
            sold_queue.append(item)
            break

        item = local_stock_queue.popleft()
        sold_queue.append(item)
        quantity_to_adjust -= item["quantity"]

    return sold_queue
