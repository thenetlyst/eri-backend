from alembic import op
import sqlalchemy as sa

revision = "e28d11afa123"
down_revision = "5457f0fd4d64"
branch_labels = None
depends_on = None


def upgrade():

    # 1️⃣ add uuid column to users
    op.add_column("users", sa.Column("id_uuid", sa.UUID(), nullable=True))

    # 2️⃣ generate uuid
    op.execute("""
        UPDATE users
        SET id_uuid = gen_random_uuid();
    """)

    # 3️⃣ add temp column in participants
    op.add_column(
        "participants",
        sa.Column("user_id_uuid", sa.UUID(), nullable=True)
    )

    # 4️⃣ map participants -> users
    op.execute("""
        UPDATE participants p
        SET user_id_uuid = u.id_uuid
        FROM users u
        WHERE p.user_id = u.id;
    """)

    # 5️⃣ drop FK
    op.execute("""
        ALTER TABLE participants
        DROP CONSTRAINT IF EXISTS participants_user_id_fkey;
    """)

    # 6️⃣ drop old columns
    op.drop_column("participants", "user_id")
    op.drop_column("users", "id")

    # 7️⃣ rename
    op.alter_column("users", "id_uuid", new_column_name="id")
    op.alter_column("participants", "user_id_uuid", new_column_name="user_id")

    # ⭐ 8️⃣ create PK FIRST
    op.create_primary_key("users_pkey", "users", ["id"])

    # ⭐ 9️⃣ create FK AFTER
    op.create_foreign_key(
        "participants_user_id_fkey",
        "participants",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    pass