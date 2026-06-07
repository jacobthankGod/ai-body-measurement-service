/**
 * KORRA Analytics Engine | Block 17: Platform Intelligence
 * ========================================================
 * High-fidelity Chart.js implementations for Obsidian & Mint.
 */

window.KORRA_ANALYTICS = {
    charts: {},

    initPlatformTrends: function(ctxId, dataLabels, scanData, merchantData) {
        const ctx = document.getElementById(ctxId);
        if (!ctx) return;

        if (this.charts['trends']) this.charts['trends'].destroy();

        this.charts['trends'] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dataLabels,
                datasets: [
                    {
                        label: 'GLOBAL SCANS',
                        data: scanData,
                        borderColor: '#57D7C0',
                        backgroundColor: 'rgba(87, 215, 192, 0.1)',
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 4,
                        pointBackgroundColor: '#57D7C0'
                    },
                    {
                        label: 'NEW MERCHANTS',
                        data: merchantData,
                        borderColor: '#FFFFFF',
                        borderDash: [5, 5],
                        borderWidth: 2,
                        tension: 0,
                        fill: false,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: { color: '#737373', font: { family: 'Inter', size: 10, weight: 'bold' } }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#737373', font: { size: 10 } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#737373', font: { size: 10 } }
                    }
                }
            }
        });
    },

    initIndustryMix: function(ctxId, labels, data) {
        const ctx = document.getElementById(ctxId);
        if (!ctx) return;

        if (this.charts['mix']) this.charts['mix'].destroy();

        this.charts['mix'] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        '#57D7C0',
                        'rgba(87, 215, 192, 0.6)',
                        'rgba(87, 215, 192, 0.3)',
                        '#111111'
                    ],
                    borderColor: '#000000',
                    borderWidth: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '80%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#A3A3A3', font: { size: 10 } }
                    }
                }
            }
        });
    }
};
