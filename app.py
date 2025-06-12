import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import threading
import time
from bot import TradingBot
import logging

# Initialize the bot
bot = TradingBot()

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "AI Trading Bot Dashboard"

# Layout components
def create_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("AI Trading Bot Dashboard", className="text-center mb-4"),
                html.Div(id="last-update", className="text-center mb-4")
            ])
        ]),
        
        dbc.Row([
            # Trading Status Card
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Trading Status"),
                    dbc.CardBody([
                        html.Div(id="position-status"),
                        html.Div(id="entry-price"),
                        html.Div(id="current-price"),
                        html.Div(id="pnl")
                    ])
                ], className="mb-4")
            ], width=4),
            
            # Account Balance Card
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Account Balance"),
                    dbc.CardBody([
                        html.Div(id="usdt-balance"),
                        html.Div(id="btc-balance")
                    ])
                ], className="mb-4")
            ], width=4),
            
            # Controls Card
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Bot Controls"),
                    dbc.CardBody([
                        dbc.Button("Start Bot", id="start-bot", color="success", className="me-2"),
                        dbc.Button("Stop Bot", id="stop-bot", color="danger", className="me-2"),
                        dbc.Button("Close Position", id="close-position", color="warning"),
                        html.Div(id="bot-status", className="mt-3")
                    ])
                ], className="mb-4")
            ], width=4)
        ]),
        
        dbc.Row([
            # Main Chart
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Price Chart"),
                    dbc.CardBody([
                        dcc.Graph(id="price-chart"),
                        dcc.Interval(id="chart-update", interval=5000)  # Update every 5 seconds
                    ])
                ])
            ], width=12)
        ]),
        
        dbc.Row([
            # Data Quality Dashboard
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Data Quality"),
                    dbc.CardBody([
                        dcc.Graph(id="quality-chart"),
                        dcc.Interval(id="quality-update", interval=30000)  # Update every 30 seconds
                    ])
                ])
            ], width=12)
        ])
    ], fluid=True)

app.layout = create_layout()

# Callbacks
@app.callback(
    [Output("position-status", "children"),
     Output("entry-price", "children"),
     Output("current-price", "children"),
     Output("pnl", "children"),
     Output("usdt-balance", "children"),
     Output("btc-balance", "children"),
     Output("last-update", "children")],
    [Input("chart-update", "n_intervals")]
)
def update_status(n):
    try:
        # Get current position info
        position = bot.position
        entry_price = bot.entry_price
        current_price = float(bot.client.get_symbol_ticker(symbol=bot.symbol)['price'])
        
        # Calculate PnL
        pnl = 0
        if position and entry_price:
            pnl = ((current_price - entry_price) / entry_price) * 100
            if position == 'SELL':
                pnl = -pnl
        
        # Get account balances
        usdt_balance = bot.get_account_balance()
        btc_balance = 0
        for asset in bot.client.get_account()['balances']:
            if asset['asset'] == 'BTC':
                btc_balance = float(asset['free'])
        
        return [
            f"Position: {position if position else 'None'}",
            f"Entry Price: ${entry_price:.2f}" if entry_price else "Entry Price: N/A",
            f"Current Price: ${current_price:.2f}",
            f"PnL: {pnl:.2f}%" if position else "PnL: N/A",
            f"USDT Balance: ${usdt_balance:.2f}",
            f"BTC Balance: {btc_balance:.8f}",
            f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
    except Exception as e:
        logging.error(f"Error updating status: {e}")
        return ["Error"] * 7

@app.callback(
    Output("price-chart", "figure"),
    [Input("chart-update", "n_intervals")]
)
def update_price_chart(n):
    try:
        # Get data for all timeframes
        data_dict = bot.data_manager.get_multiple_timeframes(
            bot.symbol, bot.intervals, bot.lookback
        )
        
        # Create figure with subplots
        fig = make_subplots(rows=len(data_dict), cols=1,
                          shared_xaxes=True,
                          vertical_spacing=0.05)
        
        for i, (interval, df) in enumerate(data_dict.items(), 1):
            # Add candlestick
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
            
            # Add volume
            fig.add_trace(
                go.Bar(
                    x=df['timestamp'],
                    y=df['volume'],
                    name=f'Volume {interval}',
                    showlegend=False
                ),
                row=i, col=1
            )
        
        fig.update_layout(
            title=f"{bot.symbol} - Multiple Timeframes",
            height=300 * len(data_dict),
            template="plotly_dark",
            xaxis_rangeslider_visible=False
        )
        
        return fig
    except Exception as e:
        logging.error(f"Error updating price chart: {e}")
        return go.Figure()

@app.callback(
    Output("quality-chart", "figure"),
    [Input("quality-update", "n_intervals")]
)
def update_quality_chart(n):
    try:
        quality_metrics = bot.data_manager.get_data_quality_report()
        
        # Create figure with subplots
        fig = make_subplots(rows=3, cols=1,
                          subplot_titles=('Timestamp Issues', 'Price Issues', 'Volume Issues'))
        
        # Prepare data for visualization
        symbols = list(quality_metrics.keys())
        timestamp_issues = []
        price_issues = []
        volume_issues = []
        
        for symbol in symbols:
            metrics = quality_metrics[symbol]
            timestamp_issues.append({
                'gaps': metrics['timestamp']['gaps'],
                'duplicates': metrics['timestamp']['duplicates']
            })
            price_issues.append({
                'missing': sum(metrics['price']['missing'].values()),
                'zeros': sum(metrics['price']['zeros'].values())
            })
            volume_issues.append({
                'missing': metrics['volume']['missing'],
                'zeros': metrics['volume']['zeros']
            })
        
        # Add traces
        fig.add_trace(
            go.Bar(x=symbols, y=[d['gaps'] for d in timestamp_issues], name='Gaps'),
            row=1, col=1
        )
        fig.add_trace(
            go.Bar(x=symbols, y=[d['missing'] for d in price_issues], name='Missing'),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(x=symbols, y=[d['missing'] for d in volume_issues], name='Missing'),
            row=3, col=1
        )
        
        fig.update_layout(
            title='Data Quality Metrics',
            height=600,
            template="plotly_dark",
            barmode='group'
        )
        
        return fig
    except Exception as e:
        logging.error(f"Error updating quality chart: {e}")
        return go.Figure()

@app.callback(
    [Output("bot-status", "children"),
     Output("start-bot", "disabled"),
     Output("stop-bot", "disabled")],
    [Input("start-bot", "n_clicks"),
     Input("stop-bot", "n_clicks"),
     Input("close-position", "n_clicks")],
    [State("bot-status", "children")]
)
def control_bot(start_clicks, stop_clicks, close_clicks, current_status):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "Bot Status: Stopped", False, True
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "start-bot":
        # Start bot in a separate thread
        threading.Thread(target=bot.trade, daemon=True).start()
        return "Bot Status: Running", True, False
    elif button_id == "stop-bot":
        # Stop bot (implement stop mechanism in bot class)
        return "Bot Status: Stopped", False, True
    elif button_id == "close-position":
        bot.close_position()
        return current_status, False, True
    
    return current_status, False, True

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8050) 