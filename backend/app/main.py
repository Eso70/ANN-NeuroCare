import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.health import router
from app.api.routes.predictions import router as predictions_router
from app.core.config import get_settings
from app.ml.inference import ModelUnavailable
from app.schemas.prediction import PredictionInput

logger = logging.getLogger(__name__)
app = FastAPI(title="NeuroCare API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)
app.include_router(predictions_router)


@app.exception_handler(ModelUnavailable)
async def model_unavailable(request: Request, exc: ModelUnavailable) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "Model unavailable. Train and configure a trusted model first."})


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error("Database operation failed (%s)", type(exc).__name__)
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        location = error.get("loc", ())
        field = location[1] if len(location) > 1 and location[0] == "body" else "request"
        if field not in PredictionInput.model_fields:
            field = "request"
        message = error["msg"] if field != "request" else "Provide a valid JSON object with only the expected fields."
        # Never echo input values, arbitrary field names, or exception context.
        errors.append({"field": field, "message": message})
    return JSONResponse(status_code=422, content={"detail": "Check the highlighted input fields.", "errors": errors})


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unexpected server error (%s)", type(exc).__name__)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
