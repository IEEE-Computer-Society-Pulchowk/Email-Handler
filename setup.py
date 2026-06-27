#!/usr/bin/env python3
"""One-time setup for the Email-Handler tool."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
NC = "\033[0m"


def info(msg):
    print(f"{GREEN}\u2713{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}\u26a0{NC} {msg}")


def error(msg):
    print(f"{RED}\u2717{NC} {msg}")


def run(cmd, **kwargs):
    """Run a command and return the result."""
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, **kwargs)


def confirm(prompt, default=True):
    suffix = " [Y/n]" if default else " [y/N]"
    answer = input(f"{prompt}{suffix}: ").strip().lower()
    if default:
        return answer not in ("n", "no")
    return answer in ("y", "yes")


def main():
    print("=" * 30)
    print(" Email-Handler \u2014 Setup")
    print("=" * 30)
    print()

    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)

    # ─── Prerequisites ───────────────────────────────────────────────

    info("Checking prerequisites...")

    git_path = shutil.which("git")
    if not git_path:
        error("git is required. Install from https://git-scm.com/")
        sys.exit(1)

    python = shutil.which("python") or shutil.which("python3")
    if not python:
        error("Python is required. Install from https://python.org/")
        sys.exit(1)

    pip = shutil.which("pip") or shutil.which("pip3")
    if not pip and not Path(python).parent.joinpath("pip").exists():
        # pip might be bundled as `python -m pip`
        pass

    py_version = sys.version_info
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 7):
        error(f"Python 3.7+ required (found {py_version.major}.{py_version.minor})")
        sys.exit(1)
    info(f"Python {py_version.major}.{py_version.minor}.{py_version.micro} found")

    # ─── Clone mail-jobs (private) into jobs/ ────────────────────────

    jobs_dir = script_dir / "jobs" / "mail-jobs"

    if (jobs_dir / ".git").exists():
        info("mail-jobs repo already cloned at jobs/mail-jobs")
    else:
        print()
        print("The private mail-jobs repo stores real campaign data.")
        print("It will be cloned into jobs/mail-jobs.")
        print()
        if confirm("Clone it now?"):
            result = run(
                [
                    "git",
                    "clone",
                    "git@github.com:IEEE-Computer-Society-Pulchowk/mail-jobs.git",
                    str(jobs_dir),
                ]
            )
            if result.returncode == 0:
                info("Cloned into jobs/mail-jobs")
            else:
                warn("Clone failed. Check your SSH access and try later:")
                warn(
                    "  git clone git@github.com:IEEE-Computer-Society-Pulchowk/mail-jobs.git jobs/mail-jobs"
                )
        else:
            warn("Skipped. Run later:")
            warn(
                "  git clone git@github.com:IEEE-Computer-Society-Pulchowk/mail-jobs.git jobs/mail-jobs"
            )

    # ─── Python virtual environment ──────────────────────────────────

    venv_dir = script_dir / ".venv"

    if venv_dir.exists():
        info("Virtual environment already exists")
    else:
        info("Creating virtual environment...")
        run([python, "-m", "venv", str(venv_dir)])

    # Determine the venv Python path (cross-platform)
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    info("Installing dependencies...")
    run([str(venv_python), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    run([str(venv_python), "-m", "pip", "install", "--quiet", "-r", "requirements.txt"])
    info("Dependencies installed")

    # ─── Credentials ─────────────────────────────────────────────────

    cred_file = script_dir / "credentials.json"

    if cred_file.exists():
        info("credentials.json found")
    else:
        print()
        warn("No credentials.json found.")
        print()
        print("To send emails you need OAuth credentials from Google Cloud Console.")
        print()
        print("  1. Go to https://console.cloud.google.com/apis/credentials")
        print("  2. Create a Desktop application OAuth client ID")
        print("  3. Download the JSON and save it as credentials.json")
        print()
        if confirm("Copy the example template for now?", default=False):
            shutil.copy("credentials.example.json", "credentials.json")
            warn("Placeholder copied. Edit credentials.json with real values later.")

    # ─── Done ────────────────────────────────────────────────────────

    print()
    print("=" * 30)
    info("Setup complete!")
    print("=" * 30)
    print()
    print("Quick start:")
    print()
    if sys.platform == "win32":
        print("  .venv\\Scripts\\activate")
    else:
        print("  source .venv/bin/activate")
    print("  python main.py jobs/examples/individual --dry-run")
    print()
    print("  # Or without activating:")
    print(f"  {venv_python} main.py jobs/examples/individual --dry-run")
    print()

    if (script_dir / "jobs" / "mail-jobs").exists():
        print("Run a real campaign:")
        print(f"  {venv_python} main.py jobs/mail-jobs/my-campaign --dry-run")
        print()


if __name__ == "__main__":
    main()
