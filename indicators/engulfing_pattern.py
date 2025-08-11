import backtrader as bt

class EngulfingPattern(bt.Indicator):
    lines = ('bullish', 'bearish')
    params = dict()

    def next(self):
        prev_open = self.data.open[-1]
        prev_close = self.data.close[-1]
        curr_open = self.data.open[0]
        curr_close = self.data.close[0]

        bullish = (curr_close > curr_open and
                   curr_open < prev_close and
                   curr_close > prev_open)

        bearish = (curr_close < curr_open and
                   curr_open > prev_close and
                   curr_close < prev_open)

        self.lines.bullish[0] = bullish
        self.lines.bearish[0] = bearish
