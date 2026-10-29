"""Public surface and strict input contracts; no database or event-loop substitutes."""
import pytest
from fastapi.routing import APIRoute
from pydantic import ValidationError
from starlette.routing import Match

from app.api.routes.predictions import model_contract
from app.main import app
from app.ml.data import FIELD_SPECS
from app.schemas.prediction import PredictionInput, PredictionResponse
from tests.fixtures import PAYLOAD


@pytest.mark.parametrize("path", [
    "/api/v1/predictions", "/api/v1/predictions/1", "/api/v1/history",
    "/api/v1/users", "/api/v1/users/1", "/api/predictions",
])
def test_no_public_get_route_for_prediction_or_user_records(path):
    scope = {"type": "http", "path": path, "method": "GET", "root_path": ""}
    assert not any(route.matches(scope)[0] == Match.FULL for route in app.routes)


def test_public_get_routes_are_limited_to_health_identity_and_model_information():
    public_gets = {route.path for route in app.routes
                   if isinstance(route, APIRoute) and "GET" in route.methods}
    assert public_gets == {"/api/health", "/api/health/db", "/api/v1/",
                           "/api/v1/model", "/api/v1/model/contract"}
    assert not {"input_data", "patient_reference", "email", "name", "created_at"} & PredictionResponse.model_fields.keys()


def test_form_contract_matches_all_backend_fields_and_valid_source_codes():
    contract = model_contract()
    assert len(contract["fields"]) == 21
    assert {field["name"] for field in contract["fields"]} == PredictionInput.model_fields.keys()
    for field in FIELD_SPECS:
        if field.get("options"):
            values = [option["value"] for option in field["options"]]
            assert len(values) == len(set(values))
            assert all(field["min"] <= value <= field["max"] for value in values)
    assert PredictionInput(**PAYLOAD).HighBP == 0


@pytest.mark.parametrize("change", [
    {"Age": True}, {"BMI": "25"}, {"BMI": 25.0}, {"BMI": float("inf")},
    {"HighBP": 2}, {"patient_reference": "synthetic-private-reference"},
])
def test_non_integer_and_identifying_inputs_are_rejected(change):
    with pytest.raises(ValidationError):
        PredictionInput(**{**PAYLOAD, **change})
