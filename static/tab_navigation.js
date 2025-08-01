let isMobile = window.innerWidth <= 768;
let scrollTimeout;
let isScrolling = false;
let currentTab = 'dashboard'; // Onglet par défaut

// Titres dynamiques pour chaque onglet
const tabTitles = {
    'epargne': {
        title: 'Épargne',
        subtitle: 'Gérez vos objectifs d\'épargne'
    },
    'taches': {
        title: 'Tâches',
        subtitle: 'Organisez vos tâches et étapes'
    },
    'agenda': {
        title: 'Agenda',
        subtitle: 'Planifiez vos événements'
    },
    'dashboard': {
        title: 'Dashboard',
        subtitle: 'Vue d\'ensemble de vos finances'
    },
    'notifications': {
        title: 'Notifications',
        subtitle: 'Centre de notifications'
    },
    'rapports': {
        title: 'Rapports',
        subtitle: 'Exportez vos données'
    },

};

// Fonction pour détecter si on est sur mobile
function checkMobile() {
    isMobile = window.innerWidth <= 768;
}

// Fonction pour détecter l'onglet au centre
function detectCenterTab() {
    if (!isMobile) return;

    const navTabs = document.querySelector('.nav-tabs');
    const tabs = document.querySelectorAll('.nav-tab');
    const containerCenter = navTabs.offsetLeft + navTabs.offsetWidth / 2;

    let centerTab = null;
    let minDistance = Infinity;

    tabs.forEach(tab => {
        const tabCenter = tab.offsetLeft + tab.offsetWidth / 2;
        const distance = Math.abs(tabCenter - containerCenter);

        if (distance < minDistance) {
            minDistance = distance;
            centerTab = tab;
        }
    });

    return centerTab;
}

// Fonction pour naviguer vers l'onglet au centre
function navigateToCenterTab() {
    if (!isMobile) return;

    const centerTab = detectCenterTab();
    if (centerTab && !centerTab.classList.contains('active')) {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            switchTab(centerTab.dataset.tab);
        }, 500);
    }
}

// Écouter le défilement des onglets
function setupTabScrollDetection() {
    if (!isMobile) return;

    const navTabs = document.querySelector('.nav-tabs');

    navTabs.addEventListener('scroll', () => {
        isScrolling = true;
        clearTimeout(scrollTimeout);

        scrollTimeout = setTimeout(() => {
            isScrolling = false;
            navigateToCenterTab();
        }, 150);
    });
}

// Fonction pour mettre à jour les titres dynamiques
function updateDynamicTitles(tabName) {
    const titleElement = document.getElementById('dynamicTitle');
    const subtitleElement = document.getElementById('dynamicSubtitle');

    if (tabTitles[tabName]) {
        titleElement.textContent = tabTitles[tabName].title;
        subtitleElement.textContent = tabTitles[tabName].subtitle;
    }
}

// Fonction pour changer d'onglet
function switchTab(tabName) {
    // Retirer la classe active de tous les onglets
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Activer l'onglet sélectionné
    const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }

    // Mettre à jour les titres dynamiques
    updateDynamicTitles(tabName);

    currentTab = tabName;

    // Charger le contenu dynamiquement
    loadTabContent(tabName);
}

// Fonction pour charger le contenu d'un onglet
function loadTabContent(tabName) {
    const contentContainer = document.getElementById('tabContent');

    // Afficher un indicateur de chargement
    contentContainer.innerHTML = '<div style="text-align: center; padding: 50px;"><div style="display: inline-block; width: 50px; height: 50px; border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite;"></div><p style="margin-top: 20px; color: #666;">Chargement...</p></div>';

    // Styles pour l'animation de chargement
    const style = document.createElement('style');
    style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
    document.head.appendChild(style);

    // Faire une requête AJAX pour charger le contenu
    fetch(`/api/tab-content/${tabName}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur de chargement');
            }
            return response.text();
        })
        .then(html => {
            contentContainer.innerHTML = html;

            // Réinitialiser les scripts dans le contenu chargé
            const scripts = contentContainer.querySelectorAll('script');
            scripts.forEach(script => {
                const newScript = document.createElement('script');
                if (script.src) {
                    newScript.src = script.src;
                } else {
                    newScript.textContent = script.textContent;
                }
                script.parentNode.replaceChild(newScript, script);
            });
        })
        .catch(error => {
            console.error('Erreur lors du chargement:', error);
            contentContainer.innerHTML = `
                <div style="text-align: center; padding: 50px;">
                    <h3 style="color: #e74c3c;">Erreur de chargement</h3>
                    <p style="color: #666;">Impossible de charger le contenu de l'onglet ${tabName}</p>
                    <button onclick="switchTab('${tabName}')" style="margin-top: 20px; padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">Réessayer</button>
                </div>
            `;
        });
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    // Détecter la taille de l'écran
    checkMobile();

    // Écouter les changements de taille d'écran
    window.addEventListener('resize', checkMobile);

    // Configurer la détection de défilement des onglets
    setupTabScrollDetection();

    // Ajouter les événements de clic aux onglets
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });

    // Activer l'onglet par défaut
    switchTab(currentTab);

    // Gérer la navigation par URL
    if (window.location.hash) {
        const tabName = window.location.hash.substring(1);
        if (tabTitles[tabName]) {
            switchTab(tabName);
        }
    }
});

// Fonction pour basculer le mode sombre
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    let theme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
    localStorage.setItem('theme', theme);

    // Mettre à jour tous les boutons theme-toggle
    const themeToggles = document.querySelectorAll('#theme-toggle');
    themeToggles.forEach(toggle => {
        toggle.textContent = theme === 'dark' ? 'Désactiver le Mode Nuit' : 'Activer le Mode Nuit';
    });
}

// Fonction pour charger le thème depuis le localStorage
function loadTheme() {
    const theme = localStorage.getItem('theme');
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }
}

// Fonction pour initialiser les boutons theme-toggle
function initThemeToggles() {
    const themeToggles = document.querySelectorAll('#theme-toggle');
    themeToggles.forEach(toggle => {
        const theme = localStorage.getItem('theme');
        toggle.textContent = theme === 'dark' ? 'Désactiver le Mode Nuit' : 'Activer le Mode Nuit';

        toggle.addEventListener('click', toggleDarkMode);
    });
}

// Charger le thème et initialiser les boutons
document.addEventListener('DOMContentLoaded', function() {
    loadTheme();
    initThemeToggles();
});