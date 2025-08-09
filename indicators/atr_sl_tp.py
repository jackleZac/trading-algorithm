import backtrader as bt

class StopLossTakeProfit(bt.Indicator):
    """calculate dynamic stop-loss and take-profit levels based on the Average True Range (ATR)"""
    lines = ('stop_loss', 'take_profit')
    # Uses ATR with a default period of 14
    params = (('atr_period', 14), ('sl_mult', 1.5), ('tp_mult', 3))

    def __init__(self):
        self.atr = bt.ind.ATR(self.data, period=self.p.atr_period)

    # Dynamically set SL and TP
    def set_levels(self, entry_price, direction):
        if direction == 'long':
            self.lines.stop_loss[0] = entry_price - self.atr[0] * self.p.sl_mult
            self.lines.take_profit[0] = entry_price + self.atr[0] * self.p.tp_mult
        elif direction == 'short':
            self.lines.stop_loss[0] = entry_price + self.atr[0] * self.p.sl_mult
            self.lines.take_profit[0] = entry_price - self.atr[0] * self.p.tp_mult
