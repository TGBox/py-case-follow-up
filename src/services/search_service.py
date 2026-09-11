import functools
from dataclasses import dataclass, field
from datetime import datetime
from models.case import Case
from utils.datetime_utils import hours_until_deadline, get_local_now


@dataclass
class SearchQuery:
    vip: bool | None = None
    actor: str | None = None
    status: str | None = None  # "open", "done", "archived"
    error: str | None = None
    deadline: str | None = None  # "<2h", "overdue"
    tag: str | None = None
    reminder: str | None = None  # "due", "true", "false"
    internal: bool | None = None  # True for internal tasks, False for customer cases
    free_text_terms: list[str] = field(default_factory=list)


@functools.lru_cache(maxsize=256)
def parse_search_query(query_str: str) -> SearchQuery:
    """Parses a search query string containing tokens and free text."""
    query = SearchQuery()
    if not query_str:
        return query

    tokens = query_str.strip().split()
    free_text_terms = []

    for token in tokens:
        if ":" in token:
            key, val = token.split(":", 1)
            key_lower = key.lower()
            val_lower = val.lower()

            if key_lower == "vip":
                query.vip = val_lower in ("true", "1", "yes", "ja")
            elif key_lower in ("is", "type"):
                if val_lower in ("internal", "intern"):
                    query.internal = True
                elif val_lower in ("customer", "kunde", "praxis"):
                    query.internal = False
            elif key_lower == "internal":
                query.internal = val_lower in ("true", "1", "yes", "ja")
            elif key_lower == "actor":
                query.actor = val_lower
            elif key_lower == "status":
                query.status = val_lower
            elif key_lower == "error":
                query.error = val
            elif key_lower == "deadline":
                query.deadline = val_lower
            elif key_lower in ("tag", "tags"):
                query.tag = val_lower
            elif key_lower in ("reminder", "followup", "wiedervorlage"):
                query.reminder = val_lower
            else:
                free_text_terms.append(val)
        else:
            free_text_terms.append(token)

    query.free_text_terms = free_text_terms
    return query


class SearchService:
    @staticmethod
    def matches_query(case: Case, query: SearchQuery, now: datetime | None = None) -> bool:
        ref_now = now or get_local_now()

        # 0. Internal Token
        if query.internal is not None:
            if case.is_internal != query.internal:
                return False

        # 1. VIP Token
        if query.vip is not None:
            if case.customer.is_vip != query.vip:
                return False

        # 2. Actor Token
        if query.actor is not None:
            case_actor = (case.workflow_status.current_actor or "").lower()
            target_actor = query.actor.lower()
            if target_actor == "dev":
                target_actor = "development"
            if case_actor != target_actor:
                return False

        # 3. Status Token
        if query.status is not None:
            target_status = query.status.lower()
            if target_status == "open":
                if case.workflow_status.is_completed or case.workflow_status.is_archived:
                    return False
            elif target_status == "done":
                if not case.workflow_status.is_completed:
                    return False
            elif target_status == "archived":
                if not case.workflow_status.is_archived:
                    return False

        # 4. Error Token
        if query.error is not None:
            error_val = str(case.form_data.get("error_code", ""))
            if query.error.lower() not in error_val.lower():
                return False

        # 5. Deadline Token
        if query.deadline is not None:
            if not case.classification.deadline_callback:
                return False
            h_remaining = hours_until_deadline(case.classification.deadline_callback, ref_now)
            if query.deadline == "overdue":
                if h_remaining >= 0:
                    return False
            elif query.deadline in ("<2h", "2h"):
                if not (0 <= h_remaining <= 2.0):
                    return False

        # 6. Tag Token
        if query.tag is not None:
            case_tags = [t.lower() for t in case.classification.tags]
            if query.tag.lower() not in case_tags:
                return False

        # 7. Reminder / Followup Token
        if query.reminder is not None:
            if query.reminder in ("true", "set", "ja", "due"):
                if not case.workflow_status.followup_at:
                    return False
                if query.reminder == "due":
                    try:
                        from utils.datetime_utils import parse_iso
                        fw_dt = parse_iso(case.workflow_status.followup_at)
                        if fw_dt > ref_now:
                            return False
                    except Exception:
                        pass
            elif query.reminder in ("false", "nein", "none"):
                if case.workflow_status.followup_at:
                    return False

        # 8. Free text terms
        if query.free_text_terms:
            form_vals = [str(v) for v in case.form_data.values()] if isinstance(case.form_data, dict) else []
            searchable_text = " ".join([
                case.case_id,
                case.classification.title,
                " ".join(case.classification.tags),
                case.customer.customer_id,
                case.customer.practice_name,
                case.customer.contact_person,
                case.customer.phone,
                case.workflow_status.followup_note,
                " ".join(form_vals),
                " ".join(t.note for t in case.timeline),
                " ".join(t.author for t in case.timeline),
            ]).lower()

            for term in query.free_text_terms:
                if term.lower() not in searchable_text:
                    return False

        return True

    @classmethod
    def filter_cases(cls, cases: list[Case], query_str: str, now: datetime | None = None) -> list[Case]:
        query = parse_search_query(query_str)
        return [c for c in cases if cls.matches_query(c, query, now)]

    @staticmethod
    def extract_case_search_match_summary(
        case: Case,
        terms: list[str],
        max_matches: int = 3,
        max_chars: int = 50,
    ) -> str | None:
        """Extracts matching words from non-primary case fields (timeline notes, follow-up note, form fields, tags, contacts)."""
        valid_terms = [t.strip().lower() for t in terms if t and t.strip()]
        if not valid_terms:
            return None

        # Primary fields already rendered in card
        primary_text = " ".join([
            case.case_id,
            case.customer.practice_name,
            case.classification.title,
            case.workflow_status.current_actor or "",
        ]).lower()

        fields_to_check: list[str] = []
        if case.classification.tags:
            fields_to_check.extend(case.classification.tags)
        if case.workflow_status.followup_note:
            fields_to_check.append(case.workflow_status.followup_note)
        if case.customer.contact_person:
            fields_to_check.append(case.customer.contact_person)
        if case.customer.phone:
            fields_to_check.append(case.customer.phone)
        if case.customer.email:
            fields_to_check.append(case.customer.email)
        if isinstance(case.form_data, dict):
            for v in case.form_data.values():
                if v:
                    fields_to_check.append(str(v))
        for t in case.timeline:
            if t.note:
                fields_to_check.append(t.note)
            if t.author:
                fields_to_check.append(t.author)

        unique_matches: list[str] = []
        seen: set[str] = set()
        has_more_matches = False
        strip_chars = ",;:()[]{}<>\"'\t\r\n"

        for field_text in fields_to_check:
            words = field_text.split()
            for w in words:
                clean_w = w.strip(strip_chars)
                if not clean_w:
                    continue
                w_low = clean_w.lower()
                # Check if this word matches any term
                if any(term in w_low for term in valid_terms):
                    # Check if this word already exists in primary card labels
                    if w_low in primary_text:
                        continue
                    if w_low in seen:
                        continue
                    seen.add(w_low)
                    if len(unique_matches) < max_matches:
                        unique_matches.append(clean_w)
                    else:
                        has_more_matches = True

        if not unique_matches:
            return None

        result_parts: list[str] = []
        current_len = 0
        truncated = has_more_matches

        for i, word in enumerate(unique_matches):
            add_len = len(word) + (2 if i > 0 else 0)
            if current_len + add_len > max_chars:
                if i == 0:
                    result_parts.append(word[: max(1, max_chars - 3)])
                    truncated = True
                else:
                    truncated = True
                break
            result_parts.append(word)
            current_len += add_len

        summary = ", ".join(result_parts)
        if truncated:
            summary += "..."
        return summary
