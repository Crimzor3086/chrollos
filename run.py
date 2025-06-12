#!/usr/bin/env python3

import os
import sys
import subprocess

def install_requirements():
    packages = [
        'python-binance',
        'pandas',
        'numpy',
        'ta',
        'scikit-learn',
        'joblib',
        'plotly',
        'dash',
        'dash-bootstrap-components'
    ]
    
    for package in packages:
        try:
            subprocess.run(['pipx', 'install', package], check=True)
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}")
            return False
    return True

def main():
    if install_requirements():
        try:
            import app
            app.app.run_server(debug=True, host='0.0.0.0', port=8050)
        except ImportError as e:
            print(f"Error importing app: {e}")
            sys.exit(1)
    else:
        print("Failed to install requirements")
        sys.exit(1)

if __name__ == "__main__":
    main() 