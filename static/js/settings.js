// Handle API settings form submission
document.getElementById('api-settings-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        api_key: document.getElementById('api-key').value,
        api_secret: document.getElementById('api-secret').value
    };

    try {
        const response = await fetch('/api/settings/api', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            showSuccess('API settings saved successfully');
        } else {
            showError(data.message || 'Failed to save API settings');
        }
    } catch (error) {
        showError('Error saving API settings: ' + error.message);
    }
});

// Handle trading settings form submission
document.getElementById('trading-settings-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        trading_pair: document.getElementById('trading-pair').value,
        position_size: document.getElementById('position-size').value,
        stop_loss: document.getElementById('stop-loss').value,
        take_profit: document.getElementById('take-profit').value
    };

    try {
        const response = await fetch('/api/settings/trading', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            showSuccess('Trading settings saved successfully');
        } else {
            showError(data.message || 'Failed to save trading settings');
        }
    } catch (error) {
        showError('Error saving trading settings: ' + error.message);
    }
});

// Handle notification settings form submission
document.getElementById('notification-settings-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        email_notifications: document.getElementById('email-notifications').checked,
        trade_notifications: document.getElementById('trade-notifications').checked,
        error_notifications: document.getElementById('error-notifications').checked
    };

    try {
        const response = await fetch('/api/settings/notifications', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            showSuccess('Notification settings saved successfully');
        } else {
            showError(data.message || 'Failed to save notification settings');
        }
    } catch (error) {
        showError('Error saving notification settings: ' + error.message);
    }
});

// Handle risk settings form submission
document.getElementById('risk-settings-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        max_daily_loss: document.getElementById('max-daily-loss').value,
        max_positions: document.getElementById('max-positions').value,
        leverage: document.getElementById('leverage').value
    };

    try {
        const response = await fetch('/api/settings/risk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            showSuccess('Risk settings saved successfully');
        } else {
            showError(data.message || 'Failed to save risk settings');
        }
    } catch (error) {
        showError('Error saving risk settings: ' + error.message);
    }
});

// Load current settings
async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const data = await response.json();
        
        if (data.status === 'success') {
            // API settings
            document.getElementById('api-key').value = data.api_key || '';
            document.getElementById('api-secret').value = data.api_secret || '';
            
            // Trading settings
            document.getElementById('trading-pair').value = data.trading_pair || 'BTCUSDT';
            document.getElementById('position-size').value = data.position_size || 10;
            document.getElementById('stop-loss').value = data.stop_loss || 2;
            document.getElementById('take-profit').value = data.take_profit || 4;
            
            // Notification settings
            document.getElementById('email-notifications').checked = data.email_notifications || false;
            document.getElementById('trade-notifications').checked = data.trade_notifications || false;
            document.getElementById('error-notifications').checked = data.error_notifications || false;
            
            // Risk settings
            document.getElementById('max-daily-loss').value = data.max_daily_loss || 5;
            document.getElementById('max-positions').value = data.max_positions || 3;
            document.getElementById('leverage').value = data.leverage || 1;
        }
    } catch (error) {
        console.error('Error loading settings:', error);
        showError('Error loading settings: ' + error.message);
    }
}

// Show success message
function showSuccess(message) {
    // Implement success message display
    alert(message); // Replace with better UI
}

// Show error message
function showError(message) {
    // Implement error message display
    alert(message); // Replace with better UI
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
}); 