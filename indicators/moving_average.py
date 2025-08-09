import backtrader as bt

class MovingAverage(bt.Indicator):
    """
    Custom Moving Average indicator.

    Params:
        period (int): number of bars to calculate MA
        ma_type (str): 'sma' or 'ema'
    Lines:
        ma (float): moving average value
    """
    lines = ('ma',)
    params = (('period', 20), ('ma_type', 'sma'))

    def __init__(self):
        if self.p.ma_type.lower() == 'ema':
            ma = bt.ind.EMA(self.data, period=self.p.period)
        else:
            ma = bt.ind.SMA(self.data, period=self.p.period)

        self.lines.ma = ma
