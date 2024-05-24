import nox


@nox.session(python=["3.9", "3.10", "3.11", "3.12"])
def tests(session):
    session.install("pytest")
    session.install(".")
    session.run("pytest", "./tests")


@nox.session
def lint(session):
    session.install("flake8")
    session.run("flake8", "--max-line-length=100", "./src", "./tests")


# Speed test, not enabled by default
@nox.session(python=["3.9", "3.12"], default=False)
def speedtest(session):
    session.install(".")
    session.run("python", "./tests/fixtures/spreedtest/speedtest.py")
