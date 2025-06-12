"""
This module implements the web interface for the trading bot.
It provides a dashboard for monitoring trading activities, viewing charts,
and controlling the bot's operations.
"""

from flask import Flask, render_template, jsonify, request
from bot import TradingBot
from data_manager import DataManager
from visualizer import MarketVisualizer
from binance.client import Client
from config import API_KEY, API_SECRET
import threading
import logging
import json
from datetime import datetime

app = Flask(__name__)

# Initialize components
client = Client(API_KEY, API_SECRET)
data_manager = DataManager(client)
visualizer = MarketVisualizer()
bot = TradingBot()

# Global variables for bot control
bot_thread = None
bot_running = False

def run_bot():
    """Background thread function to run the trading bot"""
    global bot_running
    bot_running = True
    while bot_running:
        try:
            bot.trade()
        except Exception as e:
            logging.error(f"Error in bot thread: {e}")

@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/api/start_bot', methods=['POST'])
def start_bot():
    """Start the trading bot"""
    global bot_thread, bot_running
    if not bot_running:
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.start()
        return jsonify({'status': 'success', 'message': 'Bot started'})
    return jsonify({'status': 'error', 'message': 'Bot is already running'})

@app.route('/api/stop_bot', methods=['POST'])
def stop_bot():
    """Stop the trading bot"""
    global bot_running
    bot_running = False
    if bot_thread:
        bot_thread.join()
    return jsonify({'status': 'success', 'message': 'Bot stopped'})

@app.route('/api/bot_status')
def bot_status():
    """Get the current status of the bot"""
    return jsonify({
        'running': bot_running,
        'position': bot.position,
        'entry_price': bot.entry_price,
        'current_price': float(client.get_symbol_ticker(symbol=bot.symbol)['price'])
    })

@app.route('/api/market_data')
def market_data():
    """Get current market data for all timeframes"""
    data = {}
    for interval in bot.intervals:
        df = data_manager.get_data(bot.symbol, interval)
        if df is not None and not df.empty:
            data[interval] = {
                'timestamp': df['timestamp'].iloc[-1].isoformat(),
                'open': float(df['open'].iloc[-1]),
                'high': float(df['high'].iloc[-1]),
                'low': float(df['low'].iloc[-1]),
                'close': float(df['close'].iloc[-1]),
                'volume': float(df['volume'].iloc[-1])
            }
    return jsonify(data)

@app.route('/api/account_balance')
def account_balance():
    """Get current account balance"""
    try:
        balance = bot.get_account_balance()
        return jsonify({'status': 'success', 'balance': balance})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/update_charts')
def update_charts():
    """Update and return paths to the latest charts"""
    try:
        # Get data for all timeframes
        data_dict = data_manager.get_multiple_timeframes(
            bot.symbol, bot.intervals, bot.lookback
        )
        
        # Create multi-timeframe chart
        chart_path = visualizer.create_multi_timeframe_chart(
            data_dict, bot.symbol
        )
        
        # Create data quality dashboard
        quality_metrics = data_manager.get_data_quality_report()
        dashboard_path = visualizer.create_data_quality_dashboard(
            quality_metrics
        )
        
        return jsonify({
            'status': 'success',
            'chart_path': chart_path,
            'dashboard_path': dashboard_path
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 