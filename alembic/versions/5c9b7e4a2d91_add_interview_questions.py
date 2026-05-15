"""Add curated interview question bank

Revision ID: 5c9b7e4a2d91
Revises: d935a759c12f
Create Date: 2026-05-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "5c9b7e4a2d91"
down_revision: Union[str, None] = "d935a759c12f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interview_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("profession", sa.String(length=80), nullable=False),
        sa.Column("language", sa.String(length=80), nullable=True),
        sa.Column("competency", sa.String(length=80), nullable=False),
        sa.Column("level", sa.String(length=32), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=False),
        sa.Column("key_points", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("red_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("follow_ups", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evaluation_rubric", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("answer_time_limit_sec", sa.Integer(), server_default="120", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("answer_time_limit_sec > 0", name="ck_interview_questions_answer_time_limit"),
        sa.CheckConstraint("difficulty >= 1 AND difficulty <= 5", name="ck_interview_questions_difficulty"),
        sa.CheckConstraint("level IN ('junior', 'middle', 'senior')", name="ck_interview_questions_level"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_interview_questions_code"),
    )
    op.create_index(op.f("ix_interview_questions_code"), "interview_questions", ["code"], unique=False)
    op.create_index(op.f("ix_interview_questions_competency"), "interview_questions", ["competency"], unique=False)
    op.create_index(op.f("ix_interview_questions_id"), "interview_questions", ["id"], unique=False)
    op.create_index(op.f("ix_interview_questions_language"), "interview_questions", ["language"], unique=False)
    op.create_index(op.f("ix_interview_questions_level"), "interview_questions", ["level"], unique=False)
    op.create_index(op.f("ix_interview_questions_profession"), "interview_questions", ["profession"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_interview_questions_profession"), table_name="interview_questions")
    op.drop_index(op.f("ix_interview_questions_level"), table_name="interview_questions")
    op.drop_index(op.f("ix_interview_questions_language"), table_name="interview_questions")
    op.drop_index(op.f("ix_interview_questions_id"), table_name="interview_questions")
    op.drop_index(op.f("ix_interview_questions_competency"), table_name="interview_questions")
    op.drop_index(op.f("ix_interview_questions_code"), table_name="interview_questions")
    op.drop_table("interview_questions")
