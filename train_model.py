"""
This module implements the training pipeline for the trading model.
It includes functionality for:
- Fetching historical market data from Binance
- Calculating technical indicators as features
- Creating target variables for classification
- Training and evaluating a Random Forest model
- Saving the trained model and scaler for later use
"""

import pandas as pd
import numpy as np
from binance.client import Client
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib
import time

# Import configuration and feature calculation functions
from config import API_KEY, API_SECRET 
from features import calculate_technical_features

# --- Configuration Parameters ---
SYMBOL = 'BTCUSDT'  # Trading pair to analyze
INTERVAL = Client.KLINE_INTERVAL_1HOUR  # Using 1-hour interval for more substantial data
DATA_START_STRING = "2 years ago UTC"  # Historical data start time
MODEL_FILENAME = 'trading_model.joblib'  # Output file for trained model
SCALER_FILENAME = 'scaler.joblib'  # Output file for feature scaler
TARGET_SHIFT_PERIODS = 1  # Number of periods ahead to predict
PRICE_CHANGE_THRESHOLD = 0.005  # 0.5% price change threshold for buy/sell signals

# Initialize Binance client
client = Client(API_KEY, API_SECRET)

def get_historical_data(symbol, interval, start_str):
    """
    Fetches historical klines (candlestick data) from Binance.
    
    This function uses a generator to efficiently fetch large amounts of historical data
    and converts it into a pandas DataFrame with proper data types.
    
    Args:
        symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
        interval (str): Candlestick interval (e.g., '1h', '4h', '1d')
        start_str (str): Start time for historical data
        
    Returns:
        pd.DataFrame: DataFrame containing OHLCV data with proper data types
    """
    print(f"Fetching historical data for {symbol} from {start_str} with interval {interval}")
    klines_generator = client.get_historical_klines_generator(symbol, interval, start_str)
    all_klines = list(klines_generator) 

    if not all_klines:
        print(f"No kline data returned for {symbol} with start_str {start_str} and interval {interval}.")
        return pd.DataFrame()

    # Convert API response to DataFrame
    df = pd.DataFrame(all_klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Convert numeric columns
    cols_to_numeric = ['open', 'high', 'low', 'close', 'volume']
    for col in cols_to_numeric:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # Remove rows with missing values
    df.dropna(subset=['open', 'high', 'low', 'close', 'volume'], inplace=True)
        
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]


def create_target_variable(df, shift_periods=1, price_change_threshold=0.005):
    """
    Creates a target variable for classification based on future price movements.
    
    The target variable is defined as:
    - 1 (Buy): If price increases by threshold% in N periods
    - -1 (Sell): If price decreases by threshold% in N periods
    - 0 (Hold): If price change is within threshold%
    
    Args:
        df (pd.DataFrame): DataFrame with OHLCV data
        shift_periods (int): Number of periods to look ahead
        price_change_threshold (float): Minimum price change to trigger buy/sell signal
        
    Returns:
        pd.DataFrame: DataFrame with added target variable
    """
    # Calculate future closing price
    df['future_close'] = df['close'].shift(-shift_periods)
    
    # Calculate percentage change
    df['price_change_pct'] = (df['future_close'] - df['close']) / df['close']

    # Define target variable
    df['target'] = 0  # Default to hold
    df.loc[df['price_change_pct'] > price_change_threshold, 'target'] = 1  # Buy signal
    df.loc[df['price_change_pct'] < -price_change_threshold, 'target'] = -1  # Sell signal
    
    # Clean up intermediate columns
    df.drop(columns=['future_close', 'price_change_pct'], inplace=True)
    return df


def main():
    """
    Main function to execute the model training pipeline.
    
    The pipeline includes:
    1. Fetching historical data
    2. Calculating technical features
    3. Creating target variables
    4. Preprocessing data
    5. Training and evaluating the model
    6. Saving the model and scaler
    """
    print(f"Fetching historical data for {SYMBOL}...")
    df_raw = get_historical_data(SYMBOL, INTERVAL, DATA_START_STRING)
    if df_raw.empty:
        print("No data fetched. Exiting.")
        return
    print(f"Fetched {len(df_raw)} data points.")

    print("Calculating technical features...")
    # Calculate technical indicators
    df_features = calculate_technical_features(df_raw.copy())

    print("Creating target variable...")
    # Create target variable for classification
    df_processed = create_target_variable(df_features.copy(), 
                                        shift_periods=TARGET_SHIFT_PERIODS, 
                                        price_change_threshold=PRICE_CHANGE_THRESHOLD)

    # --- Data Preprocessing ---
    # Remove rows with missing values
    df_processed.dropna(inplace=True)
    if df_processed.empty:
        print("DataFrame is empty after NaN removal. Check data, feature calculation, or target definition. Exiting.")
        return
        
    print(f"Data shape after NaN removal: {df_processed.shape}")
    print("Target distribution (0: Hold, 1: Buy, -1: Sell):")
    print(df_processed['target'].value_counts(normalize=True).sort_index())

    # Select feature columns (exclude timestamp, price data, and target)
    feature_columns = [col for col in df_processed.columns if col not in 
                      ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'target']]
    
    X = df_processed[feature_columns]
    y = df_processed['target']

    if X.empty or y.empty:
        print("Features (X) or target (y) is empty. This could be due to all data being NaNs or an issue in feature selection. Exiting.")
        return

    # Check if we can use stratified sampling
    unique_classes, counts = np.unique(y, return_counts=True)
    can_stratify = len(unique_classes) > 1 and all(c >= 2 for c in counts)

    # Split data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, 
        stratify=y if can_stratify else None, 
        shuffle=True
    )

    if X_train.empty or y_train.empty:
        print("Training set is empty after split. Check data volume or split ratio. Exiting.")
        return

    print(f"Training data shape: {X_train.shape}, Test data shape: {X_test.shape}")

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("Training RandomForestClassifier model...")
    # Initialize and train the model
    model = RandomForestClassifier(
        n_estimators=100,  # Number of trees
        random_state=42,   # For reproducibility
        class_weight='balanced',  # Handle class imbalance
        n_jobs=-1  # Use all available CPU cores
    )
    model.fit(X_train_scaled, y_train)

    print("\nEvaluating model...")
    # Make predictions
    y_pred_train = model.predict(X_train_scaled)
    y_pred_test = model.predict(X_test_scaled)

    # Prepare classification report labels
    expected_labels = sorted(list(set(y_train) | set(y_test)))
    target_names_report = None
    if set(expected_labels).issubset({-1, 0, 1}):
        label_map = {-1: 'Sell (-1)', 0: 'Hold (0)', 1: 'Buy (1)'}
        actual_report_labels = sorted([l for l in label_map.keys() if l in expected_labels])
        target_names_report = [label_map[l] for l in actual_report_labels]
        if not target_names_report: 
            target_names_report = None 
    else:
        actual_report_labels = expected_labels

    # Print model performance metrics
    print("\nTraining Set Performance:")
    print(f"Accuracy: {accuracy_score(y_train, y_pred_train):.4f}")
    print(classification_report(y_train, y_pred_train, 
                              zero_division=0, 
                              labels=actual_report_labels, 
                              target_names=target_names_report))

    print("\nTest Set Performance:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred_test):.4f}")
    print(classification_report(y_test, y_pred_test, 
                              zero_division=0, 
                              labels=actual_report_labels, 
                              target_names=target_names_report))
    
    # Analyze feature importance
    importances = model.feature_importances_
    feature_importance_df = pd.DataFrame({
        'feature': feature_columns, 
        'importance': importances
    })
    feature_importance_df = feature_importance_df.sort_values(
        by='importance', 
        ascending=False
    )
    print("\nFeature Importances:")
    print(feature_importance_df.head(10))

    # Save the trained model and scaler
    print(f"\nSaving model to {MODEL_FILENAME}...")
    joblib.dump(model, MODEL_FILENAME)
    print(f"Saving scaler to {SCALER_FILENAME}...")
    joblib.dump(scaler, SCALER_FILENAME) 
    print("Model and scaler saved.")

if __name__ == "__main__":
    main()
