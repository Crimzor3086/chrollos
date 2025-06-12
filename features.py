"""
This module provides functionality for calculating technical analysis indicators
that are used as features for the trading model. It includes various technical
indicators such as moving averages, RSI, MACD, and Bollinger Bands.
"""

import pandas as pd
import ta

def calculate_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates technical indicators and adds them to the DataFrame.
    This function adds several technical analysis indicators that are commonly
    used in trading strategies.

    Args:
        df: Pandas DataFrame with at least 'high', 'low', 'close', 'volume' columns.
            It's assumed the 'close' column is numeric.

    Returns:
        Pandas DataFrame with added technical indicator columns including:
        - SMA (Simple Moving Averages) for fast and slow periods
        - RSI (Relative Strength Index)
        - MACD (Moving Average Convergence Divergence) and its components
        - Bollinger Bands and related indicators
    """
    # Ensure 'close' is numeric (it should be from bot.py's get_data)
    df['close'] = pd.to_numeric(df['close'])

    # Simple Moving Averages (SMA)
    # Fast SMA (5 periods) for short-term trend
    df['sma_fast'] = ta.trend.sma_indicator(df['close'], window=5)
    # Slow SMA (20 periods) for long-term trend
    df['sma_slow'] = ta.trend.sma_indicator(df['close'], window=20)

    # Relative Strength Index (RSI)
    # Standard 14-period RSI for momentum
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)

    # Moving Average Convergence Divergence (MACD)
    # MACD is calculated using 12 and 26 periods by default
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()  # MACD line
    df['macd_signal'] = macd.macd_signal()  # Signal line
    df['macd_diff'] = macd.macd_diff()  # MACD histogram

    # Bollinger Bands
    # Standard 20-period Bollinger Bands with 2 standard deviations
    bollinger = ta.volatility.BollingerBands(df['close'])
    df['bb_upper'] = bollinger.bollinger_hband()  # Upper band
    df['bb_middle'] = bollinger.bollinger_mavg()  # Middle band (20-period SMA)
    df['bb_lower'] = bollinger.bollinger_lband()  # Lower band
    df['bb_width'] = bollinger.bollinger_wband()  # Bandwidth indicator
    df['bb_pband'] = bollinger.bollinger_pband()  # %B indicator

    # Drop rows with NaN values created by indicators (especially at the beginning)
    # df.dropna(inplace=True) # We'll handle NaNs in train_model.py after target creation

    return df

if __name__ == '__main__':
    # Example usage with sample data
    # This section is for testing the function if run directly
    data = {
        'timestamp': pd.to_datetime(['2023-01-01 00:00:00', '2023-01-01 00:01:00', '2023-01-01 00:02:00'] * 10),
        'open': [100, 101, 102, 103, 102, 101, 100, 99, 100, 101] * 3,
        'high': [102, 103, 104, 105, 104, 103, 102, 101, 102, 103] * 3,
        'low': [99, 100, 101, 102, 101, 100, 99, 98, 99, 100] * 3,
        'close': [101, 102, 103, 104, 103, 102, 101, 100, 101, 102] * 3,
        'volume': [10, 12, 15, 13, 14, 16, 11, 9, 10, 12] * 3
    }
    sample_df = pd.DataFrame(data)
    sample_df['close'] = pd.to_numeric(sample_df['close'])

    # Generate more realistic sample data with slight price variations
    sample_data_list = []
    base_close = 100
    for i in range(50):  # Generate 50 data points
        base_close += (i % 5 - 2) * 0.1  # Add slight price variation
        sample_data_list.append({
            'timestamp': pd.Timestamp('2023-01-01') + pd.Timedelta(minutes=i),
            'open': base_close - 0.5,
            'high': base_close + 1,
            'low': base_close - 1,
            'close': base_close,
            'volume': 100 + i % 10
        })
    sample_df_large = pd.DataFrame(sample_data_list)
    sample_df_large['close'] = pd.to_numeric(sample_df_large['close'])

    # Display results
    print("Original DataFrame:")
    print(sample_df_large.head())
    
    featured_df = calculate_technical_features(sample_df_large.copy())
    
    print("\nDataFrame with Technical Features:")
    print(featured_df.head(25))
    print("\nDataFrame Info:")
    featured_df.info()
