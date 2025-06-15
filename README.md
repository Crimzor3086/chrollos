# Chrolo - AI Trading Bot

An advanced cryptocurrency trading bot that combines machine learning with technical analysis to make trading decisions. The bot features a modern web-based dashboard for real-time monitoring and control, with Solana blockchain integration.

## Features

### Trading Capabilities
- Real-time market data analysis
- Multiple timeframe analysis (1m, 5m, 15m, 1h)
- Machine learning model integration
- Technical indicators (SMA, RSI, MACD, Bollinger Bands)
- Risk management with stop-loss and take-profit
- Position sizing based on account balance
- Solana blockchain integration
- Phantom wallet support

### Data Management
- Efficient data caching
- Multiple timeframe support
- Data quality monitoring
- Automatic data validation
- Gap detection and handling
- Solana network data integration

### Web Dashboard
- Real-time price charts
- Multiple timeframe visualization
- Trading status monitoring
- Account balance tracking
- Data quality metrics
- Interactive controls
- Dark theme interface
- Wallet connection management
- Order book visualization
- Open orders tracking

## Prerequisites

- Python 3.8 or higher
- Solana wallet (Phantom recommended)
- Sufficient SOL for trading

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/chrolo.git
cd chrolo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your Solana network settings:
   - Create a `config.py` file in the project root
   - Add your network configuration:
```python
SOLANA_NETWORK = 'mainnet-beta'  # or 'testnet' for testing
```

## Usage

### Starting the Web Dashboard

1. Run the web application:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

### Dashboard Features

1. **Wallet Connection**
   - Phantom wallet integration
   - Balance display
   - Network selection
   - Account management

2. **Trading Status**
   - Current position (Buy/Sell/None)
   - Entry price
   - Current price
   - Profit/Loss percentage
   - Bot status monitoring

3. **Account Balance**
   - SOL balance
   - Token balances
   - Portfolio distribution

4. **Bot Controls**
   - Start/Stop trading
   - Close positions
   - Status monitoring
   - Strategy selection

5. **Trading Interface**
   - Real-time order book
   - Market/Limit order placement
   - Open orders management
   - Price charts with indicators

6. **Settings**
   - Trading parameters
   - Risk management
   - Notification preferences
   - API configuration

### Trading Strategy

The bot uses a combination of:
1. Technical Analysis
   - SMA crossovers
   - RSI indicators
   - MACD signals
   - Bollinger Bands

2. Machine Learning
   - Random Forest Classifier
   - Feature engineering
   - Multiple timeframe signals

3. Risk Management
   - Stop-loss (2%)
   - Take-profit (4%)
   - Position sizing (10% of balance)
   - Custom risk rules

## Project Structure

```
chrolo/
├── app.py              # Web dashboard application
├── bot.py             # Main trading bot logic
├── data_manager.py    # Data handling and caching
├── strategy.py        # Trading strategies
├── features.py        # Feature engineering
├── visualizer.py      # Chart generation
├── config.py          # Configuration
├── requirements.txt   # Project dependencies
├── templates/         # Web interface templates
│   ├── index.html    # Main dashboard
│   ├── trading.html  # Trading interface
│   ├── analytics.html # Analytics dashboard
│   └── settings.html # Settings interface
└── README.md         # Project documentation
```

## Safety Features

- Data validation and quality checks
- Error handling and logging
- Network rate limiting
- Position size limits
- Stop-loss protection
- Wallet security measures
- Transaction confirmation checks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This trading bot is for educational purposes only. Use at your own risk. Cryptocurrency trading involves significant risk and can result in the loss of your invested capital. You should not invest more than you can afford to lose.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.
