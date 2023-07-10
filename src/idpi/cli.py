"""Command line interface of idpi."""
# Third-party
import click

# Local
from . import __version__


def print_version(ctx, _, value: bool) -> None:
    """Print the version number and exit."""
    if value:
        click.echo(__version__)
        ctx.exit(0)


@click.option(
    "--version",
    "-V",
    help="Print version and exit.",
    is_flag=True,
    expose_value=False,
    callback=print_version,
)
@click.group()
def main() -> None:
    """Console script for test_cli_project."""
    print("CLI for IDPI")
