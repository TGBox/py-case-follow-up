import json
from pathlib import Path
from models.customer import Customer
from models.profile import Colleague, UserProfile
from models.case import Case
from models.export_template import ExportTemplate
from models.schema import QuestionSchema

DATA_EXAMPLES_DIR = Path(__file__).parent.parent / "data_examples"


def test_customers_example_data():
    file_path = DATA_EXAMPLES_DIR / "customers.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list) and len(data) > 0
    expected_fields = {
        "customer_id",
        "practice_name",
        "is_vip",
        "system_version",
        "website",
        "vm_number",
        "instance_number",
        "general_notes",
        "contacts",
    }

    for item in data:
        assert expected_fields.issubset(item.keys()), f"Missing fields in customers.json item: {expected_fields - set(item.keys())}"
        cust = Customer.from_dict(item)
        assert len(cust.validate()) == 0


def test_colleagues_example_data():
    file_path = DATA_EXAMPLES_DIR / "colleagues.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list) and len(data) > 0
    expected_fields = {
        "username",
        "name",
        "department",
        "extension",
        "email",
        "mobile",
        "notes",
        "cases_path",
        "is_absent",
        "absence_reason",
    }

    for item in data:
        assert expected_fields.issubset(item.keys()), f"Missing fields in colleagues.json item: {expected_fields - set(item.keys())}"
        colleague = Colleague.from_dict(item)
        assert len(colleague.validate()) == 0


def test_cases_example_data():
    for filename in ["cases.json", "archive.json"]:
        file_path = DATA_EXAMPLES_DIR / filename
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, list) and len(data) > 0
        for item in data:
            case = Case.from_dict(item)
            assert len(case.validate()) == 0
            # Check classification keys
            assert "tags" in item.get("classification", {})
            # Check workflow status keys
            wf = item.get("workflow_status", {})
            assert "followup_at" in wf
            assert "followup_note" in wf


def test_app_profile_example_data():
    file_path = DATA_EXAMPLES_DIR / "app_profile.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    profile = UserProfile.from_dict(data)
    assert profile.user.name != ""
    assert profile.user.department != ""


def test_export_templates_example_data():
    file_path = DATA_EXAMPLES_DIR / "export_templates.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    templates = [ExportTemplate.from_dict(t) for t in data.get("templates", [])]
    assert len(templates) > 0


def test_question_schemas_example_data():
    file_path = DATA_EXAMPLES_DIR / "question_schemas.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    schemas = [QuestionSchema.from_dict(s) for s in data.get("schemas", [])]
    assert len(schemas) > 0
