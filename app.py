import streamlit as st
import multiprocessing as mp
import vectorbt as vbt
from backtesting import Backtest, Strategy
from finta import TA
from ta.trend import adx


def create_df(symbol, timeframe, start, end, ema_short_len, ema_mid_len, ema_long_len, adx_index):
    df = vbt.CCXTData.download(
        symbols=symbol,
        missing_index="drop",
        exchange="binanceusdm",
        timeframe=timeframe,
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
        sl_short = price + atr * self.sl_m

        distance_long = price - sl_long
        distance_short = sl_short - price

        cash = 100_000
        risk_long = (cash * self.risk) / distance_long
        risk_short = (cash * self.risk) / distance_short

        pos_size_long = ((risk_long * price) / 125) / cash
        pos_size_short = ((risk_short * price) / 125) / cash

        if buy_signal:
            if not self.position:
                self.buy(size=pos_size_long, sl=sl_long, tp=tp_long)
        elif sell_signal:
            if not self.position:
                self.sell(size=pos_size_short, sl=sl_short, tp=tp_short)


def main():
    st.title("Trading Strategy Backtester")

    # Sidebar for input parameters
    symbol = st.sidebar.text_input("Symbol", value="BTCUSDT")
    timeframe = st.sidebar.selectbox(
        "Timeframe", options=["15m", "1h", "4h", "1d"])
    start = st.sidebar.text_input("Start Date", value="2 day ago UTC")
    end = st.sidebar.text_input("End Date", value="now")
    ema_short_len = st.sidebar.number_input(
        "EMA Short Length", value=9, min_value=1)
    ema_mid_len = st.sidebar.number_input(
        "EMA Mid Length", value=21, min_value=1)
    ema_long_len = st.sidebar.number_input(
        "EMA Long Length", value=50, min_value=1)
    adx_index = st.sidebar.number_input("ADX Index", value=20, min_value=1)
    tp_m = st.sidebar.number_input("Take Profit Multiplier", value=7.0)
    sl_m = st.sidebar.number_input("Stop Loss Multiplier", value=4.0)
    risk = st.sidebar.number_input("Risk per Trade", value=0.05)

    if st.sidebar.button("Run Backtest"):
        with st.spinner("Downloading data and running backtest..."):
            # Download data
            df = create_df(symbol, timeframe, start, end,
                           ema_short_len, ema_mid_len, ema_long_len, adx_index)

            bt = Backtest(df, qm_strat, cash=100_000, margin=0.008)
            stats = bt.optimize(tp_m=tp_m, sl_m=sl_m, risk=risk,
                                maximize='Win Rate [%]' and 'Return (Ann.) [%]', method='grid')

            # Plot the backtest results
            bt.plot()

            # Display the stats
            st.write(stats)


if __name__ == "__main__":
    mp.set_start_method('fork', force=True)
    main()
