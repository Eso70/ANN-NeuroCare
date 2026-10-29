from pydantic import BaseModel, ConfigDict, Field, create_model

from app.ml.data import FIELD_SPECS


class StrictInputs(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


PredictionInput = create_model("PredictionInput", __base__=StrictInputs, **{
    spec["name"]: (int, Field(ge=spec["min"], le=spec["max"], strict=True,
                             description="Annual household income (configured survey year's nominal USD)" if spec["name"] == "Income" else spec["label"]))
    for spec in FIELD_SPECS
})


class PredictionResponse(BaseModel):
    id: int
    predicted_class: int
    predicted_probability: float
    model_version: str
    decision_threshold: float = Field(gt=0, lt=1)
    notice: str = "Educational classification of a survey dataset label; not a diagnosis or future-risk estimate."
