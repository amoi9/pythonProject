# import requests
# import csv
# from datetime import datetime
import pandas as pd
from algo_trade.johansen import coint_johansen


# def fetch_daily_adjusted(symbol):
#     url = "https://alpha-vantage.p.rapidapi.com/query"
#     querystring = {"function": "TIME_SERIES_DAILY_ADJUSTED", "symbol": symbol, "outputsize": "compact",
#                    "datatype": "csv"}
#     headers = {
#         'x-rapidapi-key': "6e73a64168mshac6de5c58d04104p1f42f5jsnc6a5148414cc",
#         'x-rapidapi-host': "alpha-vantage.p.rapidapi.com"
#     }
#     response = requests.request("GET", url, headers=headers, params=querystring)
#     return response.content.decode('utf-8')
#
#
# def parse_csv(csv_content):
#     cr = csv.reader(csv_content.splitlines(), delimiter=',')
#     lines = list(cr)
#     # csv_header = ['timestamp', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume', 'dividend_amount',
#     # 'split_coefficient']
#     header = lines[0]
#     for i in range(1, len(lines)):
#         row = lines[i]
#         str_timestamp = row[header.index('timestamp')]
#         element = datetime.strptime(str_timestamp, "%Y-%m-%d")
#         timestamp = datetime.timestamp(element)


def fetch_daily_adj_csv(symbol):
    return 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={' \
           '}&datatype=csv&apikey=6e73a64168mshac6de5c58d04104p1f42f5jsnc6a5148414cc'.format(symbol)


ewa = fetch_daily_adj_csv('EWA')
ewc = fetch_daily_adj_csv('EWC')
df_ewa = pd.read_csv(ewa)
df_ewc = pd.read_csv(ewc)
df = pd.DataFrame({'x': df_ewa['close'], 'y': df_ewc['close']})
result = coint_johansen(df, 0, 1)
