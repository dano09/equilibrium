import pandas as pd
from datetime import datetime


def convert_index_names(date_string):
    """"
    Example:
    2017-04-01 -> 2017-06-01
    2017-01-01 -> 2017-03-01
    2016-10-01 -> 2016-12-01
    2016-07-01 -> 2016-09-01

    :return: datetime
    """
    month = date_string[5:7]
    quarter_end = int(month) + 2
    return datetime.strptime(date_string[:4] + str(quarter_end), '%Y%m').date()


def process_tbills(files):
    t_bills = []
    for data in files:
        data['observation_date'] = data['observation_date'].astype(str)
        data['observation_date'] = data.observation_date.str[:10]
        d = data.set_index('observation_date')
        indxs = d.index.values
        relabeled_indxs = {i: convert_index_names(str(i)) for i in indxs}
        d = d.rename(index=relabeled_indxs)
        t_bills.append(d)
    # str(data['observation_date'].values[0])[:10]
    #data['observation_date'].values[0].strftime('%Y-%m-%d')
    t_bill_data = t_bills[0].join(t_bills[1], how='outer')
    t_bill_data.sort_index(ascending=False, inplace=True)
    return t_bill_data


path = 'C:/Users/Justin/PycharmProjects/equilibrium/data/'
files = ['3month_tbills.xls', '10yr_tbills.xls']
excel_data = [pd.read_excel(path + file, header=10) for file in files]
result = process_tbills(excel_data)
result.to_csv('C:/Users/Justin/PycharmProjects/equilibrium/data/t_bill_data.csv')