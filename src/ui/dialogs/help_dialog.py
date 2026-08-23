import customtkinter as ctk


HELP_ARTICLES = [
    {
        "id": "basics",
        "title": "🚀 Grundlagen & Layouts",
        "category": "Grundlagen",
        "content": """
### 🚀 Grundlagen der Benutzeroberfläche

Das **Support-Cockpit** unterstützt Sie bei der effizienten Nachverfolgung, Kategorisierung und Priorisierung von Support-Fällen und Praxisanfragen.

#### Die 3 Ansichten (Layout-Modi)
In der oberen Menüleiste können Sie jederzeit zwischen 3 Ansichten umschalten:

1. **Cockpit-Ansicht (Standard)**: 
   - Dreigeteilte Ansicht für maximale Übersicht.
   - **Links**: Filterbare Fall-Liste sortiert nach Dringlichkeit (Score).
   - **Mitte**: Hauptdaten des aktiven Falls (Kunde, Status, Dringlichkeit, dynamische Formularfelder, Zeitleiste & Anhänge).
   - **Rechts**: Integriertes BookStack Wiki zur schnellen Lösungssuche.

2. **Tab-Ansicht (Reiter-Modus)**:
   - Übersichtliche Reiter-Navigation für kompakte Bildschirme.
   - Schnelles Umschalten zwischen Fallübersicht, Falldetails und Historie.

3. **Split-Ansicht (2-Spalten-Modus)**:
   - Links Fall-Liste, rechts Falldetailansicht für fokussiertes Arbeiten ohne Wiki-Seitenleiste.

---

#### 🔍 Such- & Filterfunktion
- Nutzen Sie das Suchfeld oben in der Fallliste, um Fälle nach **Fall-ID**, **Praxisname**, **Betreff** oder **Tags** zu filtern.
- Tastenkürzel zum Fokussieren der Suche: `Strg+F`
"""
    },
    {
        "id": "praxis",
        "title": "🏥 Praxis- & Kundenverwaltung",
        "category": "Kunden",
        "content": """
### 🏥 Praxis- & Kundenverwaltung

Jeder Support-Fall ist einer bestimmten Praxis (Kunde) zugeordnet.

#### 1. Praxis-Verwaltung öffnen
- Klicken Sie in der oberen Menüleiste auf **🏥 Praxen**.
- Hier sehen Sie eine vollständige Liste aller registrierten Praxen mit Kundennummer, Praxisname, Hauptansprechpartner, E-Mail und Telefon.

#### 2. Neue Praxis anlegen
- Öffnen Sie **🏥 Praxen** -> **+ Neue Praxis anlegen**.
- Oder direkt beim Erstellen eines neuen Falls im Dialog **+ Neuer Fall**: Klicken Sie auf den Button **+ Neue Praxis** neben der Praxisauswahl. Die neue Praxis steht sofort zur Auswahl bereit!

#### 3. Ansprechpartner (Kontakte) verwalten
- In den Praxis-Details können Sie mehrere Ansprechpartner (z.B. Praxisinhaber, IT-Beauftragter, MFAs) hinterlegen.
"""
    },
    {
        "id": "scoring",
        "title": "📊 Fall-Scoring & Priorisierung",
        "category": "Workflow",
        "content": """
### 📊 Automatisches Dringlichkeits-Scoring

Das Support-Cockpit berechnet für jeden offenen Fall automatisch einen **Dringlichkeits-Score** (Punkte), damit Sie dringende Fälle sofort erkennen.

#### Wie setzt sich der Score zusammen?
- **Priorität**: Critical (60 Pkt), High (40 Pkt), Medium (20 Pkt), Low (10 Pkt).
- **VIP-Status**: VIP-Praxen erhalten einen Bonus von +30 Punkten.
- **Wartezeit (Liegezeit)**: Je länger ein Fall offen ist, desto höher steigt der Score (+2 Pkt / Tag).
- **Inaktivität**: Fälle ohne Update in den letzten 48 Stunden erhalten zusätzliche Punkte.
- **Workflow-Status**: In Bearbeitung (+10 Pkt), Warten auf Kunden (+0 Pkt), Vorort-Termin nötig (+20 Pkt).

#### Automatische Stundenneuberechnung
Ein Hintergrund-Timer aktualisiert die Scores aller offenen Fälle stündlich.
"""
    },
    {
        "id": "schemas",
        "title": "🛠️ Formular-Baukasten (Schemas)",
        "category": "Formulare",
        "content": """
### 🛠️ Dynamische Formular-Baukästen

Unterschiedliche Support-Typen (z.B. Hardware-Tausch, Abrechnungsfrage, Schnittstellen-Problem) erfordern unterschiedliche Informationen.

#### Eigene Formulare erstellen & anpassen
1. Klicken Sie in der Menüleiste auf **🛠️ Formular-Baukasten**.
2. Erstellen Sie ein neues Schema (z.B. *"PVS-Schnittstelle"*) oder bearbeiten Sie ein bestehendes.
3. Fügen Sie eigene Felder hinzu:
   - **Text-Felder** (z.B. Fehlermeldung)
   - **Zahlen-Felder** (z.B. Port-Nummer)
   - **Ja/Nein Kontrollkästchen** (z.B. Dienst neu gestartet)
   - **Drop-Down Auswahlfelder** (z.B. PVS-Hersteller)
4. Legen Sie Pflichtfelder fest (*).

Beim Ausfüllen eines Falls im Cockpit passt sich das Formular automatisch an das gewählte Schema an!
"""
    },
    {
        "id": "export",
        "title": "📤 Export-Engine & Vorlagen",
        "category": "Export",
        "content": """
### 📤 Übergabe- & Export-Engine

Generieren Sie mit einem Klick fertige Übergabeprotokolle, E-Mails oder Dokumentationen für Kollegen oder Ticketsysteme.

#### Fall exportieren
1. Wählen Sie den gewünschten Fall aus und klicken Sie auf **📤 Export (Strg+E)**.
2. Wählen Sie eine Vorlage (z.B. *"Standard Übergabe"*, *"Kunden-Zusammenfassung"*, *"Entwickler-Bugreport"*).
3. Wählen Sie das Ausgabeformat:
   - **Markdown** (ideal für Wikis / Jira / GitHub)
   - **HTML / Text** (ideal für E-Mails)
   - **PDF** (für Ausdruck / Archivierung)
4. Nutzen Sie den Button **📋 In Zwischenablage kopieren** oder **💾 Als Datei speichern**.
"""
    },
    {
        "id": "wiki",
        "title": "📚 BookStack Wiki Integration",
        "category": "Wiki",
        "content": """
### 📚 BookStack Wiki Integration

Das Support-Cockpit ist direkt mit Ihrem BookStack Wiki verbunden, um Lösungsartikel sofort griffbereit zu haben.

#### Funktionen
- **Automatische Suche**: Tippen Sie Suchbegriffe in die Wiki-Suchleiste ein, um passende Artikel zu finden.
- **Artikel-Vorschau**: Artikel-Inhalte werden direkt im rechten Cockpit-Panel gerendert.
- **In BookStack öffnen**: Öffnen Sie Artikel mit einem Klick in Ihrem Standard-Browser.
- **Fall-Verknüpfung**: Verknüpfen Sie gelöste Fälle mit dem entsprechenden Wiki-Artikel.
- **Konfiguration**: Tragen Sie Ihre BookStack URL und API-Tokens in **Profil & Einstellungen** (`👤`) ein.
"""
    },
    {
        "id": "p2p",
        "title": "🔄 Peer-to-Peer Sync (Kollegen)",
        "category": "Sync",
        "content": """
### 🔄 Peer-to-Peer (P2P) Synchronisation

Arbeiten Sie mit Kollegen ohne zentralen Server zusammen! Die P2P-Sync ermöglicht das Abgleichen von Fällen direkt zwischen lokalen Arbeitsplätzen.

#### Ablauf
1. Klicken Sie auf **🔄 P2P-Sync**.
2. Wählen Sie den Kollegen aus, mit dem Sie synchronisieren möchten.
3. Das System vergleicht den Versionsstand der Fälle.
4. Im **Diff-Dialog** sehen Sie Konflikte oder neu hinzugefügte Fälle und können Änderungen sicher zusammenführen.
"""
    },
    {
        "id": "shortcuts",
        "title": "⌨️ Tastenkürzel & Hotkeys",
        "category": "Tastenkürzel",
        "content": """
### ⌨️ Tastenkürzel (Shortcuts)

Arbeiten Sie noch schneller mit folgenden Hotkeys:

| Aktion | Tastenkürzel |
| :--- | :--- |
| **Neuer Fall** | `Strg + N` |
| **Fall exportieren** | `Strg + E` |
| **Fall speichern** | `Strg + S` |
| **Wiki-Suche fokussieren** | `Strg + F` |

*Hinweis: Tastenkürzel können in den Einstellungen (`👤 Profil & Einstellungen`) angepasst werden.*
"""
    }
]


class HelpDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("📖 Handbuch & Anwendungsdokumentation")
        self.geometry("960x640")
        self.minsize(800, 500)

        # Make modal window
        self.transient(parent)
        self.grab_set()

        self.filtered_articles = list(HELP_ARTICLES)
        self.active_article = HELP_ARTICLES[0]

        self.create_widgets()
        self.select_article(self.active_article["id"])

    def create_widgets(self):
        # Main Layout: Top search bar, Left navigation list, Right detail view
        top_bar = ctk.CTkFrame(self, height=50, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        ctk.CTkLabel(top_bar, text="📖 Handbuch & Hilfe", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        self.search_entry = ctk.CTkEntry(top_bar, placeholder_text="🔍 Themen & Stichworte suchen...", width=320)
        self.search_entry.pack(side="right", padx=10)
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)

        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Left Sidebar (Article list)
        left_frame = ctk.CTkFrame(body_frame, width=280)
        left_frame.pack(side="left", fill="y", padx=(0, 5), pady=0)
        left_frame.pack_propagate(False)

        ctk.CTkLabel(left_frame, text="Themenübersicht", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.nav_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.nav_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Right Detail View (Article Content)
        right_frame = ctk.CTkFrame(body_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)

        self.article_title_lbl = ctk.CTkLabel(right_frame, text="", font=ctk.CTkFont(size=18, weight="bold"), anchor="w")
        self.article_title_lbl.pack(fill="x", padx=15, pady=(15, 5))

        self.content_textbox = ctk.CTkTextbox(right_frame, wrap="word", font=ctk.CTkFont(size=13))
        self.content_textbox.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        self.content_textbox.configure(state="disabled")

        self.render_nav_list()

    def render_nav_list(self):
        for w in self.nav_scroll.winfo_children():
            w.destroy()

        if not self.filtered_articles:
            ctk.CTkLabel(self.nav_scroll, text="Keine Themen gefunden.", text_color="gray").pack(pady=20)
            return

        for art in self.filtered_articles:
            is_active = art["id"] == self.active_article["id"]
            fg_color = ("gray75", "gray30") if is_active else ("gray85", "gray20")
            btn = ctk.CTkButton(
                self.nav_scroll,
                text=art["title"],
                anchor="w",
                fg_color=fg_color,
                hover_color=("gray70", "gray35"),
                text_color=("black", "white") if is_active else ("gray10", "gray90"),
                command=lambda a_id=art["id"]: self.select_article(a_id)
            )
            btn.pack(fill="x", pady=3, padx=2)

    def select_article(self, article_id: str):
        article = next((a for a in HELP_ARTICLES if a["id"] == article_id), None)
        if not article:
            return

        self.active_article = article
        self.article_title_lbl.configure(text=article["title"])

        self.content_textbox.configure(state="normal")
        self.content_textbox.delete("1.0", "end")
        self.content_textbox.insert("1.0", article["content"].strip())
        self.content_textbox.configure(state="disabled")

        self.render_nav_list()

    def on_search_changed(self, event=None):
        query = self.search_entry.get().strip().lower()
        if not query:
            self.filtered_articles = list(HELP_ARTICLES)
        else:
            self.filtered_articles = [
                a for a in HELP_ARTICLES
                if query in a["title"].lower() or query in a["content"].lower() or query in a["category"].lower()
            ]

        if self.filtered_articles and self.active_article not in self.filtered_articles:
            self.active_article = self.filtered_articles[0]
            self.select_article(self.active_article["id"])

        self.render_nav_list()
