from dataclasses import dataclass, field
from datetime import datetime
import functools

from constants import (
    ACTOR_ALIAS_DEV,
    ACTOR_DEV_FULL,
    CUSTOMER_SEARCH_MAX_CHARS,
    CUSTOMER_SEARCH_MAX_MATCHES,
    DEADLINE_SEARCH_NEAR,
    DEADLINE_SEARCH_OVERDUE,
    DEADLINE_WARNING_HOURS,
    DEFAULT_ELLIPSIS,
    FALSY_SEARCH_VALUES,
    FIELD_ERROR_CODE,
    REMINDER_SEARCH_DUE,
    REMINDER_SET_VALUES,
    SEARCH_CACHE_MAXSIZE,
    SEARCH_KEY_ACTOR,
    SEARCH_KEY_DEADLINE,
    SEARCH_KEY_ERROR,
    SEARCH_KEY_INTERNAL,
    SEARCH_KEY_STATUS,
    SEARCH_KEY_VIP,
    SEARCH_KEYS_REMINDER,
    SEARCH_KEYS_TAG,
    SEARCH_KEYS_TYPE,
    SEARCH_STRIP_PUNCTUATION,
    SEARCH_TOKEN_SEPARATOR,
    SEARCH_VALUES_CUSTOMER,
    SEARCH_VALUES_INTERNAL,
    SEPARATOR_COMMA_SPACE,
    STATUS_SEARCH_ARCHIVED,
    STATUS_SEARCH_DONE,
    STATUS_SEARCH_OPEN,
    TRUTHY_SEARCH_VALUES,
)
from models.case import Case
from utils.datetime_utils import get_local_now, hours_until_deadline, parse_iso


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


@functools.lru_cache(maxsize=SEARCH_CACHE_MAXSIZE)
def parse_search_query(query_str: str) -> SearchQuery:
    """Parses a search query string containing tokens and free text."""
    query = SearchQuery()
    if not query_str:
        return query

    tokens = query_str.strip().split()
    free_text_terms = []

    for token in tokens:
        if SEARCH_TOKEN_SEPARATOR in token:
            key, val = token.split(SEARCH_TOKEN_SEPARATOR, 1)
            key_lower = key.lower()
            val_lower = val.lower()

            if key_lower == SEARCH_KEY_VIP:
                query.vip = val_lower in TRUTHY_SEARCH_VALUES
            elif key_lower in SEARCH_KEYS_TYPE:
                if val_lower in SEARCH_VALUES_INTERNAL:
                    query.internal = True
                elif val_lower in SEARCH_VALUES_CUSTOMER:
                    query.internal = False
            elif key_lower == SEARCH_KEY_INTERNAL:
                query.internal = val_lower in TRUTHY_SEARCH_VALUES
            elif key_lower == SEARCH_KEY_ACTOR:
                query.actor = val_lower
            elif key_lower == SEARCH_KEY_STATUS:
                query.status = val_lower
            elif key_lower == SEARCH_KEY_ERROR:
                query.error = val
            elif key_lower == SEARCH_KEY_DEADLINE:
                query.deadline = val_lower
            elif key_lower in SEARCH_KEYS_TAG:
                query.tag = val_lower
            elif key_lower in SEARCH_KEYS_REMINDER:
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
            if target_actor == ACTOR_ALIAS_DEV:
                target_actor = ACTOR_DEV_FULL
            if case_actor != target_actor:
                return False

        # 3. Status Token
        if query.status is not None:
            target_status = query.status.lower()
            if target_status == STATUS_SEARCH_OPEN:
                if case.workflow_status.is_completed or case.workflow_status.is_archived:
                    return False
            elif target_status == STATUS_SEARCH_DONE:
                if not case.workflow_status.is_completed:
                    return False
            elif target_status == STATUS_SEARCH_ARCHIVED:
                if not case.workflow_status.is_archived:
                    return False

        # 4. Error Token
        if query.error is not None:
            error_val = str(case.form_data.get(FIELD_ERROR_CODE, ""))
            if query.error.lower() not in error_val.lower():
                return False

        # 5. Deadline Token
        if query.deadline is not None:
            if not case.classification.deadline_callback:
                return False
            h_remaining = hours_until_deadline(case.classification.deadline_callback, ref_now)
            if query.deadline == DEADLINE_SEARCH_OVERDUE:
                if h_remaining >= 0:
                    return False
            elif query.deadline in DEADLINE_SEARCH_NEAR:
                if not (0 <= h_remaining <= DEADLINE_WARNING_HOURS):
                    return False

        # 6. Tag Token
        if query.tag is not None:
            case_tags = [t.lower() for t in case.classification.tags]
            if query.tag.lower() not in case_tags:
                return False

        # 7. Reminder / Followup Token
        if query.reminder is not None:
            if query.reminder in REMINDER_SET_VALUES:
                if not case.workflow_status.followup_at:
                    return False
                if query.reminder == REMINDER_SEARCH_DUE:
                    try:
                        fw_dt = parse_iso(case.workflow_status.followup_at)
                        if fw_dt > ref_now:
                            return False
                    except Exception:
                        pass
            elif query.reminder in FALSY_SEARCH_VALUES:
                if case.workflow_status.followup_at:
                    return False

        # 8. Free text terms
        if query.free_text_terms:
            searchable_text = case.get_searchable_text()
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
        max_matches: int = CUSTOMER_SEARCH_MAX_MATCHES,
        max_chars: int = CUSTOMER_SEARCH_MAX_CHARS,
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

        for field_text in fields_to_check:
            words = field_text.split()
            for w in words:
                clean_w = w.strip(SEARCH_STRIP_PUNCTUATION)
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
        sep_len = len(SEPARATOR_COMMA_SPACE)
        ellipsis_len = len(DEFAULT_ELLIPSIS)

        for i, word in enumerate(unique_matches):
            add_len = len(word) + (sep_len if i > 0 else 0)
            if current_len + add_len > max_chars:
                if i == 0:
                    result_parts.append(word[: max(1, max_chars - ellipsis_len)])
                    truncated = True
                else:
                    truncated = True
                break
            result_parts.append(word)
            current_len += add_len

        summary = SEPARATOR_COMMA_SPACE.join(result_parts)
        if truncated:
            summary += DEFAULT_ELLIPSIS
        return summary

