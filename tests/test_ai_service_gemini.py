import json
import pytest
from unittest.mock import patch, MagicMock
from models.case import Case, CaseCustomer
from services.ai_service import AiService


def test_ai_service_gemini_query_with_anonymization():
    ai_service = AiService(
        provider="GEMINI",
        gemini_api_key="test_fake_key_123",
        gemini_model="gemini-1.5-flash",
        enable_anonymization=True,
    )

    case = Case(
        case_id="FALL-2026-10",
        customer=CaseCustomer(
            customer_id="KD-55",
            practice_name="Praxis Dr. Med. Hoffmann",
            contact_person="Herr Klaus Hoffmann",
            email="hoffmann@praxis.de"
        )
    )

    fake_gemini_raw_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Sehr geehrte Damen und Herren,\n\nwir haben das Problem für [PRAXIS_1] bezüglich [CASE_ID_1] analysiert."}
                    ]
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(fake_gemini_raw_response).encode("utf-8")

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = ai_service.summarize_case(case)

        # Verify urllib was called with Gemini URL
        assert mock_urlopen.called
        req_arg = mock_urlopen.call_args[0][0]
        assert "generativelanguage.googleapis.com" in req_arg.full_url
        assert "test_fake_key_123" in req_arg.full_url

        # Check payload sent to Gemini had placeholders, NOT real PII
        request_body = req_arg.data.decode("utf-8")
        assert "Praxis Dr. Med. Hoffmann" not in request_body
        assert "[PRAXIS_1]" in request_body

        # Check returned result was DE-ANONYMIZED back to original practice name!
        assert "Praxis Dr. Med. Hoffmann" in result
        assert "FALL-2026-10" in result
        assert "[PRAXIS_1]" not in result


def test_check_gemini_status_valid():
    ai_service = AiService(provider="GEMINI", gemini_api_key="valid_key")
    
    mock_resp = MagicMock()
    mock_resp.status = 200

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        ok, msg = ai_service.check_gemini_status()
        assert ok is True
        assert "gültig" in msg
