import pandas as pd
import functools
import numpy as np
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

O_INCOME_FILE = 'income_statement.csv'
O_BALANCE_SHEET_FILE = 'balance_sheet.csv'
O_CASH_FLOW_FILE = 'cash_flow.csv'
O_SHARES_FILE = 'shares.csv'
O_STOCK_VALUE_FILE = 'stock_values.csv'
O_TREASURY_FILE = 't_bill_data.csv'
file_names = [O_INCOME_FILE, O_BALANCE_SHEET_FILE, O_CASH_FLOW_FILE, O_SHARES_FILE, O_STOCK_VALUE_FILE]
FACTOR_INPUT_COLS = ['REVENUE', 'OPEX', 'EBITDA', 'TAX_EXPENSE', 'CAPEX', 'CHNG_WC']
VALUTION_INPUT_COLS = ['CASH_INVESTMENTS', 'DEBT', 'PREF_SEC', 'NON_CON_INT', 'WADS', 'PRICE']
PATH = 'C:/Users/Justin/PycharmProjects/equilibrium/data/'

def _get_data(location, directory):
    data_dir = location + directory
    s_files = [pd.read_csv(data_dir + '/' + fn) for fn in file_names]
    s2_files = [t.set_index(t.columns[0]) for t in s_files]
    df = functools.reduce(lambda base, f: base.join(f, how='outer'), s2_files)
    df.sort_index(ascending=False, inplace=True)
    tbill_data = pd.read_csv(location + '/' + O_TREASURY_FILE)
    return df, tbill_data


def _calculate_free_cash_flow(df):
    # Calculate FREE_CASH_FLOW
    df['C_FREE_CASH_FLOW'] = df['EBITDA'] - df['TAX_EXPENSE'] - df['CAPEX'] - df['CHNG_WC']
    return df


def _transform_to_trailing_12_months(df):
    # Trailing 12 months (TTM) by taking T-1, T-2, T-3, T-4
    return df.apply(lambda x: x.shift(-1) + x.shift(-2) + x.shift(-3) + x.shift(-4))


def _calculate_margins(df):
    df['EBITDA_MARGIN'] = df.EBITDA / df.REVENUE
    # want EBITDA Expense Margin (to avoid dividing by zeros)
    # EBITDA expense margin = (REVENUE - EBITDA) / REVENUE
    # Need to verify formula
    df['EBITDA_EXPENSE_MARGIN'] = (df.REVENUE - df.EBITDA) / df.REVENUE

    df['TAX_EXPENSE_MARGIN'] = df.TAX_EXPENSE / df.REVENUE
    df['CAPEX_MARGIN'] = df.CAPEX / df.REVENUE
    df['CHNG_WC_MARGIN'] = df.CHNG_WC / df.REVENUE
    return df


def _calculate_growth_rates(df):
    #   Calculate Growth Factors
    #   pct_change(-1)                     - Since descending in time use -1
    #   replace([np.inf, -np.inf], np.nan) - Handles cases when margin is zero
    #   fillna(0)                          - Converts all NaN to zero
    df['REVENUE_GROWTH'] = df.REVENUE.pct_change(-1).replace([np.inf, -np.inf], np.nan).fillna(0)
    df['EBITDA_GROWTH'] = df.EBITDA_EXPENSE_MARGIN.pct_change(-1).replace([np.inf, -np.inf], np.nan).fillna(0)
    df['CAPEX_GROWTH'] = df.CAPEX_MARGIN.pct_change(-1).replace([np.inf, -np.inf], np.nan).fillna(0)
    return df


def calculate_factors(df, tbill_data):
    """
    Factors:
    1.  Revenue                             REVENUE
    2.  EBITDA Margin                       EBITDA_MARGIN
    3.  Tax Margin                          TAX_EXPENSE_MARGIN
    4.  CAPEX Margin                        CAPEX_MARGIN
    5.  Change in working Capital Margin    CHNG_WC_MARGIN
    6.  Revenue Growth                      REVENUE_GROWTH
    7.  EBITDA Expense margin Growth        EBITDA_GROWTH
    8.  CAPEX Growth                        CAPEX_GROWTH
    9.  Three-month US Treasury             TB3M
    10. Ten-year US Treasury                TB10YR

    :param
        df - DataFrame : financial statement metrics in one dataframe
            ['REVENUE', 'OPEX', 'EBITDA', 'TAX_EXPENSE', 'CHNG_WC']

        tbill_data - DataFrame : Treasury Data
            ['observation_date', 'TB3MS', 'DGS10']

    :return: DataFrame
            ['REVENUE', 'EBITDA_MARGIN', 'TAX_EXPENSE_MARGIN', 'CAPEX_MARGIN', 'CHNG_WC_MARGIN',
             'REVENUE_GROWTH', 'EBITDA_GROWTH', 'CAPEX_GROWTH', 'TB3M', 'TB10YR']
    """

    df.loc[df['EBITDA'] < 0, 'EBITDA'] = 0

    df = _calculate_free_cash_flow(df)
    df = _transform_to_trailing_12_months(df)
    df = _calculate_margins(df)
    df = _calculate_growth_rates(df)
    model_factors = df[['REVENUE', 'EBITDA_MARGIN', 'TAX_EXPENSE_MARGIN', 'CAPEX_MARGIN', 'CHNG_WC_MARGIN', 'REVENUE_GROWTH', 'EBITDA_GROWTH', 'CAPEX_GROWTH']]

    tbill_data.set_index('observation_date', inplace=True)
    tbill_data = tbill_data.rename(index=str, columns={'TB3MS': 'TB3M', 'DGS10': 'TB10YR'})

    model_factors = model_factors.join(tbill_data, how='inner')
    return model_factors


def _calculate_noa(df):
    """
    NOA = C + I - D - PS - NCI
    Non-Operating Assets (NOA) = Cash + Investments - Debt - Preferred securities - Non-controlling interests
    :param df:
    :return: df
    """
    df['NON_OP_ASSETS'] = df.CASH_INVESTMENTS - df.DEBT - df.PREF_SEC - df.NON_CON_INT


def _calculate_mc(df):
    """
    MC = SP * WAD
    Quarterly average Market Capitalization (MC) in period (n) = Stock Price in period (n) * Weighted Average Diluted Shares (WADS) in period (n-1)
    :param df:
    :return: df
    """
    df['MARKET_CAP'] = df.PRICE * df.WADS.shift(-1)


def _calculate_fv(df):
    """
    FV = MC - NOA
    Firm value in period (n) = Market Capitalization in period (n) - Non-operating assets in period (n-1)
    :param df:
    :return:d f
    """
    df['FIRM_VALUE'] = df.MARKET_CAP - df.NON_OP_ASSETS.shift(-1)


def calculate_valuation(df):
    """
    Determine Firm Value based on the following quarterly metrics:
    1. Cash                             CASH_INVESTMENTS
    2. Investments                      CASH_INVESTMENTS
    3. Debt                             DEBT
    4. Preferred Securities             PREF_SEC
    5. Non-controlling interests        NON_CON_INT
    6. Weighted Average Diluted Shares  WADS
    7. Closing Stock Price              PRICE

    :param df
        columns: ['CASH_INVESTMENTS', 'DEBT', 'PREF_SEC', 'NON_CON_INT', 'WADS', 'PRICE']
    :return: df
        columns: ['FIRM_VALUE', 'NON_OP_ASSETS', 'WADS', 'PRICE']
    """
    _calculate_noa(df)
    _calculate_mc(df)
    _calculate_fv(df)
    return df[['FIRM_VALUE', 'NON_OP_ASSETS', 'WADS', 'PRICE']]


def _model_cleanup(model):
    pass
    #TODO Maybe need maybe not


def build_model(company):
    stock_data, tbill_data = _get_data(PATH, company)
    factors = calculate_factors(stock_data[FACTOR_INPUT_COLS], tbill_data)
    valuation = calculate_valuation(stock_data[VALUTION_INPUT_COLS])
    model = factors.join(valuation, how='inner')
    return model


def save_model(file_dir, data):
    data.to_csv(PATH + file_dir + '/model.csv', mode='w', index_label='DATE')


if __name__ == "__main__":
    companies = ['apple', 'amazon', 'boeing', 'coke', 'comcast', 'exxon', 'ibm', 'netflix', 'pg']
    for company in companies:
        print('Processing : {}'.format(company))
        model = build_model(company)
        save_model(company, model)
