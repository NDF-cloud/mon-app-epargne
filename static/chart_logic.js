// Fichier : static/chart_logic.js

document.addEventListener('DOMContentLoaded', function() {
    const chartCanvas = document.getElementById('evolutionChart');
    // On récupère l'ID de l'objectif depuis l'attribut 'data-' du canvas
    const objectifId = chartCanvas.dataset.objectifId;

    // S'il n'y a pas d'ID, on ne fait rien
    if (!objectifId) return;

    fetch(`/api/chart_data/${objectifId}`)
        .then(response => response.json())
        .then(chartData => {
            const ctx = chartCanvas.getContext('2d');

            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: chartData.labels,
                    datasets: [
                        {
                            label: 'Entrées cumulées (XAF)',
                            data: chartData.data_entrees,
                            fill: true,
                            borderColor: '#0a9396',
                            backgroundColor: 'rgba(148, 210, 189, 0.2)',
                            tension: 0.1
                        },
                        {
                            label: 'Sorties cumulées (XAF)',
                            data: chartData.data_sorties,
                            fill: false,
                            borderColor: '#e63946',
                            tension: 0.1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        })
        .catch(error => console.error("Erreur lors de la récupération des données du graphique:", error));
});