# 🤖 Ollama PVS Support-Assistent — Modelfile

## Voraussetzungen

1. **Ollama** muss lokal installiert sein: https://ollama.com/download
2. Das **Basismodell** muss heruntergeladen werden:
   ```bash
   ollama pull qwen2.5:7b-instruct
   ```

## Installation & Erstellung

Navigiere in diesen Ordner und erstelle das Custom-Model:

```bash
cd ollama
ollama create pvs-support -f Modelfile
```

## Verwendung

### Direkt in der Kommandozeile testen

```bash
ollama run pvs-support
```

### In der App verwenden

1. Öffne **⚙ Profil & Einstellungen** → Tab **🤖 KI & NLP**
2. Trage als **Modell-Name** ein: `pvs-support`
3. Speichern — fertig!

Die App sendet ab sofort alle E-Mail-Generierungen und Zusammenfassungen an dein Custom-Model mit dem eingebetteten Regelwerk.

## Was das Modelfile enthält

| Bereich | Beschreibung |
|---------|-------------|
| **Basismodell** | `qwen2.5:7b-instruct` — kompaktes, schnelles Instruct-Modell |
| **Temperature** | `0.3` — deterministische, konsistente Antworten |
| **System-Prompt** | Vollständiges PVS-Support-Regelwerk mit 12 Regeln |
| **Beispiele** | 2 Few-Shot-Beispiele für typische Support-Szenarien |
| **Architektur** | `<analysis>` + `<response>` Zwei-Phasen-Generierung |

## Regeln im Überblick

| Regel-ID | Inhalt |
|----------|--------|
| `greeting` | Korrekte Anrede (Herr/Frau Nachname vs. Praxisteam) |
| `problem_framing` | Neutrale Problembeschreibung ("unerwartetes Verhalten") |
| `language_and_clarity` | Verständliches Praxis-Deutsch, lineare Klickpfade |
| `structure` | Einleitung + nummerierte Schritte, kompakt |
| `clarification_questions` | Max. 1–3 gezielte Rückfragen bei fehlenden Details |
| `patient_data_privacy` | Nur anonymisierte/pseudonymisierte Daten anfordern |
| `backup_prerequisite` | Datensicherung als Schritt 1 bei Reparaturen |
| `admin_privileges` | Hinweis auf Administratorrechte bei Systemänderungen |
| `commitments_and_escalation` | Keine verbindlichen Release-Termine ohne Autorisierung |
| `remote_support` | Fernwartung anbieten bei komplexen Problemen |
| `internal_data_filter` | Keine internen IDs, Tickets oder Zeitstempel |
| `closing` | Standardmäßige Grußformel |

## Zusammenspiel mit der App

```
┌─────────────────────────────────────────────────────────┐
│  SupportCockpit App                                     │
│                                                         │
│  ┌─────────────────┐    ┌───────────────────────────┐   │
│  │  Globale Basis-  │    │  Praxis-spezifische      │   │
│  │  Regeln (Profil) │    │  Regeln (pro Kunde)      │   │
│  └────────┬────────┘    └──────────┬────────────────┘   │
│           │                        │                     │
│           └──────────┬─────────────┘                     │
│                      ▼                                   │
│          ┌───────────────────────┐                       │
│          │   AiService           │                       │
│          │   build_system_prompt │                       │
│          └───────────┬───────────┘                       │
│                      │                                   │
│                      ▼                                   │
│          ┌───────────────────────┐                       │
│          │  Ollama REST API      │                       │
│          │  POST /api/generate   │                       │
│          │  model: pvs-support   │◄── Modelfile Regeln   │
│          └───────────────────────┘    (Basisschicht)     │
└─────────────────────────────────────────────────────────┘
```

**Dreischichtiges Regelwerk:**
1. **Modelfile** (Basisschicht): Im System-Prompt fest eingebettet — greift immer
2. **Globale Basis-Regeln** (App-Profil): Zur Laufzeit über `build_system_prompt()` hinzugefügt
3. **Praxis-spezifische Regeln** (pro Kunde): Überschreiben bei Konflikten die Basis-Regeln

## Tipps

- **Modell aktualisieren**: Nach Änderungen am Modelfile einfach erneut `ollama create pvs-support -f Modelfile` ausführen.
- **Alternatives Basismodell**: Ersetze `FROM qwen2.5:7b-instruct` durch z. B. `FROM llama3:8b-instruct` oder `FROM mistral:7b-instruct`.
- **Temperature anpassen**: Für kreativere Antworten auf `0.5`–`0.7` erhöhen, für striktere auf `0.1`–`0.2` senken.
