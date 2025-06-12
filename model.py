"""
This module handles the machine learning model for trading signal prediction.
It loads a pre-trained model and provides functionality to make predictions on new data.
"""

import joblib
import pandas as pd
import ta

# Load the pre-trained machine learning model
model = joblib.load("model.pkl")

def predict_signal(df):
    """
    Predicts trading signals (buy/sell) based on the input dataframe.
    
    Args:
        df (pandas.DataFrame): Input dataframe containing OHLCV data
        
    Returns:
        str: 'buy' if prediction is 1, 'sell' if prediction is 0
    """
    # Add technical analysis features to the dataframe
    df = ta.add_all_ta_features(df, "open", "high", "low", "close", "volume")
    df = df.dropna()
    
    # Get the latest data point for prediction
    latest = df.iloc[-1:]
    
    # Prepare features by dropping timestamp column
    X = latest.drop(['timestamp'], axis=1, errors='ignore')
    
    # Make prediction and convert to trading signal
    prediction = model.predict(X)[0]
    return "buy" if prediction == 1 else "sell"
