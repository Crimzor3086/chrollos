"""
This module implements the web interface for the trading bot.
It provides a dashboard for monitoring trading activities, viewing charts,
and controlling the bot's operations.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from bot import TradingBot
from data_manager import DataManager
from visualizer import MarketVisualizer
from wallet_manager import WalletManager
from binance.client import Client
from config import API_KEY, API_SECRET, ETH_NETWORKS
import threading
import logging
import json
from datetime import datetime
import os

app = Flask(__name__, static_folder='static')

# Initialize components
client = Client(API_KEY, API_SECRET)
data_manager = DataManager(client)
visualizer = MarketVisualizer()
bot = TradingBot()
wallet_manager = WalletManager()

# Global variables for bot control
bot_thread = None
bot_running = False

# Store connected wallets
connected_wallets = set()

@app.route('/favicon.ico')
def favicon():
    """Serve the favicon"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/charts/<path:filename>')
def serve_chart(filename):
    """Serve chart files from the charts directory"""
    return send_from_directory('charts', filename)

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
        
        # Convert absolute paths to relative URLs
        if chart_path:
            chart_path = os.path.basename(chart_path)
        if dashboard_path:
            dashboard_path = os.path.basename(dashboard_path)
        
        return jsonify({
            'status': 'success',
            'chart_path': f'/charts/{chart_path}' if chart_path else None,
            'dashboard_path': f'/charts/{dashboard_path}' if dashboard_path else None
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/wallet_connected', methods=['POST'])
def wallet_connected():
    """Handle wallet connection"""
    try:
        data = request.get_json()
        wallet_address = data.get('address')
        if wallet_address:
            wallet_info = wallet_manager.connect_wallet(wallet_address)
            logging.info(f"Wallet connected: {wallet_address}")
            return jsonify({
                'status': 'success',
                'message': 'Wallet connected',
                'wallet_info': wallet_info
            })
        return jsonify({'status': 'error', 'message': 'No wallet address provided'}), 400
    except Exception as e:
        logging.error(f"Error connecting wallet: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/wallet_disconnected', methods=['POST'])
def wallet_disconnected():
    """Handle wallet disconnection"""
    try:
        data = request.get_json()
        wallet_address = data.get('address')
        if wallet_address:
            wallet_manager.disconnect_wallet(wallet_address)
            logging.info(f"Wallet disconnected: {wallet_address}")
            return jsonify({'status': 'success', 'message': 'Wallet disconnected'})
        return jsonify({'status': 'error', 'message': 'No wallet address provided'}), 400
    except Exception as e:
        logging.error(f"Error disconnecting wallet: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/wallet_balance', methods=['GET'])
def get_wallet_balance():
    """Get the balance of the connected wallet"""
    try:
        wallet_address = request.args.get('address')
        if not wallet_address:
            return jsonify({'status': 'error', 'message': 'No wallet address provided'}), 400
            
        if wallet_address not in wallet_manager.connected_wallets:
            return jsonify({'status': 'error', 'message': 'Wallet not connected'}), 400
            
        wallet_info = wallet_manager.connected_wallets[wallet_address]
        return jsonify({
            'status': 'success',
            'balance': str(wallet_info['balance']),
            'currency': 'ETH',
            'network': wallet_info['network']
        })
    except Exception as e:
        logging.error(f"Error getting wallet balance: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/switch_network', methods=['POST'])
def switch_network():
    """Switch Ethereum network"""
    try:
        data = request.get_json()
        network = data.get('network')
        if not network or network not in ETH_NETWORKS:
            return jsonify({'status': 'error', 'message': 'Invalid network'}), 400
            
        wallet_manager.switch_network(network)
        return jsonify({
            'status': 'success',
            'message': f'Switched to {network}',
            'network': network
        })
    except Exception as e:
        logging.error(f"Error switching network: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/transaction_history', methods=['GET'])
def get_transaction_history():
    """Get transaction history for a wallet"""
    try:
        wallet_address = request.args.get('address')
        if not wallet_address:
            return jsonify({'status': 'error', 'message': 'No wallet address provided'}), 400
            
        transactions = wallet_manager.get_transaction_history(wallet_address)
        return jsonify({
            'status': 'success',
            'transactions': transactions
        })
    except Exception as e:
        logging.error(f"Error getting transaction history: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/available_networks', methods=['GET'])
def get_available_networks():
    """Get list of available Ethereum networks"""
    return jsonify({
        'status': 'success',
        'networks': ETH_NETWORKS
    })

@app.route('/api/portfolio')
def get_portfolio():
    """Get current portfolio information"""
    try:
        # Get account information from Binance
        account = client.get_account()
        balances = []
        for asset in account['balances']:
            if float(asset['free']) > 0 or float(asset['locked']) > 0:
                balances.append({
                    'asset': asset['asset'],
                    'free': float(asset['free']),
                    'locked': float(asset['locked'])
                })
        return jsonify({
            'status': 'success',
            'balances': balances
        })
    except Exception as e:
        logging.error(f"Error getting portfolio: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/recent_activity')
def get_recent_activity():
    """Get recent trading activity"""
    try:
        # Get recent trades from Binance
        trades = client.get_my_trades(symbol=bot.symbol, limit=10)
        activity = []
        for trade in trades:
            activity.append({
                'time': datetime.fromtimestamp(trade['time'] / 1000).isoformat(),
                'side': 'BUY' if trade['isBuyer'] else 'SELL',
                'price': float(trade['price']),
                'quantity': float(trade['qty']),
                'total': float(trade['quoteQty'])
            })
        return jsonify({
            'status': 'success',
            'activity': activity
        })
    except Exception as e:
        logging.error(f"Error getting recent activity: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/notifications')
def get_notifications():
    """Get system notifications"""
    try:
        # Get notifications from the bot
        notifications = []
        if bot.position:
            notifications.append({
                'type': 'position',
                'message': f'Active {bot.position} position at {bot.entry_price}'
            })
        if bot_running:
            notifications.append({
                'type': 'status',
                'message': 'Trading bot is running'
            })
        return jsonify({
            'status': 'success',
            'notifications': notifications
        })
    except Exception as e:
        logging.error(f"Error getting notifications: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000) 