"""
Configuration file containing all the settings and parameters for the trading bot.
This includes API credentials, trading parameters, and risk management settings.
"""

# Binance API credentials
# These are used to authenticate with the Binance API
API_KEY = 'yPLvUkt6JP1x0WXqYhNrp5oXfleok4KZed5elSWh46qdz4NuAWdG53C581zzBApm'
API_SECRET = 'AZ63gxtmOBM8jPaQa3lYqtv6rIfhpnvROHBfzsaxy6GzB2rbVZzKTaH1kgKEmm2j'

# Ethereum network configuration
ETH_NETWORKS = {
    'mainnet': {
        'name': 'Ethereum Mainnet',
        'rpc_url': 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY',
        'chain_id': 1,
        'explorer': 'https://etherscan.io'
    },
    'testnet': {
        'name': 'Sepolia Testnet',
        'rpc_url': 'https://sepolia.infura.io/v3/YOUR_INFURA_KEY',
        'chain_id': 11155111,
        'explorer': 'https://sepolia.etherscan.io'
    }
}

# Default network
DEFAULT_NETWORK = 'testnet'

# Smart contract addresses
CONTRACT_ADDRESSES = {
    'mainnet': {
        'router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',  # Uniswap V2 Router
        'factory': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'  # Uniswap V2 Factory
    },
    'testnet': {
        'router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',  # Testnet Router
        'factory': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'  # Testnet Factory
    }
}

# Gas settings
GAS_LIMIT = 300000
GAS_PRICE_MULTIPLIER = 1.1  # 10% above market price

# Transaction settings
MAX_SLIPPAGE = 0.5  # 0.5% maximum slippage
MIN_LIQUIDITY = 1000  # Minimum liquidity in USD

# Trading parameters
SYMBOL = 'BTCUSDT'  # The trading pair to monitor and trade
INTERVALS = ['1m', '5m', '15m', '1h']  # Time intervals for data collection
LOOKBACK = 100  # Number of historical candles to consider for analysis

# Risk management parameters
STOP_LOSS_PCT = 0.02  # Stop loss percentage (2% of entry price)
TAKE_PROFIT_PCT = 0.04  # Take profit percentage (4% of entry price)
MAX_POSITION_SIZE = 0.1  # Maximum position size as a fraction of available balance (10%)