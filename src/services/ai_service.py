import json
import urllib.request
import urllib.error
import re
import logging
from typing import Any
from models.case import Case
from enums import get_actor_display, get_board_column_display
from services.anonymizer_service import PiiAnonymizer
from constants import (
    DEFAULT_OLLAMA_URL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_GEMINI_MODEL,
    GEMINI_API_BASE_URL,
    DEFAULT_MODELFILE_PATH,
    DEFAULT_PVS_MODEL_NAME,
    OLLAMA_FALLBACK_BASE_MODELS,
    OLLAMA_TIMEOUT_STATUS,
    OLLAMA_TIMEOUT_GENERATE,
    AI_USER_AGENT,
    AI_SYSTEM_ROLE_DEFAULT,
    AI_SYSTEM_ROLE_EMAIL,
    AI_PROMPT_BASE_RULES_HEADER,
    AI_PROMPT_PRACTICE_RULES_HEADER,
    AI_PROMPT_OVERRIDE_NOTICE,
    AI_PROMPT_CUSTOM_INSTRUCTION_HEADER,
    AI_PROMPT_CUSTOM_INSTRUCTION_NOTICE,
)

logger = logging.getLogger("AiService")


class AiService:
    """Service providing Hybrid AI Capabilities: 
    - Local Ollama LLM REST API
    - Cloud Google Gemini REST API (with Client-Side PII Anonymization for GDPR/Medical Compliance)
    - Rule-Based Zero-Token Fallback Engine
    """

    def __init__(
        self,
        provider: str = "OLLAMA",
        ollama_url: str = DEFAULT_OLLAMA_URL,
        model_name: str = DEFAULT_OLLAMA_MODEL,
        gemini_api_key: str = "",
        gemini_model: str = DEFAULT_GEMINI_MODEL,
        enable_anonymization: bool = True,
    ):
        self.provider = provider.upper()  # "OLLAMA" or "GEMINI"
        self.ollama_url = ollama_url.rstrip("/")
        self.model_name = model_name
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model
        self.enable_anonymization = enable_anonymization
        self.anonymizer = PiiAnonymizer(enable_anonymization=self.enable_anonymization)

    def check_ollama_status(self) -> tuple[bool, list[str]]:
        """Checks if local Ollama server is running and lists installed LLM models."""
        try:
            url = f"{self.ollama_url}/api/tags"
            req = urllib.request.Request(url, headers={"User-Agent": AI_USER_AGENT})
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_STATUS) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                    return True, models
        except Exception:
            pass
        return False, []

    def check_gemini_status(self, api_key: str | None = None, model: str | None = None) -> tuple[bool, str]:
        """Checks if Google Gemini API key is valid by querying the models list API."""
        key = api_key if api_key is not None else self.gemini_api_key
        if not key or not key.strip():
            return False, "Kein Gemini API Key konfiguriert."

        try:
            url = f"{GEMINI_API_BASE_URL}?key={key.strip()}"
            req = urllib.request.Request(url, headers={"User-Agent": AI_USER_AGENT})
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status == 200:
                    return True, f"Google Gemini API Key gültig! (Modell: {model or self.gemini_model})"
        except urllib.error.HTTPError as e:
            try:
                err_data = json.loads(e.read().decode("utf-8"))
                msg = err_data.get("error", {}).get("message", f"HTTP {e.code}")
                return False, f"Gemini API Fehler: {msg}"
            except Exception:
                return False, f"HTTP Fehler {e.code}: {e.reason}"
        except Exception as e:
            return False, f"Verbindungsfehler zu Google Gemini: {e}"

        return False, "Unbekannter API-Fehler."

    def get_available_models(self) -> list[str]:
        """Returns list of installed model names from Ollama."""
        is_online, models = self.check_ollama_status()
        return models if is_online else []

    def get_running_models(self) -> list[str]:
        """Queries /api/ps to return list of models currently loaded in memory."""
        try:
            url = f"{self.ollama_url}/api/ps"
            req = urllib.request.Request(url, headers={"User-Agent": AI_USER_AGENT})
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_STATUS) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except Exception:
            pass
        return []

    def preload_model(self, model_name: str | None = None) -> tuple[bool, str]:
        """Preloads a model into VRAM/RAM by sending an empty generation request."""
        target_model = model_name or self.model_name
        try:
            url = f"{self.ollama_url}/api/generate"
            payload = {"model": target_model, "prompt": ""}
            json_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=json_bytes, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60.0) as resp:
                if resp.status == 200:
                    return True, f"Modell '{target_model}' erfolgreich geladen!"
        except Exception as e:
            return False, f"Fehler beim Laden von '{target_model}': {e}"
        return False, f"Modell '{target_model}' konnte nicht geladen werden."

    def unload_model(self, model_name: str | None = None) -> tuple[bool, str]:
        """Unloads a model from VRAM/RAM by setting keep_alive to 0."""
        target_model = model_name or self.model_name
        try:
            url = f"{self.ollama_url}/api/generate"
            payload = {"model": target_model, "keep_alive": 0}
            json_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=json_bytes, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                if resp.status == 200:
                    return True, f"Modell '{target_model}' erfolgreich aus Speicher entladen."
        except Exception as e:
            return False, f"Fehler beim Entladen von '{target_model}': {e}"
        return False, f"Modell '{target_model}' konnte nicht entladen werden."

    def create_pvs_support_model(self, modelfile_path: str = DEFAULT_MODELFILE_PATH, base_model_override: str | None = None) -> tuple[bool, str]:
        """Creates/updates the custom 'pvs-support' model via Ollama REST API /api/create."""
        from pathlib import Path
        p = Path(modelfile_path)
        if not p.exists():
            return False, f"Modelfile '{modelfile_path}' nicht gefunden."
        try:
            content = p.read_text(encoding="utf-8")
            available = self.get_available_models()
            base_model = base_model_override
            if not base_model:
                for line in content.splitlines():
                    if line.strip().startswith("FROM "):
                        base_model = line.strip().split(maxsplit=1)[1].strip()
                        break
            if base_model and available and base_model not in available:
                for fallback in OLLAMA_FALLBACK_BASE_MODELS:
                    if any(fallback in m for m in available):
                        base_model = [m for m in available if fallback in m][0]
                        break
                else:
                    base_model = available[0]

            payload = {
                "name": DEFAULT_PVS_MODEL_NAME,
                "modelfile": content,
                "stream": False,
            }
            if base_model:
                payload["from"] = base_model

            url = f"{self.ollama_url}/api/create"
            json_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=json_bytes, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120.0) as resp:
                if resp.status == 200:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    if res_data.get("status") == "success" or "error" not in res_data:
                        self.model_name = "pvs-support"
                        return True, f"Modell 'pvs-support' aus '{modelfile_path}' (Basis: {base_model}) erfolgreich erstellt!"
                    return False, f"Erstellung fehlgeschlagen: {res_data.get('error', 'Unbekannter Fehler')}"
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                return False, f"Ollama API Fehler: {err_body.get('error', e)}"
            except Exception:
                return False, f"HTTP Fehler {e.code}: {e.reason}"
        except Exception as e:
            return False, f"Fehler bei Erstellung: {e}"
        return False, "Unbekannter Fehler bei der Erstellung."

    def start_ollama_server(self) -> tuple[bool, str]:
        """Starts the local Ollama server process in background."""
        import subprocess
        import shutil
        ollama_bin = shutil.which("ollama")
        if not ollama_bin:
            return False, "Ollama ausführbare Datei ('ollama.exe') im System-PATH nicht gefunden."

        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.Popen([ollama_bin, "serve"], creationflags=creationflags)
            return True, "Ollama Server-Prozess gestartet ('ollama serve')."
        except Exception as e:
            return False, f"Fehler beim Starten des Ollama-Servers: {e}"

    def stop_ollama_server(self) -> tuple[bool, str]:
        """Terminates running local Ollama server processes."""
        import subprocess
        import sys
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/IM", "ollama.exe", "/T"], capture_output=True)
                subprocess.run(["taskkill", "/F", "/IM", "ollama app.exe", "/T"], capture_output=True)
            else:
                subprocess.run(["pkill", "-f", "ollama"], capture_output=True)
            return True, "Ollama Server-Prozess beendet."
        except Exception as e:
            return False, f"Fehler beim Beenden des Ollama-Servers: {e}"

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
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_GENERATE) as resp:
                if resp.status == 200:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    return res_data.get("response", "").strip()
        except Exception as e:
            logger.warning(f"Ollama generation request failed or timed out: {e}")
        return None

    def _query_gemini(self, prompt: str, system_prompt: str = "") -> str | None:
        """Sends a generation request to Google Gemini API via HTTP REST."""
        if not self.gemini_api_key or not self.gemini_api_key.strip():
            logger.warning("Gemini API key is missing.")
            return None

        try:
            url = f"{GEMINI_API_BASE_URL}/{self.gemini_model}:generateContent?key={self.gemini_api_key.strip()}"
            
            combined_text = prompt
            if system_prompt:
                combined_text = f"System-Anweisungen:\n{system_prompt}\n\nBenutzer-Anfrage:\n{prompt}"

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": combined_text}
                        ]
                    }
                ]
            }

            json_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=json_bytes,
                headers={"Content-Type": "application/json", "User-Agent": AI_USER_AGENT}
            )
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                if resp.status == 200:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    candidates = res_data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                logger.warning(f"Gemini API HTTP Error {e.code}: {err_body}")
            except Exception:
                logger.warning(f"Gemini API HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            logger.warning(f"Gemini generation request failed: {e}")
        return None

    def query_llm(self, prompt: str, system_prompt: str = "", case: Case | None = None) -> str | None:
        """Unified method for querying LLM (Ollama or Gemini) with PII Anonymization."""
        # 1. Anonymize prompt and system prompt locally if Gemini or anonymization enabled
        should_anonymize = self.enable_anonymization or (self.provider == "GEMINI")
        
        mapping: dict[str, str] = {}
        anon_prompt = prompt
        anon_system = system_prompt

        if should_anonymize:
            anon_prompt, mapping_prompt = self.anonymizer.anonymize(prompt, case=case)
            anon_system, mapping_sys = self.anonymizer.anonymize(system_prompt, case=case)
            mapping = {**mapping_prompt, **mapping_sys}

        # 2. Dispatch to provider
        raw_response: str | None = None
        if self.provider == "GEMINI":
            raw_response = self._query_gemini(anon_prompt, system_prompt=anon_system)
        else:
            raw_response = self._query_ollama(anon_prompt, system_prompt=anon_system)

        if not raw_response:
            return None

        # 3. De-anonymize response locally
        if should_anonymize and mapping:
            final_response = self.anonymizer.deanonymize(raw_response, mapping)
            return final_response

        return raw_response

    @staticmethod
    def build_system_prompt(
        base_rules: list[str] | None = None,
        practice_rules: list[str] | None = None,
        custom_instruction: str | None = None,
        default_role: str = AI_SYSTEM_ROLE_DEFAULT,
    ) -> str:
        """Builds a hierarchical system prompt where practice rules override base rules and custom instructions take top priority."""
        prompt_parts = [default_role]
        base_rules = [r.strip() for r in (base_rules or []) if r.strip()]
        practice_rules = [r.strip() for r in (practice_rules or []) if r.strip()]

        if base_rules:
            prompt_parts.append(f"\n{AI_PROMPT_BASE_RULES_HEADER}")
            for idx, r in enumerate(base_rules, 1):
                prompt_parts.append(f"{idx}. {r}")

        if practice_rules:
            prompt_parts.append(f"\n{AI_PROMPT_PRACTICE_RULES_HEADER}")
            prompt_parts.append(AI_PROMPT_OVERRIDE_NOTICE)
            for idx, r in enumerate(practice_rules, 1):
                prompt_parts.append(f"{idx}. {r}")

        if custom_instruction and custom_instruction.strip():
            prompt_parts.append(f"\n{AI_PROMPT_CUSTOM_INSTRUCTION_HEADER}")
            prompt_parts.append(AI_PROMPT_CUSTOM_INSTRUCTION_NOTICE)
            prompt_parts.append(custom_instruction.strip())

        return "\n".join(prompt_parts)

    def summarize_case(
        self,
        case: Case,
        base_rules: list[str] | None = None,
        practice_rules: list[str] | None = None,
        custom_instruction: str | None = None,
    ) -> str:
        """Generates a concise bulleted summary of a support case using LLM or Rule-Based NLP."""
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
        sys_prompt = self.build_system_prompt(base_rules, practice_rules, custom_instruction=custom_instruction)
        
        res = self.query_llm(prompt, system_prompt=sys_prompt, case=case)
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
        custom_instruction: str | None = None,
    ) -> str:
        """Generates a polite German customer reply draft tailored to the case."""
        prompt = (
            f"Formuliere eine höfliche, professionelle deutsche Support-E-Mail-Antwort für folgenden Fall:\n"
            f"Kunde / Ansprechpartner: {case.customer.contact_person or case.customer.practice_name}\n"
            f"Fall-ID: {case.case_id}\n"
            f"Titel: {case.classification.title}\n"
            f"Nutzerwunsch/Ziel: {intent or 'Status-Update und nächste Schritte mitteilen'}\n"
            f"Absender: {user_name}"
        )
        sys_prompt = self.build_system_prompt(
            base_rules,
            practice_rules,
            custom_instruction=custom_instruction,
            default_role=AI_SYSTEM_ROLE_EMAIL,
        )
        
        res = self.query_llm(prompt, system_prompt=sys_prompt, case=case)
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
