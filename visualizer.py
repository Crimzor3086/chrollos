"""
This module provides visualization capabilities for market data using Plotly.
It includes functionality for creating interactive candlestick charts,
multi-timeframe analysis, and data quality dashboards.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List
import logging
from datetime import datetime
import webbrowser
import os

class MarketVisualizer:
    """
    A class for creating interactive market data visualizations.
    
    This class provides methods to create various types of charts and dashboards
    for analyzing market data, including candlestick charts with indicators,
    multi-timeframe analysis, and data quality monitoring.
    """
    
    def __init__(self, output_dir: str = 'charts'):
        """
        Initialize the MarketVisualizer with an output directory.
        
        Args:
            output_dir (str): Directory where chart files will be saved
        """
        self.output_dir = output_dir
        self.logger = logging.getLogger('MarketVisualizer')
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
    def create_candlestick_chart(self, 
                                df: pd.DataFrame, 
                                symbol: str, 
                                interval: str,
                                indicators: Dict = None) -> str:
        """
        Create an interactive candlestick chart with optional technical indicators.
        
        This method creates a two-panel chart:
        - Upper panel: Candlestick chart with optional technical indicators
        - Lower panel: Volume bars
        
        Args:
            df (pd.DataFrame): OHLCV data
            symbol (str): Trading pair symbol
            interval (str): Time interval
            indicators (Dict, optional): Dictionary of technical indicators to plot
            
        Returns:
            str: Path to the saved HTML chart file, or None if creation failed
        """
        try:
            # Create figure with secondary y-axis
            fig = make_subplots(rows=2, cols=1, 
                              shared_xaxes=True,
                              vertical_spacing=0.03,
                              row_heights=[0.7, 0.3])

            # Add candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='OHLC'
                ),
                row=1, col=1
            )

            # Add volume bars
            fig.add_trace(
                go.Bar(
                    x=df['timestamp'],
                    y=df['volume'],
                    name='Volume'
                ),
                row=2, col=1
            )

            # Add technical indicators if provided
            if indicators:
                for name, data in indicators.items():
                    if isinstance(data, pd.Series):
                        fig.add_trace(
                            go.Scatter(
                                x=df['timestamp'],
                                y=data,
                                name=name,
                                line=dict(width=1)
                            ),
                            row=1, col=1
                        )

            # Update layout with dark theme
            fig.update_layout(
                title=f'{symbol} - {interval}',
                yaxis_title='Price',
                yaxis2_title='Volume',
                xaxis_rangeslider_visible=False,
                template='plotly_dark'
            )

            # Save the chart as interactive HTML
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{symbol}_{interval}_{timestamp}.html'
            filepath = os.path.join(self.output_dir, filename)
            fig.write_html(filepath)
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error creating chart: {e}")
            return None
            
    def create_multi_timeframe_chart(self,
                                   data_dict: Dict[str, pd.DataFrame],
                                   symbol: str) -> str:
        """
        Create a chart showing multiple timeframes for the same symbol.
        
        This method creates a stacked chart with one panel per timeframe,
        each showing candlestick data and volume.
        
        Args:
            data_dict (Dict[str, pd.DataFrame]): Dictionary of dataframes for each timeframe
            symbol (str): Trading pair symbol
            
        Returns:
            str: Path to the saved HTML chart file, or None if creation failed
        """
        try:
            # Create figure with subplots for each timeframe
            n_timeframes = len(data_dict)
            fig = make_subplots(rows=n_timeframes, cols=1,
                              shared_xaxes=True,
                              vertical_spacing=0.05)

            # Add candlestick and volume for each timeframe
            for i, (interval, df) in enumerate(data_dict.items(), 1):
                # Add candlestick chart
                fig.add_trace(
                    go.Candlestick(
                        x=df['timestamp'],
                        open=df['open'],
                        high=df['high'],
                        low=df['low'],
                        close=df['close'],
                        name=f'{interval}'
                    ),
                    row=i, col=1
                )

                # Add volume bars
                fig.add_trace(
                    go.Bar(
                        x=df['timestamp'],
                        y=df['volume'],
                        name=f'Volume {interval}',
                        showlegend=False
                    ),
                    row=i, col=1
                )

            # Update layout with dark theme
            fig.update_layout(
                title=f'{symbol} - Multiple Timeframes',
                height=300 * n_timeframes,  # Adjust height based on number of timeframes
                xaxis_rangeslider_visible=False,
                template='plotly_dark'
            )

            # Save the chart as interactive HTML
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{symbol}_multi_timeframe_{timestamp}.html'
            filepath = os.path.join(self.output_dir, filename)
            fig.write_html(filepath)
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error creating multi-timeframe chart: {e}")
            return None
            
    def create_data_quality_dashboard(self,
                                    quality_metrics: Dict) -> str:
        """
        Create a dashboard showing data quality metrics.
        
        This method creates a three-panel dashboard showing:
        1. Timestamp-related issues (gaps, duplicates)
        2. Price-related issues (missing, zeros, negative values)
        3. Volume-related issues (missing, zeros, negative values)
        
        Args:
            quality_metrics (Dict): Dictionary containing quality metrics for each symbol
            
        Returns:
            str: Path to the saved HTML dashboard file, or None if creation failed
        """
        try:
            # Create figure with subplots for each metric type
            fig = make_subplots(rows=3, cols=1,
                              subplot_titles=('Timestamp Issues', 'Price Issues', 'Volume Issues'))

            # Prepare data for visualization
            symbols = list(quality_metrics.keys())
            timestamp_issues = []
            price_issues = []
            volume_issues = []

            # Process metrics for each symbol
            for symbol in symbols:
                metrics = quality_metrics[symbol]
                
                # Timestamp issues
                timestamp_issues.append({
                    'gaps': metrics['timestamp']['gaps'],
                    'duplicates': metrics['timestamp']['duplicates']
                })
                
                # Price issues
                price_issues.append({
                    'missing': sum(metrics['price']['missing'].values()),
                    'zeros': sum(metrics['price']['zeros'].values()),
                    'negative': sum(metrics['price']['negative'].values())
                })
                
                # Volume issues
                volume_issues.append({
                    'missing': metrics['volume']['missing'],
                    'zeros': metrics['volume']['zeros'],
                    'negative': metrics['volume']['negative']
                })

            # Add timestamp issues to the first panel
            fig.add_trace(
                go.Bar(
                    x=symbols,
                    y=[d['gaps'] for d in timestamp_issues],
                    name='Timestamp Gaps'
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Bar(
                    x=symbols,
                    y=[d['duplicates'] for d in timestamp_issues],
                    name='Duplicate Timestamps'
                ),
                row=1, col=1
            )

            # Add price issues to the second panel
            fig.add_trace(
                go.Bar(
                    x=symbols,
                    y=[d['missing'] for d in price_issues],
                    name='Missing Prices'
                ),
                row=2, col=1
            )
            fig.add_trace(
                go.Bar(
                    x=symbols,
                    y=[d['zeros'] for d in price_issues],
                    name='Zero Prices'
                ),
                row=2, col=1
            )

            # Add volume issues to the third panel
            fig.add_trace(
                go.Bar(
                    x=symbols,
                    y=[d['missing'] for d in volume_issues],
                    name='Missing Volume'
                ),
                row=3, col=1
            )
            fig.add_trace(
                go.Bar(
                    x=symbols,
                    y=[d['zeros'] for d in volume_issues],
                    name='Zero Volume'
                ),
                row=3, col=1
            )

            # Update layout with dark theme
            fig.update_layout(
                title='Data Quality Dashboard',
                height=900,
                template='plotly_dark',
                barmode='group'
            )

            # Save the dashboard as interactive HTML
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data_quality_dashboard_{timestamp}.html'
            filepath = os.path.join(self.output_dir, filename)
            fig.write_html(filepath)
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error creating data quality dashboard: {e}")
            return None
            
    def open_chart(self, filepath: str):
        """
        Open a chart in the default web browser.
        
        Args:
            filepath (str): Path to the HTML chart file
        """
        try:
            webbrowser.open('file://' + os.path.abspath(filepath))
        except Exception as e:
            self.logger.error(f"Error opening chart: {e}") 