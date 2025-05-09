#!/usr/bin/env python3
"""
Script to reset a user's password in the database.
Run this script directly: python reset_password.py
"""

import argparse
import getpass

import bcrypt

from public_transport_watcher.db.models.user import User
from public_transport_watcher.utils import get_db_session


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(2)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    # Return string or decoded bytes
    if isinstance(hashed, str):
        return hashed
    return hashed.decode("utf-8")


def reset_password(email: str, new_password: str = None) -> bool:
    """Reset a user's password."""
    session = get_db_session()
    try:
        user = session.query(User).filter_by(email=email).first()

        if not user:
            print(f"No user found with email: {email}")
            return False

        # Get password if not provided
        if not new_password:
            new_password = getpass.getpass("Enter new password: ")
            confirm = getpass.getpass("Confirm new password: ")

            if new_password != confirm:
                print("Passwords do not match")
                return False

            if len(new_password) < 8:
                print("Password must be at least 8 characters")
                return False

        # Hash the new password
        hashed_password = hash_password(new_password)

        # Update the user's password
        user.password_hash = hashed_password
        session.commit()

        print(f"Password reset for user: {user.username}")
        return True

    except Exception as e:
        session.rollback()
        print(f"Error resetting password: {e}")
        return False
    finally:
        session.close()


def list_users():
    """List all users in the database."""
    session = get_db_session()
    try:
        users = session.query(User).all()
        if not users:
            print("No users found in the database")
            return

        print("Users in the database:")
        for user in users:
            print(f"Username: {user.username}, Email: {user.email}")
    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Reset a user's password")
    parser.add_argument("--email", help="User's email address")
    parser.add_argument("--password", help="New password (optional, will prompt if not provided)")
    parser.add_argument("--list", action="store_true", help="List all users")

    args = parser.parse_args()

    if args.list:
        list_users()
        return

    if not args.email:
        print("Please provide a user email with --email")
        return

    reset_password(args.email, args.password)


if __name__ == "__main__":
    main()
