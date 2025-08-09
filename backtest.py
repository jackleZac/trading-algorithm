import argparse
import os
import pandas as pd
import backtrader as bt
from backtrader.analyzers import SharpeRatio, DrawDown, TradeAnalyzer
from strategy.ema_bollinger_strategy import EMABollingerStrategy
from strategy.support_resistance_strategy import MVSupportResistanceStrategy

STRATEGY_MAP = {
    'ema_bollinger': EMABollingerStrategy,
    'support_resistance': MVSupportResistanceStrategy
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
    # Initialize Cerebro
    cerebro = bt.Cerebro()
    cerebro.addstrategy(selected_strategy)

    # Check file
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file {csv_file} not found")

    try:
        # Load CSV (Alpha Vantage 1H data from save_date.py)
        data_df = pd.read_csv(csv_file, parse_dates=[0], index_col=0)

        # Ensure column names are capitalized for Backtrader
        data_df.columns = [c.capitalize() for c in data_df.columns]

        # Verify required columns
        required_columns = ['Open', 'High', 'Low', 'Close']
        if not all(col in data_df.columns for col in required_columns):
            raise ValueError(f"CSV must contain columns: {required_columns}")

    except Exception as e:
        raise ValueError(f"Failed to load CSV or parse dates: {e}")

    # Create Backtrader feed
    data = bt.feeds.PandasData(
        dataname=data_df,
        timeframe=bt.TimeFrame.Minutes,
        compression=60  # 1-hour bars
    )

    cerebro.adddata(data)
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    cerebro.addsizer(bt.sizers.FixedSize, stake=5)

    # Add analyzers
    cerebro.addanalyzer(SharpeRatio, _name='sharpe', timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(DrawDown, _name='drawdown')
    cerebro.addanalyzer(TradeAnalyzer, _name='trades')

    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')
    results = cerebro.run()
    strategy = results[0]

    # Metrics
    print(f'Ending Portfolio Value: {cerebro.broker.getvalue():.2f}')
    sharpe = strategy.analyzers.sharpe.get_analysis()
    drawdown = strategy.analyzers.drawdown.get_analysis()
    trades = strategy.analyzers.trades.get_analysis()

    total_trades = trades.get('total', {}).get('total', 0)
    winning_trades = trades.get('won', {}).get('total', 0)
    losing_trades = trades.get('lost', {}).get('total', 0)
    win_percentage = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

    print(f"Max Drawdown: {drawdown.get('max', {}).get('drawdown', 'N/A'):.2f}%")
    print(f"Total Trades: {total_trades}")
    print(f"Winning Trades: {winning_trades}")
    print(f"Losing Trades: {losing_trades}")
    print(f"Win Percentage: {win_percentage:.2f}%")
    sr_value = sharpe.get('sharperatio', None)
    if sr_value is not None:
        print(f"Sharpe Ratio: {sr_value:.2f}")
    else:
        print("Sharpe Ratio: N/A (no trades made)")

    # Plot
    if plot or plot_file:
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            plotobj = cerebro.plot(style='candlestick')[0][0]
            if plot_file:
                plt.savefig(plot_file)
                print(f"Plot saved to {plot_file}")
            if plot:
                plt.show()
        except Exception as e:
            print(f"Plotting failed: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=f"Backtesting a Strategy")
    parser.add_argument('--csv', type=str, default='data/XAUUSD_1H.csv', help='Path to CSV data file')
    parser.add_argument('--strategy', type=str, required=True, help='Strategy name (e.g., ema_bollinger)')
    parser.add_argument('--cash', type=float, default=100000.0, help='Initial portfolio cash')
    parser.add_argument('--commission', type=float, default=0.001, help='Broker commission per trade')
    parser.add_argument('--plot', action='store_true', help='Plot the backtest results')
    args = parser.parse_args()

    if args.strategy not in STRATEGY_MAP:
        raise ValueError(f"Unknown strategy '{args.strategy}'. Available: {list(STRATEGY_MAP.keys())}")

    selected_strategy = STRATEGY_MAP[args.strategy]
    run_backtest(args.csv, selected_strategy, args.cash, args.commission, args.plot)

