document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const darkModeToggle = document.getElementById('darkModeToggle');
    const defaultVolume = document.getElementById('defaultVolume');
    const saveButton = document.querySelector('.save-button');

    // Load saved settings
    loadSettings();

    // Event listeners
    darkModeToggle.addEventListener('change', function() {
        document.body.classList.toggle('dark-mode', this.checked);
    });

    defaultVolume.addEventListener('change', function() {
        // Update volume display if needed
        updateVolumeValue(this.value);
    });

    saveButton.addEventListener('click', saveSettings);

    // Load settings from localStorage
    function loadSettings() {
        // Dark mode setting
        const darkMode = localStorage.getItem('darkMode') === 'true';
        darkModeToggle.checked = darkMode;
        document.body.classList.toggle('dark-mode', darkMode);

        // Volume setting
        const volume = localStorage.getItem('defaultVolume') || '50';
        defaultVolume.value = volume;
        updateVolumeValue(volume);
    }

    // Save settings
    function saveSettings() {
        // Save to localStorage
        localStorage.setItem('darkMode', darkModeToggle.checked);
        localStorage.setItem('defaultVolume', defaultVolume.value);

        // Save to server
        fetch('/save_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                darkMode: darkModeToggle.checked,
                defaultVolume: parseInt(defaultVolume.value)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Configuración guardada correctamente', 'success');
            } else {
                showNotification('Error al guardar la configuración', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error al guardar la configuración', 'error');
        });
    }

    // Helper function to update volume display
    function updateVolumeValue(value) {
        // You can add a volume display element if needed
        console.log(`Volume: ${value}%`);
    }

    // Notification system
    function showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        // Add notification styles if not already in CSS
        const style = document.createElement('style');
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 25px;
                border-radius: 5px;
                color: white;
                font-weight: bold;
                opacity: 0;
                transform: translateY(-20px);
                animation: slideIn 0.3s forwards;
                z-index: 1000;
            }
            .notification.success {
                background-color: #1db954;
            }
            .notification.error {
                background-color: #ff4444;
            }
            @keyframes slideIn {
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        document.head.appendChild(style);

        document.body.appendChild(notification);

        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s forwards';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
});