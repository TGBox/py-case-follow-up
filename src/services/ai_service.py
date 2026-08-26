import json
import urllib.request
import urllib.error
import re
from typing import Any
from models.case import Case
from enums import get_actor_display, get_board_column_display


class AiService:
    """Service providing Hybrid AI Capabilities: Ollama Local LLM REST API + Rule-Based Zero-Token Fallback Engine."""

    def __init__(self, ollama_url: str = "http://localhost:11434", model_name: str = "llama3"):
        self.ollama_url = ollama_url.rstrip("/")
        self.model_name = model_name

    def check_ollama_status(self) -> tuple[bool, list[str]]:
        """Checks if local Ollama server is running and lists installed LLM models."""
        try:
            url = f"{self.ollama_url}/api/tags"
            req = urllib.request.Request(url, headers={"User-Agent": "SupportCockpit/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                    return True, models
        except Exception:
            pass
        return False, []

    def _query_ollama(self, prompt: str, system_prompt: str = "") -> str | None:
        """Sends a generation request to the local Ollama LLM API."""
        try:
            url = f"{self.ollama_url}/api/generate"
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
            }
            if system_prompt:
                payload["system"] = system_prompt

            json_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=json_bytes, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                if resp.status == 200:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    return res_data.get("response", "").strip()
        except Exception:
            pass
        return None

    @staticmethod
    def build_system_prompt(
        base_rules: list[str] | None = None,
        practice_rules: list[str] | None = None,
        default_role: str = "Du bist ein hochqualifizierter IT-Support-Assistent für Arztpraxis-Software im deutschen Gesundheitswesen.",
    ) -> str:
        """Builds a hierarchical system prompt where practice-specific rules explicitly override global base rules."""
        prompt_parts = [default_role]
        base_rules = [r.strip() for r in (base_rules or []) if r.strip()]
        practice_rules = [r.strip() for r in (practice_rules or []) if r.strip()]

        if base_rules:
            prompt_parts.append("\n--- GLOBALE BASIS-REGELN ---")
            for idx, r in enumerate(base_rules, 1):
                prompt_parts.append(f"{idx}. {r}")

        if practice_rules:
            prompt_parts.append("\n--- PRAXIS-SPEZIFISCHE REGELN (VORRANGIG UND BINDEND!) ---")
            prompt_parts.append("WICHTIGER HINWEIS: Die folgenden Praxis-Regeln haben IMMER Vorrang vor den globalen Basis-Regeln! Falls eine Praxis-Regel einer Basis-Regel widerspricht, musst du dich ZWINGEND an die Praxis-Regel halten:")
            for idx, r in enumerate(practice_rules, 1):
                prompt_parts.append(f"{idx}. {r}")

        return "\n".join(prompt_parts)

    def summarize_case(
        self,
        case: Case,
        base_rules: list[str] | None = None,
        practice_rules: list[str] | None = None,
    ) -> str:
        """Generates a concise bulleted summary of a support case using Ollama LLM or Rule-Based NLP."""
        is_online, _ = self.check_ollama_status()
        if is_online:
            timeline_str = "\n".join(f"- [{t.timestamp[:16]}] {t.author} ({t.channel}): {t.note}" for t in case.timeline)
            prompt = (
                f"Bitte erstelle eine präzise, übersichtliche stichpunktartige Zusammenfassung auf Deutsch für folgenden Support-Fall:\n\n"
                f"Fall-ID: {case.case_id}\n"
                f"Praxis / Kunde: {case.customer.practice_name} ({case.customer.customer_id})\n"
                f"Thema: {case.classification.title}\n"
                f"Zuständig: {get_actor_display(case.workflow_status.current_actor)}\n"
                f"Status: {get_board_column_display(case.workflow_status.board_column)}\n"
                f"Zeitleiste:\n{timeline_str}\n\n"
                f"Formatiere das Ergebnis in 3 Abschnitte:\n"
                f"1. Problembeschreibung\n"
                f"2. Bisherige Maßnahmen\n"
                f"3. Nächster erforderlicher Schritt"
            )
            sys_prompt = self.build_system_prompt(base_rules, practice_rules)
            res = self._query_ollama(prompt, system_prompt=sys_prompt)
            if res:
                return res

        # Fallback Engine (Rule-Based Zero-Token NLP)
        return self._generate_rule_based_summary(case)

    def _generate_rule_based_summary(self, case: Case) -> str:
        lines = [
            f"📌 FALL-ZUSAMMENFASSUNG [{case.case_id}]",
            f"• Kunde / Praxis: {case.customer.practice_name} ({case.customer.customer_id})",
            f"• Thema: {case.classification.title}",
            f"• Aktueller Status: {get_board_column_display(case.workflow_status.board_column)} | Zuständig: {get_actor_display(case.workflow_status.current_actor)}",
            "",
            "1. PROBLEM-ÜBERSICHT:",
        ]

        unformatted = case.form_data.get("unformatted_description", "")
        if unformatted:
            lines.append(f"  - {unformatted.strip()[:200]}...")
        else:
            lines.append(f"  - {case.classification.title}")

        lines.extend(["", "2. ZEITLEISTE & MASSNAHMEN:"])
        if case.timeline:
            for entry in case.timeline[-3:]:
                note_snippet = entry.note.strip().replace("\n", " ")[:100]
                lines.append(f"  - [{entry.timestamp[:16]}] {entry.author}: {note_snippet}")
        else:
            lines.append("  - Keine bisherigen Zeitleisten-Einträge.")

        lines.extend(["", "3. NÄCHSTER SCHRITT:"])
        if case.workflow_status.followup_at:
            from utils.datetime_utils import format_german_date_with_relative
            fw_str = format_german_date_with_relative(case.workflow_status.followup_at)
            lines.append(f"  - 🔔 Geplante Wiedervorlage am {fw_str} ({case.workflow_status.followup_note or 'Rückruf'})")
        elif case.workflow_status.is_completed:
            lines.append("  - ✓ Fall abgeschlossen.")
        else:
            lines.append(f"  - Bearbeitung durch {get_actor_display(case.workflow_status.current_actor)} ausstehend.")

        return "\n".join(lines)

    def suggest_solutions(self, case: Case, wiki_articles: list[dict] | None = None) -> list[dict[str, str]]:
        """Scans case context and returns matched solution cards from Wiki articles and error patterns."""
        solutions = []
        full_text = f"{case.classification.title} {' '.join(str(v) for v in case.form_data.values())} {' '.join(t.note for t in case.timeline)}".lower()

        # Known error pattern rules
        if "cobra" in full_text or "schnittstelle" in full_text:
            solutions.append({
                "title": "⚡ COBRA-Schnittstelle: Neustart & Token-Refresh",
                "snippet": "1. COBRA Bridge Dienst beenden.\n2. Config.ini Token erneuern.\n3. Dienst neu starten und Datenimport erneut ausführen.",
                "confidence": "95%",
                "source": "Fehlercode-Muster (COBRA)",
            })

        if "erezept" in full_text or "verordnung" in full_text or "egk" in full_text:
            solutions.append({
                "title": "⚡ eRezept / TI-Kartenleser Verbindungsprüfung",
                "snippet": "1. SMC-B Karte im Terminal neu stecken.\n2. KTR-Dienst Status auf 'GRÜN' prüfen.\n3. Signaturzertifikat aktualisieren.",
                "confidence": "90%",
                "source": "Fehlercode-Muster (eRezept/TI)",
            })

        if "labor" in full_text or "ldt" in full_text:
            solutions.append({
                "title": "⚡ LDT-Laborbefund Importpfad prüfen",
                "snippet": "1. Eingangsverzeichnis auf Leserechte prüfen.\n2. LDT3-Zeichensatz auf ISO-8859-15 umstellen.",
                "confidence": "85%",
                "source": "Fehlercode-Muster (Labor)",
            })

        # Match against BookStack Wiki articles if provided
        if wiki_articles:
            for art in wiki_articles:
                t_str = str(art.get("title", "")).lower()
                c_str = str(art.get("content", "")).lower()
                if any(w in full_text for w in t_str.split()) and len(t_str) > 3:
                    solutions.append({
                        "title": f"📚 Wiki: {art.get('title', '')}",
                        "snippet": str(art.get("content", ""))[:180] + "...",
                        "confidence": "80%",
                        "source": "BookStack Wiki",
                    })

        if not solutions:
            solutions.append({
                "title": "💡 Standard-Diagnose: Logfile-Analyse",
                "snippet": "1. Log-Dateien unter data/attachments/ prüfen.\n2. Programmbereich-Zuordnung kontrollieren.\n3. Rücksprache mit Entwicklung (DEV) veranlassen.",
                "confidence": "70%",
                "source": "Standard-Verfahren",
            })

        return solutions

    def generate_customer_response(
        self,
        case: Case,
        intent: str = "",
        user_name: str = "Ihr Support-Team",
        base_rules: list[str] | None = None,
        practice_rules: list[str] | None = None,
    ) -> str:
        """Generates a polite German customer reply draft tailored to the case."""
        is_online, _ = self.check_ollama_status()
        if is_online:
            prompt = (
                f"Formuliere eine höfliche, professionelle deutsche Support-E-Mail-Antwort für folgenden Fall:\n"
                f"Kunde / Ansprechpartner: {case.customer.contact_person or case.customer.practice_name}\n"
                f"Fall-ID: {case.case_id}\n"
                f"Titel: {case.classification.title}\n"
                f"Nutzerwunsch/Ziel: {intent or 'Status-Update und nächste Schritte mitteilen'}\n"
                f"Absender: {user_name}"
            )
            sys_prompt = self.build_system_prompt(base_rules, practice_rules, default_role="Du bist ein freundlicher IT-Support-Mitarbeiter im deutschen Gesundheitswesen.")
            res = self._query_ollama(prompt, system_prompt=sys_prompt)
            if res:
                return res

        # Fallback Template
        cp = case.customer.contact_person or case.customer.practice_name
        salutation = f"Sehr geehrte/r {cp}," if cp else "Sehr geehrte Damen und Herren,"
        return (
            f"{salutation}\n\n"
            f"vielen Dank für Ihre Rückmeldung zu Ihrem Support-Anliegen (Fall-ID: {case.case_id}).\n\n"
            f"Wir haben Ihr Anliegen bezüglich '{case.classification.title}' geprüft. "
            f"{intent or 'Unsere Fachabteilung arbeitet aktuell an der Bereinigung.'}\n\n"
            f"Sobald uns neue Erkenntnisse vorliegen, informieren wir Sie unverzüglich.\n\n"
            f"Mit freundlichen Grüßen,\n"
            f"{user_name}"
        )
