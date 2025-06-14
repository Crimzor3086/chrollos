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
from datetime import datetime, timedelta
import os
from web3 import Web3
import random
from solana.rpc.api import Client

app = Flask(__name__, static_folder='static')

# Initialize components
try:
    if not API_KEY or not API_SECRET:
        raise ValueError("Binance API credentials are not configured")
        
    client = Client(API_KEY, API_SECRET)
    # Test the connection
    client.get_system_status()
    
    data_manager = DataManager(client)
    visualizer = MarketVisualizer()
    bot = TradingBot()
    wallet_manager = WalletManager()
    binance_initialized = True
    logging.info("Successfully initialized all components")
except ValueError as e:
    logging.error(f"Configuration error: {e}")
    client = None
    data_manager = None
    visualizer = None
    bot = None
    wallet_manager = None
    binance_initialized = False
except Exception as e:
    logging.error(f"Failed to initialize components: {e}")
    client = None
    data_manager = None
    visualizer = None
    bot = None
    wallet_manager = None
    binance_initialized = False

# Global variables for bot control
bot_thread = None
bot_running = False

# Store connected wallets
connected_wallets = set()

@app.route('/favicon.ico')
def favicon():
    """Serve the favicon"""
    return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

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
    try:
        if not binance_initialized:
            return jsonify({
                'status': 'error',
                'message': 'Binance API not initialized. Please check your API credentials.',
                'running': False,
                'last_update': datetime.now().isoformat()
            })
            
        return jsonify({
            'status': 'success',
            'running': bot_running,
            'last_update': datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Error getting bot status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'running': False,
            'last_update': datetime.now().isoformat()
        }), 500

@app.route('/api/market_data')
def market_data():
    """Get current market data"""
    if not binance_initialized:
        return jsonify({
            'status': 'error',
            'message': 'Binance API not initialized. Please check your API credentials.'
        }), 500

    try:
        # Get klines data for BTC/USDT
        klines = client.get_klines(
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
        ticker_24h = client.get_ticker(symbol='BTCUSDT')
        
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

@app.route('/api/notifications')
def notifications():
    """Get system notifications"""
    try:
        notifications = []
        
        # Add system status notification
        if not binance_initialized:
            notifications.append({
                'type': 'danger',
                'message': 'Binance API not initialized. Please check your API credentials.',
                'time': datetime.now().isoformat()
            })
            return jsonify({
                'status': 'success',
                'notifications': notifications
            })
        
        # Add bot status notification
        if bot_running:
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
            if client:  # Check if client exists before making API call
                ticker = client.get_ticker(symbol='BTCUSDT')
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
    try:
        if not binance_initialized:
            return jsonify({
                'status': 'error',
                'message': 'Binance API not initialized. Please check your API credentials.'
            }), 500

        if not client:
            return jsonify({
                'status': 'error',
                'message': 'Binance client not initialized'
            }), 500

        # Get account information from Binance
        account = client.get_account()
        
        # Get current prices for all assets
        prices = client.get_all_tickers()
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
            tickers_24h = client.get_ticker()
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
        
        if not address:
            return jsonify({
                'status': 'error',
                'message': 'No wallet address provided'
            }), 400
        
        # Initialize Solana connection
        solana_client = Client(SOLANA_NETWORKS[DEFAULT_NETWORK]['rpc_url'])
        
        try:
            # Get wallet balance
            balance = solana_client.get_balance(address)
            balance_sol = balance['result']['value'] / 1e9  # Convert lamports to SOL
            
            # Get network information
            network_name = SOLANA_NETWORKS[DEFAULT_NETWORK]['name']
            
            return jsonify({
                'status': 'success',
                'wallet_info': {
                    'address': address,
                    'balance': float(balance_sol),
                    'network': network_name
                }
            })
        except Exception as e:
            logging.error(f"Error getting Solana wallet info: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Failed to get wallet information: {str(e)}'
            }), 500
    except Exception as e:
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
            
        if wallet_address not in wallet_manager.connected_wallets:
            return jsonify({'status': 'error', 'message': 'Wallet not connected'}), 400
            
        wallet_info = wallet_manager.connected_wallets[wallet_address]
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
    """Get list of available Solana networks"""
    return jsonify({
        'status': 'success',
        'networks': SOLANA_NETWORKS
    })

@app.route('/api/recent_activity')
def recent_activity():
    """Get recent trading activity"""
    if not binance_initialized:
        return jsonify({
            'status': 'error',
            'message': 'Binance API not initialized. Please check your API credentials.'
        }), 500

    try:
        # Get recent trades from Binance
        trades = client.get_my_trades(symbol='BTCUSDT', limit=10)
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
    try:
        return jsonify({
            'status': 'success',
            'api_key': API_KEY,
            'api_secret': API_SECRET,
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

@app.route('/api/settings/api', methods=['POST'])
def update_api_settings():
    """Update API settings"""
    try:
        data = request.get_json()
        # Update API settings in config
        # Note: In a production environment, you should use a secure method to store these
        global API_KEY, API_SECRET
        API_KEY = data.get('api_key')
        API_SECRET = data.get('api_secret')
        
        # Reinitialize client with new credentials
        if API_KEY and API_SECRET:
            client = Client(API_KEY, API_SECRET)
            client.get_system_status()  # Test connection
            binance_initialized = True
        else:
            binance_initialized = False
            
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error updating API settings: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/settings/trading', methods=['POST'])
def update_trading_settings():
    """Update trading settings"""
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
    try:
        if not binance_initialized:
            return jsonify({
                'status': 'error',
                'message': 'Binance API not initialized'
            }), 500
            
        data = request.get_json()
        order = client.create_order(
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

@app.route('/api/open_orders')
def get_open_orders():
    """Get open orders"""
    try:
        if not binance_initialized:
            return jsonify({
                'status': 'error',
                'message': 'Binance API not initialized'
            }), 500
            
        orders = client.get_open_orders()
        return jsonify({'status': 'success', 'orders': orders})
    except Exception as e:
        logging.error(f"Error getting open orders: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Analytics endpoints
@app.route('/api/performance_metrics')
def get_performance_metrics():
    """Get performance metrics"""
    try:
        if not binance_initialized:
            return jsonify({
                'status': 'error',
                'message': 'Binance API not initialized'
            }), 500
            
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
    try:
        if not binance_initialized:
            return jsonify({
                'status': 'error',
                'message': 'Binance API not initialized'
            }), 500
            
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
    try:
        if not binance_initialized:
            return jsonify({
                'status': 'error',
                'message': 'Binance API not initialized'
            }), 500
            
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
    # Check if running on Vercel
    if os.environ.get('VERCEL'):
        # Production settings for Vercel
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    else:
        # Development settings
        app.run(debug=False, host='0.0.0.0', port=5000) 