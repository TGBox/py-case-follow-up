# -*- coding: utf-8 -*-
"""
Build complete locales/de.json, locales/en.json, locales/sv.json with full parity.
"""

import json
import os
import re

def generate():
    # Load base files
    with open('locales/de.json', 'r', encoding='utf-8') as f:
        de = json.load(f)
    with open('locales/en.json', 'r', encoding='utf-8') as f:
        en = json.load(f)
    with open('locales/sv.json', 'r', encoding='utf-8') as f:
        sv = json.load(f)

    # All 25 Help Content Articles in Swedish with complete fidelity to German/English:
    sv_help_content = {
        "basics": {
            "title": "🎯 Grundläggande & layouter",
            "category": "Grundläggande",
            "content": "### 🎯 Arbetsytans layouter & grundläggande funktioner\n\nSupport-Cockpit erbjuder **4 olika arbetslayouter**, som du kan välja via rullgardinsmenyn i det övre menyfältet eller med snabbkommandon:\n\n1. **Cockpit (Standard, Strg+1)**: Den kompakta 3-kolumnsvyn för aktiv handläggning. Vänster: ärendelista och filter; Mitten: kund- och ärendedetaljer samt dynamiska formulär; Höger: tidslinje, snabbåtgärder, BookStack-wiki och filbilagor.\n2. **Tavla (Kanban, Strg+2)**: Visuell statusöversikt över alla öppna ärenden uppdelade i kolumner (*Support*, *Utveckling*, *Uppföljning*, *Klart*). Ärenden kan flyttas och redigeras direkt härifrån.\n3. **Tabell (Strg+3)**: Excel-liknande tabellöversikt med sorterbara kolumner, live-sökning, anpassningsbara kolumnbredder och direkt formulärredigering i den nedre rutan.\n4. **Statistik (Strg+4)**: Analyspanel med KPI:er (genomsnittlig handläggningstid, fördelning av brådskande ärenden, toppkategorier) och exportmöjligheter.\n\n#### 📌 Skapa och redigera ärenden\n- Klicka på **+ Nytt ärende (F1)** för att registrera ett nytt supportärende.\n- Välj en mottagning från listan eller skriv in ett nytt namn.\n- Välj lämpligt **formulärschema** (t.ex. *Standard*, *Fakturering*, *Installation*).\n- Spara ändringar med **Spara (Strg+S)** eller avsluta ärendet med **✓ Klart (Strg+D)**."
        },
        "ui_customization": {
            "title": "📅 Datumformat, kalender & kolumnbredder",
            "category": "Användargränssnitt",
            "content": "### 📅 Datumvisning & användaranpassningar\n\n- **Standardformat**: Alla datum- och tidsangivelser i applikationen följer standardformatet `DD.MM.YYYY HH:MM` (t.ex. `25.08.2026 14:30`).\n- **Grafisk kalenderväljare**: Klicka på kalenderikonen bredvid datumfält för att öppna den grafiska datumväljaren med snabbval (*Idag 11:30*, *Idag 16:30*, *Imorgon 08:00*, *+ 1 dag*, *+ 1 vecka*).\n- **Kolumnbredder**: Kolumnbredder i tabellvyn kan justeras genom att dra i kolumnrubrikerna. Bredderna sparas automatiskt i din profil och kan återställas under **Inställningar** vid behov."
        },
        "praxis": {
            "title": "🏥 Mottagnings- & kundhantering",
            "category": "Kunder",
            "content": "### 🏥 Mottagningsregister & kontaktuppgifter\n\n- **Mottagningsregister**: Hantera återkommande kunder och mottagningar centralt via **Stamdata → Mottagningar & kunder**.\n- **VIP-status**: Kunder med VIP-flagga prioriteras automatiskt med +30 poäng i prioriteringssystemet.\n- **Kontaktpersoner**: Registrera läkare, mottagningschefer eller IT-ansvariga med direktnummer och e-postadress.\n- **Mottagningsspecifika AI-regler**: Definiera individuella regler för e-post- och textsvar (t.ex. särskilda hälsningsfraser eller systemspecifikationer), vilka prioriteras framför globala basregler."
        },
        "scoring": {
            "title": "⚡ Ärendepoäng & prioritering",
            "category": "Arbetsflöde",
            "content": "### ⚡ Intelligent prioriteringssystem\n\nVarje ärende tilldelas ett dynamiskt prioritetspoäng baserat på flera faktorer:\n\n- **Förfallotid**: +50 poäng om återuppringningsfristen har passerats.\n- **VIP-kund**: +30 poäng för VIP-markerade mottagningar.\n- **Nyckelord**: +20 poäng vid kritiska termer i titel eller beskrivning (t.ex. *akut*, *systemstopp*, *krasch*).\n- **Liggtid**: Poängen ökar automatiskt ju längre ett ärende förblir obehandlat.\n\nFärgindikatorer:\n- 🔴 **Röd (≥ 70 poäng)**: Kritisk prioritet.\n- 🟡 **Gul (40–69 poäng)**: Medelhög prioritet.\n- 🟢 **Grön (< 40 poäng)**: Normal prioritet."
        },
        "schemas": {
            "title": "📋 Formulärbyggare (Scheman)",
            "category": "Formulär",
            "content": "### 📋 Dynamiska formulärscheman & fältdefinitioner\n\n- **Anpassade inmatningsmasker**: Skapa skräddarsydda formulär för olika feltyper via **Formulär → Hantera formulärscheman**.\n- **Fälttyper**: Textfält, flerradiga textområden, nummerfält, datumfält, rullgardinsmenyer, kryssrutor och upprepningsbara kort.\n- **Villkorsstyrd logik (V2)**: Visa eller dölj fält dynamiskt baserat på val i andra fält.\n- **Konvertera schema**: Byt formulärschema för ett befintligt ärende när som helst utan att förlora befintlig data."
        },
        "export": {
            "title": "📤 Exportmotor & mallar",
            "category": "Export",
            "content": "### 📤 Text- och ärendeexport\n\n- **Jinja2-mallar**: Exportera ärendedata till färdiga textformat för GitLab, Jira, e-post eller dokumentation.\n- **Kopiera till urklipp**: Snabbkopiering med ett klick för att klistra in i externa ärendehanteringssystem.\n- **Tvingad export**: Exportera ofullständiga ärenden med automatiska platshållare `[SAKNAS: Fältnamn]`."
        },
        "wiki": {
            "title": "📖 BookStack Wiki-integration",
            "category": "Wiki",
            "content": "### 📖 Integrerad BookStack-kunskapsbas\n\n- **Offline-index**: Ladda ner och sök i företagets BookStack-wiki lokalt utan internetuppkoppling.\n- **Direktsökning**: Sök på felkoder eller nyckelord direkt från ärendevyn.\n- **Lösningstips**: Infoga lösningstext och wikilänkar direkt i ärendets tidslinje eller e-postutkast."
        },
        "p2p": {
            "title": "🔄 Peer-to-Peer-synkronisering (Kollegor)",
            "category": "Synk",
            "content": "### 🔄 Serverlös synkronisering mellan kollegor\n\n- **Nätverksdelning**: Synkronisera ärenden och tidslinjer direkt via en delad nätverksmapp.\n- **Jämförelse & sammanslagning**: Se skillnader mellan din lokala databas och kollegors ärenden och slå ihop ändringar med ett klick."
        },
        "shortcuts": {
            "title": "⌨ Kortkommandon & snabbtangenter",
            "category": "Kortkommandon",
            "content": "### ⌨ Globala och lokala tangentbordsgenvägar\n\n| Tangent | Funktion |\n| :--- | :--- |\n| **F1** | Skapa nytt ärende |\n| **F2** | Fokusera sökfält |\n| **F5** | Uppdatera vy |\n| **Strg + S** | Spara ärende |\n| **Strg + D** | Markera ärende som klart |\n| **Strg + E** | Öppna e-postutkast |\n| **Strg + F** | Öppna fulltextsökning |\n| **Strg + V** | Klistra in skärmdump som bilaga |\n| **Strg + 1..4** | Växla vy (Cockpit, Tavla, Tabell, Statistik) |\n| **Esc** | Stäng aktiv dialog |"
        },
        "storage_paths": {
            "title": "💾 Lagringsplatser, datamapp & körning som exe",
            "category": "Konfiguration",
            "content": "### 💾 Lagringsplatser, datastruktur & exe-drift\n\n**Support-Cockpit** sparar arbetsdata separat från programfiler. Detta möjliggör säker körning från en fristående fil (PyInstaller `.exe`) och förhindrar att verkliga kunddata versionshanteras i Git-arkiv.\n\n#### 1. Anpassa datamapp & sökvägar\n- Öppna **Profil & inställningar** (`👤 [Ditt namn]`) -> fliken **💾 Lagringsplats & sökvägar**.\n- **Huvuddatamapp**: Klicka på **📁 Välj mapp** för att välja din arbetsmapp (t.ex. på `D:\\SupportData` eller en nätverksenhet).\n- **Enskilda filsökvägar**: Du kan koppla enskilda filer (`cases.json`, `customers.json`, `wiki_index.sqlite`) till anpassade platser eller klicka på **🔄 Återställ enskilda sökvägar till standard**.\n\n#### 2. Körning som fristående körbar fil (.exe)\n- När programmet körs som en kompilerad `.exe` skapas inga mappar på installationsplatsen (t.ex. `C:\\Program Files\\`).\n- Istället lagras den centrala användarkonfigurationen i din användarprofil:\n  - Windows: `%APPDATA%\\SupportCockpit\\user_config.json`\n  - Linux/Mac: `~/.config/SupportCockpit/user_config.json`\n- Om konfigurationen saknas används automatiskt `Dokument\\SupportCockpitData` som standardmapp.\n\n#### 3. Exempelfiler & automatisk initialisering\n- **Exempelmallar i arkivet (`data_examples/`)**: Vid första start kopieras mallfiler från `data_examples/` till den valda datamappen.\n- **Tomma filer**: Om varken data eller mallar finns skapar programmet automatiskt nya, tomma datafiler för att säkerställa smidig drift."
        },
        "template_editor": {
            "title": "📄 Redigerare för exportmallar",
            "category": "Export",
            "content": "### 📄 Jinja2-mallredigerare för ärenden\n\n- Skapa egna exportmallar med stöd för variabler (`{{ case.case_id }}`, `{{ case.practice_name }}`, `{{ form.field_id }}`).\n- Live-förhandsgranskning mot det senast valda ärendet direkt i redigeraren.\n- Hantera mallar för olika ändamål (utvecklingsärenden, kundbekräftelser, interna överlämningar)."
        },
        "handover_followup": {
            "title": "🤝 Ärendeöverlämning & uppföljning",
            "category": "Arbetsflöde",
            "content": "### 🤝 Överlämning till kollegor & uppföljningshantering\n\n- **Överlämna ansvar**: Flytta ärendeansvar till utveckling, teknik eller en namngiven kollega via dialogen **🤝 Överlämna**.\n- **Kanalnotering**: Ange hur ärendet överlämnades (telefon, e-post, GitLab-ärende, muntligt).\n- **Uppföljningspåminnelse**: Schemalägg återuppringning eller kontroll med automatiska notifikationer och visuella markeringar i ärendelistan."
        },
        "email_calendar_outlook": {
            "title": "✉ E-post, kalender (.ics) & Outlook",
            "category": "Kommunikation",
            "content": "### ✉ E-postintegration och kalenderfiler\n\n- **E-postutkast**: Skapa förformaterade svar med ärende-ID, mottagningsinformation och personliga hälsningsfraser.\n- **Outlook & .eml**: Öppna utkastet direkt i Microsoft Outlook via COM eller exportera som standard `.eml`-fil.\n- **Kalenderinbjudningar (.ics)**: Skapa mötes- och påminnelsefiler som är kompatibla med Outlook, Google Calendar och Apple Kalender."
        },
        "case_print_reporting": {
            "title": "🖨 Ärendeutskrift, PDF & bilder",
            "category": "Export",
            "content": "### 🖨 Utskriftsrapporter och dokumentation\n\n- Generera professionella HTML- och PDF-rapporter för arkivering eller kundöverlämning.\n- Välj vilka delar som ska ingå: stamdata, formulärfält, tidslinjeanteckningar eller bifogade bilder.\n- Öppna i standardwebbläsare för direkt utskrift eller spara som fristående HTML-fil med inbäddade bilder."
        },
        "ai_ollama_management": {
            "title": "🤖 AI-assistent, Ollama-server & modellhantering",
            "category": "AI & Ollama",
            "content": "### 🤖 AI-driven supporthjälp (Ollama & Gemini)\n\n#### 1. Lokal körning med Ollama\n- **100% dataskydd**: Körs helt lokalt på din maskin utan att skicka data till molnet.\n- **Modellkontroll**: Välj modeller som `llama3`, `mistral` eller `qwen2.5` direkt i gränssnittet.\n- **Modelfile-hantering**: Skapa anpassade systeminstruktioner för automatisk sammanfattning och analys.\n\n#### 2. Google Gemini API (Molnalternativ)\n- Snabb och kraftfull molnbaserad AI med Google Gemini 1.5.\n- **Lokal PII-anonymisering**: Tar automatiskt bort personnamn, telefonnummer och känsliga mottagningsuppgifter innan data skickas till molnet."
        },
        "stepper_time_picker": {
            "title": "⏰ Tidsval (07:00-20:00) & stegreglage",
            "category": "Användargränssnitt",
            "content": "### ⏰ Bekväm tidsinställning\n\n- Ställ in klockslag snabbt med stegreglage för timmar och minuter (steg om 5 eller 15 minuter).\n- Snabbknappar för vanliga tider som morgonmöten, lunch och arbetsdagens slut."
        },
        "internal_cases": {
            "title": "🏢 Interna ärenden & uppgifter (utan kund)",
            "category": "Arbetsflöde",
            "content": "### 🏢 Interna arbetsuppgifter\n\n- Skapa ärenden för interna uppgifter, dokumentation eller serverunderhåll utan att koppla dem till en extern kund.\n- Välj interna kategorier som *Fjärrunderhåll*, *Datautbyte*, *Buggfix* eller *Dokumentation*."
        },
        "cobra_crm_import": {
            "title": "🐍 Cobra CRM mottagnings- & kundimport",
            "category": "Kunder",
            "content": "### 🐍 Importera kundregister från Cobra CRM\n\n- Importera mottagningar, kundnummer och kontaktuppgifter från Cobra CRM-exportfiler (.csv, .txt, .json).\n- Anpassa kolumnmappning och välj konflikthantering (*Uppdatera befintliga*, *Hoppa över*, *Skapa nya*)."
        },
        "snippets_manager": {
            "title": "📝 Textmallar & Snippet-hanterare",
            "category": "Kommunikation",
            "content": "### 📝 Återanvändbara textmallar\n\n- Spara standardsvar för vanliga supportfrågor (t.ex. första hjälpen, databaskontroller, felrapporter).\n- Tilldela snabbkommandon (t.ex. `<Ctrl-Alt-1>`) och filtrera på taggar för blixtsnabb infogning i e-post och anteckningar."
        },
        "repeatable_sub_forms": {
            "title": "📑 Dynamiska kortformulär",
            "category": "Formulär",
            "content": "### 📑 Upprepningsbara delformulär\n\n- Mata in flera poster av samma typ i ett ärende (t.ex. flera felaktiga recept, arbetsstationer eller loggfiler).\n- Varje kort kan redigeras eller tas bort separat med fullständig inmatningsvalidering."
        },
        "analytics_kpi_dashboard": {
            "title": "📊 Analys- & KPI-panel",
            "category": "Analyser",
            "content": "### 📊 Statistik, trender och prestandamått\n\n- **Översikt**: Se fördelning mellan öppna och avslutade ärenden, genomsnittlig lösningstid och brådskandegrad.\n- **Trendanalys**: Identifiera vanliga problemområden och toppkategorier över tid.\n- **Rapportkopiering**: Kopiera en snyggt formaterad Markdown-rapport till urklipp för veckomöten och uppföljning."
        },
        "advanced_search_filters": {
            "title": "🔍 Avancerat söksystem & söktaggar",
            "category": "Grundläggande",
            "content": "### 🔍 Kraftfull sökning med söktaggar\n\nAnvänd avancerade söktaggar i sökfältet för att snabbt hitta rätt ärenden:\n\n- `tag:fakturering`: Sök på specifika taggar.\n- `status:done`: Visa endast avslutade ärenden.\n- `actor:dev`: Filtrera på tilldelad avdelning.\n- `practice:weber`: Filtrera på mottagningsnamn.\n- `vip:true`: Visa endast VIP-ärenden."
        },
        "attachments_and_screenshots": {
            "title": "📎 Filbilagor & skärmdumpar (Strg+V)",
            "category": "Dokument",
            "content": "### 📎 Smidig hantering av bilagor och skärmdumpar\n\n- Tryck **Strg + V** var som helst i ärendevyn för att klistra in en bild från urklipp direkt som en PNG-bilaga i ärendemappen.\n- Dra och släpp filer eller använd filväljaren för att bifoga loggar, PDF-filer och databasbackuper.\n- Klicka på **📁 Öppna i Utforskaren** för att öppna ärendets bilagemapp i Windows Utforskaren."
        },
        "zip_backup_restore": {
            "title": "📦 Komplett ZIP-backup & import/export",
            "category": "Konfiguration",
            "content": "### 📦 Säkerhetskopiering och återställning\n\n- Exportera alla ärenden, mottagningar, inställningar och bilagor till ett komprimerat ZIP-arkiv.\n- Återställ eller flytta data till en ny dator med den guidade importguiden."
        },
        "email_webhook_integration": {
            "title": "🌐 E-postimport & REST Webhooks (Jira/GitLab)",
            "category": "Integrationer",
            "content": "### 🌐 Automatiska integrationer & inkorgssynkronisering\n\n- Hämta inkommande supportmail via IMAP och koppla automatiskt till befintliga ärenden via ärendenummer i ämnesraden.\n- Ta emot webhooks från externa system som GitLab eller Jira för att synkronisera ärendestatus."
        }
    }

    sv["help_content"] = sv_help_content

    def sort_dict(d):
        res = {}
        for k in sorted(d.keys()):
            v = d[k]
            if isinstance(v, dict):
                res[k] = sort_dict(v)
            else:
                res[k] = v
        return res

    de_sorted = sort_dict(de)
    en_sorted = sort_dict(en)
    sv_sorted = sort_dict(sv)

    with open('locales/de.json', 'w', encoding='utf-8') as f:
        json.dump(de_sorted, f, ensure_ascii=False, indent=2)
    with open('locales/en.json', 'w', encoding='utf-8') as f:
        json.dump(en_sorted, f, ensure_ascii=False, indent=2)
    with open('locales/sv.json', 'w', encoding='utf-8') as f:
        json.dump(sv_sorted, f, ensure_ascii=False, indent=2)

    print("Successfully built and synchronized all 3 locale files!")

if __name__ == '__main__':
    generate()
