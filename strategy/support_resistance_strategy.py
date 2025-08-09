"""
Support & Resistance Breakout Strategy using Backtrader (EMA filter, no volatility, no volume)

Buy criteria:
    - Price breaks ABOVE resistance by breakout buffer (0.05)
    - Close price is above fast EMA and fast EMA is above slow EMA (uptrend)
    - Only during London/New York overlap (13:00–17:00 UTC)
Sell criteria:
    - Price breaks BELOW support by breakout buffer (0.05)
    - Close price is below fast EMA and fast EMA is below slow EMA (downtrend)
    - Only during London/New York overlap (13:00–17:00 UTC)
Stop Loss:
    - Fixed at 0.50 USD (50 pips) from entry

Take Profit:
    - Fixed at 1.00 USD (100 pips) from entry
"""

import backtrader as bt
from indicators.support_resistance import SupportResistance

class MVSupportResistanceStrategy(bt.Strategy):
    params = dict(
        sl_pips=0.50,          # Stop loss in dollars (for gold)
        tp_pips=1.00,          # Take profit in dollars
        ema_fast_period=12,    # Fast EMA period
        ema_slow_period=26,    # Slow EMA period
        session_start=13,      # 13:00 UTC (London/New York overlap start)
        session_end=17,        # 17:00 UTC (end of overlap)
        breakout_buffer=0.05   # Buffer beyond S/R to confirm breakout
    )

    def __init__(self):
        self.sr = SupportResistance(period=320)
        self.ema_fast = bt.ind.EMA(self.data, period=self.p.ema_fast_period)
        self.ema_slow = bt.ind.EMA(self.data, period=self.p.ema_slow_period)

        self.stop_loss_price = None
        self.take_profit_price = None

    def in_session(self):
        """Check if current time is within the London/New York overlap session."""
        current_hour = self.data.datetime.datetime().hour
        return self.p.session_start <= current_hour < self.p.session_end
    
    def next(self):
        # Only trade if conditions met
        if not self.in_session():
            return

        if not self.position:
            # --- LONG ENTRY ---
            if (self.data.close[0] > self.sr.resistance[-1] + self.p.breakout_buffer and
                self.data.close[0] > self.ema_fast[0] > self.ema_slow[0]):

                self.buy()
                self.stop_loss_price = self.data.close[0] - self.p.sl_pips
                self.take_profit_price = self.data.close[0] + self.p.tp_pips

            # --- SHORT ENTRY ---
            elif (self.data.close[0] < self.sr.support[-1] - self.p.breakout_buffer and
                  self.data.close[0] < self.ema_fast[0] < self.ema_slow[0]):

                self.sell()
                self.stop_loss_price = self.data.close[0] + self.p.sl_pips
                self.take_profit_price = self.data.close[0] - self.p.tp_pips

        else:
            # Manage exits
            if self.position.size > 0:
                if self.data.close[0] <= self.stop_loss_price or self.data.close[0] >= self.take_profit_price:
                    self.close()

            elif self.position.size < 0:
                if self.data.close[0] >= self.stop_loss_price or self.data.close[0] <= self.take_profit_price:
                    self.close()

    def stop(self):
        """Ensure all positions are closed at the end of backtest."""
        if self.position:
            self.close()
