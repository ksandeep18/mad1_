/**
 * Utility functions for Chart.js integration in the Quiz Platform
 */

// Colors for charts
const chartColors = {
    primary: '#0d6efd',
    secondary: '#6c757d',
    success: '#198754',
    info: '#0dcaf0',
    warning: '#ffc107',
    danger: '#dc3545',
    light: '#f8f9fa',
    dark: '#212529'
};

/**
 * Creates a bar chart with the given data
 * @param {string} canvasId - The ID of the canvas element
 * @param {array} labels - The labels for the chart
 * @param {array} data - The data for the chart
 * @param {string} title - The title of the chart
 */
function createBarChart(canvasId, labels, data, title) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: data,
                backgroundColor: chartColors.primary,
                borderColor: chartColors.primary,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 16
                    }
                }
            }
        }
    });
}

/**
 * Creates a pie chart with the given data
 * @param {string} canvasId - The ID of the canvas element
 * @param {array} labels - The labels for the chart
 * @param {array} data - The data for the chart
 * @param {string} title - The title of the chart
 */
function createPieChart(canvasId, labels, data, title) {
    const backgroundColors = [
        chartColors.primary,
        chartColors.success,
        chartColors.warning,
        chartColors.danger,
        chartColors.info,
        chartColors.secondary
    ];
    
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 16
                    }
                }
            }
        }
    });
}

/**
 * Creates a line chart with the given data
 * @param {string} canvasId - The ID of the canvas element
 * @param {array} labels - The labels for the chart
 * @param {array} data - The data for the chart
 * @param {string} title - The title of the chart
 */
function createLineChart(canvasId, labels, data, title) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: data,
                backgroundColor: 'rgba(13, 110, 253, 0.2)',
                borderColor: chartColors.primary,
                borderWidth: 2,
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 16
                    }
                }
            }
        }
    });
}
