import os
from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Tải biến môi trường từ file .env (nếu có)
load_dotenv("./app/.env")

# Lấy giá trị DATABASE_URL từ biến môi trường


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Sử dụng cấu hình Alembic
config = context.config

# Sử dụng DATABASE_URL từ .env thay vì từ file alembic.ini
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    from logging.config import fileConfig
    fileConfig(config.config_file_name)

# Đưa metadata vào context để Alembic có thể auto-generate các migration
from app.db.base import Base
from app.Models import device, sync_log, sync_setting, user, channel, channel_record_day, channel_record_time_range, monitor_setting
from app.Models import device_user, device_integration_users, device_system_info, device_storage
from app.Models import channel_extensions, channel_stream_config
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
