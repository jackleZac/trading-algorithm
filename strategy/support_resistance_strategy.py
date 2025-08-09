"""
A script for Support and Resistance (20 bars lookback) and Support & Resistance strategy using Backtrader
Buy criteria:
    - Hit support level
    - Above moving average
Sell criteria:
    - Hit resistance level
    - Below moving average
Stop Loss criteria:
    - Hit 30 pips away
Take Profit criteria:
    - Reach 60 pips away
"""

from indicators.moving_average import MovingAverage
from indicators.support_resistance import SupportResistance
import backtrader as bt

class MVSupportResistanceStrategy(bt.Strategy):
    params = dict(atr_period=14, sl_mult=1.5, tp_mult=3, ma_period=50)

    def __init__(self):
        self.sr = SupportResistance(period=20)
        self.atr = bt.ind.ATR(self.data, period=self.p.atr_period)
        self.ma = MovingAverage(period=self.p.ma_period, ma_type='sma')

        self.stop_loss_price = None
        self.take_profit_price = None

    def next(self):
        if not self.position:
            # Long entry: price above MA & breakout above resistance
            if self.data.close[0] > self.ma.ma[0] and self.data.close[0] > self.sr.resistance[-1]:
                self.buy()
                self.stop_loss_price = self.data.close[0] - self.atr[0] * self.p.sl_mult
                self.take_profit_price = self.data.close[0] + self.atr[0] * self.p.tp_mult

            # Short entry: price below MA & breakdown below support
            elif self.data.close[0] < self.ma.ma[0] and self.data.close[0] < self.sr.support[-1]:
                self.sell()
                self.stop_loss_price = self.data.close[0] + self.atr[0] * self.p.sl_mult
                self.take_profit_price = self.data.close[0] - self.atr[0] * self.p.tp_mult

        else:
            if self.position.size > 0:
                if self.data.close[0] <= self.stop_loss_price or self.data.close[0] >= self.take_profit_price:
                    self.close()
            elif self.position.size < 0:
                if self.data.close[0] >= self.stop_loss_price or self.data.close[0] <= self.take_profit_price:
                    self.close()

    def stop(self):
        if self.position:
            self.close()
