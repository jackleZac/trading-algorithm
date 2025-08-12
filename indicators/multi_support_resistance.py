import backtrader as bt
import math

class MultiSupportResistance(bt.Indicator):
    """
    Identify up to 6 supports and resistances
    params:
        period (int): number of bars to calculate MA
    """
    lines = (
        'resistance1', 'resistance2', 'resistance3', 
        'support1', 'support2', 'support3' )
    params = dict(period=80)

    def __init__(self):
        self.addminperiod(self.p.period)

    def next(self):
        available_bars = min(len(self.data), self.p.period)
        high_vals = [self.data.high[-i] for i in range(available_bars)]
        low_vals = [self.data.low[-i] for i in range(available_bars)]

        sorted_highs = sorted(high_vals, reverse=True)
        sorted_lows = sorted(low_vals)

        nan = float('nan')

        self.lines.resistance1[0] = sorted_highs[0] if len(sorted_highs) >= 1 else nan
        self.lines.resistance2[0] = sorted_highs[1] if len(sorted_highs) >= 2 else nan
        self.lines.resistance3[0] = sorted_highs[2] if len(sorted_highs) >= 3 else nan

        self.lines.support1[0] = sorted_lows[0] if len(sorted_lows) >= 1 else nan
        self.lines.support2[0] = sorted_lows[1] if len(sorted_lows) >= 2 else nan
        self.lines.support3[0] = sorted_lows[2] if len(sorted_lows) >= 3 else nan
