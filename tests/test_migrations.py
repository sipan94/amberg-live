"""Migrations: a fresh database built with `flask db upgrade` must match the models.

Guards against two earlier problems: the version entry not being saved on SQLite, and
model changes that were never turned into a migration.
"""
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from flask_migrate import upgrade
from sqlalchemy import create_engine, text

from app import create_app
from app.extensions import db

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


def test_upgrade_saves_version_and_matches_models(tmp_path):
    db_file = tmp_path / "fresh.db"
    url = f"sqlite:///{db_file.as_posix()}"
    app = create_app("testing", overrides={"SQLALCHEMY_DATABASE_URI": url})
    with app.app_context():
        upgrade(directory=str(MIGRATIONS))
        db.engine.dispose()

    head = ScriptDirectory(str(MIGRATIONS)).get_current_head()
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == head
            diff = compare_metadata(MigrationContext.configure(conn), db.metadata)
    finally:
        engine.dispose()
    assert diff == [], f"Models and migrations differ – run `flask db migrate`: {diff}"
