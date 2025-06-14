// Initialize charts
let tradingHistoryChart;
let tradeDistributionChart;

function initializeCharts() {
    // Trading history chart
    const historyCtx = document.getElementById('trading-history-chart').getContext('2d');
    tradingHistoryChart = new Chart(historyCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Portfolio Value',
                data: [],
                borderColor: '#0d6efd',
                tension: 0.4,
                fill: true,
                backgroundColor: 'rgba(13, 110, 253, 0.1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });

    // Trade distribution chart
    const distributionCtx = document.getElementById('trade-distribution-chart').getContext('2d');
    tradeDistributionChart = new Chart(distributionCtx, {
        type: 'doughnut',
        data: {
            labels: ['Winning Trades', 'Losing Trades'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['#198754', '#dc3545']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// Update performance metrics
async function updatePerformanceMetrics() {
    try {
        const response = await fetch('/api/performance_metrics');
        const data = await response.json();
        
        if (data.status === 'success') {
            document.getElementById('total-return').textContent = data.total_return + '%';
            document.getElementById('win-rate').textContent = data.win_rate + '%';
            document.getElementById('avg-trade').textContent = data.avg_trade + '%';
            document.getElementById('sharpe-ratio').textContent = data.sharpe_ratio;
            document.getElementById('max-drawdown').textContent = data.max_drawdown + '%';
            document.getElementById('risk-reward').textContent = data.risk_reward;
        }
    } catch (error) {
        console.error('Error updating performance metrics:', error);
    }
}

// Update trading history
async function updateTradingHistory() {
    try {
        const response = await fetch('/api/trading_history');
        const data = await response.json();
        
        if (data.status === 'success') {
            tradingHistoryChart.data.labels = data.history.map(h => h.date);
            tradingHistoryChart.data.datasets[0].data = data.history.map(h => h.value);
            tradingHistoryChart.update();
        }
    } catch (error) {
        console.error('Error updating trading history:', error);
    }
}

// Update trade distribution
async function updateTradeDistribution() {
    try {
        const response = await fetch('/api/trade_distribution');
        const data = await response.json();
        
        if (data.status === 'success') {
            tradeDistributionChart.data.datasets[0].data = [
                data.winning_trades,
                data.losing_trades
            ];
            tradeDistributionChart.update();
        }
    } catch (error) {
        console.error('Error updating trade distribution:', error);
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    updatePerformanceMetrics();
    updateTradingHistory();
    updateTradeDistribution();
    
    // Update data periodically
    setInterval(() => {
        updatePerformanceMetrics();
        updateTradingHistory();
        updateTradeDistribution();
    }, 30000);
}); 