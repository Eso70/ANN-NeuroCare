"""Initial educational demonstration schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_reference", sa.String(100)),
        sa.Column("input_data", postgresql.JSONB(), nullable=False),
        sa.Column("predicted_class", sa.Integer()),
        sa.Column("predicted_probability", sa.Float()),
        sa.Column("model_version", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.CheckConstraint("predicted_probability >= 0 AND predicted_probability <= 1",
                           name="ck_predictions_probability"),
    )
    op.create_index("ix_predictions_patient_reference", "predictions", ["patient_reference"])
    op.create_index("ix_predictions_created_at", "predictions", ["created_at"])


def downgrade():
    op.drop_table("predictions")
    op.drop_table("users")
