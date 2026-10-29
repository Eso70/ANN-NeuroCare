from sqlalchemy.orm import Session

from app.models import Prediction


def save_prediction(session: Session, features: dict, label: int, probability: float, version: str) -> Prediction:
    record = Prediction(
        input_data=features, predicted_class=label, predicted_probability=probability,
        model_version=version,
    )
    try:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
    except Exception:
        session.rollback()
        raise
