"""
This module implements trading strategies using various technical indicators.
It includes functions for calculating technical indicators and generating trading
signals based on a combination of multiple indicators with weighted importance.
"""

import pandas as pd
import numpy as np
import ta

def calculate_additional_indicators(df):
    """
    Calculate additional technical indicators for signal generation.
    This function adds various technical analysis indicators that are used
    in the trading strategy.

    Args:
        df (pandas.DataFrame): DataFrame containing OHLCV data

    Returns:
        pandas.DataFrame: DataFrame with added technical indicators
    """
    # Relative Strength Index (RSI) - Momentum indicator
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    
    # Moving Average Convergence Divergence (MACD)
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()  # MACD line
    df['macd_signal'] = macd.macd_signal()  # Signal line
    df['macd_diff'] = macd.macd_diff()  # MACD histogram
    
    # Bollinger Bands - Volatility indicator
    bollinger = ta.volatility.BollingerBands(df['close'])
    df['bb_upper'] = bollinger.bollinger_hband()  # Upper band
    df['bb_middle'] = bollinger.bollinger_mavg()  # Middle band
    df['bb_lower'] = bollinger.bollinger_lband()  # Lower band
    
    # Stochastic Oscillator - Momentum indicator
    stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
    df['stoch_k'] = stoch.stoch()  # %K line
    df['stoch_d'] = stoch.stoch_signal()  # %D line
    
    # Average True Range (ATR) - Volatility indicator
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
    
    # On-Balance Volume (OBV) - Volume indicator
    df['obv'] = ta.volume.on_balance_volume(df['close'], df['volume'])
    
    return df

def generate_signal(df):
    """
    Generate trading signal based on multiple indicators.
    This function combines signals from various technical indicators
    using a weighted average approach.

    Args:
        df (pandas.DataFrame): DataFrame with calculated technical indicators

    Returns:
        str: 'buy', 'sell', or 'hold' based on the combined signals
    """
    signals = []
    
    # SMA Crossover Strategy
    sma_fast = df['close'].rolling(window=5).mean()  # 5-period SMA
    sma_slow = df['close'].rolling(window=20).mean()  # 20-period SMA
    sma_signal = 1 if sma_fast.iloc[-1] > sma_slow.iloc[-1] and sma_fast.iloc[-2] <= sma_slow.iloc[-2] else \
                -1 if sma_fast.iloc[-1] < sma_slow.iloc[-1] and sma_fast.iloc[-2] >= sma_slow.iloc[-2] else 0
    signals.append(sma_signal)
    
    # RSI Strategy (Oversold/Overbought)
    rsi = df['rsi'].iloc[-1]
    rsi_signal = 1 if rsi < 30 else -1 if rsi > 70 else 0  # Buy when oversold, sell when overbought
    signals.append(rsi_signal)
    
    # MACD Crossover Strategy
    macd_signal = 1 if df['macd'].iloc[-1] > df['macd_signal'].iloc[-1] and df['macd'].iloc[-2] <= df['macd_signal'].iloc[-2] else \
                 -1 if df['macd'].iloc[-1] < df['macd_signal'].iloc[-1] and df['macd'].iloc[-2] >= df['macd_signal'].iloc[-2] else 0
    signals.append(macd_signal)
    
    # Bollinger Bands Strategy
    bb_signal = 1 if df['close'].iloc[-1] < df['bb_lower'].iloc[-1] else \
               -1 if df['close'].iloc[-1] > df['bb_upper'].iloc[-1] else 0
    signals.append(bb_signal)
    
    # Stochastic Oscillator Strategy
    stoch_signal = 1 if df['stoch_k'].iloc[-1] < 20 and df['stoch_d'].iloc[-1] < 20 else \
                  -1 if df['stoch_k'].iloc[-1] > 80 and df['stoch_d'].iloc[-1] > 80 else 0
    signals.append(stoch_signal)
    
    # Volume Confirmation Strategy
    volume_signal = 1 if df['volume'].iloc[-1] > df['volume'].rolling(window=20).mean().iloc[-1] else -1
    signals.append(volume_signal)
    
    # Combine signals using weighted average
    # Weights can be adjusted based on strategy preference and backtesting results
    weights = [0.3, 0.2, 0.2, 0.15, 0.1, 0.05]  # SMA, RSI, MACD, BB, Stochastic, Volume
    weighted_signal = np.average(signals, weights=weights)
    
    # Generate final signal based on weighted average threshold
    if weighted_signal > 0.3:  # Strong buy signal
        return 'buy'
    elif weighted_signal < -0.3:  # Strong sell signal
        return 'sell'
    return 'hold'  # Neutral signal

def sma_strategy(df):
    """
    Enhanced SMA strategy with additional technical indicators.
    This is the main strategy function that combines all indicators
    and generates the final trading signal.

    Args:
        df (pandas.DataFrame): DataFrame containing OHLCV data

    Returns:
        str: 'buy', 'sell', or 'hold' based on the combined analysis
    """
    # Calculate all technical indicators
    df = calculate_additional_indicators(df)
    
    # Generate and return the final trading signal
    return generate_signal(df)
