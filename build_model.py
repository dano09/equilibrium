import pandas as pd
import functools

BALANCE_SHEET_FILE = 'balance_sheet.csv'
CASH_FLOW_FILE = 'cash_flow.csv'
INCOME_FILE = 'income_statement.csv'
SHARES_FILE = 'shares.csv'
STOCK_VALUE_FILE = 'stock_values.csv'
TREASURY_FILE = 't_bill_data.csv'

file_names = [INCOME_FILE, CASH_FLOW_FILE, BALANCE_SHEET_FILE, SHARES_FILE, STOCK_VALUE_FILE]


def _get_data(location, dirs):
    data = {}
    for stock in dirs:
        data_dir = location + stock
        s_files = [pd.read_csv(data_dir + '/' + fn) for fn in file_names]
        s2_files = [t.set_index(t.columns[0]) for t in s_files]
        df = functools.reduce(lambda base, f: base.join(f, how='outer'), s2_files)
    data['tbill'] = pd.read_csv(location + '/' + TREASURY_FILE)
    return data


def _calculate_free_cash_flow():
    pass


def _transform_to_trailing_12_months():
    pass


def _calculate_ratios():
    pass


def _calculate_growth_factors():
    pass


def build_model():
    path = 'C:/Users/Justin/PycharmProjects/equilibrium/data/'
    companies = ['apple']
    data = _get_data(path, companies)

    files = ['3month_tbills.xls', '10yr_tbills.xls']