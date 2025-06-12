#!/bin/bash

# Install required system packages
echo "Installing system packages..."
sudo apt update
sudo apt install -y python3-venv python3-pip

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install required packages
echo "Installing Python packages..."
pip install python-binance pandas numpy ta scikit-learn joblib plotly dash dash-bootstrap-components

# Run the application
echo "Starting the trading bot UI..."
python app.py 