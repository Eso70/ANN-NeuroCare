from sqlalchemy.orm import Session

from app.ml.inference import Predictor
from app.repositories.predictions import save_prediction
from app.schemas.prediction import PredictionInput, PredictionResponse


def create_prediction(data: PredictionInput, session: Session, predictor: Predictor) -> PredictionResponse:
    features = data.model_dump()
    label, probability, version = predictor.predict(features)
    record = save_prediction(session, features, label, probability, version)
    response = PredictionResponse(
        id=record.id, predicted_class=label, predicted_probability=probability,
        model_version=version, decision_threshold=predictor.threshold,
    )
    notice = getattr(predictor, "metadata", {}).get("operating_point_notice")
    if isinstance(notice, str) and notice:
        response.notice = f"{response.notice} {notice}"
    return response
