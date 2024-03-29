# type: ignore
"""Noxfile for tests."""
import os

import nox
from nox.sessions import Session

DEFAULT_PYTHON_VERSIONS = ["3.7", "3.8", "3.9", "3.10"]

PYTHON_VERSIONS = os.environ.get(
    "NOX_PYTHON_VERSIONS", ",".join(DEFAULT_PYTHON_VERSIONS)
).split(",")

paths_to_check = ["xplogger", "noxfile.py"]


def setup(session: Session) -> None:
    """Install xplogger."""
    session.install("--upgrade", "setuptools", "pip")
    session.install("-r", "requirements/dev.txt")
    session.install(".")


@nox.session(python=PYTHON_VERSIONS)
def lint(session: Session) -> None:
    """Run black, flake8 and isort."""
    setup(session)
    for _path in paths_to_check:
        session.run("black", "--check", _path)
        session.run("flake8", _path)
        session.run("isort", _path, "--check", "--diff")


@nox.session(python=PYTHON_VERSIONS)
def mypy(session: Session) -> None:
    """Run mypy."""
    setup(session)
    for _path in paths_to_check:
        session.run("mypy", "--strict", _path)


@nox.session(python=PYTHON_VERSIONS)
def test(session: Session) -> None:
    """Run tests."""
    setup(session)
    session.run("pytest", "tests")
