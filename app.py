"""
Flask application for the trading bot web interface.
This module provides the web interface for monitoring and controlling the trading bot,
including real-time market data visualization and trading controls.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from bot import TradingBot
from data_manager import DataManager
from visualizer import MarketVisualizer
from wallet_manager import WalletManager
from config import SOLANA_NETWORKS, DEFAULT_NETWORK
from solana.rpc.api import Client
from solana.rpc.providers.http import HTTPProvider
from solders.keypair import Keypair
from solders.pubkey import Pubkey
import logging
import threading
import time
import json
import os
import httpx
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__, static_folder='static')

# Patch the HTTPProvider class to not use proxy
original_init = HTTPProvider.__init__
def patched_init(self, endpoint, timeout=30, extra_headers=None, proxy=None):
    self.endpoint = endpoint
    self.endpoint_uri = urlparse(endpoint)
    self.timeout = timeout
    self.extra_headers = extra_headers or {}
    self.session = httpx.Client(timeout=timeout)
    self.health_uri = f"{endpoint}/health"

HTTPProvider.__init__ = patched_init

# Initialize Solana client
solana_client = Client(SOLANA_NETWORKS[DEFAULT_NETWORK]['rpc_url'])

# Global variables
bot = None
bot_thread = None
wallet = None
is_running = False

def initialize_components():
    """
    Initialize the trading bot and other components.
    """
    global bot
    try:
        bot = TradingBot()
        logging.info("Components initialized successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize components: {e}")
        return False

@app.route('/favicon.ico')
def favicon():
    """Serve the favicon"""
    return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/charts/<path:filename>')
def serve_chart(filename):
    """Serve chart files from the charts directory"""
    return send_from_directory('charts', filename)

@app.route('/')
def index():
    """
    Render the main page.
    """
    return render_template('index.html')

@app.route('/trading')
def trading():
    """Render the trading page"""
    return render_template('trading.html')

@app.route('/analytics')
def analytics():
    """Render the analytics page"""
    return render_template('analytics.html')

@app.route('/settings')
def settings():
    """Render the settings page"""
    return render_template('settings.html')

@app.route('/api/connect_wallet', methods=['POST'])
def connect_wallet():
    """
    Connect to a Solana wallet.
    """
    global wallet
    try:
        # Get wallet data from request
        wallet_data = request.json
        if not wallet_data or 'public_key' not in wallet_data:
            return jsonify({'error': 'Invalid wallet data'}), 400
            
        # Create wallet object
        wallet = Keypair.from_public_key(Pubkey(wallet_data['public_key']))
        
        # Initialize bot with wallet
        if bot:
            bot.wallet = wallet
            
        return jsonify({
            'status': 'success',
            'message': 'Wallet connected successfully',
            'public_key': str(wallet.public_key)
        })
    except Exception as e:
        logging.error(f"Error connecting wallet: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/start_bot', methods=['POST'])
def start_bot():
    """
    Start the trading bot.
    """
    global bot_thread, is_running
    try:
        if not wallet:
            return jsonify({'error': 'Please connect wallet first'}), 400
            
        if is_running:
            return jsonify({'error': 'Bot is already running'}), 400
            
        # Initialize bot if not already initialized
        if not bot and not initialize_components():
            return jsonify({'error': 'Failed to initialize bot'}), 500
            
        # Start bot in a separate thread
        is_running = True
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Bot started successfully'
        })
    except Exception as e:
        logging.error(f"Error starting bot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop_bot', methods=['POST'])
def stop_bot():
    """
    Stop the trading bot.
    """
    global is_running
    try:
        if not is_running:
            return jsonify({'error': 'Bot is not running'}), 400
            
        is_running = False
    if bot_thread:
            bot_thread.join(timeout=5)

    return jsonify({
            'status': 'success',
            'message': 'Bot stopped successfully'
        })
    except Exception as e:
        logging.error(f"Error stopping bot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot_status', methods=['GET'])
def get_bot_status():
    """
    Get the current status of the trading bot.
    """
    try:
        status = {
            'is_running': is_running,
            'wallet_connected': wallet is not None,
            'current_position': bot.position if bot else None,
            'entry_price': bot.entry_price if bot else None
        }
        return jsonify(status)
    except Exception as e:
        logging.error(f"Error getting bot status: {e}")
        return jsonify({'error': str(e)}), 500

def run_bot():
    """
    Main bot loop that runs in a separate thread.
    """
    global is_running
    while is_running:
        try:
            # Update market data
            bot.update_charts()
            
            # Check stop loss and take profit
            bot.check_stop_loss_take_profit()
            
            # Get trading signals
            signal = bot.get_ml_signal(bot.data_manager.get_market_data(
                bot.symbol, bot.intervals[0], bot.lookback
            ))
            
            # Execute trades based on signals
            if signal == 'buy' and not bot.position:
                quantity = bot.calculate_position_size()
                bot.place_order('BUY', quantity)
            elif signal == 'sell' and bot.position == 'BUY':
                bot.close_position()
                
            # Sleep for a short interval
            time.sleep(1)
        except Exception as e:
            logging.error(f"Error in bot thread: {e}")
            time.sleep(5)  # Sleep longer on error

@app.route('/api/market_data')
def market_data():
    """Get current market data"""
    if not bot:
        return jsonify({
            'status': 'error',
            'message': 'Bot not initialized'
        }), 500

    try:
        # Get klines data for BTC/USDT
        klines = solana_client.get_klines(
            symbol='BTCUSDT',
            interval=Client.KLINE_INTERVAL_1HOUR,
            limit=24
        )
        
        # Format klines data
        formatted_klines = []
        for k in klines:
            formatted_klines.append({
                'timestamp': datetime.fromtimestamp(k[0] / 1000).isoformat(),
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5])
            })
        
        # Get 24h ticker
        ticker_24h = solana_client.get_ticker(symbol='BTCUSDT')
        
        return jsonify({
            'status': 'success',
            'klines': formatted_klines,
            'metrics': {
                'volume_24h': ticker_24h['volume'],
                'high_24h': ticker_24h['highPrice'],
                'low_24h': ticker_24h['lowPrice'],
                'price_change_24h': float(ticker_24h['priceChangePercent'])
            }
        })
    except Exception as e:
        logging.error(f"Error getting market data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/account_balance')
def account_balance():
    """Get current account balance"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        balance = bot.get_account_balance()
        return jsonify({'status': 'success', 'balance': balance})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/update_charts')
def update_charts():
    """Update and return paths to the latest charts"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        # Get data for all timeframes
        data_dict = bot.data_manager.get_multiple_timeframes(
            bot.symbol, bot.intervals, bot.lookback
        )
        
        # Create multi-timeframe chart
        chart_path = bot.visualizer.create_multi_timeframe_chart(
            data_dict, bot.symbol
        )
        
        # Create data quality dashboard
        quality_metrics = bot.data_manager.get_data_quality_report()
        dashboard_path = bot.visualizer.create_data_quality_dashboard(
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

@app.route('/api/notifications')
def notifications():
    """Get system notifications"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        notifications = []
        
        # Add system status notification
        if not wallet:
            notifications.append({
                'type': 'danger',
                'message': 'Wallet not connected',
                'time': datetime.now().isoformat()
            })
            return jsonify({
                'status': 'success',
                'notifications': notifications
            })
        
        # Add bot status notification
        if is_running:
            notifications.append({
                'type': 'info',
                'message': 'Trading bot is running',
                'time': datetime.now().isoformat()
            })
        else:
            notifications.append({
                'type': 'warning',
                'message': 'Trading bot is stopped',
                'time': datetime.now().isoformat()
            })
        
        # Add position notification if any
        if bot and hasattr(bot, 'position') and bot.position:
            notifications.append({
                'type': 'info',
                'message': f'Active {bot.position} position at {bot.entry_price}',
                'time': datetime.now().isoformat()
            })
        
        # Add error notifications if any
        if bot and hasattr(bot, 'last_error') and bot.last_error:
            notifications.append({
                'type': 'danger',
                'message': f'Error: {bot.last_error}',
                'time': datetime.now().isoformat()
            })
        
        # Add market condition notifications
        try:
            if solana_client:  # Check if client exists before making API call
                ticker = solana_client.get_ticker(symbol='BTCUSDT')
                price_change = float(ticker['priceChangePercent'])
                
                if abs(price_change) > 5:
                    notifications.append({
                        'type': 'warning',
                        'message': f'High volatility detected: {price_change}% price change in 24h',
                        'time': datetime.now().isoformat()
                    })
        except Exception as e:
            logging.error(f"Error getting market data: {e}")
            notifications.append({
                'type': 'warning',
                'message': 'Unable to fetch market data',
                'time': datetime.now().isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'notifications': notifications
        })
    except Exception as e:
        logging.error(f"Error getting notifications: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/portfolio')
def portfolio():
    """Get portfolio information"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        if not wallet:
            return jsonify({
                'status': 'error',
                'message': 'Wallet not connected'
            }), 500

        # Get account information from Solana
        account = solana_client.get_account()
        
        # Get current prices for all assets
        prices = solana_client.get_all_tickers()
        price_dict = {item['symbol']: float(item['price']) for item in prices}
        
        # Calculate total balance in USDT
        total_balance = 0
        balances = []
        
        for asset in account['balances']:
            free = float(asset['free'])
            locked = float(asset['locked'])
            total = free + locked
            
            if total > 0:
                symbol = asset['asset']
                if symbol == 'USDT':
                    usdt_value = total
                else:
                    # Try to get USDT value
                    try:
                        if f"{symbol}USDT" in price_dict:
                            usdt_value = total * price_dict[f"{symbol}USDT"]
                        else:
                            # Try to get value through BTC
                            btc_price = price_dict.get(f"{symbol}BTC", 0)
                            btc_usdt = price_dict.get("BTCUSDT", 0)
                            usdt_value = total * btc_price * btc_usdt
                    except:
                        usdt_value = 0
                
                total_balance += usdt_value
                balances.append({
                    'asset': symbol,
                    'free': str(free),
                    'locked': str(locked),
                    'total': str(total),
                    'usdt_value': str(usdt_value)
                })
        
        # Get 24h P&L
        pnl_24h = 0
        try:
            # Get 24h ticker for all symbols
            tickers_24h = solana_client.get_ticker()
            for ticker in tickers_24h:
                if ticker['symbol'].endswith('USDT'):
                    pnl_24h += float(ticker['priceChangePercent'])
        except:
            pass
        
        # Get active trades count
        active_trades = len(bot.get_active_trades()) if bot and hasattr(bot, 'get_active_trades') else 0
        
        return jsonify({
            'status': 'success',
            'balances': balances,
            'total_balance': str(total_balance),
            'pnl_24h': str(pnl_24h),
            'active_trades': active_trades
        })
    except Exception as e:
        logging.error(f"Error getting portfolio: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/wallet_connected', methods=['POST'])
def wallet_connected():
    """Handle wallet connection"""
    try:
        data = request.get_json()
        address = data.get('address')
        balance = data.get('balance')
        network = data.get('network')
        
        if not address:
            return jsonify({
                'status': 'error',
                'message': 'No wallet address provided'
            }), 400
        
        # Store wallet info in session or database if needed
        # For now, we'll just return success with the provided info
        
        return jsonify({
            'status': 'success',
            'wallet_info': {
                'address': address,
                'balance': float(balance) if balance else 0,
                'network': network or 'devnet'
            }
        })
    except Exception as e:
        logging.error(f"Error in wallet_connected: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/wallet_disconnected', methods=['POST'])
def wallet_disconnected():
    """Handle wallet disconnection"""
    try:
        data = request.get_json()
        address = data.get('address')
        
        if not address:
            return jsonify({
                'status': 'error',
                'message': 'No wallet address provided'
            }), 400
        
        # Here you can add any cleanup logic needed when a wallet disconnects
        # For example, clearing session data, stopping any ongoing processes, etc.
        
        return jsonify({
            'status': 'success',
            'message': 'Wallet disconnected successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/wallet_balance', methods=['GET'])
def get_wallet_balance():
    """Get the balance of the connected wallet"""
    try:
        wallet_address = request.args.get('address')
        if not wallet_address:
            return jsonify({'status': 'error', 'message': 'No wallet address provided'}), 400
            
        if wallet_address not in bot.wallet_manager.connected_wallets:
            return jsonify({'status': 'error', 'message': 'Wallet not connected'}), 400
            
        wallet_info = bot.wallet_manager.connected_wallets[wallet_address]
        return jsonify({
            'status': 'success',
            'balance': str(wallet_info['balance']),
            'currency': 'SOL',
            'network': wallet_info['network']
        })
    except Exception as e:
        logging.error(f"Error getting wallet balance: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/switch_network', methods=['POST'])
def switch_network():
    """Switch Solana network"""
    try:
        data = request.get_json()
        network = data.get('network')
        if not network or network not in SOLANA_NETWORKS:
            return jsonify({'status': 'error', 'message': 'Invalid network'}), 400
            
        bot.wallet_manager.switch_network(network)
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
            
        transactions = bot.wallet_manager.get_transaction_history(wallet_address)
        return jsonify({
            'status': 'success',
            'transactions': transactions
        })
    except Exception as e:
        logging.error(f"Error getting transaction history: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/available_networks', methods=['GET'])
def get_available_networks():
    """Get list of available Solana networks"""
    return jsonify({
        'status': 'success',
        'networks': SOLANA_NETWORKS
    })

@app.route('/api/recent_activity')
def recent_activity():
    """Get recent trading activity"""
    if not bot:
        return jsonify({
            'status': 'error',
            'message': 'Bot not initialized'
        }), 500

    try:
        # Get recent trades from Solana
        trades = solana_client.get_my_trades(symbol='BTCUSDT', limit=10)
        activity = []
        
        for trade in trades:
            activity.append({
                'time': datetime.fromtimestamp(trade['time'] / 1000).isoformat(),
                'symbol': trade['symbol'],
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
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Settings endpoints
@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all settings"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        return jsonify({
            'status': 'success',
            'trading_pair': bot.symbol if bot else 'BTCUSDT',
            'position_size': bot.position_size if bot else 10,
            'stop_loss': bot.stop_loss if bot else 2,
            'take_profit': bot.take_profit if bot else 4,
            'email_notifications': True,  # Default values
            'trade_notifications': True,
            'error_notifications': True,
            'max_daily_loss': 5,
            'max_positions': 3,
            'leverage': 1
        })
    except Exception as e:
        logging.error(f"Error getting settings: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/settings/trading', methods=['POST'])
def update_trading_settings():
    """Update trading settings"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        data = request.get_json()
        if bot:
            bot.symbol = data.get('trading_pair')
            bot.position_size = float(data.get('position_size'))
            bot.stop_loss = float(data.get('stop_loss'))
            bot.take_profit = float(data.get('take_profit'))
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error updating trading settings: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/settings/notifications', methods=['POST'])
def update_notification_settings():
    """Update notification settings"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        data = request.get_json()
        # Store notification settings
        # Note: In a production environment, you should use a database
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error updating notification settings: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/settings/risk', methods=['POST'])
def update_risk_settings():
    """Update risk settings"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        data = request.get_json()
        if bot:
            bot.max_daily_loss = float(data.get('max_daily_loss'))
            bot.max_positions = int(data.get('max_positions'))
            bot.leverage = int(data.get('leverage'))
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error updating risk settings: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Trading endpoints
@app.route('/api/place_order', methods=['POST'])
def place_order():
    """Place a new order"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        data = request.get_json()
        order = solana_client.create_order(
            symbol=data['symbol'],
            side=data['side'],
            type=data['orderType'],
            quantity=data['amount'],
            price=data['price'] if data['orderType'] == 'LIMIT' else None
        )
        return jsonify({'status': 'success', 'order': order})
    except Exception as e:
        logging.error(f"Error placing order: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/order_book')
def get_order_book():
    """Get current order book"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        # Initialize Solana client if not already initialized
        if not hasattr(solana_client, 'endpoint'):
            solana_client.endpoint = SOLANA_NETWORKS[DEFAULT_NETWORK]['rpc_url']
        
        # Get current market price from Solana
        try:
            price_info = solana_client.get_token_supply("So11111111111111111111111111111111111111112")
            current_price = float(price_info['result']['value']['uiAmount'] or 0)
        except Exception as e:
            logging.error(f"Error getting token supply: {e}")
            # Fallback to a default price if we can't get the real one
            current_price = 100.0
        
        # Simulate order book data since Solana doesn't have a direct order book
        # In a real implementation, you would get this from a DEX or order book service
        spread = current_price * 0.001  # 0.1% spread
        
        asks = []
        bids = []
        
        # Generate simulated asks (sell orders)
        for i in range(10):
            price = current_price + (spread * (i + 1))
            amount = 0.1 + (i * 0.1)  # Increasing amounts
            asks.append({
                'price': round(price, 2),
                'amount': round(amount, 4)
            })
        
        # Generate simulated bids (buy orders)
        for i in range(10):
            price = current_price - (spread * (i + 1))
            amount = 0.1 + (i * 0.1)  # Increasing amounts
            bids.append({
                'price': round(price, 2),
                'amount': round(amount, 4)
            })
        
        return jsonify({
            'status': 'success',
            'asks': asks,
            'bids': bids,
            'current_price': round(current_price, 2)
        })
    except Exception as e:
        logging.error(f"Error getting order book: {e}")
        # Return simulated data even if there's an error
        current_price = 100.0
        spread = current_price * 0.001
        
        asks = [{'price': round(current_price + (spread * (i + 1)), 2), 
                'amount': round(0.1 + (i * 0.1), 4)} for i in range(10)]
        bids = [{'price': round(current_price - (spread * (i + 1)), 2), 
                'amount': round(0.1 + (i * 0.1), 4)} for i in range(10)]
        
        return jsonify({
            'status': 'success',
            'asks': asks,
            'bids': bids,
            'current_price': round(current_price, 2)
        })

@app.route('/api/open_orders')
def get_open_orders():
    """Get open orders"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        if not wallet:
            return jsonify({
                'status': 'success',
                'orders': []
            })
            
        # Get token accounts for the wallet
        token_accounts = solana_client.get_token_accounts_by_owner(
            wallet.public_key,
            {'programId': "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}
        )
        
        # Format the response
        formatted_orders = []
        
        # In a real implementation, you would get actual open orders from a DEX
        # For now, we'll return an empty list since Solana doesn't have a direct open orders API
        return jsonify({
            'status': 'success',
            'orders': formatted_orders
        })
    except Exception as e:
        logging.error(f"Error getting open orders: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Analytics endpoints
@app.route('/api/performance_metrics')
def get_performance_metrics():
    """Get performance metrics"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        # Calculate performance metrics
        # Note: In a production environment, you should use a database to store historical data
        return jsonify({
            'status': 'success',
            'total_return': 0.0,
            'win_rate': 0.0,
            'avg_trade': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'risk_reward': 0.0
        })
    except Exception as e:
        logging.error(f"Error getting performance metrics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/trading_history')
def get_trading_history():
    """Get trading history"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        # Get trading history
        # Note: In a production environment, you should use a database to store historical data
        return jsonify({
            'status': 'success',
            'history': []
        })
    except Exception as e:
        logging.error(f"Error getting trading history: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/trade_distribution')
def get_trade_distribution():
    """Get trade distribution"""
    if not bot:
        return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500

    try:
        # Get trade distribution
        # Note: In a production environment, you should use a database to store historical data
        return jsonify({
            'status': 'success',
            'winning_trades': 0,
            'losing_trades': 0
        })
    except Exception as e:
        logging.error(f"Error getting trade distribution: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Initialize components
    if not initialize_components():
        logging.error("Failed to initialize components. Exiting...")
        exit(1)
        
    # Start the Flask application without debug mode
    app.run(host='0.0.0.0', port=5000, debug=False) 