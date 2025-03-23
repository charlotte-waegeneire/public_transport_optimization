import os
import sys
import subprocess
from pathlib import Path


def run_alembic_command(command, *args):
    project_root = Path(__file__).parent.parent.parent

    os.chdir(project_root)

    alembic_cmd = ["alembic", command]
    alembic_cmd.extend(args)

    result = subprocess.run(alembic_cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("ERREUR:", result.stderr, file=sys.stderr)

    return result.returncode


def generate_migration(message):
    return run_alembic_command("revision", "--autogenerate", "-m", message)


def upgrade(revision="head"):
    return run_alembic_command("upgrade", revision)


def downgrade(revision="-1"):
    return run_alembic_command("downgrade", revision)


def show_current():
    return run_alembic_command("current")


def show_history():
    return run_alembic_command("history")


if __name__ == "__main__":
    # Utilisation example
    if len(sys.argv) < 2:
        print(
            "Usage: python -m public_transport_watcher.db.alembic_manager [command] [args]"
        )
        print("Commands: generate, upgrade, downgrade, current, history")
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "generate":
        if not args:
            print("Error: Message required for generate command")
            sys.exit(1)
        generate_migration(args[0])
    elif command == "upgrade":
        revision = args[0] if args else "head"
        upgrade(revision)
    elif command == "downgrade":
        revision = args[0] if args else "-1"
        downgrade(revision)
    elif command == "current":
        show_current()
    elif command == "history":
        show_history()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
