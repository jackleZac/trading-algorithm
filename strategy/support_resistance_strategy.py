"""
Multi Support & Resistance Breakout Strategy using Backtrader

Buy criteria:
    - Price breaks ABOVE resistance by breakout buffer (0.10)
    - Close price is above fast EMA and fast EMA is above slow EMA (uptrend)
    - During London session and London/New York overlap (13:00–17:00 UTC)
    - A bullish engulfing pattern is formed within a loose proximity
Sell criteria:
    - Price breaks BELOW support by breakout buffer (0.10)
    - Close price is below fast EMA and fast EMA is below slow EMA (downtrend)
    - During London session and London/New York overlap (13:00–17:00 UTC)
    - A bearish engulfing pattern is formed within a loose proximity
Stop Loss:
    - Fixed at 0.50 USD (50 pips) from entry

Take Profit:
    - Fixed at 1.00 USD (100 pips) from entry

Note: Max 5 layers
"""

import math
import backtrader as bt
from indicators.multi_support_resistance import MultiSupportResistance
from indicators.moving_average import MovingAverage
from indicators.engulfing_pattern import EngulfingPattern

class EMAMultiSupportResistanceStrategy(bt.Strategy):
    params = dict(
        sl_pips=0.50,             # Stop loss in dollars
        tp_pips=1.00,             # Take profit in dollars
        session_overlap_start=13, # 13:00 UTC (London/New York overlap start)
        session_overlap_end=17,   # 17:00 UTC (London/New York overlap end)
        session_london_start=8,   # 08:00 UTC (London session start)
        session_london_end=16,    # 16:00 UTC (London session end)
        breakout_buffer=0.1,      # Buffer beyond S/R to confirm breakout
        layer_size=0.01,          # Size of each layer
        max_layers=5,             # Max layers per direction (total)
        proximity_tolerance=1.5   # Max distance from S/R for engulfing candle
    )

    def __init__(self):
        # Multi-timeframe S/R
        self.sr_15m = MultiSupportResistance(self.datas[0], period=80, subplot=False, plot=False)
        self.sr_1h = MultiSupportResistance(self.datas[1], period=120, subplot=False, plot=False) if len(self.datas) > 1 else None
        self.sr_4h = MultiSupportResistance(self.datas[2], period=40, subplot=False, plot=False) if len(self.datas) > 2 else None

        # Moving averages
        self.ema_fast = MovingAverage(self.datas[0], period=25, ma_type='ema')
        self.ema_slow = MovingAverage(self.datas[0], period=50, ma_type='ema')

        # Bullish/Bearish Engulfing
        self.engulfing = EngulfingPattern(self.datas[0])

        # Risk management
        self.stop_loss_price = None
        self.take_profit_price = None

        # Track layering
        self.long_layers = 0
        self.short_layers = 0

    def valid_levels(self, levels):
        """Filter out None or NaN levels."""
        return [lv for lv in levels if lv is not None and not math.isnan(lv)]

    def in_session(self):
        """Check if within trading hours."""
        current_hour = self.data.datetime.datetime().hour
        return (
            self.p.session_overlap_start <= current_hour < self.p.session_overlap_end or
            self.p.session_london_start <= current_hour < self.p.session_london_end
        )

    def next(self):
        if len(self.data) < self.sr_15m.p.period:
            return
        if not self.in_session():
            return
        
        # Collect & validate S/R levels
        all_resistances, all_supports = [], []

        if self.sr_15m and len(self.sr_15m.data) >= self.sr_15m.p.period:
            all_resistances.extend(self.valid_levels([
                self.sr_15m.resistance1[0], self.sr_15m.resistance2[0], self.sr_15m.resistance3[0]
            ]))
            all_supports.extend(self.valid_levels([
                self.sr_15m.support1[0], self.sr_15m.support2[0], self.sr_15m.support3[0]
            ]))

        if self.sr_1h and len(self.sr_1h.data) >= self.sr_1h.p.period:
            all_resistances.extend(self.valid_levels([
                self.sr_1h.resistance1[0], self.sr_1h.resistance2[0], self.sr_1h.resistance3[0]
            ]))
            all_supports.extend(self.valid_levels([
                self.sr_1h.support1[0], self.sr_1h.support2[0], self.sr_1h.support3[0]
            ]))

        if self.sr_4h and len(self.sr_4h.data) >= self.sr_4h.p.period:
            all_resistances.extend(self.valid_levels([
                self.sr_4h.resistance1[0], self.sr_4h.resistance2[0], self.sr_4h.resistance3[0]
            ]))
            all_supports.extend(self.valid_levels([
                self.sr_4h.support1[0], self.sr_4h.support2[0], self.sr_4h.support3[0]
            ]))

        if not all_resistances and not all_supports:
            return

        close = self.datas[0].close[0]
        fast_ema = self.ema_fast[0]
        slow_ema = self.ema_slow[0]
        bullish_engulfing = self.engulfing.bullish[0]
        bearish_engulfing = self.engulfing.bearish[0]

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
                if (
                    bullish_engulfing
                    and abs(close - resistance) <= self.p.proximity_tolerance
                    and close > fast_ema > slow_ema
                ):
                    self.buy(size=self.p.layer_size)
                    self.long_layers += 1
                    self.stop_loss_price = close - self.p.sl_pips
                    self.take_profit_price = close + self.p.tp_pips

        # --- Short entries ---
        if not self.position or (self.position.size < 0 and self.short_layers < self.p.max_layers):
            for support in all_supports:
                if self.short_layers >= self.p.max_layers:
                    break
                if (
                    bearish_engulfing
                    and abs(close - support) <= self.p.proximity_tolerance
                    and close < fast_ema < slow_ema
                ):
                    self.sell(size=self.p.layer_size)
                    self.short_layers += 1
                    self.stop_loss_price = close + self.p.sl_pips
                    self.take_profit_price = close - self.p.tp_pips

    def stop(self):
        if self.position:
            self.close()
        self.long_layers = 0
        self.short_layers = 0


class ATRSupportResistanceStrategy(bt.Strategy):
    params = dict(
        sl_usd=0.50,
        tp_usd=1.00,
        breakout_buffer=0.10,
        proximity_tolerance=0.5,
        atr_period=14,
        atr_multiplier=1.0,
        session_overlap_start=13,
        session_overlap_end=17,
        session_london_start=8,
        session_london_end=16,
        layer_size=0.01,
        max_layers=5
    )

    def __init__(self):
        self.sr_15m = MultiSupportResistance(self.datas[0], period=80, subplot=False, plot=False)
        self.sr_1h = MultiSupportResistance(self.datas[1], period=120, subplot=False, plot=False) if len(self.datas) > 1 else None
        self.sr_4h = MultiSupportResistance(self.datas[2], period=40, subplot=False, plot=False) if len(self.datas) > 2 else None

        self.engulfing = EngulfingPattern(self.datas[0])
        self.atr = bt.ind.ATR(self.datas[0], period=self.p.atr_period)

        self.long_layers = 0
        self.short_layers = 0
        self.stop_loss_price = None
        self.take_profit_price = None

    def valid_levels(self, levels):
        return [lv for lv in levels if lv is not None and not math.isnan(lv)]

    def in_session(self):
        hour = self.data.datetime.datetime().hour
        return (
            self.p.session_overlap_start <= hour < self.p.session_overlap_end or
            self.p.session_london_start <= hour < self.p.session_london_end
        )

    def near_level(self, price, level):
        return abs(price - level) <= self.p.proximity_tolerance

    def next(self):
        if len(self.data) < self.sr_15m.p.period:
            return
        if not self.in_session():
            return

        close = self.data.close[0]
        atr_value = self.atr[0]
        bullish_engulfing = self.engulfing.bullish[0]
        bearish_engulfing = self.engulfing.bearish[0]

        all_resistances, all_supports = [], []

        if self.sr_15m and len(self.sr_15m.data) >= self.sr_15m.p.period:
            all_resistances.extend(self.valid_levels([self.sr_15m.resistance1[0], self.sr_15m.resistance2[0], self.sr_15m.resistance3[0]]))
            all_supports.extend(self.valid_levels([self.sr_15m.support1[0], self.sr_15m.support2[0], self.sr_15m.support3[0]]))

        if self.sr_1h and len(self.sr_1h.data) >= self.sr_1h.p.period:
            all_resistances.extend(self.valid_levels([self.sr_1h.resistance1[0], self.sr_1h.resistance2[0], self.sr_1h.resistance3[0]]))
            all_supports.extend(self.valid_levels([self.sr_1h.support1[0], self.sr_1h.support2[0], self.sr_1h.support3[0]]))

        if self.sr_4h and len(self.sr_4h.data) >= self.sr_4h.p.period:
            all_resistances.extend(self.valid_levels([self.sr_4h.resistance1[0], self.sr_4h.resistance2[0], self.sr_4h.resistance3[0]]))
            all_supports.extend(self.valid_levels([self.sr_4h.support1[0], self.sr_4h.support2[0], self.sr_4h.support3[0]]))

        if not all_resistances and not all_supports:
            return

        # --- Exit handling ---
        if self.position:
            if self.position.size > 0:  # Long
                if close <= self.stop_loss_price or close >= self.take_profit_price:
                    self.close()
                    self.long_layers = 0
            elif self.position.size < 0:  # Short
                if close >= self.stop_loss_price or close <= self.take_profit_price:
                    self.close()
                    self.short_layers = 0

        # --- Long entries (Breakout) ---
        if (not self.position or self.position.size > 0) and self.long_layers < self.p.max_layers:
            for resistance in all_resistances:
                if self.long_layers >= self.p.max_layers:
                    break
                if (
                    close > resistance + self.p.breakout_buffer and
                    bullish_engulfing and
                    atr_value >= self.p.atr_multiplier
                ):
                    self.buy(size=self.p.layer_size)
                    self.long_layers += 1
                    self.stop_loss_price = close - self.p.sl_usd
                    self.take_profit_price = close + self.p.tp_usd

        # --- Long entries (Bounce) ---
        if (not self.position or self.position.size > 0) and self.long_layers < self.p.max_layers:
            for support in all_supports:
                if self.long_layers >= self.p.max_layers:
                    break
                if (
                    self.near_level(close, support) and
                    bullish_engulfing and
                    close > support and  # stays above support
                    atr_value >= self.p.atr_multiplier
                ):
                    self.buy(size=self.p.layer_size)
                    self.long_layers += 1
                    self.stop_loss_price = close - self.p.sl_usd
                    self.take_profit_price = close + self.p.tp_usd

        # --- Short entries (Breakout) ---
        if (not self.position or self.position.size < 0) and self.short_layers < self.p.max_layers:
            for support in all_supports:
                if self.short_layers >= self.p.max_layers:
                    break
                if (
                    close < support - self.p.breakout_buffer and
                    bearish_engulfing and
                    atr_value >= self.p.atr_multiplier
                ):
                    self.sell(size=self.p.layer_size)
                    self.short_layers += 1
                    self.stop_loss_price = close + self.p.sl_usd
                    self.take_profit_price = close - self.p.tp_usd

        # --- Short entries (Bounce) ---
        if (not self.position or self.position.size < 0) and self.short_layers < self.p.max_layers:
            for resistance in all_resistances:
                if self.short_layers >= self.p.max_layers:
                    break
                if (
                    self.near_level(close, resistance) and
                    bearish_engulfing and
                    close < resistance and  # stays below resistance
                    atr_value >= self.p.atr_multiplier
                ):
                    self.sell(size=self.p.layer_size)
                    self.short_layers += 1
                    self.stop_loss_price = close + self.p.sl_usd
                    self.take_profit_price = close - self.p.tp_usd

    def stop(self):
        if self.position:
            self.close()
        self.long_layers = 0
        self.short_layers = 0
