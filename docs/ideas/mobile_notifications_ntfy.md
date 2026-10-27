# Mobile Benachrichtigungen bei Abwesenheit (ntfy.sh)

## Problem Statement

Wie können wir den Support-Mitarbeiter bei Abwesenheit vom Arbeitsplatz datensparsam und zuverlässig auf seinem Smartphone über kritische Vorfälle und fällige Wiedervorlagen informieren, ohne Server-Infrastruktur oder Datenschutzrisiken?

## Recommended Direction

Implementierung einer 6-stufigen, inkrementellen Benachrichtigungsarchitektur auf Basis des datensparsamen Open-Source-Push-Dienstes **ntfy.sh** kombiniert mit nativer Windows-Inaktivitäts- und Bildschirmsperre-Erkennung (`GetLastInputInfo` / Lock-Status).

Die Benachrichtigungen werden über ein individuelles, im Profil konfigurierbares Topic ausgelöst. Der Übertragungs-Payload wird von Beginn an pseudonymisiert (Ticket-Token statt sensibler Kunden-/Patientendaten), um DSGVO-Konformität zu garantieren.

### Stufenweiser Ausbau

1. **Stufe 1 (MVP)**: Win32-Inaktivitätserkennung (`IdleDetector`) + sicherer `NtfyService` + Profil-Konfiguration in `ReminderSettings` + Unittests.
2. **Stufe 2 (Filter)**: Granulare Profil-Checkboxen (Wiedervorlage, Prio 1, Zuweisungen, Notizen) mit Hook in den Reminder-Loop.
3. **Stufe 3 (Smart Digest)**: Zeitfenster-Bündelung von Routine-Notizen bei Abwesenheit mit Sofort-Bypass für Prio-1 Eskalationen.
4. **Stufe 4 (Notdienst)**: Globaler Bereitschafts-Umschalter im Tray/Cockpit für Dauerüberwachung ohne Inaktivitätszwang.
5. **Stufe 5 (Team-Brücke)**: Automatische Status-Kopplung (Windows-Lock setzt Abwesenheitsstatus im Team-Verzeichnis).
6. **Stufe 6 (Fernsteuerung)**: Interaktive Ntfy-Action-Buttons mit Hintergrund-SSE-Listener auf privatem Response-Topic.

## Key Assumptions to Validate

- [ ] Windows API `GetLastInputInfo` liefert im Benutzer-Desktop unter Windows 10/11 zuverlässig Millisekunden seit der letzten Eingabe.
- [ ] `ntfy.sh` ist ohne Registrierung über Standard-HTTPS (Port 443) aus dem Firmennetzwerk/Homeoffice erreichbar.
- [ ] Die Benachrichtigungstexte genügen für das Smartphone ohne Kundennamen/Diagnosen (z. B. `[Fall #1042] Fällige Wiedervorlage (Prio: Hoch)`).
- [ ] Die Desktop-App kann im Hintergrund (Tray/Minimiert) über `check_due_followups` periodisch prüfen, ohne den UI-Thread zu blockieren.

## MVP Scope (Stufe 1)

- **In**:
  - `src/utils/idle_detector.py`: Plattform-Erkennung (Windows `user32.dll` via `ctypes` mit Fallback für Tests).
  - `src/services/ntfy_service.py`: Versand von Push-Nachrichten via `urllib.request` (asynchron/thread-sicher, ohne externe Abhängigkeiten).
  - `src/models/profile.py`: Erweiterung von `ReminderSettings` um `mobile_ntfy_enabled`, `mobile_ntfy_topic`, `mobile_ntfy_idle_minutes`.
  - `src/constants.py`: Alle Default-Werte, Timeouts, Server-URLs und String-Keys.
  - `locales/{de,en,sv}.json`: Vollständige Übersetzung aller neuen Einstellungs- und Test-Strings.
  - Umfassende automatisierte Unittests mit 100% Mocking externer HTTP-Aufrufe.
- **Out**:
  - Keine interaktiven Action-Buttons (erst Stufe 6).
  - Keine Bündelung/Digest-Warteschlange (erst Stufe 3).
  - Keine automatische Modifikation des Team-Status (erst Stufe 5).

## Not Doing (and Why)

- **Kein eigener Push-Server**: Stattdessen Nutzung von ntfy.sh (oder selbstgehosteter ntfy-Server-URL), um Wartungs- und Hostingaufwand zu vermeiden.
- **Keine Klartext-Kundendaten über ntfy**: Keine Namen, Adressen oder medizinischen Details im Push-Body, um DSGVO-Verstöße auszuschließen.
- **Keine direkten Port-Freigaben für Fernsteuerung**: Aus Sicherheitsgründen kein lokaler HTTP-Server auf dem Client-PC; Stufe 6 nutzt ausschließlich Outbound-SSE.

## Open Questions

- Soll der ntfy-Topic-Name im Profil manuell eingegeben werden oder per Klick einen kryptischen Zufallswert (z. B. `pvs-desk-39a7b2`) generieren können? (Lösung in Stufe 1: Beides – Eingabefeld plus Zufalls-Button).
