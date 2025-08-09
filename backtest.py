import argparse
import os
import pandas as pd
import backtrader as bt
from backtrader.analyzers import SharpeRatio, DrawDown, TradeAnalyzer
from strategy.ema_bollinger_strategy import EMABollingerStrategy

STRATEGY_MAP = {
    'ema_bollinger': EMABollingerStrategy,
}


def run_backtest(csv_file, selected_strategy, initial_cash=100000.0, commission=0.001, plot=False, plot_file=None):
    """
    Run backtest with the specified CSV file and parameters.
    
    Args:
        csv_file (str): Path to the CSV file with historical data.
        initial_cash (float): Initial portfolio cash.
        commission (float): Broker commission per trade (e.g., 0.001 = 0.1%).
        plot (bool): Whether to plot the results.
        plot_file (str, optional): File path to save the plot (e.g., 'plot.png').
    """
    # Initialize Cerebro engine
    cerebro = bt.Cerebro()
    cerebro.addstrategy(selected_strategy)

    # Load data from CSV
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file {csv_file} not found")
    
    try:
        # Parse dates with format: 'YYYY-MM-DD HH:MM:SS'
        data_df = pd.read_csv(csv_file, parse_dates=['Date'], date_format='%Y-%m-%d %H:%M:%S')
        # Ensure Date is datetime
        if not pd.api.types.is_datetime64_any_dtype(data_df['Date']):
            data_df['Date'] = pd.to_datetime(data_df['Date'], errors='coerce')
        data_df.set_index('Date', inplace=True)
    except Exception as e:
        raise ValueError(f"Failed to load CSV or parse dates: {e}. Ensure 'Date' column uses format 'YYYY-MM-DD HH:MM:SS' (e.g., '2004-06-11 04:00:00').")

    # Drop rows with invalid dates
    if data_df.index.hasnans:
        invalid_dates = data_df[data_df.index.isna()]
        raise ValueError(f"CSV contains invalid or unparseable dates: {invalid_dates.head().to_string()}")

    # Verify required columns
    required_columns = ['Open', 'High', 'Low', 'Close']
    if not all(col in data_df.columns for col in required_columns):
        raise ValueError(f"CSV must contain columns: {required_columns}")

    # Create Backtrader data feed
    data = bt.feeds.PandasData(dataname=data_df)

    cerebro.adddata(data)
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    # Add analyzers for performance metrics
    cerebro.addanalyzer(SharpeRatio, _name='sharpe', timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(DrawDown, _name='drawdown')
    cerebro.addanalyzer(TradeAnalyzer, _name='trades')

    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')
    results = cerebro.run()
    strategy = results[0]

    # Print performance metrics
    print(f'Ending Portfolio Value: {cerebro.broker.getvalue():.2f}')
    sharpe = strategy.analyzers.sharpe.get_analysis()
    drawdown = strategy.analyzers.drawdown.get_analysis()
    trades = strategy.analyzers.trades.get_analysis()

    total_trades = trades.get('total', {}).get('total', 0)
    winning_trades = trades.get('won', {}).get('total', 0)
    losing_trades = trades.get('lost', {}).get('total', 0)
    win_percentage = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

    print(f"Sharpe Ratio: {sharpe.get('sharperatio', 'N/A'):.2f}")
    print(f"Max Drawdown: {drawdown.get('max', {}).get('drawdown', 'N/A'):.2f}%")
    print(f"Total Trades: {total_trades}")
    print(f"Winning Trades: {winning_trades}")
    print(f"Losing Trades: {losing_trades}")
    print(f"Win Percentage: {win_percentage:.2f}%")

    if plot or plot_file:
        try:
            import matplotlib
            matplotlib.use('Agg')  # Use non-GUI backend for WSL
            import matplotlib.pyplot as plt
            plotobj = cerebro.plot(style='candlestick')[0][0]
            if plot_file:
                plt.savefig(plot_file)
                print(f"Plot saved to {plot_file}")
            if plot:
                plt.show()  # May warn on WSL without GUI
        except Exception as e:
            print(f"Plotting failed: {e}. Try running without --plot or check matplotlib compatibility.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=f"Backtesting a Strategy")
    parser.add_argument('--csv', type=str, default='data.csv', help='Path to CSV data file')
    parser.add_argument('--strategy', type=str, required=True, help='Strategy name to use (e.g., ema_bollinger)')
    parser.add_argument('--cash', type=float, default=100000.0, help='Initial portfolio cash')
    parser.add_argument('--commission', type=float, default=0.001, help='Broker commission per trade')
    parser.add_argument('--plot', action='store_true', help='Plot the backtest results')
    args = parser.parse_args()

    # Validate the selected strategy
    if args.strategy not in STRATEGY_MAP:
        raise ValueError(f"Unknown strategy '{args.strategy}'. Available strategies: {list(STRATEGY_MAP.keys())}")

    selected_strategy = STRATEGY_MAP[args.strategy]
    run_backtest(args.csv, selected_strategy, args.cash, args.commission, args.plot)
