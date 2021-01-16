from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))

import pandas as pd
from strategy.golden_cross import GoldenCross

import argparse
import datetime

# The above could be sent to an independent module
import backtrader as bt


# python algo_trade/run/golden_cross.py --data0 SPY-STK-SMART-USD --live --resample --timeframe Days --compression 1 --fromdate 2020-02-01 --port 7497 --slow=50 --fast=20
def run_live(cerebro, args):
    storekwargs = dict(
        host=args.host, port=args.port,
        clientId=args.clientId, timeoffset=not args.no_timeoffset,
        reconnect=args.reconnect, timeout=args.timeout,
        notifyall=args.notifyall, _debug=args.debug
    )

    if args.usestore:
        ibstore = bt.stores.IBStore(**storekwargs)

    if args.broker:
        if args.usestore:
            broker = ibstore.getbroker()
        else:
            broker = bt.brokers.IBBroker(**storekwargs)

        cerebro.setbroker(broker)

    timeframe = bt.TimeFrame.TFrame(args.timeframe)
    # Manage data1 parameters
    tf1 = args.timeframe1
    tf1 = bt.TimeFrame.TFrame(tf1) if tf1 is not None else timeframe
    cp1 = args.compression1
    cp1 = cp1 if cp1 is not None else args.compression

    if args.resample or args.replay:
        datatf = datatf1 = bt.TimeFrame.Ticks
        datacomp = datacomp1 = 1
    else:
        datatf = timeframe
        datacomp = args.compression
        datatf1 = tf1
        datacomp1 = cp1

    fromdate = None
    if args.fromdate:
        dtformat = '%Y-%m-%d' + ('T%H:%M:%S' * ('T' in args.fromdate))
        fromdate = datetime.datetime.strptime(args.fromdate, dtformat)

    IBDataFactory = ibstore.getdata if args.usestore else bt.feeds.IBData

    datakwargs = dict(
        timeframe=datatf, compression=datacomp,
        historical=args.historical, fromdate=fromdate,
        rtbar=args.rtbar,
        qcheck=args.qcheck,
        what=args.what,
        backfill_start=not args.no_backfill_start,
        backfill=not args.no_backfill,
        latethrough=args.latethrough,
        tz=args.timezone
    )

    if not args.usestore and not args.broker:  # neither store nor broker
        datakwargs.update(storekwargs)  # pass the store args over the data

    data0 = IBDataFactory(dataname=args.data0, **datakwargs)

    data1 = None
    if args.data1 is not None:
        if args.data1 != args.data0:
            datakwargs['timeframe'] = datatf1
            datakwargs['compression'] = datacomp1
            data1 = IBDataFactory(dataname=args.data1, **datakwargs)
        else:
            data1 = data0

    rekwargs = dict(
        timeframe=timeframe, compression=args.compression,
        bar2edge=not args.no_bar2edge,
        adjbartime=not args.no_adjbartime,
        rightedge=not args.no_rightedge,
        takelate=not args.no_takelate,
    )

    if args.replay:
        cerebro.replaydata(data0, **rekwargs)

        if data1 is not None:
            rekwargs['timeframe'] = tf1
            rekwargs['compression'] = cp1
            cerebro.replaydata(data1, **rekwargs)

    elif args.resample:
        cerebro.resampledata(data0, **rekwargs)

        if data1 is not None:
            rekwargs['timeframe'] = tf1
            rekwargs['compression'] = cp1
            cerebro.resampledata(data1, **rekwargs)

    else:
        cerebro.adddata(data0)
        if data1 is not None:
            cerebro.adddata(data1)

    # Live data ... avoid long data accumulation by switching to "exactbars"
    cerebro.run(exactbars=args.exactbars)

    if args.plot and args.exactbars < 1:  # plot if possible
        cerebro.plot()


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Test Interactive Brokers integration')

    parser.add_argument('--live', default=False,
                        required=False, action='store_true',
                        help='Use live data instead of historical data')

    parser.add_argument('--fast', default=50, type=int,
                        required=False, action='store',
                        help='Fast SMA')

    parser.add_argument('--slow', default=200, type=int,
                        required=False, action='store',
                        help='Slow SMA')

    parser.add_argument('--exactbars', default=1, type=int,
                        required=False, action='store',
                        help='exactbars level, use 0/-1/-2 to enable plotting')

    parser.add_argument('--plot',
                        required=False, action='store_true',
                        help='Plot if possible')

    parser.add_argument('--stopafter', default=0, type=int,
                        required=False, action='store',
                        help='Stop after x lines of LIVE data')

    parser.add_argument('--usestore',
                        required=False, action='store_true',
                        help='Use the store pattern')

    parser.add_argument('--notifyall',
                        required=False, action='store_true',
                        help='Notify all messages to strategy as store notifs')

    parser.add_argument('--debug',
                        required=False, action='store_true',
                        help='Display all info received form IB')

    parser.add_argument('--host', default='127.0.0.1',
                        required=False, action='store',
                        help='Host for the Interactive Brokers TWS Connection')

    parser.add_argument('--qcheck', default=0.5, type=float,
                        required=False, action='store',
                        help=('Timeout for periodic '
                              'notification/resampling/replaying check'))

    parser.add_argument('--port', default=7496, type=int,
                        required=False, action='store',
                        help='Port for the Interactive Brokers TWS Connection')

    parser.add_argument('--clientId', default=None, type=int,
                        required=False, action='store',
                        help='Client Id to connect to TWS (default: random)')

    parser.add_argument('--no-timeoffset',
                        required=False, action='store_true',
                        help=('Do not Use TWS/System time offset for non '
                              'timestamped prices and to align resampling'))

    parser.add_argument('--reconnect', default=3, type=int,
                        required=False, action='store',
                        help='Number of recconnection attempts to TWS')

    parser.add_argument('--timeout', default=3.0, type=float,
                        required=False, action='store',
                        help='Timeout between reconnection attempts to TWS')

    parser.add_argument('--data0', default=None,
                        required=True, action='store',
                        help='data 0 into the system')

    parser.add_argument('--data1', default=None,
                        required=False, action='store',
                        help='data 1 into the system')

    parser.add_argument('--timezone', default=None,
                        required=False, action='store',
                        help='timezone to get time output into (pytz names)')

    parser.add_argument('--what', default=None,
                        required=False, action='store',
                        help='specific price type for historical requests')

    parser.add_argument('--no-backfill_start',
                        required=False, action='store_true',
                        help='Disable backfilling at the start')

    parser.add_argument('--latethrough',
                        required=False, action='store_true',
                        help=('if resampling replaying, adjusting time '
                              'and disabling time offset, let late samples '
                              'through'))

    parser.add_argument('--no-backfill',
                        required=False, action='store_true',
                        help='Disable backfilling after a disconnection')

    parser.add_argument('--rtbar', default=False,
                        required=False, action='store_true',
                        help='Use 5 seconds real time bar updates if possible')

    parser.add_argument('--historical',
                        required=False, action='store_true',
                        help='do only historical download')

    parser.add_argument('--fromdate',
                        required=False, action='store',
                        help=('Starting date for historical download '
                              'with format: YYYY-MM-DD[THH:MM:SS]'))

    parser.add_argument('--smaperiod', default=5, type=int,
                        required=False, action='store',
                        help='Period to apply to the Simple Moving Average')

    pgroup = parser.add_mutually_exclusive_group(required=False)

    pgroup.add_argument('--replay',
                        required=False, action='store_true',
                        help='replay to chosen timeframe')

    pgroup.add_argument('--resample',
                        required=False, action='store_true',
                        help='resample to chosen timeframe')

    parser.add_argument('--timeframe', default=bt.TimeFrame.Names[0],
                        choices=bt.TimeFrame.Names,
                        required=False, action='store',
                        help='TimeFrame for Resample/Replay')

    parser.add_argument('--compression', default=1, type=int,
                        required=False, action='store',
                        help='Compression for Resample/Replay')

    parser.add_argument('--timeframe1', default=None,
                        choices=bt.TimeFrame.Names,
                        required=False, action='store',
                        help='TimeFrame for Resample/Replay - Data1')

    parser.add_argument('--compression1', default=None, type=int,
                        required=False, action='store',
                        help='Compression for Resample/Replay - Data1')

    parser.add_argument('--no-takelate',
                        required=False, action='store_true',
                        help=('resample/replay, do not accept late samples '
                              'in new bar if the data source let them through '
                              '(latethrough)'))

    parser.add_argument('--no-bar2edge',
                        required=False, action='store_true',
                        help='no bar2edge for resample/replay')

    parser.add_argument('--no-adjbartime',
                        required=False, action='store_true',
                        help='no adjbartime for resample/replay')

    parser.add_argument('--no-rightedge',
                        required=False, action='store_true',
                        help='no rightedge for resample/replay')

    parser.add_argument('--broker',
                        required=False, action='store_true',
                        help='Use IB as broker')

    parser.add_argument('--trade',
                        required=False, action='store_true',
                        help='Do Sample Buy/Sell operations')

    parser.add_argument('--donotsell',
                        required=False, action='store_true',
                        help='Do not sell after a buy')

    parser.add_argument('--exectype', default=bt.Order.ExecTypes[0],
                        choices=bt.Order.ExecTypes,
                        required=False, action='store',
                        help='Execution to Use when opening position')

    parser.add_argument('--stake', default=10, type=int,
                        required=False, action='store',
                        help='Stake to use in buy operations')

    parser.add_argument('--valid', default=None, type=int,
                        required=False, action='store',
                        help='Seconds to keep the order alive (0 means DAY)')

    pgroup = parser.add_mutually_exclusive_group(required=False)
    pgroup.add_argument('--stoptrail',
                        required=False, action='store_true',
                        help='Issue a stoptraillimit after buy( do not sell')

    pgroup.add_argument('--traillimit',
                        required=False, action='store_true',
                        help='Issue a stoptrail after buying (do not sell')

    pgroup.add_argument('--oca',
                        required=False, action='store_true',
                        help='Test oca by putting 2 orders in a group')

    pgroup.add_argument('--bracket',
                        required=False, action='store_true',
                        help='Test bracket orders by issuing high/low sides')

    pgroup = parser.add_mutually_exclusive_group(required=False)
    pgroup.add_argument('--trailamount', default=None, type=float,
                        required=False, action='store',
                        help='trailamount for StopTrail order')

    pgroup.add_argument('--trailpercent', default=None, type=float,
                        required=False, action='store',
                        help='trailpercent for StopTrail order')

    parser.add_argument('--limitoffset', default=None, type=float,
                        required=False, action='store',
                        help='limitoffset for StopTrailLimit orders')

    parser.add_argument('--cancel', default=0, type=int,
                        required=False, action='store',
                        help=('Cancel a buy order after n bars in operation,'
                              ' to be combined with orders like Limit'))

    return parser.parse_args()


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    args = parse_args()
    cerebro.addstrategy(
        GoldenCross,
        fast=args.fast,
        slow=args.slow)

    if args.live:
        run_live(cerebro, args)
    else:
        cerebro.broker.setcash(100000)

        spy_prices = pd.read_csv(
            '/Users/qi/PycharmProjects/pythonProject/algo_trade/data/SPY.csv',
            index_col='Date',
            parse_dates=True)
        feed = bt.feeds.PandasData(dataname=spy_prices)
        cerebro.adddata(feed)
        cerebro.run()
        cerebro.plot()
