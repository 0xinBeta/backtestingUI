import multiprocessing as mp
import vectorbt as vbt
from backtesting import Backtest, Strategy
from finta import TA
from ta.trend import adx

mp.set_start_method('fork')

symbol = "BTCUSDT"
timeframe = "15m"
start = "2 day ago UTC"
end = "now"
ema_short_len = 9
ema_mid_len = 21
ema_long_len = 50
adx_index = 20

def create_df(symbol, timeframe, start, end, ema_short_len, ema_mid_len, ema_long_len, adx_index):
    df = vbt.CCXTData.download(
        symbols=symbol,
        missing_index="drop",
        exchange="binanceusdm",
        timeframe= timeframe,
        start=start,
        end=end
    ).get()



    df['ema_short'] = TA.EMA(df, ema_short_len, 'close')
    df['ema_mid'] = TA.EMA(df, ema_mid_len, 'close')
    df['ema_long'] = TA.EMA(df, ema_long_len, 'close')
    df['SMMA200'] = TA.SMMA(df, period=200)

    # Identify crossovers between ema_short and ema_mid

    df['cross_above'] = (df['ema_short'] > df['ema_mid']) & (df['ema_short'
            ].shift(1) < df['ema_mid'].shift(1))
    df['cross_below'] = (df['ema_short'] < df['ema_mid']) & (df['ema_short'
            ].shift(1) > df['ema_mid'].shift(1))

    # Calculate additional technical indicators

    df['ADX'] = adx(df['High'], df['Low'], df['Close'])
    df['ATR'] = TA.ATR(df, 14)
    df['RSI'] = TA.RSI(df, period=14)

    # Determine long and short trading opportunities based on set conditions

    df['long'] = (df['Close'] > df['SMMA200']) & (df['ema_short']
            > df['SMMA200']) & (df['ema_mid'] > df['SMMA200']) & (df['RSI'
            ] < 75) & (df['ema_mid'] > df['ema_long']) & df['cross_above'] \
        & (df['ADX'] > adx_index) & (df['ema_long'] > df['SMMA200'])
    df['short'] = (df['Close'] < df['SMMA200']) & (df['ema_short']
            < df['SMMA200']) & (df['ema_mid'] < df['SMMA200']) & (df['RSI'
            ] > 20) & (df['ema_mid'] < df['ema_long']) & df['cross_below'] \
        & (df['ADX'] > adx_index) & (df['ema_long'] < df['SMMA200'])

    
    return df


df = create_df(symbol, timeframe, start, end, ema_short_len, ema_mid_len, ema_long_len, adx_index)

class qm_strat(Strategy):
    tp_m = 7
    sl_m = 4
    risk = 0.005

    def init(self):
        pass

    def next(self):
        buy_signal = self.data.long[-1]
        sell_signal = self.data.short[-1]
        price = self.data.Close[-1]
        atr = self.data.ATR[-1]
        tp_long = price + atr * self.tp_m
        sl_long = price - atr * self.sl_m
        tp_short = price - atr * self.tp_m
        sl_short = price + atr * self.tp_m

        distance_long = price - sl_long
        distance_short = sl_short - price

        cash = 100_000
        risk = self.risk
        
        risk_long = (cash * risk) / distance_long
        risk_short = (cash * risk) / distance_short

        pos_size_long = ((risk_long * price) / 125) / cash
        pos_size_short = ((risk_short * price) / 125) / cash
        


        if buy_signal:
            if not self.position:
                print(pos_size_long)
                self.buy(size=pos_size_long,sl=sl_long, tp=tp_long)
        elif sell_signal:
            if not self.position:
                print(pos_size_short)
                self.sell(size=pos_size_short,sl=sl_short, tp=tp_short)


# Initialize backtest with $100,000 cash
bt = Backtest(df, qm_strat, cash=100_000, margin=0.008)


# Run the backtest and generate the performance report
stats = bt.run()

# Plot the backtest results
bt.plot()

# Print the performance reports
print(stats)

stats = bt.optimize(tp_m=tp_m, sl_m=sl_m, risk=risk,
                                maximize='Win Rate [%]' and 'Return (Ann.) [%]', method='grid')