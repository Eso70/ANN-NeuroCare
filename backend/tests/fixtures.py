from app.ml.data import FIELD_SPECS

PAYLOAD = {spec["name"]: spec["min"] for spec in FIELD_SPECS}
PAYLOAD.update(BMI=25, Age=6, Education=4, Income=5, GenHlth=3)
