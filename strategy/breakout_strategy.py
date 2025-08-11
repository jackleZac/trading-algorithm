"""
A Breakout Strategy using Backtrader

Buy criteria:
    - Price breaks ABOVE upper trendline by breakout buffer (0.10)
    - A bullish engulfing pattern is formed
    - During London session and London/New York overlap (13:00–17:00 UTC)
Sell criteria:
    - Price breaks BELOW lower trendline by breakout buffer (0.10)
    - A bearish engulfing pattern is formed
    - During London session and London/New York overlap (13:00–17:00 UTC)
Stop Loss:
    - Fixed at 0.50 USD (50 pips) from entry

Take Profit:
    - Fixed at 1.00 USD (100 pips) from entry

Note: Max 5 layers
"""

import backtrader as bt
from indicators.triangle_pattern import TrianglePattern
from indicators.engulfing_pattern import EngulfingPattern
from indicators.volatility import Volatility

class BreakoutStrategy(bt.Strategy):
    params = dict(
        base_layer_size=0.01,
        max_layers=5,
        sl_pips=0.50,
        tp_pips=1.00,
        martingale_multiplier=2,
        volatility_threshold=0.05,
        breakout_buffer=0.10,
        session_overlap_start=13, # 13:00 UTC (London/New York overlap start)
        session_overlap_end=17,   # 17:00 UTC (London/New York overlap end)
        session_london_start=8,   # 08:00 UTC (London session start)
        session_london_end=16,    # 16:00 UTC (London session end)
    )

    def __init__(self):
        self.triangle = TrianglePattern(self.data)
        self.volatility = Volatility(self.data)
        self.engulfing = EngulfingPattern(self.data)

        self.layer_size = self.p.base_layer_size
        self.layers_built = 0
        self.stop_loss_price = None
        self.take_profit_price = None

    def in_session(self):
        current_hour = self.data.datetime.datetime().hour
        in_overlap = self.p.session_overlap_start <= current_hour < self.p.session_overlap_end
        in_london = self.p.session_london_start <= current_hour < self.p.session_london_end
        return in_overlap or in_london
    
    def next(self):
        if not self.in_session():
            return
        
        close = self.data.close[0]

        # Exit Management with Martingale sizing
        if self.position:
            # Long position stop loss / take profit check
            if self.position.size > 0:
                if close <= self.stop_loss_price:
                    self.close()
                    self._on_loss()
                    return
                elif close >= self.take_profit_price:
                    self.close()
                    self._on_win()
                    return

            # Short position stop loss / take profit check
            elif self.position.size < 0:
                if close >= self.stop_loss_price:
                    self.close()
                    self._on_loss()
                    return
                elif close <= self.take_profit_price:
                    self.close()
                    self._on_win()
                    return

        # Entry Logic
        if not self.position or self.layers_built < self.p.max_layers:
            vol_ok = self.volatility[0] >= self.p.volatility_threshold
            breakout_buffer = self.p.breakout_buffer

            # Long entry condition: price breaks above upper trendline + bullish engulfing + volatility filter
            long_cond = (
                close > self.triangle.upper_trendline[0] + breakout_buffer and
                self.engulfing.bullish[0] and
                vol_ok
            )

            if long_cond:
                self.buy(size=self.layer_size)
                self.layers_built += 1
                self.stop_loss_price = close - self.p.sl_pips
                self.take_profit_price = close + self.p.tp_pips
                return

            # Short entry condition: price breaks below lower trendline + bearish engulfing + volatility filter
            short_cond = (
                close < self.triangle.lower_trendline[0] - breakout_buffer and
                self.engulfing.bearish[0] and
                vol_ok
            )

            if short_cond:
                self.sell(size=self.layer_size)
                self.layers_built += 1
                self.stop_loss_price = close + self.p.sl_pips
                self.take_profit_price = close - self.p.tp_pips
                return

    def _on_loss(self):
        # On losing trade, increase layer size using martingale multiplier (up to max)
        self.layers_built = 0
        self.layer_size = min(
            self.layer_size * self.p.martingale_multiplier,
            self.p.base_layer_size * (self.p.martingale_multiplier ** (self.p.max_layers - 1))
        )

    def _on_win(self):
        # On winning trade, reset layer size and layer count
        self.layers_built = 0
        self.layer_size = self.p.base_layer_size
