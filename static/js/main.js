/**
 * Ayurveda Skill Portal - Main JavaScript utilities
 * Chart.js helpers, toast notifications, and async loaders
 */

/** Create a radar chart for skill profiles */
function createRadarChart(canvasId, labels, scores) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !labels || labels.length === 0) return;

    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Skill Score',
                data: scores,
                backgroundColor: 'rgba(0, 137, 123, 0.2)',
                borderColor: 'rgba(0, 137, 123, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(0, 137, 123, 1)',
            }]
        },
        options: {
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { stepSize: 20 }
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}

/** Create a bar chart for gap analysis or analytics */
function createBarChart(canvasId, labels, values, label) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !labels || labels.length === 0) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label || 'Value',
                data: values,
                backgroundColor: 'rgba(0, 137, 123, 0.7)',
                borderColor: 'rgba(0, 137, 123, 1)',
                borderWidth: 1,
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

/** Create a grouped bar chart comparing Current Scores vs Required Target Benchmark */
function createCareerComparisonChart(canvasId, labels, currentScores, requiredScores) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !labels || labels.length === 0) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Current Score',
                    data: currentScores,
                    backgroundColor: 'rgba(0, 137, 123, 0.85)',
                    borderColor: 'rgba(0, 137, 123, 1)',
                    borderWidth: 1,
                    borderRadius: 4,
                },
                {
                    label: 'Career Target',
                    data: requiredScores,
                    backgroundColor: 'rgba(255, 152, 0, 0.75)',
                    borderColor: 'rgba(245, 124, 0, 1)',
                    borderWidth: 1,
                    borderRadius: 4,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: { boxWidth: 14, font: { size: 12 } }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        callback: function(value) { return value + '%'; }
                    },
                    title: {
                        display: true,
                        text: 'Proficiency Score (%)',
                        font: { size: 11 }
                    }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}


/** Show toast notification */
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const id = 'toast-' + Date.now();
    const bgClass = type === 'error' ? 'bg-danger' : type === 'warning' ? 'bg-warning' : 'bg-success';

    container.insertAdjacentHTML('beforeend', `
        <div id="${id}" class="toast ${bgClass} text-white" role="alert">
            <div class="toast-body">${message}</div>
        </div>
    `);

    const toastEl = document.getElementById(id);
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

/** Generic API fetch with CSRF and loading spinner */
async function apiCall(url, method = 'GET', data = null) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || document.cookie.match(/csrftoken=([^;]+)/)?.[1];

    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        credentials: 'same-origin',
    };

    if (data) options.body = JSON.stringify(data);

    const response = await fetch(url, options);
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || err.detail || 'Request failed');
    }
    return response.json();
}

/** Show/hide loading spinner on a button */
function setButtonLoading(btn, loading) {
    const spinner = btn.querySelector('.spinner-border');
    if (loading) {
        btn.disabled = true;
        spinner?.classList.remove('d-none');
    } else {
        btn.disabled = false;
        spinner?.classList.add('d-none');
    }
}
