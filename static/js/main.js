/**
 * SecureBank Fraud Detection System
 * Main JavaScript File
 */

// ========================================
// Initialize on DOM Load
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    initializeSidebar();
    initializeAlerts();
    initializeTooltips();
    initializeNavScroll();
    initializeAnimations();
}

// ========================================
// Sidebar Toggle
// ========================================
function initializeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
    
    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768 && sidebar) {
            if (!sidebar.contains(e.target) && !toggleBtn?.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        }
    });
}

// ========================================
// Auto-dismiss Alerts
// ========================================
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.classList.add('fade');
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    });
}

// ========================================
// Bootstrap Tooltips
// ========================================
function initializeTooltips() {
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(function(tooltip) {
        new bootstrap.Tooltip(tooltip);
    });
}

// ========================================
// Navigation Scroll Effect
// ========================================
function initializeNavScroll() {
    const nav = document.querySelector('.landing-nav');
    if (nav) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                nav.classList.add('scrolled');
            } else {
                nav.classList.remove('scrolled');
            }
        });
    }
}

// ========================================
// Scroll Animations
// ========================================
function initializeAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        animatedElements.forEach(function(el) {
            observer.observe(el);
        });
    }
}

// ========================================
// Password Toggle
// ========================================
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const passwordIcon = document.getElementById('password-icon');
    
    if (passwordInput && passwordIcon) {
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            passwordIcon.classList.remove('bi-eye');
            passwordIcon.classList.add('bi-eye-slash');
        } else {
            passwordInput.type = 'password';
            passwordIcon.classList.remove('bi-eye-slash');
            passwordIcon.classList.add('bi-eye');
        }
    }
}

// ========================================
// Fill Demo Credentials
// ========================================
function fillCredentials(username, password) {
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    
    if (usernameInput && passwordInput) {
        usernameInput.value = username;
        passwordInput.value = password;
        
        // Visual feedback
        usernameInput.classList.add('filled');
        passwordInput.classList.add('filled');
        
        setTimeout(function() {
            usernameInput.classList.remove('filled');
            passwordInput.classList.remove('filled');
        }, 500);
    }
}

// ========================================
// Format Currency
// ========================================
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// ========================================
// Format Date
// ========================================
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ========================================
// Show Loading Spinner
// ========================================
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    spinner.id = 'loading-spinner';
    element.appendChild(spinner);
}

function hideLoading() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.remove();
    }
}

// ========================================
// Confirm Dialog
// ========================================
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// ========================================
// Toast Notifications
// ========================================
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} show`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="bi bi-${getToastIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="bi bi-x"></i>
        </button>
    `;
    
    toastContainer.appendChild(toast);
    
    setTimeout(function() {
        toast.classList.add('fade-out');
        setTimeout(function() {
            toast.remove();
        }, 300);
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
    document.body.appendChild(container);
    return container;
}

function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || icons.info;
}

// ========================================
// Search Functionality
// ========================================
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = function() {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

const handleSearch = debounce(function(searchInput, tableId) {
    const filter = searchInput.value.toLowerCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.getElementsByTagName('td');
        let found = false;
        
        for (let j = 0; j < cells.length; j++) {
            if (cells[j].textContent.toLowerCase().indexOf(filter) > -1) {
                found = true;
                break;
            }
        }
        
        row.style.display = found ? '' : 'none';
    }
}, 300);

// ========================================
// Chart Utilities
// ========================================
function createDoughnutChart(ctx, data, labels, colors) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            cutout: '70%'
        }
    });
}

function createBarChart(ctx, data, labels, color) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: color,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function createLineChart(ctx, data, labels, color) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                borderColor: color,
                backgroundColor: color + '20',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ========================================
// API Helper Functions
// ========================================
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'API request failed');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message, 'error');
        throw error;
    }
}

// ========================================
// Export Data
// ========================================
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    rows.forEach(function(row) {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(function(col) {
            rowData.push('"' + col.textContent.replace(/"/g, '""') + '"');
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
}

// ========================================
// Print Functionality
// ========================================
function printElement(elementId) {
    const element = document.getElementById(elementId);
    const printWindow = window.open('', '_blank');
    
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Print</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { padding: 20px; }
                @media print {
                    .no-print { display: none; }
                }
            </style>
        </head>
        <body>
            ${element.innerHTML}
            <script>
                window.onload = function() {
                    window.print();
                    window.close();
                };
            </script>
        </body>
        </html>
    `);
    
    printWindow.document.close();
}

// ========================================
// Form Validation
// ========================================
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('[required]');
    let isValid = true;
    
    inputs.forEach(function(input) {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// ========================================
// Smooth Scroll
// ========================================
document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href !== '#') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        }
    });
});

// ========================================
// Real-time Stats Update
// ========================================
function updateStats() {
    apiRequest('/api/stats')
        .then(function(data) {
            const elements = {
                'stat-total': data.total_transactions,
                'stat-amount': formatCurrency(data.total_amount),
                'stat-fraud': data.fraud_count,
                'stat-rate': data.fraud_rate.toFixed(2) + '%'
            };
            
            Object.keys(elements).forEach(function(id) {
                const el = document.getElementById(id);
                if (el) {
                    el.textContent = elements[id];
                }
            });
        })
        .catch(function(error) {
            console.error('Failed to update stats:', error);
        });
}

// Update stats every 30 seconds if on dashboard
if (window.location.pathname.includes('dashboard')) {
    setInterval(updateStats, 30000);
}
