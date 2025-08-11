"""
Multi Support & Resistance Breakout Strategy using Backtrader

Buy criteria:
    - Price breaks ABOVE resistance by breakout buffer (0.10)
    - Close price is above fast EMA and fast EMA is above slow EMA (uptrend)
    - During London session and London/New York overlap (13:00–17:00 UTC)
Sell criteria:
    - Price breaks BELOW support by breakout buffer (0.10)
    - Close price is below fast EMA and fast EMA is below slow EMA (downtrend)
    - During London session and London/New York overlap (13:00–17:00 UTC)
Stop Loss:
    - Fixed at 0.50 USD (50 pips) from entry

Take Profit:
    - Fixed at 1.00 USD (100 pips) from entry

Note: Max 5 layers
"""

import backtrader as bt
import math
from indicators.multi_support_resistance import MultiSupportResistance
from indicators.moving_average import MovingAverage

class EMAMultiSupportResistanceStrategy(bt.Strategy):
    params = dict(
        sl_pips=0.50,
        tp_pips=1.00,
        session_overlap_start=13,
        session_overlap_end=17,
        session_london_start=8,
        session_london_end=16,
        breakout_buffer=0.1,
        layer_size=0.01,
        max_layers=5
    )

    def __init__(self):
        self.sr_15m = MultiSupportResistance(self.datas[0], period=80, subplot=False, plot=False)
        self.sr_1h = None
        self.sr_4h = None

        if len(self.datas) > 1:
            self.sr_1h = MultiSupportResistance(self.datas[1], period=40, subplot=False, plot=False)
        if len(self.datas) > 2:
            self.sr_4h = MultiSupportResistance(self.datas[2], period=20, subplot=False, plot=False)

        self.ema_fast = MovingAverage(period=12, ma_type='ema')
        self.ema_slow = MovingAverage(period=26, ma_type='ema')

        self.stop_loss_price = None
        self.take_profit_price = None

        self.long_layers = 0
        self.short_layers = 0

    def in_session(self):
        current_hour = self.data.datetime.datetime().hour
        in_overlap = self.p.session_overlap_start <= current_hour < self.p.session_overlap_end
        in_london = self.p.session_london_start <= current_hour < self.p.session_london_end
        return in_overlap or in_london

    def next(self):
        if len(self.data) < self.sr_15m.p.period:
            return
        if not self.in_session():
            return

        # Collect only valid (non-NaN) S/R levels
        def valid_levels(indicator):
            return [
                lvl for lvl in [
                    indicator.resistance1[0],
                    indicator.resistance2[0],
                    indicator.resistance3[0],
                    indicator.support1[0],
                    indicator.support2[0],
                    indicator.support3[0]
                ] if not math.isnan(lvl)
            ]

        all_resistances, all_supports = [], []

        if self.sr_15m and len(self.sr_15m.data) >= self.sr_15m.p.period:
            all_resistances.extend([lvl for lvl in [
                self.sr_15m.resistance1[0], self.sr_15m.resistance2[0], self.sr_15m.resistance3[0]
            ] if not math.isnan(lvl)])
            all_supports.extend([lvl for lvl in [
                self.sr_15m.support1[0], self.sr_15m.support2[0], self.sr_15m.support3[0]
            ] if not math.isnan(lvl)])

        if self.sr_1h and len(self.sr_1h.data) >= self.sr_1h.p.period:
            all_resistances.extend([lvl for lvl in [
                self.sr_1h.resistance1[0], self.sr_1h.resistance2[0], self.sr_1h.resistance3[0]
            ] if not math.isnan(lvl)])
            all_supports.extend([lvl for lvl in [
                self.sr_1h.support1[0], self.sr_1h.support2[0], self.sr_1h.support3[0]
            ] if not math.isnan(lvl)])

        if self.sr_4h and len(self.sr_4h.data) >= self.sr_4h.p.period:
            all_resistances.extend([lvl for lvl in [
                self.sr_4h.resistance1[0], self.sr_4h.resistance2[0], self.sr_4h.resistance3[0]
            ] if not math.isnan(lvl)])
            all_supports.extend([lvl for lvl in [
                self.sr_4h.support1[0], self.sr_4h.support2[0], self.sr_4h.support3[0]
            ] if not math.isnan(lvl)])

        if not all_resistances and not all_supports:
            return

        close = self.datas[0].close[0]
        fast_ema = self.ema_fast[0]
        slow_ema = self.ema_slow[0]

        # --- Manage exits ---
        if self.position:
            if self.position.size > 0:  # Long
                if close <= self.stop_loss_price or close >= self.take_profit_price:
                    self.close()
                    self.long_layers = 0
            elif self.position.size < 0:  # Short
                if close >= self.stop_loss_price or close <= self.take_profit_price:
                    self.close()
                    self.short_layers = 0

        # --- Long entries ---
        if not self.position or (self.position.size > 0 and self.long_layers < self.p.max_layers):
            for resistance in all_resistances:
                if self.long_layers >= self.p.max_layers:
                    break
                if (close > resistance + self.p.breakout_buffer and close > fast_ema > slow_ema):
                    self.buy(size=self.p.layer_size)
                    self.long_layers += 1
                    self.stop_loss_price = close - self.p.sl_pips
                    self.take_profit_price = close + self.p.tp_pips

        # --- Short entries ---
        if not self.position or (self.position.size < 0 and self.short_layers < self.p.max_layers):
            for support in all_supports:
                if self.short_layers >= self.p.max_layers:
                    break
                if (close < support - self.p.breakout_buffer and close < fast_ema < slow_ema):
                    self.sell(size=self.p.layer_size)
                    self.short_layers += 1
                    self.stop_loss_price = close + self.p.sl_pips
                    self.take_profit_price = close - self.p.tp_pips

    def stop(self):
        if self.position:
            self.close()
            self.long_layers = 0
            self.short_layers = 0
