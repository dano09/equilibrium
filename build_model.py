import pandas as pd
import functools
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

O_INCOME_FILE = 'income_statement.csv'
O_BALANCE_SHEET_FILE = 'balance_sheet.csv'
O_CASH_FLOW_FILE = 'cash_flow.csv'
O_SHARES_FILE = 'shares.csv'
O_STOCK_VALUE_FILE = 'stock_values.csv'
O_TREASURY_FILE = 't_bill_data.csv'

file_names = [O_INCOME_FILE, O_BALANCE_SHEET_FILE, O_CASH_FLOW_FILE, O_SHARES_FILE, O_STOCK_VALUE_FILE]


def _get_data(location, dirs):
    data = {}
    for stock in dirs:
        data_dir = location + stock
        s_files = [pd.read_csv(data_dir + '/' + fn) for fn in file_names]
        s2_files = [t.set_index(t.columns[0]) for t in s_files]
        df = functools.reduce(lambda base, f: base.join(f, how='outer'), s2_files)
        df.sort_index(ascending=False, inplace=True)
        data[stock] = df
    #data['tbill'] = pd.read_csv(location + '/' + O_TREASURY_FILE)
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


build_model()