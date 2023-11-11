import streamlit as st
import multiprocessing as mp
import vectorbt as vbt
from backtesting import Backtest
from backtesting.lib import Strategy
from finta import TA
from ta.trend import adx
from bokeh.resources import CDN
from bokeh.embed import file_html
from streamlit.components.v1 import html

# Constants for default parameters and configuration
DEFAULT_CASH = 100_000
DEFAULT_MARGIN = 0.008
DEFAULT_RISK = 0.005
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_TIMEFRAME_OPTIONS = ["1m", "3m", "5m",
                             "15m", "30m", "1h", "4h", "1d", "1w"]
DEFAULT_START = "2 day ago UTC"
DEFAULT_END = "now"
EXCHANGE_NAME = "binanceusdm"


def create_df(symbol: str, timeframe: str, start: str, end: str,
              ema_short_len: int, ema_mid_len: int, ema_long_len: int,
              adx_index: int):
    """Download and compute technical indicators for a given symbol and time frame."""
    df = vbt.CCXTData.download(
        symbols=symbol,
        missing_index="drop",
        exchange=EXCHANGE_NAME,
        timeframe=timeframe,
        start=start,
        end=end
    ).get()

    # Calculate EMAs and SMMA
    for length, column in [(ema_short_len, 'ema_short'), (ema_mid_len, 'ema_mid'), (ema_long_len, 'ema_long')]:
        df[column] = TA.EMA(df, length, 'close')
    df['SMMA200'] = TA.SMMA(df, period=200)

    # Identify crossovers between short and mid EMAs
    df['cross_above'] = df['ema_short'].gt(
        df['ema_mid']) & df['ema_short'].shift(1).lt(df['ema_mid'].shift(1))
    df['cross_below'] = df['ema_short'].lt(
        df['ema_mid']) & df['ema_short'].shift(1).gt(df['ema_mid'].shift(1))

    # Calculate additional technical indicators
    df['ADX'] = adx(df['High'], df['Low'], df['Close'], window=14)
    df['ATR'] = TA.ATR(df, 14)
    df['RSI'] = TA.RSI(df, period=14)

    # Determine long and short trading opportunities
    df['long'] = (
        (df['Close'] > df['SMMA200']) &
        (df['ema_short'] > df['SMMA200']) &
        (df['ema_mid'] > df['SMMA200']) &
        (df['RSI'] < 75) &
        (df['ema_mid'] > df['ema_long']) &
        df['cross_above'] &
        (df['ADX'] > adx_index) &
        (df['ema_long'] > df['SMMA200'])
    )
    df['short'] = (
        (df['Close'] < df['SMMA200']) &
        (df['ema_short'] < df['SMMA200']) &
        (df['ema_mid'] < df['SMMA200']) &
        (df['RSI'] > 20) &
        (df['ema_mid'] < df['ema_long']) &
        df['cross_below'] &
        (df['ADX'] > adx_index) &
        (df['ema_long'] < df['SMMA200'])
    )

    return df


class QuantitativeModelStrategy(Strategy):
    """Strategy that defines buy and sell signals based on technical indicators."""
    tp_m = 7
    sl_m = 4
    risk = DEFAULT_RISK

    def init(self):
        # Initialize the strategy
        pass

    def next(self):
        # Logic for placing trades in the next step
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
        cash = DEFAULT_CASH
        risk_long = (cash * self.risk) / distance_long
        risk_short = (cash * self.risk) / distance_short

        pos_size_long = ((risk_long * price) / 125) / cash
        pos_size_short = ((risk_short * price) / 125) / cash

        if buy_signal and not self.position:
            self.buy(size=pos_size_long, sl=sl_long, tp=tp_long)
        elif sell_signal and not self.position:
            self.sell(size=pos_size_short, sl=sl_short, tp=tp_short)


def configure_sidebar():
    """Configure and display sidebar options for user input with styling."""
    st.sidebar.title("Input Parameters")

    # Symbol and Timeframe on one line
    col1, col2 = st.sidebar.columns(2)
    with col1:
        symbol = st.text_input("Symbol", value=DEFAULT_SYMBOL)
    with col2:
        timeframe = st.selectbox(
            "Timeframe", options=DEFAULT_TIMEFRAME_OPTIONS)

    # Start and End date on one line
    col3, col4 = st.sidebar.columns(2)
    with col3:
        start = st.text_input("Start Date", value=DEFAULT_START)
    with col4:
        end = st.text_input("End Date", value=DEFAULT_END)

    # EMA Lengths on one line
    col5, col6, col7 = st.sidebar.columns(3)
    with col5:
        ema_short_len = st.number_input("EMA Short", value=9, min_value=1)
    with col6:
        ema_mid_len = st.number_input("EMA Mid", value=21, min_value=1)
    with col7:
        ema_long_len = st.number_input("EMA Long", value=50, min_value=1)

    # ADX Index and Risk per Trade on one line
    col8, col9 = st.sidebar.columns(2)
    with col8:
        adx_index = st.number_input("ADX Index", value=20, min_value=1)
    with col9:
        risk = st.number_input("Risk per Trade", value=DEFAULT_RISK)

    # TP Multiplier Range on one line
    col10, col11 = st.sidebar.columns(2)
    with col10:
        tp_m_low = st.number_input(
            "Take Profit Multiplier Low", value=5, min_value=1)
    with col11:
        tp_m_high = st.number_input(
            "Take Profit Multiplier High", value=10, min_value=1)

    # SL Multiplier Range on one line
    col12, col13 = st.sidebar.columns(2)
    with col12:
        sl_m_low = st.number_input(
            "Stop Loss Multiplier Low", value=3, min_value=1)
    with col13:
        sl_m_high = st.number_input(
            "Stop Loss Multiplier High", value=7, min_value=1)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "start": start,
        "end": end,
        "ema_short_len": ema_short_len,
        "ema_mid_len": ema_mid_len,
        "ema_long_len": ema_long_len,
        "adx_index": adx_index,
        "risk": risk,
        "tp_m_low": tp_m_low,
        "tp_m_high": tp_m_high,
        "sl_m_low": sl_m_low,
        "sl_m_high": sl_m_high
    }


def main():
    # Set up the UI
    params = configure_sidebar()

    if st.sidebar.button("Run Backtest"):
        with st.spinner("Downloading data and running backtest..."):
            df = create_df(symbol=params['symbol'],
                           timeframe=params['timeframe'],
                           start=params['start'],
                           end=params['end'],
                           ema_short_len=params['ema_short_len'],
                           ema_mid_len=params['ema_mid_len'],
                           ema_long_len=params['ema_long_len'],
                           adx_index=params['adx_index'])
            bt = Backtest(df, QuantitativeModelStrategy,
                          cash=DEFAULT_CASH, margin=DEFAULT_MARGIN)
            stats = bt.optimize(
                tp_m=range(params['tp_m_low'], params['tp_m_high'] + 1),
                sl_m=range(params['sl_m_low'], params['sl_m_high'] + 1),
                risk=params['risk'],
                maximize='Win Rate [%]' and 'Return (Ann.) [%]' and 'Sharpe Ratio' and 'Sortino Ratio',
                method='grid'
            )

            
            fig = bt.plot()
            # Center the plot in the main area
            st.write('## Strategy Plot', unsafe_allow_html=True)
            st.bokeh_chart(fig, use_container_width=True)  # This will make it responsive

            # Display stats dataframe with full width
            st.write('## Strategy Stats', unsafe_allow_html=True)
            st.dataframe(stats, width=None, height=None)


if __name__ == "__main__":
    mp.set_start_method('fork', force=True)
    main()
