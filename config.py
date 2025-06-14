"""
Configuration file containing all the settings and parameters for the trading bot.
This includes API credentials, trading parameters, and risk management settings.
"""

# Binance API credentials
# These are used to authenticate with the Binance API
API_KEY = 'yPLvUkt6JP1x0WXqYhNrp5oXfleok4KZed5elSWh46qdz4NuAWdG53C581zzBApm'
API_SECRET = 'AZ63gxtmOBM8jPaQa3lYqtv6rIfhpnvROHBfzsaxy6GzB2rbVZzKTaH1kgKEmm2j'

# Solana network configuration
SOLANA_NETWORKS = {
    'mainnet': {
        'name': 'Solana Mainnet',
        'rpc_url': 'https://api.mainnet-beta.solana.com',
        'chain_id': 'mainnet-beta',
        'explorer': 'https://explorer.solana.com'
    },
    'testnet': {
        'name': 'Solana Testnet',
        'rpc_url': 'https://api.testnet.solana.com',
        'chain_id': 'testnet',
        'explorer': 'https://explorer.solana.com/?cluster=testnet'
    },
    'devnet': {
        'name': 'Solana Devnet',
        'rpc_url': 'https://api.devnet.solana.com',
        'chain_id': 'devnet',
        'explorer': 'https://explorer.solana.com/?cluster=devnet'
    }
}

# Default network
DEFAULT_NETWORK = 'devnet'

# Program IDs (Smart Contract addresses)
PROGRAM_IDS = {
    'mainnet': {
        'token_program': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
        'system_program': '11111111111111111111111111111111',
        'rent': 'SysvarRent111111111111111111111111111111111'
    },
    'testnet': {
        'token_program': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
        'system_program': '11111111111111111111111111111111',
        'rent': 'SysvarRent111111111111111111111111111111111'
    },
    'devnet': {
        'token_program': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
        'system_program': '11111111111111111111111111111111',
        'rent': 'SysvarRent111111111111111111111111111111111'
    }
}

# Transaction settings
MAX_RETRIES = 3
COMMITMENT = 'confirmed'
PRIORITY_FEE = 0.000005  # SOL

# Trading parameters
SYMBOL = 'BTCUSDT'  # The trading pair to monitor and trade
INTERVALS = ['1m', '5m', '15m', '1h']  # Time intervals for data collection
LOOKBACK = 100  # Number of historical candles to consider for analysis

# Risk management parameters
STOP_LOSS_PCT = 0.02  # Stop loss percentage (2% of entry price)
TAKE_PROFIT_PCT = 0.04  # Take profit percentage (4% of entry price)
MAX_POSITION_SIZE = 0.1  # Maximum position size as a fraction of available balance (10%)