import csv
import decimal
import locale
import logging
import urllib.request
from datetime import datetime
from io import StringIO
from urllib.parse import urlencode

from dateutil.relativedelta import relativedelta

from insurrector import (
    CNB_BASE_URL,
    CNB_CSV_HEADER_ROWS,
    CNB_DATE_FORMAT,
    CNB_SPLIT_BY_MONTHS,
)
from insurrector.cached_exchange_rates import load_exchange_rates

logger = logging.getLogger("exchange_rates")

decimal.getcontext().rounding = decimal.ROUND_HALF_UP


def get_exchange_rates(first_date, last_date):
    first_date -= relativedelta(
        months=1
    )  # Get one extra month of data to ensure there was a published exchange rate
    exchange_rates = {}
    while True:
        curr_fs_date = first_date
        curr_ls_date = first_date + relativedelta(months=CNB_SPLIT_BY_MONTHS)
        exchange_rates.update(query_exchange_rates(curr_fs_date, curr_ls_date))
        first_date = curr_ls_date + relativedelta(days=1)

        if first_date > last_date:
            break

    return exchange_rates


def query_exchange_rates(first_date, last_date):
    logger.debug(
        f"Obtaining exchange rate from date range: [{first_date}] - [{last_date}]"
    )

    params = {
        "mena": "USD",
        "format": "txt",
    }

    params["od"] = first_date.strftime(CNB_DATE_FORMAT)
    params["do"] = last_date.strftime(CNB_DATE_FORMAT)

    exchange_rates = {}
    oldnumericlocale = locale.getlocale(locale.LC_NUMERIC)

    try:
        response = urllib.request.urlopen(CNB_BASE_URL + urlencode(params))

        data = response.read()
        text = data.decode("utf-8")

        fd = StringIO(text)

        reader = csv.reader(fd, delimiter="|")

        locale.setlocale(locale.LC_NUMERIC, "cs_CZ.utf8")
        locale.getlocale(locale.LC_NUMERIC)
        for index, row in enumerate(reader):
            if index < CNB_CSV_HEADER_ROWS:
                continue

            if not row:
                continue

            date = datetime.strptime(row[0], CNB_DATE_FORMAT)
            exchange_rates[date] = locale.atof(row[1].strip(), decimal.Decimal)
    except Exception as e:
        logging.exception(
            f"Unable to get exchange rate from CNB. Please, try again later: {e}."
        )
        raise SystemExit(1)
    finally:
        locale.setlocale(locale.LC_NUMERIC, oldnumericlocale)

    return exchange_rates


def find_last_published_exchange_rate(exchange_rates, search_date):
    return min(exchange_rates.keys(), key=lambda date: abs(date - search_date))


def populate_exchange_rates(statements, use_cnb):
    first_date = statements[0]["trade_date"]
    last_date = statements[-1]["trade_date"]

    exchange_rates = {}
    if use_cnb:
        exchange_rates = get_exchange_rates(first_date, last_date)
    else:
        exchange_rates = load_exchange_rates()

    for statement in statements:
        if statement["trade_date"] in exchange_rates:
            statement["exchange_rate"] = exchange_rates[statement["trade_date"]]
            statement["exchange_rate_date"] = statement["trade_date"]
            continue

        statement["exchange_rate_date"] = find_last_published_exchange_rate(
            exchange_rates, statement["trade_date"]
        )
        statement["exchange_rate"] = exchange_rates[statement["exchange_rate_date"]]
