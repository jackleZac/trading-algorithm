import backtrader as bt
import numpy as np

class TrianglePattern(bt.Indicator):
    lines = ('breakout', 'upper_trendline', 'lower_trendline')
    params = dict(
        lookback=30,
        breakout_buffer=0.01,
    )

    def __init__(self):
        self.addminperiod(self.p.lookback + 1)

    def next(self):
        highs = np.array([self.data.high[-i] for i in reversed(range(self.p.lookback))])
        lows = np.array([self.data.low[-i] for i in reversed(range(self.p.lookback))])

        x = np.arange(self.p.lookback)

        high_coef = np.polyfit(x, highs, 1)
        low_coef = np.polyfit(x, lows, 1)

        resistance = high_coef[0] * (self.p.lookback - 1) + high_coef[1]
        support = low_coef[0] * (self.p.lookback - 1) + low_coef[1]

        close = self.data.close[0]

        dist_start = highs[0] - lows[0]
        dist_end = resistance - support

        converging = dist_end < dist_start

        breakout_signal = 0
        buffer = self.p.breakout_buffer

        if converging:
            if close > resistance + buffer:
                breakout_signal = 1
            elif close < support - buffer:
                breakout_signal = -1

        self.lines.breakout[0] = breakout_signal
        self.lines.upper_trendline[0] = resistance
        self.lines.lower_trendline[0] = support
