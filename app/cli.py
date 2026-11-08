"""Custom `flask` commands: seed, seed-categories, create-admin."""
import os

import click
from flask import current_app
from sqlalchemy import select

from .extensions import db
from .models import Role, User
from .utils.timeutils import utcnow


def register_cli(app) -> None:
    app.cli.add_command(seed_command)
    app.cli.add_command(seed_categories_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(premium_expire_command)


@click.command("premium-expire")
def premium_expire_command() -> None:
    """Switch off premium listings whose end date has passed (run daily via cron)."""
    from .billing import expire_premiums

    click.echo(f"Expired premium listings: {expire_premiums()}")


@click.command("seed")
@click.option("--reset", is_flag=True, help="Delete ALL data first, then insert demo data.")
def seed_command(reset: bool) -> None:
    """Fill the database with realistic Amberg demo data (development only)."""
    if current_app.config["ENV_NAME"] == "production":
        raise click.ClickException("Demo data is never seeded in production.")
    from .seed import SeedError, run_seed

    password = os.environ.get("SEED_PASSWORD", "amberg-demo-2026")
    try:
        summary = run_seed(password=password, reset=reset)
    except SeedError as exc:
        raise click.ClickException(str(exc)) from None

    click.echo("Demo data created:")
    for name, count in summary["counts"].items():
        click.echo(f"  {name:<14} {count}")
    click.echo(f"\nAdmin login:   {summary['admin_email']}")
    click.echo(f"Business login: {summary['sample_org_email']}")
    click.echo("Password for all demo accounts: value of SEED_PASSWORD (see .env)")


@click.command("seed-categories")
def seed_categories_command() -> None:
    """Create or update the default categories. Safe to run in production."""
    from .seed import seed_categories

    seed_categories()
    db.session.commit()
    click.echo("Categories are up to date.")


@click.command("create-admin")
@click.argument("email")
@click.password_option(help="At least 12 characters.")
def create_admin_command(email: str, password: str) -> None:
    """Create an admin account, or promote an existing user to admin."""
    if len(password) < 12:
        raise click.ClickException("Admin passwords need at least 12 characters.")
    email = email.strip().lower()
    user = db.session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email)
        db.session.add(user)
    user.role = Role.ADMIN
    user.is_verified = True
    user.verified_at = user.verified_at or utcnow()
    user.set_password(password)
    db.session.commit()
    click.echo(f"Admin ready: {email}")
