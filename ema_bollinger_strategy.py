"""
A script for EMA (50, 20) and Bollinger Bands trading strategy using Backtrader.
Buy criteria:
    - EMA 20 crosses above EMA 50
    - BB signals oversold
Sell criteria:
    - EMA 20 crosses below EMA 50
    - BB signals overbought
"""

import backtrader as bt

class EMABollingerStrategy(bt.Strategy):
    params = (
        ('ema_short', 20),
        ('ema_long', 50),
        ('bb_period', 20),
        ('bb_dev', 2.0),
        ('size', 100),
    )

    def __init__(self):
        self.ema_short = bt.indicators.EMA(self.data.close, period=self.params.ema_short)
        self.ema_long = bt.indicators.EMA(self.data.close, period=self.params.ema_long)
        self.bollinger = bt.indicators.BollingerBands(self.data.close, period=self.params.bb_period, devfactor=self.params.bb_dev)
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # Buy when EMA 20 crosses above EMA 50 and BB signals oversold
            if self.ema_short > self.ema_long and self.data.close < self.bollinger.lines.bot:
                self.order = self.buy(size=self.params.size)
        else:
            # Sell when EMA 50 crosses above EMA 20 and BB signals overbought
            if self.data.close > self.bollinger.lines.top or self.ema_short < self.ema_long:
                self.order = self.sell(size=self.params.size)

    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None