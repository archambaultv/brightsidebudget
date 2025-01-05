import nox


@nox.session(python=["3.13"])
def tests(session):
    session.install("pytest")
    session.install(".")
    session.run("pytest", "./tests")


@nox.session
def lint(session):
    session.install("flake8")
    session.run("flake8", "--max-line-length=100", "./src", "./tests")
