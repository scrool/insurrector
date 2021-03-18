# Tool to process income from stock trading to prepare Czech tax return

## Introduction

It is fairly easy to start trading stocks in Revolut. Processing monthly
statements in pdf format from trading is not fun at all.

Insurrector is a project that makes it easier to process Revolut statement
documents and produces files in a format that can be used by spreadsheet
programs to make further calculations for tax returns.

Project provides two interfaces:
* command line interface (CLI)
* graphical user interface (GUI) 

Project is from large part based on [Revolut Stocks calculator for Bulgarian
National Revenue Agency](https://github.com/doino-gretchenliev/revolut-stocks/)
by [Doino Gretchenliev](https://github.com/doino-gretchenliev/). If you find
this useful, navigate to his project page and consider a support.

Please beware that you should double check output of the tooling. There are
quite a few places where the results could be off. That includes parser or bug
in a code that hasn't been tested very well.

## How it works

1. The tool recursively scans the input directory for statement files(`*.pdf`).
2. The statement files are then being parsed to extract all activity
   information.
3. The calculator then obtains the last published exchange rate (USD to CZK)
   for the day of each trade.
4. During the last step all activities are processed to produce the required
   data.

## Considerations

1. The calculator parses exported statements in `pdf` format. Parsing a `pdf`
   file is a risky task and heavily depends on the structure of the file. In
   order to prevent miscalculations, please review the generated
   `statements.csv` file under the `output` directory and make sure all
   activities are correctly extracted from your statement files.
2. Revolut doesn't provide information about which exact stock asset is being
   sold during a sale. As currently indicated at the end of each statement
   file, the default tax lot disposition method is `First-In, First-Out`. The
   tool is developed according to that rule.
3. The trade date (instead of the settlement date) is used for any calculation.
4. By default the tool uses locally cached exchange rates located
   [here](https://github.com/scrool/insurrector/tree/main/insurrector/). It is
   also possible to automatically download exchange rates provided Czech
   Central Bank (CNB).

## Requirements

* **Python** version >= 3.7
* Linux

## CLI Usage

#### Install

```console
$ pip install .
```

#### Help

```console
$ insurrector-cli --help
```

#### Run

```console
$ insurrector-cli -i <path_to_input_dir> -o <path_to_output_dir>
```

**Output**:
```console
[INFO]: Collecting statement files.
[INFO]: Collected statement files for processing: ['input/statement-3cbc62e0-2e0c-44a4-ae0c-8daa4b7c41bc.pdf', 'input/statement-19ed667d-ba66-4527-aa7a-3a88e9e4d613.pdf'].
[INFO]: Parsing statement files.
[INFO]: Generating [statements.csv] file.
```

## GUI Usage

#### Requirements

GUI is based on Qt5 and might require some additional libraries installed.

#### Install

```console
$ pip install '.[gui]'
```

#### Run

```console
$ insurrector-gui
```

## Errors

Errors are being reported along with an `ERROR` label.

### "Unable to get exchange rate from CNB"

The error indicates that there was an issue obtaining the exchange rate from
CNB online service. Navigate to [CNB online
service](https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/vybrane_form.html),
select all months, year, currency: USD, and output format: text. If that works,
you can report an issue.

### "No statement files found"

There was an issue finding input statement files. Please, check your input
directory configuration and file permissions.

### "Not activities found. Please, check your statement files"

The calculator parser was unable to parse any activities within your statement
file. Please, check your statement files and ensure there are reported
activities. If there are reported activities, but the error still persists,
please open an issue.

### "Statements contain unsupported activity types"

The calculator found unsupported activity type/s. Please, open an issue and
include the reported activity type.

### "Unable to find previously purchased shares to surrender as part of SSP"

The calculator, while trying to perform the SSP surrender shares operation, was
unable to find the previously purchased shares for the same stock symbol.
Please, ensure there is a statement file in the input directory, containing the
original purchase.

## Parsers

### Revolut

File format: `.pdf`

That's the default parser and handler statement files downloaded from Revolut app.

### CSV

File format: `.csv`

A generic parser for statements in CSV format. The parser could be used with
structured data, that could be easily organized to fit the parser's
requirements.

In order for the file to be correctly parsed the following requirements should be met:
1. The following columns should be presented:
   1. `trade_date`: The column should contain the date of the trade in
      dd.MM.YYYY format.
   2. `activity_type`: The current row activity type. The following types are
      supported: ["SELL", "BUY", "DIV", "DIVNRA", "SSP", "MAS"]
   3. `company`: The name of the stock company. For example Apple INC.
   4. `symbol`: The symbol of the stock. For example AAPL.
   5. `quantity`: The quantity of the activity. In order to correctly recognize
      surrender from addition SSP and MAS activities, the quantity should be
      positive or negative. For all other activity types, there is no such
      requirement(it could be an absolute value).
   6. `price`: The activity price per share.
   7. `amount`: The total amount of the activity. It should be a result of
      (quantity x price) + commissions + taxes.
2. The first row should contain headers, indicating the column name, according
   to the mapping above. There is *no* requirement for columns to be presented
   in any particular order.
3. The activities, listed in the file/s should be sorted from the earliest
   trading date to the latest one. The earliest date should be located at the
   very begging of the file. When you're processing multiple statement files
   you can append them together(no need to merge the activities).
4. DIVNRA, which represents the tax that was paid upon receiving dividends,
   should follow DIV activity. Other activities could be listed between those
   two events. DIVNRA is not required for all DIVs but would trigger
   calculations for dividend tax owed to NAP. DIV activity amount should be
   equal to dividend value + tax.

In order to verify the parser correctness, you can compare the generated
`statements.csv` file with your input file. The data should be the same in both
files.

## Epilogue

This was created as a simple fork of [Revolut Stocks calculator for Bulgarian
National Revenue Agency](https://github.com/doino-gretchenliev/revolut-stocks/)
by [Doino Gretchenliev](https://github.com/doino-gretchenliev/) to prepare tax
return in Czechia. Since then I have moved away from Revolut. I don't have
intention to improve this.

If you find this useful, navigate to Doino's project page and consider to
support him.
