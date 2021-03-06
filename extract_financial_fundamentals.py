import pandas as pd
import functools
from datetime import datetime

# pd.set_option('display.height', 1000)
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


# Input files from Bloomberg
INCOME_STATEMENT = 'Income - Adjusted'
BALANCE_SHEET = 'Bal Sheet - Standardized'
CASH_FLOW = 'Cash Flow - Standardized'
SHARES = 'Per Share'
STOCK_VALUE = 'Stock Value'

# Output data files we save after cleaning
O_INCOME_FILE = 'income_statement.csv'
O_BALANCE_SHEET_FILE = 'balance_sheet.csv'
O_CASH_FLOW_FILE = 'cash_flow.csv'
O_SHARES_FILE = 'shares.csv'
O_STOCK_VALUE_FILE = 'stock_values.csv'


INCOME_STATEMENT_METRICS = ['SALES_REV_TURN', 'IS_COGS_TO_FE_AND_PP_AND_G', 'IS_OPERATING_EXPN', 'EBITDA', 'IS_INC_TAX_EXP']

# CHANGE IN WC = Total Current Assets - Total Current Liabilities,
# CASH INVESTMENTS = (Cash, Cash Equivalents & STI) + (LT Investments & Receivables)
# DEBT = ST DEBT + LT Debt
BALANCE_SHEET_METRICS = ['BS_CUR_ASSET_REPORT', 'BS_CUR_LIAB', 'C&CE_AND_STI_DETAILED', 'BS_LT_INVEST', 'BS_ST_BORROW',
                         'BS_LT_BORROW', 'MINORITY_NONCONTROLLING_INTEREST', 'BS_PFD_EQTY_&_HYBRID_CPTL']

# Change in Fixed & Intang -> CHG_IN_FXD_&_INTANG_AST_DETAILED
# Free Cash Flow -> CF_FREE_CASH_FLOW
CASH_FLOW_METRICS = ['CHG_IN_FXD_&_INTANG_AST_DETAILED', 'CF_FREE_CASH_FLOW']

# Diluted Weighted Avg Shares -> IS_SH_FOR_DILUTED_EPS
SHARES_METRICS = ['IS_SH_FOR_DILUTED_EPS']

#  Last Price -> PX_LAST
STOCK_VALUE_METRICS = ['PX_LAST']


def convert_index_names(date_string):
    """"
    Example:
    Q4 2017 -> 2017-9
    Q3 2017 -> 2017-6
    Q2 2017 -> 2017-3
    Q1 2017 -> 2016-12

    :return: datetime
    """

    if date_string[1] == '1':
        str_date = str(int(date_string[3:]) - 1) + '-12'
        # ex: '1989-12'
        # we need it as a date object since we want to sort dataframe based on time
        return datetime.strptime(str_date, '%Y-%m').date()
    elif date_string[1] == '2':
        return datetime.strptime(date_string[3:] + '-3', '%Y-%m').date()
    elif date_string[1] == '3':
        return datetime.strptime(date_string[3:] + '-6', '%Y-%m').date()
    elif date_string[1] == '4':
        return datetime.strptime(date_string[3:] + '-9', '%Y-%m').date()
    else:
        return 'error, cannot parse {}'.format(date_string)


def process_file(data_file, required_metrics):
    # Fundamentals to code
    # not used directly but useful to understand what column names are
    metric_mapping = data_file[['In Millions of USD except Per Share', 'Unnamed: 1']]

    # Quarters to exact dates
    # not used currently, but may be needed in analysis
    date_mapping = data_file.iloc[0]

    # Remove fundamentals string
    data = data_file.drop(data_file.columns[0], axis=1)

    data.drop(0, inplace=True)
    data.rename(columns={'Unnamed: 1': 'METRIC'}, inplace=True)

    data.set_index('METRIC', inplace=True)

    data = data[data.columns.drop(list(data.filter(regex='Est|Current')))]
    data = data.transpose()

    data = data[required_metrics]

    indxs = data.index.values
    relabeled_indxs = {i: convert_index_names(i) for i in indxs}
    data = data.rename(index=relabeled_indxs)

    return data


def post_merge_cleaning(df):
    df.sort_index(ascending=False, inplace=True)
    df = df.replace({'—': 0})
    return df[~df.index.duplicated(keep='first')]


def process_income_statement(income_statement_data):
    income_statement_data['OPEX'] = income_statement_data['IS_COGS_TO_FE_AND_PP_AND_G'] + income_statement_data['IS_OPERATING_EXPN']
    income_statement_data.rename(columns={'SALES_REV_TURN': 'REVENUE', 'IS_INC_TAX_EXP': 'TAX_EXPENSE'}, inplace=True)
    #income_statement_data.drop(['IS_COGS_TO_FE_AND_PP_AND_G', 'IS_OPERATING_EXPN'], axis=1, inplace=True)
    return income_statement_data[['REVENUE', 'OPEX', 'EBITDA', 'TAX_EXPENSE']]


def process_balance_sheet(balance_sheet_data):
    balance_sheet_data['WORKING_CAP'] = balance_sheet_data['BS_CUR_ASSET_REPORT'] - balance_sheet_data['BS_CUR_LIAB']
    balance_sheet_data['CHNG_WC'] = balance_sheet_data['WORKING_CAP'] - balance_sheet_data['WORKING_CAP'].shift(-1)
    balance_sheet_data['CASH_INVESTMENTS'] = balance_sheet_data['C&CE_AND_STI_DETAILED'] + balance_sheet_data['BS_LT_INVEST']
    balance_sheet_data['DEBT'] = balance_sheet_data['BS_ST_BORROW'] + balance_sheet_data['BS_LT_BORROW']
    balance_sheet_data.rename(columns={'MINORITY_NONCONTROLLING_INTEREST': 'NON_CON_INT', 'BS_PFD_EQTY_&_HYBRID_CPTL': 'PREF_SEC'}, inplace=True)
    return balance_sheet_data[['CHNG_WC', 'CASH_INVESTMENTS', 'DEBT', 'NON_CON_INT', 'PREF_SEC']]


def process_cash_flow(cash_flow_data):
    cash_flow_data.rename(columns={'CHG_IN_FXD_&_INTANG_AST_DETAILED': 'CAPEX', 'CF_FREE_CASH_FLOW': 'FREE_CASH_FLOW'},inplace=True)
    # Rightfully negative in the context of Bloomberg, however we want to simply the free cash flow calculation so
    # making all factors positive that are subtracted from EBITDA
    cash_flow_data['CAPEX'] = cash_flow_data['CAPEX'] * -1
    return cash_flow_data


def process_shares(shares_data):
    shares_data.rename(columns={'IS_SH_FOR_DILUTED_EPS': 'WADS'}, inplace=True)
    return shares_data


def process_stock_values(stock_values_data):
    stock_values_data.rename(columns={'PX_LAST': 'PRICE'}, inplace=True)
    return stock_values_data


def parse_data_for_a_company(files, file_path):
    # Income Parameters:
    sheet_names = [INCOME_STATEMENT, BALANCE_SHEET, CASH_FLOW, SHARES, STOCK_VALUE]
    excel_data = [pd.read_excel(file_path + file, sheet_name=sheet_names, header=3) for file in files]

    '''
    data is a list of OrderedDicts (key-value pairs)
    each OrderedDict has a key:value pair
    Key: one of the values in sheet_names (example: INCOME_STATEMENT, which is 'Income - Adjusted')
    Value: dataframe of the data  

    #####  First file for example (index starts at 0) #####

    data[0].keys()
    odict_keys(['Income - Adjusted', 'Bal Sheet - Standardized', 'Cash Flow - Standardized', 'Per Share', 'Stock Value'])

    #######################################################

    ##### Income statement for the first file #############

    data[0][INCOME_STATEMENT].head()
      In Millions of USD except Per Share                  Unnamed: 1     Q1 1990     Q2 1990     Q3 1990     Q4 1990     Q1 1991     Q2 1991     Q3 1991     Q4 1991     Q1 1992     Q2 1992     Q3 1992     Q4 1992     Q1 1993     Q2 1993     Q3 1993     Q4 1993     Q1 1994     Q2 1994     Q3 1994     Q4 1994     Q1 1995     Q2 1995     Q3 1995     Q4 1995     Q1 1996     Q2 1996     Q3 1996     Q4 1996     Q1 1997     Q2 1997     Q3 1997     Q4 1997     Q1 1998     Q2 1998     Q3 1998     Q4 1998     Q1 1999
    0                     3 Months Ending                         NaN  12/29/1989  03/30/1990  06/29/1990  09/28/1990  12/28/1990  03/29/1991  06/28/1991  09/27/1991  12/27/1991  03/27/1992  06/26/1992  09/25/1992  12/25/1992  03/26/1993  06/25/1993  09/24/1993  12/31/1993  03/31/1994  07/01/1994  09/30/1994  12/30/1994  03/31/1995  06/30/1995  09/29/1995  12/29/1995  03/29/1996  06/28/1996  09/27/1996  12/27/1996  03/28/1997  06/27/1997  09/26/1997  12/26/1997  03/27/1998  06/26/1998  09/25/1998  12/26/1998
    1                             Revenue              SALES_REV_TURN     1493.38      1346.2     1364.76     1354.09     1675.51     1597.68      1528.6     1507.06     1862.61     1716.03     1740.17     1767.73     2000.29     1973.89     1861.98     2140.79     2468.85      2076.7     2149.91     2493.29        2832        2652        2575        3003        3148        2185        2179        2321        2129        1601        1737        1614        1578        1405        1402        1556        1710
    2                   - Cost of Revenue  IS_COGS_TO_FE_AND_PP_AND_G      716.21      609.59     628.188     652.235     814.862     818.607     828.354     852.295     1049.33     960.496     968.844     1012.67     1189.37     1213.13     1255.97     1590.36     1876.83     1577.64     1576.04     1814.41        2018        1957        1847        2382        2673        2606        1776        1810        1732        1298        1389        1294        1225        1056        1042        1139        1228
    3                        Gross Profit                GROSS_PROFIT     777.173     736.612     736.572     701.855     860.644     779.071      700.25     654.766     813.281     755.529     771.327     755.068     810.925     760.763     606.004     550.428     592.024     499.064     573.872     678.873         814         695         728         621         475        -421         403         511         397         303         348         320         353         349         360         417         482
    4                - Operating Expenses           IS_OPERATING_EXPN     587.089      537.44     554.331      561.34     632.252     592.526     565.048     533.513     550.627     545.124     570.266      623.38      570.14     591.697     591.814     543.275     527.317     464.329     341.451     615.317         547         529         572         549         594         554         519         505         521         489         408         353         313         298         292         308         355

    #######################################################
    '''

    income_statement_data = [time_period[INCOME_STATEMENT] for time_period in excel_data]
    income_statement = functools.reduce(lambda base, incom: base.append(incom),
                                        [process_file(inc_file, INCOME_STATEMENT_METRICS) for inc_file in income_statement_data])

    income_statement = post_merge_cleaning(income_statement)
    i_s = process_income_statement(income_statement)

    balance_sheet_data = [time_period[BALANCE_SHEET] for time_period in excel_data]
    balance_sheet = functools.reduce(lambda base, bs: base.append(bs),
                                     [process_file(bal_sht_file, BALANCE_SHEET_METRICS) for bal_sht_file in balance_sheet_data])

    balance_sheet = post_merge_cleaning(balance_sheet)
    b_s = process_balance_sheet(balance_sheet)

    cash_flow_data = [time_period[CASH_FLOW] for time_period in excel_data]
    cash_flow = functools.reduce(lambda base, cf: base.append(cf),
                                 [process_file(chs_flow_file, CASH_FLOW_METRICS) for chs_flow_file in cash_flow_data])

    cash_flow = post_merge_cleaning(cash_flow)
    c_f = process_cash_flow(cash_flow)

    shares_data = [time_period[SHARES] for time_period in excel_data]
    shares = functools.reduce(lambda base, shs: base.append(shs),
                              [process_file(shares_file, SHARES_METRICS) for shares_file in shares_data])

    shares = post_merge_cleaning(shares)
    shs = process_shares(shares)

    stock_value_data = [time_period[STOCK_VALUE] for time_period in excel_data]
    stock_value = functools.reduce(lambda base, sv: base.append(sv),
                                   [process_file(stock_file, STOCK_VALUE_METRICS) for stock_file in stock_value_data])

    stock_value = post_merge_cleaning(stock_value)
    s_v = process_stock_values(stock_value)

    return i_s, b_s, c_f, shs, s_v


def save_files(path, data_files):
    data_files[0].to_csv(path + O_INCOME_FILE, mode='w', index_label='DATE')
    data_files[1].to_csv(path + O_BALANCE_SHEET_FILE, mode='w', index_label='DATE')
    data_files[2].to_csv(path + O_CASH_FLOW_FILE, mode='w', index_label='DATE')
    data_files[3].to_csv(path + O_SHARES_FILE, mode='w', index_label='DATE')
    data_files[4].to_csv(path + O_STOCK_VALUE_FILE, mode='w', index_label='DATE')


if __name__ == "__main__":
    # Read Data
    path = 'C:/Users/Justin/PycharmProjects/equilibrium/data/'
    data_set = {'amazon': ['AMZ_1997Q1-1998Q3.xlsx', 'AMZ_1998Q4-2008Q4.xlsx', 'AMZ_2009-2018.xlsx'],
                'apple': ['appl_09q2_18q3.xlsx', 'appl_90q1_99q1.xlsx', 'appl_99q2_09q1.xlsx'],
                'boeing': ['Boeing_08Q3_18Q2.xlsx', 'Boeing_90q1_98q2.xlsx', 'Boeing_98q3_08q2.xlsx'],
                'coke': ['COKE_08Q4_18Q3.xlsx', 'COKE_90Q1_98Q3.xlsx', 'COKE_98Q4_08Q3.xlsx'],
                'comcast': ['Comcast_09Q1_18Q2.xlsx', 'Comcast_90Q1_98Q3.xlsx', 'Comcast_98Q4_08Q4.xlsx'],
                'exxon': ['Exxon_1990Q1-1998Q2.xlsx', 'Exxon_1998Q3-2008Q2.xlsx', 'Exxon_2008Q3-2018Q2.xlsx'],
                'ibm': ['IBM_08Q4_18Q3.xlsx', 'IBM_88Q4_98Q3.xlsx', 'IBM_98Q4_08Q3.xlsx'],
                'netflix': ['netflix_02q1_09q1.xlsx', 'netflix_09q2_18q3.xlsx'],
                'pg': ['PG_08Q4_18Q3.xlsx', 'PG_90Q1_98Q3.xlsx', 'PG_98Q4_08Q3.xlsx']}

    for company_name, files in data_set.items():
        print('Processing company: {} with files: {}'.format(company_name, files))
        path_directory = path + company_name + '/'
        results = parse_data_for_a_company(files, path_directory)
        save_files(path_directory, results)
