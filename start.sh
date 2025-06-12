#!/bin/bash

# Create a clean directory in home
mkdir -p ~/trading_bot
cd ~/trading_bot

# Copy all project files
cp -r /home/crimzor/Documents/repos,,,,,,,/ai-trading-bot/* .

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install python-binance pandas numpy ta scikit-learn joblib plotly dash dash-bootstrap-components

# Run the application
python app.py 