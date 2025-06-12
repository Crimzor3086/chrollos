"""
This module provides functionality for managing and caching market data from Binance.
It includes features for data validation, quality checks, and efficient data retrieval
with caching mechanisms to minimize API calls.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import json
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException

class DataManager:
    """
    A class to manage market data retrieval, caching, and validation.
    
    This class handles all interactions with the Binance API for market data,
    implements caching mechanisms to reduce API calls, and performs data quality
    checks to ensure reliable data for trading decisions.
    """
    
    def __init__(self, client: Client, cache_dir: str = 'data_cache'):
        """
        Initialize the DataManager with a Binance client and cache directory.
        
        Args:
            client (Client): Initialized Binance API client
            cache_dir (str): Directory to store cached data files
        """
        self.client = client
        self.cache_dir = cache_dir
        self.cache: Dict[str, pd.DataFrame] = {}  # In-memory cache
        self.last_update: Dict[str, datetime] = {}  # Last update timestamps
        self.data_quality_metrics: Dict[str, Dict] = {}  # Data quality tracking
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        # Initialize logging
        self.logger = logging.getLogger('DataManager')
        
    def _get_cache_key(self, symbol: str, interval: str) -> str:
        """
        Generate a unique cache key for a symbol and interval combination.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
            interval (str): Time interval (e.g., '1m', '1h')
            
        Returns:
            str: Unique cache key
        """
        return f"{symbol}_{interval}"
    
    def _load_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """
        Load data from cache file if it exists.
        
        Args:
            cache_key (str): Unique identifier for the cached data
            
        Returns:
            Optional[pd.DataFrame]: Cached data if available, None otherwise
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.csv")
        if os.path.exists(cache_file):
            try:
                df = pd.read_csv(cache_file)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df
            except Exception as e:
                self.logger.error(f"Error loading cache file {cache_file}: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, df: pd.DataFrame):
        """
        Save data to cache file.
        
        Args:
            cache_key (str): Unique identifier for the data
            df (pd.DataFrame): Data to cache
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.csv")
        try:
            df.to_csv(cache_file, index=False)
        except Exception as e:
            self.logger.error(f"Error saving cache file {cache_file}: {e}")
    
    def _validate_data_quality(self, df: pd.DataFrame, symbol: str, interval: str) -> bool:
        """
        Validate data quality and update metrics.
        
        This function performs comprehensive checks on the data including:
        - Timestamp sequence integrity
        - Missing or invalid price data
        - Volume data quality
        - Data consistency
        
        Args:
            df (pd.DataFrame): Data to validate
            symbol (str): Trading pair symbol
            interval (str): Time interval
            
        Returns:
            bool: True if data passes quality checks, False otherwise
        """
        if df.empty:
            return False
            
        metrics = {
            'timestamp': {
                'gaps': self._check_timestamp_gaps(df, interval),
                'duplicates': df['timestamp'].duplicated().sum(),
                'order': df['timestamp'].is_monotonic_increasing
            },
            'price': {
                'missing': df[['open', 'high', 'low', 'close']].isnull().sum().to_dict(),
                'zeros': (df[['open', 'high', 'low', 'close']] == 0).sum().to_dict(),
                'negative': (df[['open', 'high', 'low', 'close']] < 0).sum().to_dict()
            },
            'volume': {
                'missing': df['volume'].isnull().sum(),
                'zeros': (df['volume'] == 0).sum(),
                'negative': (df['volume'] < 0).sum()
            }
        }
        
        # Update quality metrics
        self.data_quality_metrics[self._get_cache_key(symbol, interval)] = metrics
        
        # Check for critical issues
        critical_issues = (
            metrics['timestamp']['gaps'] > 0 or
            metrics['timestamp']['duplicates'] > 0 or
            not metrics['timestamp']['order'] or
            any(metrics['price']['missing'].values()) or
            any(metrics['price']['zeros'].values()) or
            any(metrics['price']['negative'].values()) or
            metrics['volume']['missing'] > 0 or
            metrics['volume']['negative'] > 0
        )
        
        return not critical_issues
    
    def _check_timestamp_gaps(self, df: pd.DataFrame, interval: str) -> int:
        """
        Check for gaps in timestamp sequence.
        
        Args:
            df (pd.DataFrame): Data to check
            interval (str): Time interval
            
        Returns:
            int: Number of gaps found in the timestamp sequence
        """
        if df.empty:
            return 0
            
        # Convert interval to timedelta
        interval_map = {
            '1m': timedelta(minutes=1),
            '5m': timedelta(minutes=5),
            '15m': timedelta(minutes=15),
            '30m': timedelta(minutes=30),
            '1h': timedelta(hours=1),
            '4h': timedelta(hours=4),
            '1d': timedelta(days=1)
        }
        
        delta = interval_map.get(interval)
        if not delta:
            return 0
            
        # Calculate expected timestamps
        start = df['timestamp'].min()
        end = df['timestamp'].max()
        expected_timestamps = pd.date_range(start=start, end=end, freq=delta)
        
        # Count missing timestamps
        missing = len(expected_timestamps) - len(df)
        return max(0, missing)
    
    def get_data(self, symbol: str, interval: str, lookback: int = 100, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        Get market data with caching and validation.
        
        This method implements a smart caching system that:
        1. Checks in-memory cache first
        2. Falls back to disk cache if needed
        3. Fetches fresh data from API if cache is stale or missing
        4. Validates data quality
        5. Updates cache with fresh data
        
        Args:
            symbol (str): Trading pair symbol
            interval (str): Time interval
            lookback (int): Number of candles to fetch
            force_refresh (bool): Force refresh from API
            
        Returns:
            Optional[pd.DataFrame]: Market data if successful, None if failed
        """
        cache_key = self._get_cache_key(symbol, interval)
        
        # Check if we need to refresh the cache
        needs_refresh = (
            force_refresh or
            cache_key not in self.last_update or
            (datetime.now() - self.last_update[cache_key]).total_seconds() > 60  # Refresh every minute
        )
        
        if not needs_refresh and cache_key in self.cache:
            return self.cache[cache_key]
            
        # Try to load from cache file
        if not needs_refresh:
            df = self._load_from_cache(cache_key)
            if df is not None:
                self.cache[cache_key] = df
                self.last_update[cache_key] = datetime.now()
                return df
        
        # Fetch new data from API
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=lookback
            )
            
            if not klines:
                return None
                
            # Convert API response to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
            ])
            
            # Convert numeric columns
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            # Validate data quality
            if not self._validate_data_quality(df, symbol, interval):
                self.logger.warning(f"Data quality issues detected for {symbol} {interval}")
                
            # Update cache
            self.cache[cache_key] = df
            self.last_update[cache_key] = datetime.now()
            self._save_to_cache(cache_key, df)
            
            return df
            
        except BinanceAPIException as e:
            self.logger.error(f"Error fetching data: {e}")
            return None
            
    def get_multiple_timeframes(self, symbol: str, intervals: List[str], lookback: int = 100) -> Dict[str, pd.DataFrame]:
        """
        Get data for multiple timeframes simultaneously.
        
        Args:
            symbol (str): Trading pair symbol
            intervals (List[str]): List of time intervals
            lookback (int): Number of candles to fetch
            
        Returns:
            Dict[str, pd.DataFrame]: Dictionary of dataframes for each interval
        """
        return {
            interval: self.get_data(symbol, interval, lookback)
            for interval in intervals
        }
        
    def get_data_quality_report(self) -> Dict:
        """
        Get a comprehensive report of data quality metrics.
        
        Returns:
            Dict: Dictionary containing quality metrics for all cached data
        """
        return self.data_quality_metrics
        
    def clear_cache(self):
        """
        Clear all cached data from memory and disk.
        This includes:
        - In-memory cache
        - Last update timestamps
        - Data quality metrics
        - Cache files on disk
        """
        self.cache.clear()
        self.last_update.clear()
        self.data_quality_metrics.clear()
        
        # Clear cache files
        for file in os.listdir(self.cache_dir):
            if file.endswith('.csv'):
                try:
                    os.remove(os.path.join(self.cache_dir, file))
                except Exception as e:
                    self.logger.error(f"Error removing cache file {file}: {e}") 