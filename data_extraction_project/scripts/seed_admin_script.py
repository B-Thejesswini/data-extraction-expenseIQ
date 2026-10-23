"""Seed an admin user into the database.

Idempotent: if an active user with the same email already exists it is left
untouched, unless --force is given (which resets the role and password).

Run from the project root:

    ./.venv/bin/python scripts/seed_admin_script.py
    ./.venv/bin/python scripts/seed_admin_script.py --email me@example.com --password 's3cret'
    ./.venv/bin/python scripts/seed_admin_script.py --force

Defaults can also come from the environment: SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD.
"""

import argparse
import asyncio
import os
import sys

from sqlalchemy import select

from data_extraction_project.core.security import hash_password
from data_extraction_project.db.postgres_db import AsyncSessionLocal, engine
from data_extraction_project.models.user import User

ADMIN_ROLE = "admin"
DEFAULT_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@expenseiq.local")
DEFAULT_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "admin123")


async def seed_admin(email: str, password: str, force: bool) -> int:
    async with AsyncSessionLocal() as session:
        existing = await session.scalar(
            select(User).where(User.email == email, User.is_deleted.is_(False))
        )

        if existing is not None:
            if not force:
                print(f"Admin {email!r} already exists (id={existing.id}); nothing to do.")
                return 0
            existing.role = ADMIN_ROLE
            existing.password_hash = hash_password(password)
            existing.is_active = True
            await session.commit()
            print(f"Updated admin {email!r} (id={existing.id}).")
            return 0

        user = User(
            role=ADMIN_ROLE,
            email=email,
            password_hash=hash_password(password),
            is_active=True,
            is_deleted=False,
        )
        session.add(user)
        await session.commit()
        print(f"Created admin {email!r} (id={user.id}).")
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed an admin user.")
    parser.add_argument("--email", default=DEFAULT_EMAIL, help="admin email")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="admin password")
    parser.add_argument(
        "--force",
        action="store_true",
        help="reset role and password if the user already exists",
    )
    return parser.parse_args()


async def run(email: str, password: str, force: bool) -> int:
    try:
        return await seed_admin(email, password, force)
    finally:
        await engine.dispose()


def main() -> int:
    args = parse_args()

    if not args.email:
        print("error: --email is required", file=sys.stderr)
        return 1
    if not args.password:
        print("error: --password is required", file=sys.stderr)
        return 1
    if args.password == "admin123":
        print("warning: using the default password; pass --password to change it.")

    try:
        return asyncio.run(run(args.email, args.password, args.force))
    except Exception as exc:  # noqa: BLE001 - surface a readable message to the operator
        print(f"error: could not seed admin: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
