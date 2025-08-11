import backtrader as bt

class SupportResistance(bt.Indicator):
    """Determine support and resistance formed over the specified number of bars"""
    lines = ('support', 'resistance',)
    # Look back over the specified number of bars (20 by default)
    params = (('period', 20),)

    def __init__(self):
        # computes the highest high - Resistance
        self.lines.resistance = bt.ind.Highest(self.data.high, period=self.p.period)
        # computes the lowest low - Support
        self.lines.support = bt.ind.Lowest(self.data.low, period=self.p.period)