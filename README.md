# Cryptocurrency Technical Analysis and Backtesting Tool

This repository contains a comprehensive tool designed for cryptocurrency traders and analysts who seek to leverage technical analysis and backtesting to make informed trading decisions. It employs a variety of technical indicators and a quantitative model strategy to simulate trading scenarios on historical data.

## Features

- **Data Fetching**: Automatically download historical cryptocurrency price data.
- **Technical Indicators**: Compute several technical indicators such as EMA (Exponential Moving Average), SMMA (Smoothed Moving Average), ADX (Average Directional Index), ATR (Average True Range), and RSI (Relative Strength Index).
- **Signal Generation**: Identify potential buy and sell opportunities based on crossover strategies and indicator thresholds.
- **Backtesting**: Run simulations to test the effectiveness of trading strategies using historical data.
- **Optimization**: Optimize strategy parameters to achieve the best performance based on specific objectives.
- **User Interface**: Configurable parameters through a sidebar enabled by Streamlit, enhancing user interaction and ease of use.
- **Visualization**: Plot the backtest results for a visual interpretation of the strategy's performance.

## How It Works

- **Input Parameters**: Users can input their trading parameters such as symbol, timeframe, EMA lengths, ADX index, and risk per trade through the sidebar provided by Streamlit.
- **Data Processing**: The tool downloads historical data for the specified symbol and timeframe, then calculates the selected technical indicators.
- **Signal Detection**: The strategy identifies buy or sell signals based on the defined criteria such as crossovers and the relationships between price and moving averages.
- **Backtesting**: The Backtest module takes in the processed data and strategy logic to simulate trades over the historical data.
- **Optimization**: Users have the option to optimize the strategy parameters to maximize certain performance metrics.
- **Result Presentation**: The results, including performance metrics and visualization plots, are displayed in the Streamlit app.

## Installation

To run this tool, you need to have Python installed on your machine. Clone this repository and install the dependencies as follows:

```bash
git clone https://github.com/0xinBeta/backtestingUI.git
cd backtestingUI
pip install -r requirements.txt
```

## Usage

After installation, you can run the tool with the following command:

```bash
streamlit run app.py
```

Configure your desired parameters in the sidebar and click "Run Backtest" to see the results.

## Strategy

The `QuantitativeModelStrategy` class defines the logic for executing trades based on the computed technical indicators. It determines position sizes and trade execution parameters such as stop loss and take profit multipliers.

## Customization

Users are encouraged to customize the strategy by modifying the conditions under which buy and sell signals are generated. Additional technical indicators can be implemented by extending the `create_df` function.

## Requirements

This tool requires the following packages:

- Backtesting==0.3.3
- ccxt==4.1.41
- finta==1.3
- numpy==1.23.5
- pandas==2.1.2
- ta==0.11.0
- vectorbt==0.25.5
- streamlit

Ensure that all dependencies are installed using `pip install -r requirements.txt` to avoid any runtime issues.

## License

This project is open-sourced under the MIT License. See the LICENSE file for more information.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check the issues page if you want to contribute.

## Support

For support, email xterminbeta@protonmail.com or join our Slack channel.

## Acknowledgements

This project makes use of the excellent vectorbt library for backtesting and the streamlit library for the frontend interface. 
Thanks to the ccxt team for providing a unified way to access cryptocurrency exchange data.
Best of luck with your trading strategies!