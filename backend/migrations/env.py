from logging.config import fileConfig
from pathlib import Path
import sys
from types import SimpleNamespace

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

# Add the backend project root to sys.path so Alembic can import the application
# package consistently when commands are executed from the backend directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Prefer the centralized application settings path requested for production use.
# A compatibility fallback is kept so Alembic remains functional in the current
# repo layout until the settings package is moved under app.core.config.
try:
    from app.config.settings import settings
except ModuleNotFoundError:
    try:
        from app.config.settings import settings  # type: ignore[attr-defined]
    except (ImportError, AttributeError):
        # Final fallback: read DATABASE_URL from the backend .env file so Alembic
        # still honors environment-based configuration instead of alembic.ini.
        env_values: dict[str, str] = {}
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            for raw_line in env_file.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env_values[key.strip()] = value.strip()
        settings = SimpleNamespace(DATABASE_URL=env_values.get("DATABASE_URL", ""))

from app.database.base import Base
import app.models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override the placeholder URL from alembic.ini with the application's runtime
# database setting so every Alembic command uses the same connection string.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importing app.models registers every mapped class before metadata is read.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Use the runtime-injected URL here as well so offline migrations stay in
    # sync with the same DATABASE_URL used by online engine creation.
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # engine_from_config reads the URL after config.set_main_option overrides the
    # placeholder ini value, which keeps online migrations aligned with app settings.
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
