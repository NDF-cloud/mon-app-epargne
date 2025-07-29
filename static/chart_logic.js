// Fichier : static/chart_logic.js
document.addEventListener('DOMContentLoaded', function() {
    const chartCanvas = document.getElementById('evolutionChart');
    if (!chartCanvas) return; // Ne fait rien si le graphique n'est pas sur la page

    const objectifId = chartCanvas.dataset.objectifId;
    if (!objectifId) return; // Ne fait rien si l'ID n'est pas trouvé

    fetch(`/api/chart_data/${objectifId}`)
        .then(response => {
            if (!response.ok) {
                // Si le serveur renvoie une erreur (ex: 403 non autorisé), on l'affiche
                throw new Error('Erreur réseau ou autorisation refusée pour les données du graphique.');
            }
            return response.json();
        })
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
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        })
        .catch(error => console.error("Erreur critique lors de la création du graphique:", error));
});