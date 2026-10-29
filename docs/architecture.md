# Phase 1 architecture

This section records the original foundation. Phase 2 extends it with offline ML training,
validated prediction inputs, a prediction service/repository, and a demonstration form;
see [Phase 2](phase2.md) for the current contracts. The Phase 1 text about no write endpoints
and no ANN applies to the original phase only.

The React dashboard reads `/api/health` and `/api/health/db` independently through
the centralized Axios client. Each request has a timeout, cancellation, loading,
success, and failure state. A failed database probe never shows a connected state.

FastAPI routes validate response schemas and call services. Services call repositories,
which own SQL queries. Each request owns a SQLAlchemy session. PostgreSQL is the only
supported persistent database; JSONB stores future demonstration inputs. There are no
write endpoints in Phase 1. Alembic owns schema creation; application startup does not
create tables. The database health probe checks connectivity, not migration readiness.

Errors return generic messages without SQL strings or connection credentials. CORS
allows only the configured frontend origin. SECRET_KEY is reserved configuration;
it does not imply authentication exists. Health and API info are public local endpoints.

User and Prediction establish the future schema only. The unique email constraint also
provides a PostgreSQL index. Prediction reference and creation timestamps are indexed,
and probability is constrained to [0, 1] when non-null. No ANN or fake metrics exist.

Only synthetic, non-identifying demonstration data is appropriate. ML dependencies are
prepared for a later phase and are not imported into the health request path.
