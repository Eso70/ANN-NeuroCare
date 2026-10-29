from typing import Annotated
import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.ml.inference import ModelUnavailable, Predictor, load_predictor
from app.ml.contracts import contract_for_model
from app.schemas.prediction import PredictionInput, PredictionResponse
from app.services.predictions import create_prediction

router = APIRouter(prefix="/api/v1", tags=["Educational predictions"])


def get_predictor() -> Predictor:
    predictor = load_predictor(get_settings().model_dir)
    try:
        contract_for_model(predictor.metadata)
    except ValueError as error:
        raise ModelUnavailable(str(error)) from error
    return predictor


@router.get("/model/contract")
def model_contract():
    directory = get_settings().model_dir
    metadata = None
    if directory is not None:
        try:
            metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass  # A missing model still permits inspection of the default input contract.
    try:
        return contract_for_model(metadata)
    except ValueError as error:
        raise ModelUnavailable(str(error)) from error


@router.get("/model")
def model_details(predictor: Annotated[Predictor, Depends(get_predictor)]):
    details = {key: predictor.metadata[key] for key in (
        "version", "contract_id", "target", "threshold", "split_sizes", "test_metrics",
        "baseline_metrics", "limitations",
    )}
    details["threshold_selection"] = predictor.metadata.get("threshold_selection")
    details["validation_metrics"] = predictor.metadata.get("validation_metrics")
    details["architecture"] = predictor.architecture
    details["training"] = predictor.metadata.get("training")
    details["training_configuration"] = predictor.metadata.get("training_configuration")
    details["dataset"] = contract_for_model(predictor.metadata)["dataset"]
    details["operating_point_notice"] = predictor.metadata.get("operating_point_notice")
    return details


@router.post("/predictions", response_model=PredictionResponse, status_code=201)
def predict(
    data: PredictionInput,
    session: Annotated[Session, Depends(get_db)],
    predictor: Annotated[Predictor, Depends(get_predictor)],
) -> PredictionResponse:
    return create_prediction(data, session, predictor)
