"""
Configuration file containing all the settings and parameters for the trading bot.
This includes API credentials, trading parameters, and risk management settings.
"""

# Binance API credentials
# These are used to authenticate with the Binance API
API_KEY = 'yPLvUkt6JP1x0WXqYhNrp5oXfleok4KZed5elSWh46qdz4NuAWdG53C581zzBApm'
API_SECRET = 'AZ63gxtmOBM8jPaQa3lYqtv6rIfhpnvROHBfzsaxy6GzB2rbVZzKTaH1kgKEmm2j'

# Trading parameters
SYMBOL = 'BTCUSDT'  # The trading pair to monitor and trade
INTERVALS = ['1m', '5m', '15m', '1h']  # Time intervals for data collection
LOOKBACK = 100  # Number of historical candles to consider for analysis

# Risk management parameters
STOP_LOSS_PCT = 0.02  # Stop loss percentage (2% of entry price)
TAKE_PROFIT_PCT = 0.04  # Take profit percentage (4% of entry price)
MAX_POSITION_SIZE = 0.1  # Maximum position size as a fraction of available balance (10%)