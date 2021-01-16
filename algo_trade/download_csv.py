from datetime import datetime
from datetime import timedelta
import sys
import requests
from algo_trade.constants import CSV_DATA_DIR

EPOCH = datetime.utcfromtimestamp(0)


def to_seconds(dt):
    return int((dt - EPOCH).total_seconds())


def run(_args):
    symbol = _args[0]
    if len(_args) == 1:
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=5 * 365)
    else:
        start_dt = datetime.fromisoformat(_args[1])
        end_dt = datetime.fromisoformat(_args[2])

    csv_url = "https://query1.finance.yahoo.com/v7/finance/download/{symbol}?period1={period1}&period2={" \
              "period2}&interval=1d&events=history&includeAdjustedClose=true".format(
        symbol=symbol,
        period1=to_seconds(start_dt),
        period2=to_seconds(end_dt))

    req = requests.get(csv_url)
    url_content = req.content

    csv_file = open('{csv_dir}/{symbol}.csv'.format(csv_dir=CSV_DATA_DIR, symbol=symbol), 'wb')

    csv_file.write(url_content)
    csv_file.close()


"""
Run command to download CSV for symbol during a time range:
    python download_csv.py GLD '2010-12-07 14:30:00' '2020-12-08 23:59:00'
    
If time range not specified, will look back five years.
"""
if __name__ == "__main__":
    args = sys.argv
    print(args)
    run(args[1:])
