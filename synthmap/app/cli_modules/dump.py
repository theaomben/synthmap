import rich_click as click  # import click


@click.group()
def dump():
    """Export Items for machines"""


@dump.command()
@click.option(
    "--db_path",
    default="main.db",
    help="Path to the SQLite3 database file against which to run.",
)
def entities(db_path):
    """Export Entities."""


@dump.command()
@click.option(
    "--db_path",
    default="main.db",
    help="Path to the SQLite3 database file against which to run.",
)
def projects(db_path):
    """Export Projects."""
