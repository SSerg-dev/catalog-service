"""create products table"""

from alembic import op
import sqlalchemy as sa


revision = "20261023_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("image_object_key", sa.String(length=512), nullable=False),
        sa.Column("image_content_type", sa.String(length=100), nullable=False),
        sa.Column("source_update_id", sa.BigInteger(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_update_id", name="uq_products_source_update_id"),
    )
    op.create_index(
        "ix_products_active_created",
        "products",
        [sa.text("created_at DESC"), sa.text("id DESC")],
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_products_active_created", table_name="products")
    op.drop_table("products")

