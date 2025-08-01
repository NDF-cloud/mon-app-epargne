// Fonctions d'exportation pour les rapports
class ExportManager {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Boutons d'export dans les rapports
        document.addEventListener('DOMContentLoaded', () => {
            const exportButtons = document.querySelectorAll('[data-export]');
            exportButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    const exportType = button.getAttribute('data-export');
                    this.handleExport(exportType);
                });
            });
        });
    }

    async handleExport(exportType) {
        try {
            this.showLoading(exportType);

            switch (exportType) {
                case 'pdf':
                    await this.exportPDF();
                    break;
                case 'excel':
                    await this.exportExcel();
                    break;
                case 'charts':
                    await this.exportCharts();
                    break;
                case 'print':
                    await this.exportPrint();
                    break;
                default:
                    console.error('Type d\'export non reconnu:', exportType);
            }
        } catch (error) {
            console.error('Erreur lors de l\'export:', error);
            this.showError('Erreur lors de l\'export: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async exportPDF() {
        try {
            const response = await fetch('/export/pdf', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                // Utiliser html2pdf.js pour générer le PDF côté client
                if (typeof html2pdf !== 'undefined') {
                    const element = document.createElement('div');
                    element.innerHTML = data.html;
                    element.style.position = 'absolute';
                    element.style.left = '-9999px';
                    document.body.appendChild(element);

                    const opt = {
                        margin: [0.5, 0.5, 0.5, 0.5],
                        filename: data.filename,
                        image: { type: 'jpeg', quality: 0.98 },
                        html2canvas: {
                            scale: 2,
                            useCORS: true,
                            allowTaint: true
                        },
                        jsPDF: {
                            unit: 'in',
                            format: 'a4',
                            orientation: 'portrait'
                        }
                    };

                    try {
                        await html2pdf().set(opt).from(element).save();
                        this.showSuccess('PDF généré avec succès !');
                    } catch (pdfError) {
                        console.error('Erreur lors de la génération PDF:', pdfError);
                        // Fallback: ouvrir dans une nouvelle fenêtre pour impression
                        const newWindow = window.open('', '_blank');
                        newWindow.document.write(data.html);
                        newWindow.document.close();
                        setTimeout(() => {
                            newWindow.print();
                        }, 1000);
                        this.showSuccess('PDF prêt pour impression !');
                    } finally {
                        document.body.removeChild(element);
                    }
                } else {
                    // Fallback: ouvrir dans une nouvelle fenêtre pour impression
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(data.html);
                    newWindow.document.close();
                    setTimeout(() => {
                        newWindow.print();
                    }, 1000);
                    this.showSuccess('PDF prêt pour impression !');
                }
            } else {
                this.showError('Erreur lors de la génération du PDF: ' + (data.error || 'Erreur inconnue'));
            }
        } catch (error) {
            console.error('Erreur lors de l\'export PDF:', error);
            this.showError('Erreur lors de l\'export PDF: ' + error.message);
        }
    }

    async exportExcel() {
        try {
            const response = await fetch('/export/excel', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                // Créer et télécharger le fichier CSV
                const blob = new Blob([data.csv], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');

                if (link.download !== undefined) {
                    const url = URL.createObjectURL(blob);
                    link.setAttribute('href', url);
                    link.setAttribute('download', data.filename);
                    link.style.visibility = 'hidden';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    URL.revokeObjectURL(url); // Libérer la mémoire
                    this.showSuccess('Fichier Excel téléchargé avec succès !');
                } else {
                    // Fallback pour les navigateurs plus anciens
                    const csvContent = 'data:text/csv;charset=utf-8,' + encodeURIComponent(data.csv);
                    window.open(csvContent);
                    this.showSuccess('Fichier Excel prêt !');
                }
            } else {
                this.showError('Erreur lors de la génération du fichier Excel: ' + (data.error || 'Erreur inconnue'));
            }
        } catch (error) {
            console.error('Erreur lors de l\'export Excel:', error);
            this.showError('Erreur lors de l\'export Excel: ' + error.message);
        }
    }

    async exportCharts() {
        const response = await fetch('/export/charts', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        if (data.success) {
            // Créer une nouvelle fenêtre avec les graphiques
            const chartWindow = window.open('', '_blank', 'width=800,height=600');
            chartWindow.document.write(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Graphiques d'Épargne</title>
                    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .chart-container { margin-bottom: 30px; }
                        .stats { display: flex; justify-content: space-around; margin-bottom: 20px; }
                        .stat { text-align: center; padding: 10px; border: 1px solid #ddd; }
                    </style>
                </head>
                <body>
                    <h1>Graphiques d'Épargne</h1>
                    <div class="stats">
                        <div class="stat">
                            <h3>Total Épargne</h3>
                            <p>${this.formatCurrency(data.chart_data.stats.total_epargne)}</p>
                        </div>
                        <div class="stat">
                            <h3>Objectifs Actifs</h3>
                            <p>${data.chart_data.stats.total_objectifs}</p>
                        </div>
                        <div class="stat">
                            <h3>Taux de Réussite</h3>
                            <p>${data.chart_data.stats.taux_reussite.toFixed(1)}%</p>
                        </div>
                    </div>
                    <div class="chart-container">
                        <canvas id="objectifsChart" width="400" height="200"></canvas>
                    </div>
                    <div class="chart-container">
                        <canvas id="tachesChart" width="400" height="200"></canvas>
                    </div>
                </body>
                </html>
            `);

            // Attendre que la page soit chargée puis créer les graphiques
            chartWindow.onload = () => {
                const objectifsCtx = chartWindow.document.getElementById('objectifsChart').getContext('2d');
                new Chart(objectifsCtx, {
                    type: 'bar',
                    data: {
                        labels: data.chart_data.objectifs.map(obj => obj.nom),
                        datasets: [{
                            label: 'Montant Actuel',
                            data: data.chart_data.objectifs.map(obj => obj.montant_actuel),
                            backgroundColor: '#667eea'
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: { y: { beginAtZero: true } }
                    }
                });

                const tachesCtx = chartWindow.document.getElementById('tachesChart').getContext('2d');
                new Chart(tachesCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Terminées', 'En cours'],
                        datasets: [{
                            data: [data.chart_data.stats.taches_terminees, data.chart_data.stats.total_taches - data.chart_data.stats.taches_terminees],
                            backgroundColor: ['#28a745', '#ffc107']
                        }]
                    }
                });
            };

            this.showSuccess('Graphiques générés avec succès !');
        } else {
            this.showError('Erreur lors de la génération des graphiques: ' + data.error);
        }
    }

    async exportPrint() {
        const response = await fetch('/export/print', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        if (data.success) {
            // Créer une fenêtre d'impression
            const printWindow = window.open('', '_blank');
            printWindow.document.write(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Rapport d'Épargne - ${data.print_data.username}</title>
                    <style>
                        @media print {
                            body { margin: 0; }
                            .no-print { display: none; }
                        }
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
                        .section { margin-bottom: 20px; }
                        .section h2 { color: #333; border-bottom: 1px solid #ccc; padding-bottom: 5px; }
                        table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
                        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        th { background-color: #f2f2f2; }
                        .stats { display: flex; justify-content: space-between; margin-bottom: 20px; }
                        .stat { text-align: center; padding: 10px; border: 1px solid #ddd; flex: 1; margin: 0 5px; }
                        .print-btn { position: fixed; top: 10px; right: 10px; padding: 10px; background: #007bff; color: white; border: none; cursor: pointer; }
                    </style>
                </head>
                <body>
                    <button class="print-btn no-print" onclick="window.print()">Imprimer</button>
                    <div class="header">
                        <h1>Rapport d'Épargne</h1>
                        <p>Généré le ${data.print_data.date_export}</p>
                        <p>Utilisateur: ${data.print_data.username}</p>
                    </div>

                    <div class="stats">
                        <div class="stat">
                            <h3>Total Épargne</h3>
                            <p>${this.formatCurrency(data.print_data.total_epargne)}</p>
                        </div>
                        <div class="stat">
                            <h3>Objectifs Actifs</h3>
                            <p>${data.print_data.total_objectifs}</p>
                        </div>
                        <div class="stat">
                            <h3>Tâches Terminées</h3>
                            <p>${data.print_data.taches_terminees}/${data.print_data.total_taches}</p>
                        </div>
                    </div>

                    <div class="section">
                        <h2>Objectifs d'Épargne</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>Nom</th>
                                    <th>Montant Cible</th>
                                    <th>Montant Actuel</th>
                                    <th>Progression</th>
                                    <th>Date Limite</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.print_data.objectifs.map(obj => {
                                    const progression = (obj.montant_actuel / obj.montant_cible * 100) || 0;
                                    return `
                                        <tr>
                                            <td>${obj.nom}</td>
                                            <td>${this.formatCurrency(obj.montant_cible)}</td>
                                            <td>${this.formatCurrency(obj.montant_actuel)}</td>
                                            <td>${progression.toFixed(1)}%</td>
                                            <td>${obj.date_limite || 'Non définie'}</td>
                                        </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>

                    <div class="section">
                        <h2>Tâches Récentes</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>Titre</th>
                                    <th>Description</th>
                                    <th>Date Limite</th>
                                    <th>Statut</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.print_data.taches.map(tache => `
                                    <tr>
                                        <td>${tache.titre}</td>
                                        <td>${tache.description || ''}</td>
                                        <td>${tache.date_limite || 'Non définie'}</td>
                                        <td>${tache.termine ? 'Terminée' : 'En cours'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </body>
                </html>
            `);
            printWindow.document.close();
            this.showSuccess('Rapport prêt pour impression !');
        } else {
            this.showError('Erreur lors de la préparation de l\'impression: ' + data.error);
        }
    }

    formatCurrency(amount) {
        // Fonction de formatage de devise robuste
        if (amount === null || amount === undefined || isNaN(amount)) {
            return '0 FCFA';
        }

        try {
            return new Intl.NumberFormat('fr-FR', {
                style: 'currency',
                currency: 'XAF',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(amount);
        } catch (error) {
            // Fallback simple si Intl n'est pas supporté
            return `${Math.round(amount).toLocaleString('fr-FR')} FCFA`;
        }
    }

    showLoading(exportType) {
        // Afficher un indicateur de chargement
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'export-loading';
        loadingDiv.innerHTML = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; justify-content: center; align-items: center;">
                <div style="background: white; padding: 20px; border-radius: 10px; text-align: center;">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Chargement...</span>
                    </div>
                    <p class="mt-2">Génération du ${exportType.toUpperCase()} en cours...</p>
                </div>
            </div>
        `;
        document.body.appendChild(loadingDiv);
    }

    hideLoading() {
        const loadingDiv = document.getElementById('export-loading');
        if (loadingDiv) {
            document.body.removeChild(loadingDiv);
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        const isSuccess = type === 'success';

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            min-width: 300px;
            max-width: 400px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease-out;
            background: ${isSuccess ? 'linear-gradient(135deg, #28a745, #20c997)' : 'linear-gradient(135deg, #dc3545, #c82333)'};
        `;

        notification.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" style="
                    background: none;
                    border: none;
                    color: white;
                    font-size: 18px;
                    cursor: pointer;
                    margin-left: 10px;
                    padding: 0;
                    width: 20px;
                    height: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">&times;</button>
            </div>
        `;

        // Ajouter l'animation CSS si elle n'existe pas
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOut 0.3s ease-in';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }
        }, 5000);
    }
}

// Initialiser le gestionnaire d'exportation
const exportManager = new ExportManager();