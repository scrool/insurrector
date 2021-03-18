import logging
import os

import insurrector.parsers.csv as csv
import insurrector.parsers.revolut as revolut
from insurrector.calculators.fifo import calculate_sales_czk
from insurrector.csv import (
    export_sales_in_currency_czk,
    export_sales_czk,
    export_statements,
)
from insurrector.exchange_rates import populate_exchange_rates
from insurrector.utils import get_unsupported_activity_types, merge_dict_of_lists

logger = logging.getLogger("process")

supported_parsers = {}

supported_parsers = {
    "revolut": revolut.Parser,
    "csv": csv.Parser,
}


def for_each_parser(func, statements, filename=None, output_dir=None, **kwargs):
    result = {}
    for parser_name, parser_statements in statements.items():
        if filename is not None:
            if len(statements) > 1:
                parser_output_dir = os.path.join(output_dir, parser_name)
                kwargs["file_path"] = os.path.join(parser_output_dir, filename)
                os.makedirs(parser_output_dir, exist_ok=True)
            else:
                kwargs["file_path"] = os.path.join(output_dir, filename)
                os.makedirs(output_dir, exist_ok=True)

        result[parser_name] = func(**{"statements": parser_statements}, **kwargs)

    return result


class Process(object):
    def __init__(self, input_dir, output_dir, parser_names, in_currency=False):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.parser_names = parser_names
        self.in_currency = in_currency

        self.statements = {}

    def _parse(self):
        logger.debug(f"Supported parsers: [{supported_parsers}]")

        parser_names = list(dict.fromkeys(self.parser_names))

        logger.info(f"Parsing statement files with parsers: {parser_names}.")
        statements = {}
        for parser_name in parser_names:
            parser_input_dir = self.input_dir
            if len(parser_names) > 1:
                parser_input_dir = os.path.join(parser_input_dir, parser_name)

            statements[parser_name] = supported_parsers[parser_name](
                parser_input_dir
            ).parse()

            if not statements[parser_name]:
                logger.error(
                    f"Not activities found with parser[{parser_name}]. Please, check the statement files."
                )
                raise SystemExit(1)
        self.statements = statements
        return self.statements

    def _generate_statements(self):
        assert self.statements
        logger.info("Generating [statements.csv] file.")
        for_each_parser(
            export_statements,
            self.statements,
            filename="statements.csv",
            output_dir=self.output_dir,
        )


class ProcessCzechia(Process):
    def __init__(self, input_dir, output_dir, parser_names, use_cnb, in_currency=False):
        self.use_cnb = use_cnb

        self.parsers_calculations = None
        self.merged_sales = None
        super().__init__(input_dir, output_dir, parser_names, in_currency)

    def _populate_exchange_rates(self):
        logger.info("Populating exchange rates.")
        for_each_parser(populate_exchange_rates, self.statements, use_cnb=self.use_cnb)

    def _calculate_sales(self):
        logger.info("Calculating sales information.")
        self.parsers_calculations = for_each_parser(
            calculate_sales_czk, self.statements
        )

        sales = {
            parser_name: parser_calculations[0]
            for parser_name, parser_calculations in self.parsers_calculations.items()
        }
        self.merged_sales = merge_dict_of_lists(sales)

    def _generate_sales(self):
        assert self.merged_sales
        logger.info("Generating [sales.csv] file.")
        if self.in_currency:
            export_sales_in_currency_czk(
                os.path.join(self.output_dir, "sales.csv"), self.merged_sales
            )
        else:
            export_sales_czk(
                os.path.join(self.output_dir, "sales.csv"), self.merged_sales
            )

    def process(self):
        self._parse()
        self._generate_statements()
        self._populate_exchange_rates()

        unsupported_activity_types = get_unsupported_activity_types(
            supported_parsers, self.statements
        )

        if len(unsupported_activity_types) == 0:
            self._calculate_sales()
            self._generate_sales()


def process_mfcr(input_dir, output_dir, parser_names, use_cnb, in_currency=False):
    process_obj = ProcessCzechia(
        input_dir, output_dir, parser_names, use_cnb, in_currency
    )
    return process_obj.process()
