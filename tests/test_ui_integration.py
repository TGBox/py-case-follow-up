import pytest # type: ignore
from pathlib import Path
from config import AppConfig
from services.storage_service import StorageService
from services.seed_service import SeedService
from services.export_service import ExportService
from services.scoring_service import ScoringService
from enums import UrgencyLevel


def test_ui_service_workflow_integration(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed_service = SeedService(storage)
    seed_service.run_seed(force=True)

    # 1. Load cases and schemas
    cases = storage.load_cases()
    schemas = storage.load_schemas()
    templates = storage.load_templates()

    assert len(cases) == 12
    target_case = cases[0]
    schema = next(s for s in schemas if s.schema_id == target_case.classification.schema_id)

    # 2. Update form data in case
    target_case.form_data["database_dump_provided"] = True
    target_case.missing_required_fields.clear()
    target_case.workflow_status.is_data_complete = True

    storage.save_cases(cases)

    # 3. Export service check
    export_service = ExportService(storage)
    template = templates[0]
    success, missing, text = export_service.render_template(target_case, template, schema)

    assert success is True
    assert "Gemeinschaftspraxis" in text

    # 4. Archiving case
    storage.archive_single_case(target_case.case_id)
    remaining_cases = storage.load_cases()
    archived_cases = storage.load_archive()

    assert len(remaining_cases) == 11
    assert len(archived_cases) == 1
    assert archived_cases[0].case_id == target_case.case_id
