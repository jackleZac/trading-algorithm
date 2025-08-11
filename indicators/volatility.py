import backtrader as bt
import math

class Volatility(bt.Indicator):
    lines = ('volatility',)
    params = dict(period=20)

    def __init__(self):
        # Use True Range (high-low) or returns to measure volatility
        self.addminperiod(self.p.period)

    def next(self):
        # Calculate standard deviation of the price range (high - low) over the period
        tr_values = [self.data.high[-i] - self.data.low[-i] for i in range(self.p.period)]
        mean_tr = sum(tr_values) / self.p.period
        variance = sum((x - mean_tr) ** 2 for x in tr_values) / self.p.period
        self.lines.volatility[0] = math.sqrt(variance)
