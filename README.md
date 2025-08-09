# Trading Algorithm: EMA and Bollinger Bands

This project implements a backtesting script for a trading strategy using EMA (50, 20) and Bollinger Bands with Backtrader.

1. **Clone the Repository**

   ```sh
   git clone <repository-url>
   cd trading-algorithm

2. **Set Up Virtual Environment**
   
   Create a virtual environment to isolate dependencies. Open the terminal and enter:
   
   ```
   python -m venv venv
   ```
   
   Activate the virtual environment
   - On Windows:
   ```
   venv\Scripts\activate
   ```
   
   - On macOS/Linux:
   ```
   source venv/bin/activate
   ```
   
   After activation, your terminal prompt should change (e.g., ``(venv)``), indicating you're in the virtual environment

   4. **Install Dependencies**

   ```sh
   pip install -r requirements.txt

5. **Backtest a strategy**
   
   Example: EMA Bollinger
   ```sh
   python3 backtest.py --csv data/gold_4h_data_cleaned.csv --strategy ema_bollinger --plot-file backtest_plot.png

# Example Results
![alt text](image.png)