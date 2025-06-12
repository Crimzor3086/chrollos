"""
This module implements a trading bot that combines technical analysis and machine learning
strategies for automated cryptocurrency trading on Binance. It includes features for
position management, risk control, and real-time market visualization.
"""

from binance.client import Client
from binance.exceptions import BinanceAPIException
from config import API_KEY, API_SECRET
from strategy import sma_strategy
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime
import joblib
from features import calculate_technical_features
from data_manager import DataManager
from visualizer import MarketVisualizer

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

class TradingBot:
    """
    A trading bot that combines technical analysis and machine learning strategies.
    
    This class implements automated trading functionality including:
    - Real-time market data analysis
    - Position management with stop-loss and take-profit
    - Risk management with position sizing
    - Multi-timeframe analysis
    - Market visualization
    """
    
    def __init__(self, symbol='BTCUSDT', intervals=['1m', '5m', '15m', '1h'], lookback=100):
        """
        Initialize the trading bot with configuration parameters.
        
        Args:
            symbol (str): Trading pair symbol
            intervals (list): List of time intervals to analyze
            lookback (int): Number of historical candles to consider
        """
        self.client = Client(API_KEY, API_SECRET)
        self.symbol = symbol
        self.intervals = intervals
        self.lookback = lookback
        self.position = None  # Current position ('BUY', 'SELL', or None)
        self.entry_price = None  # Entry price of current position
        self.stop_loss_pct = 0.02  # 2% stop loss
        self.take_profit_pct = 0.04  # 4% take profit
        self.max_position_size = 0.1  # Maximum position size as fraction of balance
        
        # Initialize data management and visualization components
        self.data_manager = DataManager(self.client)
        self.visualizer = MarketVisualizer()
        
        # Load machine learning model and scaler
        try:
            self.model = joblib.load('trading_model.joblib')
            self.scaler = joblib.load('scaler.joblib')
            logging.info("ML model and scaler loaded successfully")
        except Exception as e:
            logging.error(f"Error loading ML model: {e}")
            self.model = None
            self.scaler = None

    def get_account_balance(self):
        """
        Get the current USDT balance from the Binance account.
        
        Returns:
            float: Available USDT balance
        """
        try:
            account = self.client.get_account()
            for asset in account['balances']:
                if asset['asset'] == 'USDT':
                    return float(asset['free'])
            return 0
        except BinanceAPIException as e:
            logging.error(f"Error getting account balance: {e}")
            return 0

    def calculate_position_size(self):
        """
        Calculate the position size based on current balance and risk parameters.
        
        Returns:
            float: Position size in base currency
        """
        balance = self.get_account_balance()
        current_price = float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])
        position_size = (balance * self.max_position_size) / current_price
        return position_size

    def place_order(self, side, quantity):
        """
        Place a market order on Binance.
        
        Args:
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity
            
        Returns:
            dict: Order response from Binance, or None if failed
        """
        try:
            order = self.client.create_order(
                symbol=self.symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            logging.info(f"Order placed: {side} {quantity} {self.symbol}")
            return order
        except BinanceAPIException as e:
            logging.error(f"Error placing order: {e}")
            return None

    def check_stop_loss_take_profit(self):
        """
        Check if current position has hit stop loss or take profit levels.
        Closes position if either level is reached.
        """
        if not self.position or not self.entry_price:
            return

        current_price = float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])
        price_change = (current_price - self.entry_price) / self.entry_price

        if self.position == 'BUY':
            if price_change <= -self.stop_loss_pct:
                logging.info(f"Stop loss triggered at {current_price}")
                self.close_position()
            elif price_change >= self.take_profit_pct:
                logging.info(f"Take profit triggered at {current_price}")
                self.close_position()
        elif self.position == 'SELL':
            if price_change >= self.stop_loss_pct:
                logging.info(f"Stop loss triggered at {current_price}")
                self.close_position()
            elif price_change <= -self.take_profit_pct:
                logging.info(f"Take profit triggered at {current_price}")
                self.close_position()

    def close_position(self):
        """
        Close the current position by placing an opposite order.
        Updates position and entry price to None after closing.
        """
        if not self.position:
            return

        try:
            # Get current position size
            account = self.client.get_account()
            for asset in account['balances']:
                if asset['asset'] == self.symbol[:-4]:  # Remove USDT from symbol
                    quantity = float(asset['free'])
                    if quantity > 0:
                        side = 'SELL' if self.position == 'BUY' else 'BUY'
                        self.place_order(side, quantity)
                        logging.info(f"Position closed: {side} {quantity} {self.symbol}")
                        self.position = None
                        self.entry_price = None
                        break
        except BinanceAPIException as e:
            logging.error(f"Error closing position: {e}")

    def get_ml_signal(self, df):
        """
        Get trading signal from the machine learning model.
        
        Args:
            df (pd.DataFrame): Market data with technical indicators
            
        Returns:
            str: 'buy', 'sell', or 'hold' signal, or None if model not available
        """
        if self.model is None or self.scaler is None:
            return None

        try:
            # Calculate technical features
            df_features = calculate_technical_features(df)
            
            # Get feature columns (excluding timestamp and price columns)
            feature_columns = [col for col in df_features.columns if col not in 
                             ['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # Get the latest data point
            latest_features = df_features[feature_columns].iloc[-1:].values
            
            # Scale features using the pre-trained scaler
            scaled_features = self.scaler.transform(latest_features)
            
            # Get prediction from the model
            prediction = self.model.predict(scaled_features)[0]
            
            return 'buy' if prediction == 1 else 'sell' if prediction == -1 else 'hold'
        except Exception as e:
            logging.error(f"Error getting ML signal: {e}")
            return None

    def update_charts(self):
        """
        Update and display market charts and data quality dashboard.
        Creates and opens interactive charts for all timeframes and data quality metrics.
        """
        try:
            # Get data for all timeframes
            data_dict = self.data_manager.get_multiple_timeframes(
                self.symbol, self.intervals, self.lookback
            )
            
            # Create multi-timeframe chart
            chart_path = self.visualizer.create_multi_timeframe_chart(
                data_dict, self.symbol
            )
            
            if chart_path:
                self.visualizer.open_chart(chart_path)
                
            # Create data quality dashboard
            quality_metrics = self.data_manager.get_data_quality_report()
            if quality_metrics:
                dashboard_path = self.visualizer.create_data_quality_dashboard(
                    quality_metrics
                )
                if dashboard_path:
                    self.visualizer.open_chart(dashboard_path)
                    
        except Exception as e:
            logging.error(f"Error updating charts: {e}")

    def trade(self):
        """
        Main trading logic that combines signals from multiple timeframes and strategies.
        Implements a consensus-based approach requiring agreement between:
        - Technical analysis (SMA strategy)
        - Machine learning predictions
        - Multiple timeframes
        """
        # Get data for all timeframes
        data_dict = self.data_manager.get_multiple_timeframes(
            self.symbol, self.intervals, self.lookback
        )
        
        if not data_dict:
            return

        # Check stop loss and take profit levels
        self.check_stop_loss_take_profit()

        # Get signals from both strategies for each timeframe
        signals = {}
        for interval, df in data_dict.items():
            sma_signal = sma_strategy(df)
            ml_signal = self.get_ml_signal(df)
            signals[interval] = {'sma': sma_signal, 'ml': ml_signal}

        # Combine signals (require agreement across timeframes)
        buy_signals = sum(1 for s in signals.values() 
                         if s['sma'] == 'buy' and s['ml'] == 'buy')
        sell_signals = sum(1 for s in signals.values() 
                          if s['sma'] == 'sell' and s['ml'] == 'sell')
        
        # Require majority of timeframes to agree
        threshold = len(self.intervals) // 2 + 1
        
        if buy_signals >= threshold and self.position != 'BUY':
            # Close any existing short position
            if self.position == 'SELL':
                self.close_position()
            
            # Calculate position size and enter long position
            quantity = self.calculate_position_size()
            if quantity > 0:
                order = self.place_order('BUY', quantity)
                if order:
                    self.position = 'BUY'
                    self.entry_price = float(order['fills'][0]['price'])
                    logging.info(f"Entered long position at {self.entry_price}")

        elif sell_signals >= threshold and self.position != 'SELL':
            # Close any existing long position
            if self.position == 'BUY':
                self.close_position()
            
            # Calculate position size and enter short position
            quantity = self.calculate_position_size()
            if quantity > 0:
                order = self.place_order('SELL', quantity)
                if order:
                    self.position = 'SELL'
                    self.entry_price = float(order['fills'][0]['price'])
                    logging.info(f"Entered short position at {self.entry_price}")

def main():
    """
    Main function to run the trading bot.
    Implements the main trading loop with periodic chart updates.
    """
    bot = TradingBot()
    logging.info("Trading bot started")
    
    # Initial chart update
    bot.update_charts()
    
    chart_update_interval = 300  # Update charts every 5 minutes
    last_chart_update = time.time()
    
    while True:
        try:
            # Execute trading logic
            bot.trade()
            
            # Update charts periodically
            current_time = time.time()
            if current_time - last_chart_update >= chart_update_interval:
                bot.update_charts()
                last_chart_update = current_time
                
            # Sleep to prevent excessive API calls
            time.sleep(1)
            
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    main()
