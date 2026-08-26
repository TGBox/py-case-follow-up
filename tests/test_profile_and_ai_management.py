import pytest
from unittest.mock import MagicMock, patch
from services.ai_service import AiService
from models.profile import UserProfile
from ui.widgets.ctk_tooltip import CTkTooltip


def test_ai_service_model_management_helpers():
    svc = AiService(ollama_url="http://localhost:11434", model_name="qwen3.5:9b")

    # Test get_available_models
    with patch.object(svc, "check_ollama_status", return_value=(True, ["qwen3.5:9b", "llama3:latest"])):
        models = svc.get_available_models()
        assert "qwen3.5:9b" in models
        assert "llama3:latest" in models

    # Test get_running_models mock
    mock_ps_response = MagicMock()
    mock_ps_response.status = 200
    mock_ps_response.read.return_value = b'{"models": [{"name": "qwen3.5:9b"}]}'
    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = mock_ps_response

    with patch("urllib.request.urlopen", return_value=mock_ctx):
        running = svc.get_running_models()
        assert running == ["qwen3.5:9b"]

    # Test preload_model mock
    mock_gen_response = MagicMock()
    mock_gen_response.status = 200
    mock_gen_response.read.return_value = b'{"done": true}'
    mock_gen_ctx = MagicMock()
    mock_gen_ctx.__enter__.return_value = mock_gen_response

    with patch("urllib.request.urlopen", return_value=mock_gen_ctx):
        ok, msg = svc.preload_model("qwen3.5:9b")
        assert ok is True
        assert "geladen" in msg

    # Test unload_model mock
    with patch("urllib.request.urlopen", return_value=mock_gen_ctx):
        ok, msg = svc.unload_model("qwen3.5:9b")
        assert ok is True
        assert "entladen" in msg

    # Test start_ollama_server mock
    with patch("shutil.which", return_value="C:\\Program Files\\Ollama\\ollama.exe"):
        with patch("subprocess.Popen") as mock_popen:
            ok, msg = svc.start_ollama_server()
            assert ok is True
            assert "gestartet" in msg
            mock_popen.assert_called_once()

    # Test stop_ollama_server mock
    with patch("subprocess.run") as mock_run:
        ok, msg = svc.stop_ollama_server()
        assert ok is True
        assert "beendet" in msg
        assert mock_run.called


def test_create_pvs_support_model_mock(tmp_path):
    modelfile = tmp_path / "Modelfile"
    modelfile.write_text("FROM qwen3.5:9b\nSYSTEM \"You are a support assistant.\"", encoding="utf-8")

    svc = AiService(ollama_url="http://localhost:11434")

    mock_create_resp = MagicMock()
    mock_create_resp.status = 200
    mock_create_resp.read.return_value = b'{"status": "success"}'
    mock_create_ctx = MagicMock()
    mock_create_ctx.__enter__.return_value = mock_create_resp

    with patch.object(svc, "get_available_models", return_value=["qwen3.5:9b"]):
        with patch("urllib.request.urlopen", return_value=mock_create_ctx):
            ok, msg = svc.create_pvs_support_model(str(modelfile))
            assert ok is True
            assert "erfolgreich erstellt" in msg
            assert svc.model_name == "pvs-support"


def test_global_ai_toggle_persistence():
    profile = UserProfile()
    assert profile.ai_settings.enable_ai is True

    # Toggle off
    profile.ai_settings.enable_ai = False
    data = profile.to_dict()
    assert data["ai_settings"]["enable_ai"] is False

    # Reload profile
    reloaded = UserProfile.from_dict(data)
    assert reloaded.ai_settings.enable_ai is False


def test_ctk_tooltip_dismiss_all():
    mock_tooltip1 = MagicMock()
    mock_tooltip2 = MagicMock()

    CTkTooltip._active_tooltips.clear()
    CTkTooltip._active_tooltips.add(mock_tooltip1)
    CTkTooltip._active_tooltips.add(mock_tooltip2)

    CTkTooltip.dismiss_all()

    mock_tooltip1.cancel_timer.assert_called_once()
    mock_tooltip1.hide_tooltip.assert_called_once()
    mock_tooltip2.cancel_timer.assert_called_once()
    mock_tooltip2.hide_tooltip.assert_called_once()
