"""
KaMela Finance - Application de Gestion Financière Personnelle
Auteur: Assistant AI
Description: Application complète pour gérer finances, dettes, prêts et échéances
"""

# =============================================================================
# SECTION 1: IMPORTATIONS DES BIBLIOTHÈQUES
# =============================================================================

import tkinter as tk  # Bibliothèque standard pour créer l'interface graphique
from tkinter import ttk, messagebox, simpledialog  # Widgets supplémentaires et boîtes de dialogue
import sqlite3  # Base de données légère intégrée à Python (pas d'installation externe requise)
from datetime import datetime, timedelta  # Gestion des dates et heures
from tkcalendar import DateEntry  # Widget calendrier pour sélectionner des dates (pip install tkcalendar)
import json  # Pour manipuler des données au format JSON si besoin

# =============================================================================
# SECTION 2: CLASSE PRINCIPALE DE L'APPLICATION
# =============================================================================

class KamelaFinance:
    """
    Classe principale qui gère toute l'application KaMela Finance.
    Elle initialise la fenêtre, la base de données et toutes les fonctionnalités.
    """
    
    def __init__(self, root):
        """
        Constructeur de la classe - s'exécute automatiquement à la création d'une instance
        root: la fenêtre principale Tkinter passée en paramètre
        """
        self.root = root  # Stockage de la référence à la fenêtre principale
        self.root.title("KaMela Finance - Gestion Financière Personnelle")  # Titre de la fenêtre
        self.root.geometry("1200x800")  # Dimensions de la fenêtre (largeur x hauteur)
        self.root.configure(bg="#f0f2f5")  # Couleur de fond gris clair moderne
        
        # Variables de style pour une interface cohérente
        self.colors = {
            'primary': "#2c3e50",      # Bleu foncé pour l'en-tête
            'secondary': "#3498db",     # Bleu clair pour les boutons actifs
            'success': "#27ae60",       # Vert pour les revenus/positif
            'danger': "#e74c3c",        # Rouge pour les dépenses/alertes
            'warning': "#f39c12",       # Orange pour les avertissements
            'bg': "#f0f2f5",           # Fond général
            'card': "#ffffff",          # Fond des cartes
            'text': "#2c3e50"          # Couleur du texte principal
        }
        
        # Initialisation de la base de données (création des tables si elles n'existent pas)
        self.init_database()
        
        # Création de l'interface utilisateur
        self.create_ui()
        
        # Chargement initial des données
        self.refresh_all_data()

    # =========================================================================
    # SECTION 3: GESTION DE LA BASE DE DONNÉES SQLITE
    # =========================================================================
    
    def init_database(self):
        """
        Initialise la base de données SQLite.
        SQLite stocke les données dans un fichier local (.db) qui persiste entre les sessions.
        Avantage: pas besoin de serveur, les données sont conservées localement.
        """
        # Connexion au fichier de base de données (le crée s'il n'existe pas)
        self.conn = sqlite3.connect('kamela_finance.db')
        self.cursor = self.conn.cursor()  # Curseur pour exécuter les commandes SQL
        
        # Table des transactions (revenus et dépenses)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,           -- 'revenu' ou 'depense'
                category TEXT NOT NULL,       -- Catégorie (Salaire, Alimentation, etc.)
                amount REAL NOT NULL,         -- Montant en nombre décimal
                description TEXT,             -- Description optionnelle
                date TEXT NOT NULL,           -- Date au format YYYY-MM-DD
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des dettes et prêts
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,           -- 'dette' (je dois) ou 'pret' (on me doit)
                person_name TEXT NOT NULL,    -- Nom de la personne
                phone TEXT,                   -- Numéro de téléphone
                amount REAL NOT NULL,         -- Montant total
                amount_paid REAL DEFAULT 0,   -- Montant déjà remboursé
                interest_rate REAL DEFAULT 0, -- Taux d'intérêt (pour les prêts)
                start_date TEXT NOT NULL,     -- Date de début
                due_date TEXT,                -- Date d'échéance
                status TEXT DEFAULT 'actif',  -- 'actif', 'remboursé', 'en_retard'
                description TEXT,             -- Notes additionnelles
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des remboursements (historique des paiements sur dettes/prêts)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS repayments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                debt_id INTEGER NOT NULL,     -- Lien vers la dette concernée
                amount REAL NOT NULL,         -- Montant remboursé
                date TEXT NOT NULL,           -- Date du remboursement
                notes TEXT,                   -- Notes
                FOREIGN KEY (debt_id) REFERENCES debts (id) ON DELETE CASCADE
            )
        ''')
        
        # Table des contacts (pour garder une liste de personnes fréquentes)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,           -- Nom complet
                phone TEXT,                   -- Numéro de téléphone
                email TEXT,                   -- Email
                type TEXT,                    -- 'creancier', 'debiteur', 'autre'
                notes TEXT,                   -- Notes
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Sauvegarde des changements dans le fichier
        self.conn.commit()
        print("Base de données initialisée avec succès!")  # Message de confirmation console

    # =========================================================================
    # SECTION 4: CRÉATION DE L'INTERFACE UTILISATEUR
    # =========================================================================
    
    def create_ui(self):
        """
        Crée tous les éléments visuels de l'application.
        Organisé en: En-tête, Menu latéral, Zone de contenu principale
        """
        # Configuration du style pour les widgets ttk (thème moderne)
        style = ttk.Style()
        style.theme_use('clam')  # Thème de base adaptable
        
        # Style personnalisé pour les boutons de menu
        style.configure('Menu.TButton', 
                       font=('Helvetica', 11, 'bold'),
                       padding=10,
                       background=self.colors['card'],
                       foreground=self.colors['text'])
        
        # Style pour les cartes de statistiques
        style.configure('Card.TFrame', background=self.colors['card'])
        
        # ---------------------------------------------------------------------
        # EN-TÊTE DE L'APPLICATION
        # ---------------------------------------------------------------------
        header = tk.Frame(self.root, bg=self.colors['primary'], height=80)
        header.pack(fill=tk.X)  # Remplit toute la largeur horizontalement
        header.pack_propagate(False)  # Empêche le frame de rétrécir avec son contenu
        
        # Logo et titre dans l'en-tête
        title_frame = tk.Frame(header, bg=self.colors['primary'])
        title_frame.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Label avec le nom de l'application en grand
        tk.Label(title_frame, 
                text="💰 KaMela Finance",
                font=('Helvetica', 24, 'bold'),
                bg=self.colors['primary'],
                fg='white').pack(side=tk.LEFT)
        
        # Sous-titre
        tk.Label(title_frame,
                text="  |  Votre gestionnaire financier personnel",
                font=('Helvetica', 12),
                bg=self.colors['primary'],
                fg='#bdc3c7').pack(side=tk.LEFT, pady=8)
        
        # Date actuelle dans l'en-tête à droite
        self.date_label = tk.Label(header,
                                  text=datetime.now().strftime("%d %B %Y"),
                                  font=('Helvetica', 12),
                                  bg=self.colors['primary'],
                                  fg='white')
        self.date_label.pack(side=tk.RIGHT, padx=20, pady=25)
        
        # ---------------------------------------------------------------------
        # CONTENEUR PRINCIPAL (Menu + Contenu)
        # ---------------------------------------------------------------------
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ---------------------------------------------------------------------
        # MENU LATÉRAL DE NAVIGATION
        # ---------------------------------------------------------------------
        sidebar = tk.Frame(main_container, bg=self.colors['card'], width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))  # Y = vertical
        sidebar.pack_propagate(False)  # Garde la largeur fixe à 200px
        
        # Titre du menu
        tk.Label(sidebar,
                text="MENU",
                font=('Helvetica', 10, 'bold'),
                bg=self.colors['card'],
                fg='#7f8c8d').pack(pady=(20, 10), padx=20, anchor='w')
        
        # Liste des boutons de navigation avec leurs icônes et commandes
        menu_items = [
            ("📊 Tableau de bord", self.show_dashboard),
            ("💳 Transactions", self.show_transactions),
            ("📋 Dettes & Prêts", self.show_debts),
            ("📅 Échéances", self.show_deadlines),
            ("📞 Contacts", self.show_contacts),
            ("📈 Rapports", self.show_reports),
        ]
        
        self.menu_buttons = []  # Liste pour stocker les références aux boutons
        for text, command in menu_items:
            btn = tk.Button(sidebar,
                           text=text,
                           font=('Helvetica', 11),
                           bg=self.colors['card'],
                           fg=self.colors['text'],
                           activebackground=self.colors['secondary'],
                           activeforeground='white',
                           bd=0,  # Pas de bordure
                           padx=20,
                           pady=10,
                           anchor='w',  # Alignement texte à gauche (west)
                           cursor='hand2',  # Curseur main au survol
                           command=command)
            btn.pack(fill=tk.X, padx=10, pady=2)
            self.menu_buttons.append(btn)
        
        # Séparateur visuel
        tk.Frame(sidebar, bg='#ecf0f1', height=2).pack(fill=tk.X, padx=20, pady=20)
        
        # Bouton de sauvegarde manuelle
        tk.Button(sidebar,
                 text="💾 Sauvegarder",
                 font=('Helvetica', 10),
                 bg=self.colors['success'],
                 fg='white',
                 bd=0,
                 padx=20,
                 pady=8,
                 cursor='hand2',
                 command=self.backup_data).pack(fill=tk.X, padx=20, pady=5)
        
        # ---------------------------------------------------------------------
        # ZONE DE CONTENU PRINCIPALE (change selon la page sélectionnée)
        # ---------------------------------------------------------------------
        self.content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Afficher le tableau de bord par défaut au démarrage
        self.show_dashboard()

    # =========================================================================
    # SECTION 5: PAGE TABLEAU DE BORD
    # =========================================================================
    
    def show_dashboard(self):
        """
        Affiche la page d'accueil avec les statistiques principales.
        C'est la vue par défaut qui résume la situation financière.
        """
        self.clear_content()  # Efface le contenu précédent
        self.highlight_menu(0)  # Met en surbrillance le premier bouton du menu
        
        # Titre de la page
        tk.Label(self.content_frame,
                text="Tableau de Bord",
                font=('Helvetica', 20, 'bold'),
                bg=self.colors['bg'],
                fg=self.colors['text']).pack(anchor='w', pady=(0, 20))
        
        # Frame pour les cartes de statistiques (grille 2x2)
        stats_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Configuration de la grille
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        
        # Calcul des statistiques depuis la base de données
        stats = self.calculate_stats()
        
        # Création des 4 cartes de statistiques
        self.create_stat_card(stats_frame, "Solde Actuel", 
                             f"{stats['balance']:,.2f} CDF", 
                             self.colors['success'] if stats['balance'] >= 0 else self.colors['danger'],
                             "💰", 0, 0)
        
        self.create_stat_card(stats_frame, "Revenus du Mois", 
                             f"{stats['monthly_income']:,.2f} CDF", 
                             self.colors['success'],
                             "📈", 0, 1)
        
        self.create_stat_card(stats_frame, "Dépenses du Mois", 
                             f"{stats['monthly_expense']:,.2f} CDF", 
                             self.colors['danger'],
                             "📉", 1, 0)
        
        self.create_stat_card(stats_frame, "Dettes Actives", 
                             f"{stats['active_debts']}", 
                             self.colors['warning'],
                             "⚠️", 1, 1)
        
        # Section des alertes et échéances proches
        alerts_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        alerts_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Colonne de gauche: Alertes
        left_col = tk.Frame(alerts_frame, bg=self.colors['bg'])
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(left_col,
                text="⚠️ Alertes",
                font=('Helvetica', 14, 'bold'),
                bg=self.colors['bg'],
                fg=self.colors['text']).pack(anchor='w', pady=(0, 10))
        
        self.alerts_list = tk.Frame(left_col, bg=self.colors['card'], bd=1, relief='solid')
        self.alerts_list.pack(fill=tk.BOTH, expand=True)
        self.load_alerts()
        
        # Colonne de droite: Échéances proches
        right_col = tk.Frame(alerts_frame, bg=self.colors['bg'])
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        tk.Label(right_col,
                text="📅 Échéances des 7 jours",
                font=('Helvetica', 14, 'bold'),
                bg=self.colors['bg'],
                fg=self.colors['text']).pack(anchor='w', pady=(0, 10))
        
        self.deadlines_list = tk.Frame(right_col, bg=self.colors['card'], bd=1, relief='solid')
        self.deadlines_list.pack(fill=tk.BOTH, expand=True)
        self.load_upcoming_deadlines()

    def create_stat_card(self, parent, title, value, color, icon, row, col):
        """
        Crée une carte de statistique avec titre, valeur et icône.
        parent: frame parent
        title: titre de la statistique
        value: valeur à afficher
        color: couleur d'accentuation
        icon: emoji d'icône
        row, col: position dans la grille
        """
        card = tk.Frame(parent, bg=self.colors['card'], bd=1, relief='solid',
                       highlightbackground='#ddd', highlightthickness=1)
        card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
        
        # Padding interne
        inner = tk.Frame(card, bg=self.colors['card'])
        inner.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Ligne supérieure avec icône et titre
        header = tk.Frame(inner, bg=self.colors['card'])
        header.pack(fill=tk.X)
        
        tk.Label(header,
                text=icon,
                font=('Helvetica', 24),
                bg=self.colors['card']).pack(side=tk.LEFT)
        
        tk.Label(header,
                text=title,
                font=('Helvetica', 12),
                bg=self.colors['card'],
                fg='#7f8c8d').pack(side=tk.LEFT, padx=10)
        
        # Valeur principale en grand
        tk.Label(inner,
                text=value,
                font=('Helvetica', 28, 'bold'),
                bg=self.colors['card'],
                fg=color).pack(anchor='w', pady=(10, 0))

    # =========================================================================
    # SECTION 6: PAGE TRANSACTIONS
    # =========================================================================
    
    def show_transactions(self):
        """
        Affiche la page de gestion des transactions (revenus et dépenses).
        Permet d'ajouter, modifier et supprimer des transactions.
        """
        self.clear_content()
        self.highlight_menu(1)
        
        # En-tête avec titre et bouton d'ajout
        header = tk.Frame(self.content_frame, bg=self.colors['bg'])
        header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header,
                text="Gestion des Transactions",
                font=('Helvetica', 20, 'bold'),
                bg=self.colors['bg'],
                fg=self.colors['text']).pack(side=tk.LEFT)
        
        tk.Button(header,
                 text="+ Nouvelle Transaction",
                 font=('Helvetica', 11, 'bold'),
                 bg=self.colors['secondary'],
                 fg='white',
                 bd=0,
                 padx=20,
                 pady=8,
                 cursor='hand2',
                 command=self.add_transaction_dialog).pack(side=tk.RIGHT)
        
        # Filtres
        filter_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(filter_frame,
                text="Filtrer par type:",
                font=('Helvetica', 10),
                bg=self.colors['bg']).pack(side=tk.LEFT)
        
        self.filter_var = tk.StringVar(value="Tous")
        filter_combo = ttk.Combobox(filter_frame,
                                   textvariable=self.filter_var,
                                   values=["Tous", "Revenus", "Dépenses"],
                                   state='readonly',
                                   width=15)
        filter_combo.pack(side=tk.LEFT, padx=10)
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.load_transactions())
        
        # Tableau des transactions
        self.create_transactions_table()

    def create_transactions_table(self):
        """
        Crée un tableau (Treeview) pour afficher les transactions.
        Utilise un style moderne avec scrollbars.
        """
        # Frame contenant le tableau et les scrollbars
        table_frame = tk.Frame(self.content_frame, bg=self.colors['card'])
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Définition des colonnes
        columns = ('Date', 'Type', 'Catégorie', 'Montant', 'Description', 'Actions')
        
        # Création du Treeview (tableau)
        self.trans_tree = ttk.Treeview(table_frame, 
                                      columns=columns,
                                      show='headings',  # Affiche uniquement les en-têtes de colonnes
                                      height=15)
        
        # Configuration des en-têtes de colonnes
        self.trans_tree.heading('Date', text='Date')
        self.trans_tree.heading('Type', text='Type')
        self.trans_tree.heading('Catégorie', text='Catégorie')
        self.trans_tree.heading('Montant', text='Montant (€)')
        self.trans_tree.heading('Description', text='Description')
        self.trans_tree.heading('Actions', text='Actions')
        
        # Configuration des largeurs de colonnes
        self.trans_tree.column('Date', width=100)
        self.trans_tree.column('Type', width=80)
        self.trans_tree.column('Catégorie', width=120)
        self.trans_tree.column('Montant', width=100)
        self.trans_tree.column('Description', width=300)
        self.trans_tree.column('Actions', width=100)
        
        # Scrollbar verticale
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.trans_tree.yview)
        self.trans_tree.configure(yscrollcommand=vsb.set)
        
        # Positionnement
        self.trans_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Chargement des données
        self.load_transactions()

    def load_transactions(self):
        """
        Charge les transactions depuis la base de données et les affiche dans le tableau.
        Applique les filtres sélectionnés.
        """
        # Effacer les données existantes dans le tableau
        for item in self.trans_tree.get_children():
            self.trans_tree.delete(item)
        
        # Construction de la requête SQL selon le filtre
        filter_type = self.filter_var.get()
        query = "SELECT id, date, type, category, amount, description FROM transactions"
        params = []
        
        if filter_type == "Revenus":
            query += " WHERE type = 'revenu'"
        elif filter_type == "Dépenses":
            query += " WHERE type = 'depense'"
        
        query += " ORDER BY date DESC, created_at DESC"  # Tri par date décroissante
        
        # Exécution de la requête
        self.cursor.execute(query, params)
        transactions = self.cursor.fetchall()
        
        # Insertion des données dans le tableau avec formatage des couleurs
        for trans in transactions:
            id_, date, type_, category, amount, description = trans
            
            # Formatage du montant et de la couleur selon le type
            if type_ == 'revenu':
                amount_str = f"+{amount:,.2f}"
                tag = 'income'
            else:
                amount_str = f"-{amount:,.2f}"
                tag = 'expense'
            
            # Insertion dans le tableau
            item = self.trans_tree.insert('', tk.END, 
                                        values=(date, type_.capitalize(), category, 
                                               amount_str, description or '-', '❌ Suppr.'),
                                        tags=(tag,))
            
            # Stockage de l'ID pour les actions
            self.trans_tree.item(item, tags=(tag, str(id_)))
        
        # Configuration des couleurs de tags
        self.trans_tree.tag_configure('income', foreground=self.colors['success'])
        self.trans_tree.tag_configure('expense', foreground=self.colors['danger'])
        
        # Binding du clic sur la colonne Actions
        self.trans_tree.bind('<ButtonRelease-1>', self.on_transaction_click)

    # =========================================================================
    # SECTION 7: PAGE DETTES ET PRÊTS
    # =========================================================================
    
    def show_debts(self):
        """
        Affiche la page de gestion des dettes et prêts.
        Permet de suivre ce que vous devez et ce qu'on vous doit.
        """
        self.clear_content()
        self.highlight_menu(2)
        
        # En-tête
        header = tk.Frame(self.content_frame, bg=self.colors['bg'])
        header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header,
                text="Gestion des Dettes & Prêts",
                font=('Helvetica', 20, 'bold'),
                bg=self.colors['bg'],
                fg=self.colors['text']).pack(side=tk.LEFT)
        
        tk.Button(header,
                 text="+ Nouvelle Dette/Prêt",
                 font=('Helvetica', 11, 'bold'),
                 bg=self.colors['secondary'],
                 fg='white',
                 bd=0,
                 padx=20,
                 pady=8,
                 cursor='hand2',
                 command=self.add_debt_dialog).pack(side=tk.RIGHT)
        
        # Onglets pour séparer Dettes et Prêts
        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Onglet 1: Ce que je dois (Dettes)
        debts_tab = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(debts_tab, text="   💸 Mes Dettes   ")
        self.create_debts_table(debts_tab, 'dette')
        
        # Onglet 2: Ce qu'on me doit (Prêts)
        loans_tab = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(loans_tab, text="   💰 Mes Prêts   ")
        self.create_debts_table(loans_tab, 'pret')

    def create_debts_table(self, parent, debt_type):
        """
        Crée un tableau pour afficher les dettes ou prêts.
        parent: frame parent (l'onglet)
        debt_type: 'dette' ou 'pret' pour filtrer
        """
        # Frame pour le tableau
        table_frame = tk.Frame(parent, bg=self.colors['card'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Colonnes spécifiques aux dettes
        columns = ('Personne', 'Téléphone', 'Montant Total', 'Payé', 'Restant', 
                  'Taux', 'Début', 'Échéance', 'Statut', 'Actions')
        
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
        
        # Configuration des en-têtes
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor='center')
        
        tree.column('Personne', width=120, anchor='w')
        tree.column('Téléphone', width=100)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Stockage de la référence selon le type
        if debt_type == 'dette':
            self.debts_tree = tree
        else:
            self.loans_tree = tree
        
        # Chargement des données
        self.load_debts_data(tree, debt_type)
        
        # Binding pour les actions
        tree.bind('<ButtonRelease-1>', lambda e, t=tree, dt=debt_type: self.on_debt_click(e, t, dt))

    def load_debts_data(self, tree, debt_type):
        """
        Charge les données des dettes/prêts depuis la base de données.
        """
        # Effacer les données existantes
        for item in tree.get_children():
            tree.delete(item)
        
        # Requête SQL avec calcul du montant restant
        self.cursor.execute("""
            SELECT id, person_name, phone, amount, amount_paid, 
                   (amount - amount_paid) as remaining,
                   interest_rate, start_date, due_date, status, description
            FROM debts 
            WHERE type = ? AND status != 'remboursé'
            ORDER BY due_date ASC
        """, (debt_type,))
        
        debts = self.cursor.fetchall()
        
        for debt in debts:
            (id_, person, phone, total, paid, remaining, 
             rate, start, due, status, desc) = debt
            
            # Formatage du statut avec couleur implicite via le tag
            status_display = status.upper()
            
            # Insertion dans le tableau
            item = tree.insert('', tk.END, values=(
                person,
                phone or '-',
                f"{total:,.2f}",
                f"{paid:,.2f}",
                f"{remaining:,.2f}",
                f"{rate}%" if rate else '0%',
                start,
                due or 'Non définie',
                status_display,
                '💰 Remb.'
            ), tags=(status, str(id_)))
            
            # Coloration selon le statut
            if status == 'en_retard':
                tree.tag_configure(status, foreground=self.colors['danger'])
            elif status == 'actif':
                tree.tag_configure(status, foreground=self.colors['warning'])

    # =========================================================================
    # SECTION 8: PAGE ÉCHÉANCES
    # =========================================================================
    
    def show_deadlines(self):
        """
        Affiche la page de suivi des échéances.
        Montre un calendrier et la liste des échéances à venir.
        """
        self.clear_content()
        self.highlight_menu(3)
        
        tk.Label(self.content_frame,
                text="Suivi des Échéances",
                font=('Helvetica', 20, 'bold'),
                bg=self.colors['bg'],
                fg=self.colors['text']).pack(anchor='w', pady=(0, 20))
        
        # Frame divisé en deux colonnes
        main_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Colonne gauche: Calendrier
        left_col = tk.Frame(main_frame, bg=self.colors['card'], bd=1, relief='solid')
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(left_col,
                text="Calendrier des Échéances",
                font=('Helvetica', 14, 'bold'),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(pady=20)
        
        # Widget calendrier
        cal = DateEntry(left_col, width=20, background=self.colors['secondary'],
                       foreground='white', borderwidth=2, locale='fr_FR',
                       date_pattern='yyyy-mm-dd')
        cal.pack(pady=10)
        
        # Bouton pour voir les échéances du jour sélectionné
        tk.Button(left_col,
                 text="Voir les échéances de cette date",
                 font=('Helvetica', 10),
                 bg=self.colors['secondary'],
                 fg='white',
                 command=lambda: self.show_deadlines_for_date(cal.get())).pack(pady=10)
        
        # Colonne droite: Liste des échéances
        right_col = tk.Frame(main_frame, bg=self.colors['bg'])
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        tk.Label(right_col,
                text="Toutes les Échéances à Venir",
                font=('Helvetica', 14, 'bold'),
                bg=self.colors['bg'],
                fg=self.colors['text']).pack(anchor='w', pady=(0, 10))
        
        # Tableau des échéances
        self.create_deadlines_table(right_col)

    def create_deadlines_table(self, parent):
        """
        Crée le tableau des échéances.
        """
        table_frame = tk.Frame(parent, bg=self.colors['card'])
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('Date', 'Type', 'Personne', 'Montant', 'Jours restants', 'Action')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor='center')
        
        tree.column('Personne', width=150)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.deadlines_tree = tree
        self.load_all_deadlines()

    # =========================================================================
    # SECTION 9: PAGE CONTACTS
    # =========================================================================
    
    def show_contacts(self):
        """
        Affiche la page de gestion des contacts.
        Permet de garder une liste des personnes liées aux dettes/prêts.
        """
        self.clear_content()
        self.highlight_menu(4)
        
        header = tk.Frame(self.content_frame, bg=self.colors['bg'])
        header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header,
                text="Carnet de Contacts",
                font=('Helvetica', 20, 'bold'),
                bg=self.colors['bg'],
                fg=self.colors['text']).pack(side=tk.LEFT)
        
        tk.Button(header,
                 text="+ Ajouter Contact",
                 font=('Helvetica', 11, 'bold'),
                 bg=self.colors['secondary'],
                 fg='white',
                 bd=0,
                 padx=20,
                 pady=8,
                 cursor='hand2',
                 command=self.add_contact_dialog).pack(side=tk.RIGHT)
        
        # Tableau des contacts
        table_frame = tk.Frame(self.content_frame, bg=self.colors['card'])
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('Nom', 'Téléphone', 'Email', 'Type', 'Notes', 'Actions')
        self.contacts_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.contacts_tree.heading(col, text=col)
            self.contacts_tree.column(col, width=120, anchor='center')
        
        self.contacts_tree.column('Nom', width=150, anchor='w')
        self.contacts_tree.column('Notes', width=250)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.contacts_tree.yview)
        self.contacts_tree.configure(yscrollcommand=vsb.set)
        
        self.contacts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.load_contacts()

    # =========================================================================
    # SECTION 10: BOÎTES DE DIALOGUE ET FORMULAIRES
    # =========================================================================
    
    def add_transaction_dialog(self):
        """
        Ouvre une fenêtre modale pour ajouter une nouvelle transaction.
        """
        dialog = tk.Toplevel(self.root)  # Crée une nouvelle fenêtre fille
        dialog.title("Nouvelle Transaction")
        dialog.geometry("400x400")
        dialog.transient(self.root)  # Rend la fenêtre modale (lie à la fenêtre parent)
        dialog.grab_set()  # Empêche l'interaction avec la fenêtre principale
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (self.root.winfo_x() + 400, self.root.winfo_y() + 200))
        
        tk.Label(dialog, text="Nouvelle Transaction", font=('Helvetica', 14, 'bold')).pack(pady=20)
        
        # Formulaire
        form = tk.Frame(dialog)
        form.pack(padx=20, pady=10, fill=tk.X)
        
        # Type
        tk.Label(form, text="Type:").pack(anchor='w')
        type_var = tk.StringVar(value='revenu')
        ttk.Combobox(form, textvariable=type_var, values=['revenu', 'depense'], 
                    state='readonly').pack(fill=tk.X, pady=(0, 10))
        
        # Catégorie
        tk.Label(form, text="Catégorie:").pack(anchor='w')
        cat_var = tk.StringVar()
        categories = ['Salaire', 'Alimentation', 'Transport', 'Logement', 'Loisirs', 
                     'Santé', 'Éducation', 'Autre']
        ttk.Combobox(form, textvariable=cat_var, values=categories).pack(fill=tk.X, pady=(0, 10))
        
        # Montant
        tk.Label(form, text="Montant (€):").pack(anchor='w')
        amount_var = tk.StringVar()
        tk.Entry(form, textvariable=amount_var).pack(fill=tk.X, pady=(0, 10))
        
        # Date
        tk.Label(form, text="Date:").pack(anchor='w')
        date_cal = DateEntry(form, width=12, background='darkblue', 
                            foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        date_cal.pack(fill=tk.X, pady=(0, 10))
        
        # Description
        tk.Label(form, text="Description:").pack(anchor='w')
        desc_var = tk.StringVar()
        tk.Entry(form, textvariable=desc_var).pack(fill=tk.X, pady=(0, 10))
        
        def save():
            """Fonction interne pour sauvegarder la transaction."""
            try:
                amount = float(amount_var.get())
                if amount <= 0:
                    raise ValueError("Le montant doit être positif")
                
                self.cursor.execute("""
                    INSERT INTO transactions (type, category, amount, description, date)
                    VALUES (?, ?, ?, ?, ?)
                """, (type_var.get(), cat_var.get(), amount, desc_var.get(), date_cal.get()))
                
                self.conn.commit()
                messagebox.showinfo("Succès", "Transaction ajoutée avec succès!")
                dialog.destroy()
                self.refresh_all_data()
                
            except ValueError as e:
                messagebox.showerror("Erreur", f"Montant invalide: {str(e)}")
        
        tk.Button(dialog, text="Sauvegarder", bg=self.colors['success'], fg='white',
                 command=save).pack(pady=20)

    def add_debt_dialog(self):
        """
        Ouvre une fenêtre pour ajouter une dette ou un prêt.
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Nouvelle Dette / Prêt")
        dialog.geometry("450x550")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry("+%d+%d" % (self.root.winfo_x() + 375, self.root.winfo_y() + 150))
        
        tk.Label(dialog, text="Nouvelle Dette / Prêt", font=('Helvetica', 14, 'bold')).pack(pady=20)
        
        form = tk.Frame(dialog)
        form.pack(padx=20, pady=10, fill=tk.X)
        
        # Type (dette ou prêt)
        tk.Label(form, text="Type:").pack(anchor='w')
        type_var = tk.StringVar(value='dette')
        ttk.Combobox(form, textvariable=type_var, 
                    values=['dette', 'pret'], state='readonly').pack(fill=tk.X, pady=(0, 10))
        
        # Nom de la personne
        tk.Label(form, text="Nom de la personne:").pack(anchor='w')
        name_var = tk.StringVar()
        tk.Entry(form, textvariable=name_var).pack(fill=tk.X, pady=(0, 10))
        
        # Téléphone
        tk.Label(form, text="Numéro de téléphone:").pack(anchor='w')
        phone_var = tk.StringVar()
        tk.Entry(form, textvariable=phone_var).pack(fill=tk.X, pady=(0, 10))
        
        # Montant total
        tk.Label(form, text="Montant total (€):").pack(anchor='w')
        amount_var = tk.StringVar()
        tk.Entry(form, textvariable=amount_var).pack(fill=tk.X, pady=(0, 10))
        
        # Taux d'intérêt
        tk.Label(form, text="Taux d'intérêt annuel (%):").pack(anchor='w')
        rate_var = tk.StringVar(value='0')
        tk.Entry(form, textvariable=rate_var).pack(fill=tk.X, pady=(0, 10))
        
        # Date de début
        tk.Label(form, text="Date de début:").pack(anchor='w')
        start_cal = DateEntry(form, width=12, background='darkblue',
                             foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        start_cal.pack(fill=tk.X, pady=(0, 10))
        
        # Date d'échéance
        tk.Label(form, text="Date d'échéance:").pack(anchor='w')
        due_cal = DateEntry(form, width=12, background='darkblue',
                           foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        due_cal.pack(fill=tk.X, pady=(0, 10))
        
        # Description
        tk.Label(form, text="Description / Notes:").pack(anchor='w')
        desc_text = tk.Text(form, height=3)
        desc_text.pack(fill=tk.X, pady=(0, 10))
        
        def save():
            try:
                amount = float(amount_var.get())
                rate = float(rate_var.get())
                
                self.cursor.execute("""
                    INSERT INTO debts (type, person_name, phone, amount, interest_rate,
                                     start_date, due_date, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (type_var.get(), name_var.get(), phone_var.get(), amount, rate,
                      start_cal.get(), due_cal.get(), desc_text.get("1.0", tk.END).strip()))
                
                # Ajouter automatiquement aux contacts si nouveau
                self.cursor.execute("SELECT id FROM contacts WHERE phone = ?", (phone_var.get(),))
                if not self.cursor.fetchone() and phone_var.get():
                    contact_type = 'debiteur' if type_var.get() == 'pret' else 'creancier'
                    self.cursor.execute("""
                        INSERT INTO contacts (name, phone, type, notes)
                        VALUES (?, ?, ?, ?)
                    """, (name_var.get(), phone_var.get(), contact_type, 
                          f"Ajouté via {type_var.get()}"))
                
                self.conn.commit()
                messagebox.showinfo("Succès", "Enregistrement ajouté avec succès!")
                dialog.destroy()
                self.refresh_all_data()
                
            except ValueError:
                messagebox.showerror("Erreur", "Montant ou taux invalide!")
        
        tk.Button(dialog, text="Sauvegarder", bg=self.colors['success'], fg='white',
                 command=save).pack(pady=20)

    def add_contact_dialog(self):
        """
        Ouvre une fenêtre pour ajouter un contact.
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Nouveau Contact")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Nouveau Contact", font=('Helvetica', 14, 'bold')).pack(pady=20)
        
        form = tk.Frame(dialog)
        form.pack(padx=20, fill=tk.X)
        
        tk.Label(form, text="Nom complet:").pack(anchor='w')
        name_var = tk.StringVar()
        tk.Entry(form, textvariable=name_var).pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(form, text="Téléphone:").pack(anchor='w')
        phone_var = tk.StringVar()
        tk.Entry(form, textvariable=phone_var).pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(form, text="Email:").pack(anchor='w')
        email_var = tk.StringVar()
        tk.Entry(form, textvariable=email_var).pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(form, text="Type:").pack(anchor='w')
        type_var = tk.StringVar(value='autre')
        ttk.Combobox(form, textvariable=type_var,
                    values=['creancier', 'debiteur', 'autre']).pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(form, text="Notes:").pack(anchor='w')
        notes_var = tk.StringVar()
        tk.Entry(form, textvariable=notes_var).pack(fill=tk.X, pady=(0, 10))
        
        def save():
            self.cursor.execute("""
                INSERT INTO contacts (name, phone, email, type, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (name_var.get(), phone_var.get(), email_var.get(), 
                  type_var.get(), notes_var.get()))
            self.conn.commit()
            messagebox.showinfo("Succès", "Contact ajouté!")
            dialog.destroy()
            self.load_contacts()
        
        tk.Button(dialog, text="Sauvegarder", bg=self.colors['success'], fg='white',
                 command=save).pack(pady=20)

    # =========================================================================
    # SECTION 11: FONCTIONS UTILITAIRES ET ÉVÉNEMENTS
    # =========================================================================
    
    def on_transaction_click(self, event):
        """
        Gère le clic sur une ligne du tableau des transactions.
        Détecte si on clique sur le bouton Supprimer.
        """
        region = self.trans_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.trans_tree.identify_column(event.x)
            if column == '#6':  # Colonne Actions
                item = self.trans_tree.selection()[0]
                tags = self.trans_tree.item(item, "tags")
                if tags:
                    trans_id = tags[-1]  # L'ID est stocké dans le dernier tag
                    if messagebox.askyesno("Confirmation", "Supprimer cette transaction?"):
                        self.cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
                        self.conn.commit()
                        self.refresh_all_data()

    def on_debt_click(self, event, tree, debt_type):
        """
        Gère le clic sur une dette pour enregistrer un remboursement.
        """
        region = tree.identify("region", event.x, event.y)
        if region == "cell":
            column = tree.identify_column(event.x)
            if column == '#10':  # Colonne Actions
                item = tree.selection()[0]
                tags = tree.item(item, "tags")
                if tags:
                    debt_id = tags[-1]
                    self.show_repayment_dialog(debt_id, debt_type)

    def show_repayment_dialog(self, debt_id, debt_type):
        """
        Ouvre une fenêtre pour enregistrer un remboursement sur une dette.
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Enregistrer un Remboursement")
        dialog.geometry("350x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Récupérer les infos de la dette
        self.cursor.execute("SELECT person_name, amount, amount_paid FROM debts WHERE id = ?", (debt_id,))
        debt = self.cursor.fetchone()
        person, total, paid = debt
        remaining = total - paid
        
        tk.Label(dialog, text=f"Remboursement - {person}", 
                font=('Helvetica', 12, 'bold')).pack(pady=10)
        tk.Label(dialog, text=f"Montant restant: {remaining:,.2f} €").pack()
        
        form = tk.Frame(dialog)
        form.pack(padx=20, pady=10, fill=tk.X)
        
        tk.Label(form, text="Montant à rembourser (€):").pack(anchor='w')
        amount_var = tk.StringVar()
        tk.Entry(form, textvariable=amount_var).pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(form, text="Date:").pack(anchor='w')
        date_cal = DateEntry(form, width=12, background='darkblue',
                            foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        date_cal.pack(fill=tk.X, pady=(0, 10))
        
        def save():
            try:
                amount = float(amount_var.get())
                if amount <= 0 or amount > remaining:
                    raise ValueError("Montant invalide")
                
                # Enregistrer le remboursement
                self.cursor.execute("""
                    INSERT INTO repayments (debt_id, amount, date, notes)
                    VALUES (?, ?, ?, ?)
                """, (debt_id, amount, date_cal.get(), "Remboursement partiel"))
                
                # Mettre à jour le montant payé
                new_paid = paid + amount
                new_status = 'remboursé' if new_paid >= total else 'actif'
                
                self.cursor.execute("""
                    UPDATE debts SET amount_paid = ?, status = ? WHERE id = ?
                """, (new_paid, new_status, debt_id))
                
                self.conn.commit()
                messagebox.showinfo("Succès", "Remboursement enregistré!")
                dialog.destroy()
                self.refresh_all_data()
                
            except ValueError as e:
                messagebox.showerror("Erreur", str(e))
        
        tk.Button(dialog, text="Confirmer le remboursement", 
                 bg=self.colors['success'], fg='white', command=save).pack(pady=10)

    def calculate_stats(self):
        """
        Calcule les statistiques pour le tableau de bord.
        Retourne un dictionnaire avec les valeurs calculées.
        """
        # Solde total (tous les revenus - toutes les dépenses)
        self.cursor.execute("SELECT COALESCE(SUM(CASE WHEN type='revenu' THEN amount ELSE -amount END), 0) FROM transactions")
        balance = self.cursor.fetchone()[0] or 0
        
        # Revenus du mois en cours
        current_month = datetime.now().strftime('%Y-%m')
        self.cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM transactions 
            WHERE type='revenu' AND strftime('%Y-%m', date) = ?
        """, (current_month,))
        monthly_income = self.cursor.fetchone()[0] or 0
        
        # Dépenses du mois en cours
        self.cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM transactions 
            WHERE type='depense' AND strftime('%Y-%m', date) = ?
        """, (current_month,))
        monthly_expense = self.cursor.fetchone()[0] or 0
        
        # Nombre de dettes actives
        self.cursor.execute("SELECT COUNT(*) FROM debts WHERE status IN ('actif', 'en_retard')")
        active_debts = self.cursor.fetchone()[0] or 0
        
        return {
            'balance': balance,
            'monthly_income': monthly_income,
            'monthly_expense': monthly_expense,
            'active_debts': active_debts
        }

    def load_alerts(self):
        """
        Charge les alertes (soldes négatifs, dettes en retard, etc.).
        """
        # Effacer les alertes existantes
        for widget in self.alerts_list.winfo_children():
            widget.destroy()
        
        alerts = []
        
        # Vérifier le solde
        stats = self.calculate_stats()
        if stats['balance'] < 0:
            alerts.append(("Solde négatif!", f"Votre solde est de {stats['balance']:,.2f} €", self.colors['danger']))
        
        # Vérifier les dettes en retard
        today = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute("""
            SELECT COUNT(*) FROM debts 
            WHERE due_date < ? AND status = 'actif'
        """, (today,))
        late_debts = self.cursor.fetchone()[0]
        if late_debts > 0:
            alerts.append((f"{late_debts} dette(s) en retard", "Des échéances sont dépassées", self.colors['danger']))
        
        # Afficher les alertes ou message positif
        if not alerts:
            tk.Label(self.alerts_list,
                    text="✅ Aucune alerte, tout va bien!",
                    font=('Helvetica', 11),
                    bg=self.colors['card'],
                    fg=self.colors['success'],
                    padx=20, pady=20).pack(fill=tk.X)
        else:
            for title, desc, color in alerts:
                frame = tk.Frame(self.alerts_list, bg=self.colors['card'], padx=20, pady=10)
                frame.pack(fill=tk.X, pady=2)
                tk.Label(frame, text=title, font=('Helvetica', 11, 'bold'), 
                        bg=self.colors['card'], fg=color).pack(anchor='w')
                tk.Label(frame, text=desc, font=('Helvetica', 10), 
                        bg=self.colors['card'], fg=self.colors['text']).pack(anchor='w')

    def load_upcoming_deadlines(self):
        """
        Charge les échéances des 7 prochains jours.
        """
        for widget in self.deadlines_list.winfo_children():
            widget.destroy()
        
        today = datetime.now()
        week_later = (today + timedelta(days=7)).strftime('%Y-%m-%d')
        today_str = today.strftime('%Y-%m-%d')
        
        self.cursor.execute("""
            SELECT person_name, amount - amount_paid, due_date, type
            FROM debts 
            WHERE due_date BETWEEN ? AND ? AND status = 'actif'
            ORDER BY due_date ASC
        """, (today_str, week_later))
        
        deadlines = self.cursor.fetchall()
        
        if not deadlines:
            tk.Label(self.deadlines_list,
                    text="Aucune échéance dans les 7 jours",
                    font=('Helvetica', 11),
                    bg=self.colors['card'],
                    fg='#7f8c8d',
                    padx=20, pady=20).pack(fill=tk.X)
        else:
            for person, amount, due_date, type_ in deadlines:
                frame = tk.Frame(self.deadlines_list, bg=self.colors['card'], padx=20, pady=10)
                frame.pack(fill=tk.X, pady=2)
                
                type_str = "Prêt à recevoir" if type_ == 'pret' else "Dette à payer"
                tk.Label(frame, text=f"{person} - {type_str}", 
                        font=('Helvetica', 11, 'bold'), 
                        bg=self.colors['card'], fg=self.colors['text']).pack(anchor='w')
                tk.Label(frame, text=f"{amount:,.2f} € avant le {due_date}", 
                        font=('Helvetica', 10), 
                        bg=self.colors['card'], fg=self.colors['danger']).pack(anchor='w')

    def load_all_deadlines(self):
        """
        Charge toutes les échéances futures pour la page Échéances.
        """
        for item in self.deadlines_tree.get_children():
            self.deadlines_tree.delete(item)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        self.cursor.execute("""
            SELECT due_date, type, person_name, (amount - amount_paid), 
                   julianday(due_date) - julianday(?) as days_left
            FROM debts 
            WHERE due_date >= ? AND status = 'actif'
            ORDER BY due_date ASC
        """, (today, today))
        
        for row in self.cursor.fetchall():
            due, type_, person, amount, days = row
            days_int = int(days) if days else 0
            
            if days_int <= 3:
                tag = 'urgent'
            elif days_int <= 7:
                tag = 'warning'
            else:
                tag = 'normal'
            
            item = self.deadlines_tree.insert('', tk.END, values=(
                due, type_.capitalize(), person, f"{amount:,.2f} €", 
                f"{days_int} jours", "📞 Appeler"
            ), tags=(tag,))
            
            self.deadlines_tree.item(item, tags=(tag, person))
        
        self.deadlines_tree.tag_configure('urgent', foreground=self.colors['danger'])
        self.deadlines_tree.tag_configure('warning', foreground=self.colors['warning'])

    def show_deadlines_for_date(self, date):
        """
        Affiche les échéances pour une date spécifique sélectionnée dans le calendrier.
        """
        messagebox.showinfo("Échéances", f"Fonctionnalité: Voir les échéances pour le {date}\n(À développer selon besoins spécifiques)")

    def load_contacts(self):
        """
        Charge la liste des contacts depuis la base de données.
        """
        for item in self.contacts_tree.get_children():
            self.contacts_tree.delete(item)
        
        self.cursor.execute("SELECT id, name, phone, email, type, notes FROM contacts ORDER BY name")
        
        for contact in self.cursor.fetchall():
            id_, name, phone, email, type_, notes = contact
            self.contacts_tree.insert('', tk.END, values=(
                name, phone or '-', email or '-', type_.capitalize(), 
                notes or '-', '❌ Suppr.'
            ), tags=(str(id_),))

    def show_reports(self):
        """
        Page de rapports (placeholder pour extension future).
        """
        self.clear_content()
        self.highlight_menu(5)
        
        tk.Label(self.content_frame,
                text="Rapports & Statistiques",
                font=('Helvetica', 20, 'bold'),
                bg=self.colors['bg'],
                fg=self.colors['text']).pack(anchor='w', pady=(0, 20))
        
        tk.Label(self.content_frame,
                text="Cette section permettra de générer des rapports détaillés\n"
                     "et des graphiques de vos finances.",
                font=('Helvetica', 12),
                bg=self.colors['bg'],
                fg='#7f8c8d').pack(pady=50)

    def backup_data(self):
        """
        Crée une sauvegarde de la base de données dans un fichier JSON.
        """
        try:
            import shutil
            from datetime import datetime
            
            # Sauvegarde simple du fichier SQLite
            backup_name = f"kamela_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy('kamela_finance.db', backup_name)
            messagebox.showinfo("Sauvegarde", f"Base de données sauvegardée sous:\n{backup_name}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder: {str(e)}")

    def clear_content(self):
        """
        Efface tous les widgets du frame de contenu pour changer de page.
        """
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def highlight_menu(self, index):
        """
        Met en surbrillance le bouton de menu actif.
        index: position du bouton dans la liste (0-5)
        """
        for i, btn in enumerate(self.menu_buttons):
            if i == index:
                btn.config(bg=self.colors['secondary'], fg='white')
            else:
                btn.config(bg=self.colors['card'], fg=self.colors['text'])

    def refresh_all_data(self):
        """
        Rafraîchit toutes les données affichées.
        Appelé après chaque modification.
        """
        # Si on est sur le tableau de bord, le rafraîchir
        if hasattr(self, 'alerts_list'):
            self.load_alerts()
            self.load_upcoming_deadlines()
        
        # Rafraîchir les autres pages si elles sont actives
        if hasattr(self, 'trans_tree'):
            self.load_transactions()
        if hasattr(self, 'debts_tree'):
            self.load_debts_data(self.debts_tree, 'dette')
        if hasattr(self, 'loans_tree'):
            self.load_debts_data(self.loans_tree, 'pret')
        if hasattr(self, 'deadlines_tree'):
            self.load_all_deadlines()
        if hasattr(self, 'contacts_tree'):
            self.load_contacts()

    def on_closing(self):
        """
        Méthode appelée à la fermeture de l'application.
        Ferme proprement la connexion à la base de données.
        """
        if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter KaMela Finance?"):
            self.conn.close()  # Fermeture de la connexion SQLite
            self.root.destroy()

# =============================================================================
# SECTION 12: POINT D'ENTRÉE DU PROGRAMME
# =============================================================================

def main():
    """
    Fonction principale qui démarre l'application.
    """
    # Création de la fenêtre racine Tkinter
    root = tk.Tk()
    
    # Tentative de définition de l'icône (si disponible)
    try:
        root.iconbitmap('')  # Vous pouvez ajouter un fichier .ico ici
    except:
        pass
    
    # Création de l'instance de l'application
    app = KamelaFinance(root)
    
    # Gestion de la fermeture de fenêtre
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Lancement de la boucle principale Tkinter
    root.mainloop()

# Vérification si ce fichier est exécuté directement (pas importé)
if __name__ == "__main__":
    main()