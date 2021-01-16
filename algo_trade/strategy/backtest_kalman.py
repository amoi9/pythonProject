from algo_trade.constants import CSV_DATA_DIR
from algo_trade.strategy.kalman import *
from math import sqrt


def backtest(x, y, s1, s2):
    #############################################################
    # INPUT:
    # DataFrame of prices
    # s1: the symbol of contract one
    # s2: the symbol of contract two
    # x: the price series of contract one
    # y: the price series of contract two
    # OUTPUT:
    # df1['cum rets']: cumulative returns in pandas data frame
    # sharpe: Sharpe ratio
    # CAGR: Compound Annual Growth Rate

    # run regression (including Kalman Filter) to find hedge ratio and then create spread series
    df1 = pd.DataFrame({'x': x, 'y': y})
    df1.index = pd.to_datetime(df1.index)
    state_means = KalmanFilterRegression(KalmanFilterAverage(x), KalmanFilterAverage(y))

    df1['hr'] = - state_means[:, 0]
    df1['spread'] = df1.y + (df1.x * df1.hr)

    # calculate half life
    halflife = half_life(df1['spread'])

    # calculate z-score with window = half life period
    meanSpread = df1.spread.rolling(window=halflife).mean()
    stdSpread = df1.spread.rolling(window=halflife).std()
    df1['zScore'] = (df1.spread - meanSpread) / stdSpread

    ##############################################################
    # trading logic
    entryZscore = 2
    exitZscore = 0

    # set up num units long
    df1['long entry'] = ((df1.zScore < - entryZscore) & (df1.zScore.shift(1) > - entryZscore))
    df1['long exit'] = ((df1.zScore > - exitZscore) & (df1.zScore.shift(1) < - exitZscore))
    df1['num units long'] = np.nan
    df1.loc[df1['long entry'], 'num units long'] = 1
    df1.loc[df1['long exit'], 'num units long'] = 0
    df1['num units long'][0] = 0
    df1['num units long'] = df1['num units long'].fillna(method='pad')
    # set up num units short
    df1['short entry'] = ((df1.zScore > entryZscore) & (df1.zScore.shift(1) < entryZscore))
    df1['short exit'] = ((df1.zScore < exitZscore) & (df1.zScore.shift(1) > exitZscore))
    df1.loc[df1['short entry'], 'num units short'] = -1
    df1.loc[df1['short exit'], 'num units short'] = 0
    df1['num units short'][0] = 0
    df1['num units short'] = df1['num units short'].fillna(method='pad')

    df1['numUnits'] = df1['num units long'] + df1['num units short']
    df1['spread pct ch'] = (df1['spread'] - df1['spread'].shift(1)) / ((df1['x'] * abs(df1['hr'])) + df1['y'])
    df1['port rets'] = df1['spread pct ch'] * df1['numUnits'].shift(1)

    df1['cum rets'] = df1['port rets'].cumsum()
    df1['cum rets'] = df1['cum rets'] + 1

    ##############################################################

    try:
        sharpe = ((df1['port rets'].mean() / df1['port rets'].std()) * sqrt(252))
    except ZeroDivisionError:
        sharpe = 0.0

    ##############################################################
    start_val = 1
    end_val = df1['cum rets'].iat[-1]

    start_date = df1.iloc[0].name
    end_date = df1.iloc[-1].name

    days = (end_date - start_date).days

    CAGR = round(((float(end_val) / float(start_val)) ** (252.0 / days)) - 1, 4)

    df1[s1 + " " + s2] = df1['cum rets']

    return df1[s1 + " " + s2], sharpe, CAGR


if __name__ == '__main__':
    sym_x = 'EWA'
    sym_y = 'EWC'
    df_x = pd.read_csv('{}/{}.csv'.format(CSV_DATA_DIR, sym_x), header=0, parse_dates=True, sep=',', index_col=0)
    df_y = pd.read_csv('{}/{}.csv'.format(CSV_DATA_DIR, sym_y), header=0, parse_dates=True, sep=',', index_col=0)
    prince_col = 'Adj Close'
    rets, sharpe, CAGR = backtest(df_x[prince_col], df_y[prince_col], sym_x, sym_y)
    print("The pair {} and {} produced a Sharpe Ratio of {} and a CAGR of {}".format(sym_x, sym_y, round(sharpe, 2),
                                                                                     round(CAGR, 4)))
    rets.plot(figsize=(20, 15), legend=True)
    # plt.figure(figsize=(20, 15))
    # plt.legend()
    # plt.show(rets)
