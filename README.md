# AI Trading Bot

An advanced cryptocurrency trading bot that combines machine learning with technical analysis to make trading decisions. The bot features a modern web-based dashboard for real-time monitoring and control.

## Features

### Trading Capabilities
- Real-time market data analysis
- Multiple timeframe analysis (1m, 5m, 15m, 1h)
- Machine learning model integration
- Technical indicators (SMA, RSI, MACD, Bollinger Bands)
- Risk management with stop-loss and take-profit
- Position sizing based on account balance

### Data Management
- Efficient data caching
- Multiple timeframe support
- Data quality monitoring
- Automatic data validation
- Gap detection and handling

### Web Dashboard
- Real-time price charts
- Multiple timeframe visualization
- Trading status monitoring
- Account balance tracking
- Data quality metrics
- Interactive controls
- Dark theme interface

## Prerequisites

- Python 3.8 or higher
- Binance account with API access
- Sufficient funds for trading

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-trading-bot.git
cd ai-trading-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your Binance API credentials:
   - Create a `config.py` file in the project root
   - Add your API key and secret:
```python
API_KEY = 'your_api_key_here'
API_SECRET = 'your_api_secret_here'
```

## Usage

### Starting the Web Dashboard

1. Run the web application:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:8050
```

### Dashboard Features

1. **Trading Status**
   - Current position (Buy/Sell/None)
   - Entry price
   - Current price
   - Profit/Loss percentage

2. **Account Balance**
   - USDT balance
   - BTC balance

3. **Bot Controls**
   - Start/Stop trading
   - Close positions
   - Status monitoring

4. **Price Charts**
   - Multiple timeframe candlestick charts
   - Volume indicators
   - Auto-updating every 5 seconds

5. **Data Quality Dashboard**
   - Timestamp issues
   - Price data quality
   - Volume data quality
   - Auto-updating every 30 seconds

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

## Project Structure

```
ai-trading-bot/
├── app.py              # Web dashboard application
├── bot.py             # Main trading bot logic
├── data_manager.py    # Data handling and caching
├── strategy.py        # Trading strategies
├── features.py        # Feature engineering
├── visualizer.py      # Chart generation
├── config.py          # Configuration (API keys)
├── requirements.txt   # Project dependencies
└── README.md         # Project documentation
```

## Safety Features

- Data validation and quality checks
- Error handling and logging
- API rate limiting
- Position size limits
- Stop-loss protection

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
# chrollos
