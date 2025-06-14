// Initialize trading chart
let tradingChart;

function initializeTradingChart() {
    const ctx = document.getElementById('trading-chart').getContext('2d');
    tradingChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Price',
                data: [],
                borderColor: '#0d6efd',
                tension: 0.4,
                fill: false
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
}

// Initialize order book
function initializeOrderBook() {
    const orderBook = document.getElementById('order-book');
    // Add order book implementation
}

// Handle trading form submission
document.getElementById('trading-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        symbol: document.getElementById('symbol').value,
        orderType: document.getElementById('order-type').value,
        side: document.querySelector('[data-side].active').dataset.side,
        amount: document.getElementById('amount').value,
        price: document.getElementById('price').value
    };

    try {
        const response = await fetch('/api/place_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            showSuccess('Order placed successfully');
            updateOpenOrders();
        } else {
            showError(data.message || 'Failed to place order');
        }
    } catch (error) {
        showError('Error placing order: ' + error.message);
    }
});

// Update open orders
async function updateOpenOrders() {
    try {
        const response = await fetch('/api/open_orders');
        const data = await response.json();
        
        if (data.status === 'success') {
            const openOrders = document.getElementById('open-orders');
            openOrders.innerHTML = data.orders.map(order => `
                <div class="order-item mb-2 p-2 border rounded">
                    <div class="d-flex justify-content-between">
                        <span>${order.symbol}</span>
                        <span class="badge ${order.side === 'BUY' ? 'bg-success' : 'bg-danger'}">${order.side}</span>
                    </div>
                    <div class="small text-muted">
                        Price: ${order.price}<br>
                        Amount: ${order.amount}
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error updating open orders:', error);
    }
}

// Show success message
function showSuccess(message) {
    // Implement success message display
}

// Show error message
function showError(message) {
    // Implement error message display
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    initializeTradingChart();
    initializeOrderBook();
    updateOpenOrders();
    
    // Update data periodically
    setInterval(updateOpenOrders, 5000);
}); 