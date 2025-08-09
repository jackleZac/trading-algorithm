import os
import pandas as pd
import yfinance as yf
import platform

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


def fetch_from_yahoo(symbol="GC=F", period="60d", interval="15m"):
    print(f"Trying Yahoo Finance: {symbol}")
    df = yf.download(symbol, interval=interval, period=period, auto_adjust=False)
    return df


def fetch_from_mt5(symbol="XAUUSD", timeframe=None, bars=2000):
    if not MT5_AVAILABLE:
        raise RuntimeError("MetaTrader5 package not installed.")

    if timeframe is None:
        timeframe = mt5.TIMEFRAME_H1

    print(f"Trying MetaTrader 5: {symbol}")
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize() failed: {mt5.last_error()}")

    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    mt5.shutdown()

    if rates is None:
        raise RuntimeError(f"Failed to get data for {symbol} from MT5")

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.rename(columns={
        "time": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close"
    }, inplace=True)
    return df


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    csv_path = os.path.join("data", "gold_15min_data.csv")

    # If Windows and MT5 available, try MT5 first
    if platform.system() == "Windows" and MT5_AVAILABLE:
        try:
            df = fetch_from_mt5()
            df.to_csv(csv_path, index=False)
            print(f"Saved {len(df)} rows from MT5 spot prices to {csv_path}")
        except Exception as e:
            print(f"MT5 failed: {e}")
            print("Falling back to Yahoo Finance...")
            df = fetch_from_yahoo()
            if df.empty:
                raise ValueError("No data from Yahoo Finance either.")
            df.reset_index(inplace=True)
            df.rename(columns={
                "Datetime": "Date",
                "Open": "Open",
                "High": "High",
                "Low": "Low",
                "Close": "Close"
            }, inplace=True)
            df.to_csv(csv_path, index=False)
            print(f"Saved {len(df)} rows from Yahoo Finance to {csv_path}")
    else:
        # Linux/WSL → Yahoo Finance only
        df = fetch_from_yahoo()
        if df.empty:
            raise ValueError("No data from Yahoo Finance.")
        
        # Flatten MultiIndex columns (('Open', 'GC=F') → 'Open')
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        df.reset_index(inplace=True)
        df.rename(columns={
            "Datetime": "Date",
            "Open": "Open",
            "High": "High",
            "Low": "Low",
            "Close": "Close"
        }, inplace=True)

        # Check for missing columns
        numeric_cols = ["Open", "High", "Low", "Close"]
        missing = [col for col in numeric_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns from Yahoo Finance data: {missing}")
        
        # Convert to numeric & clean
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
        df.dropna(subset=numeric_cols, inplace=True)

        df.to_csv(csv_path, index=False)
        print(f"Saved {len(df)} rows from Yahoo Finance to {csv_path}")