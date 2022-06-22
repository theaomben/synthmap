import importlib.resources
import os
from pathlib import Path
from multiprocessing import Process
import sys
import time

import rich_click as click  # import click
import rich
import uvicorn

from synthmap.app.cli_modules import dump, show, parse_video, register
from synthmap.db import manager as db_man
from synthmap.log.logger import getLogger


log = getLogger(__name__)

# Uncomment if you don't want colors
# click.rich_click.COLOR_SYSTEM = None


@click.group()
@click.pass_context
@click.option(
    "--db-path",
    show_default=True,
    default=os.path.join(os.path.expanduser("~"), ".synthmap", "main.db"),
    help="Path to the SQLite3 database file to use.",
)
@click.option(
    "--db-read-only",
    show_default=True,
    default=False,
    help="Open the database for reading only.",
)
def cli(ctx, db_path, db_read_only):
    """Command Line Interface for the Synthmap project. Run --help on any subcommand to find out more.

    If --db-path is not specified, defaults to ~/.synthmap/main.db
    If --db-path references a non existing file in an existing folder, we create a
    new blank sqlite database at that path.
    Some commands *may* work with --db-path :memory: but anything that has to do with
    the server (or multiprocessing) will blow up."""
    root_folder = os.path.join(os.path.expanduser("~"), ".synthmap")
    if not os.path.exists(root_folder):
        print(
            f"""###
#
# The synthmap folder ({root_folder}) doesn't seem to exist.
# This may cause issues if you do not change some default arguments to
# subcommands and you will not be able to run most tests.
# Run `cli setup` or `cli setup --help` to review default parameters before using
# synthmap!
#
###"""
        )
    print(
        """Synthmap
This product includes software developed by Benoît Drumain & Contributors for the Theaomai Synthmap Project."""
    )
    if not ctx.obj:
        ctx.obj = {}
    ctx.obj["db_path"] = db_path
    log.debug(f"Starting CLI on instance {db_path}")
    if not os.path.exists(db_path) and os.path.isdir(Path(db_path).parent):
        db = db_man.mk_conn(db_path=db_path)
        db_man.setup_db(db)


# Initial configuration (paths, modules, ...)
@cli.command()
@click.pass_context
@click.option(
    "--root-path",
    show_default=True,
    default=os.path.join(os.path.expanduser("~"), ".synthmap"),
    help="Absolute path to folder in which to store our files.",
)
@click.option(
    "--fetch-images",
    is_flag=True,
    show_default=True,
    default=True,
    help="HTTP get a sample of known images & the associated data to run tests against.",
)
def setup(ctx, root_path, fetch_images):
    """**RUN ME FIRST** /!\\ Downloads files required for the test suite!
    Creates a subfolder (default ~/.synthmap) for system-wide configuration, sample data, database..."""
    if os.path.exists(root_path):
        log.warn(f"Root folder already exists: {root_path}, aborting setup.")
        return None
    os.makedirs(root_path)
    # We use importlib resources to locate our packaged file (from an importable location).
    # However these resources aren't really files so we need to read the content...
    _conf = (
        importlib.resources.files("synthmap.app").joinpath("config.json").read_text()
    )
    # ...and write it back as-is in the appropriate file.
    json_path = os.path.join(root_path, "config.json")
    with open(json_path, "w") as fd:
        fd.write(_conf)
    log.info(f"Config succesfully written to {json_path}")
    # Create all database tables
    db_path = os.path.join(root_path, "main.db")
    db = db_man.mk_conn()
    db_man.setup_db(db)
    db.commit()
    log.info(f"Empty database succesfully initialised at {db_path}")
    # Fetch sample images for tests


# Application server
@cli.command()
@click.pass_context
def run_server(ctx):
    """Launches a uvicorn instance in a subprocess. Runs against the database in --db_path (default: ~/.synthmap/main.db)"""
    db_path = Path(ctx.obj["db_path"])
    log.info("Starting Synthmap Server on db_path")
    p = Process(target=uvicorn.run, args=("synthmap.app.main:app",))
    p.start()
    log.info(f"Providing a server on {db_path}")
    while True:
        time.sleep(2.5)
    p.terminate()
    p.join()


# Log pretty-printer
@cli.command()
@click.pass_context
def watchdog(ctx):
    """View log (updates ~1s)"""
    with open("synthmap.log", "r") as fd:
        while True:
            line = fd.readline().strip()
            if not line:
                time.sleep(2.5)
            elif len(line.split("\t")) == 5:
                dt, level, pt_ids, callsite, message = line.split("\t")
                dt = dt[11:]
                pt_ids += " " * (12 - len(pt_ids))
                callsite = callsite[:-1]
                if len(callsite) < 26 and not len(callsite) % 2:
                    callsite += " "
                while len(callsite) < 26:
                    callsite += " ."
                if level == "DEBUG":
                    level = "[bold bright_black]D[/bold bright_black]"
                    callsite = f"[bright_black]{callsite}[/bright_black]"
                    message = f"[bright_black]{message}[/bright_black]"
                elif level == "INFO":
                    level = "[bold white]I[/bold white]"
                elif level == "WARNING":
                    level = "[bold black on yellow1]W[/bold black on yellow1]"
                elif level == "ERROR":
                    level = "[bold white on orange_red1]E[/bold white on orange_red1]"
                    callsite = f"[red on bright_black]{callsite.split(' ')[0]}[/red on bright_black] [bright_red]{callsite.split(' ', maxsplit=1)[1]}[/bright_red]"
                    message = f"[red on bright_black]{message}[/red on bright_black]"
                elif level == "CRITICAL":
                    level = "[bold black on bright_red]C[/bold black on bright_red]"
                    callsite = f"[bright_white on bright_black]{callsite}[/bright_white on bright_black]"
                    message = f"[bright_white on bright_black]{message}[/bright_white on bright_black]"
                else:
                    level = "[bold white]?[/bold white]"
                rich.print(
                    f"[bright_black]{dt}[/bright_black] {level} [bright_black]{pt_ids}[/bright_black]{callsite} {message}"
                )
            else:
                rich.print(f"\t\tWeirdly formatted log line: {line}")


# cli --db_path
#     register --root_folder --exclude_folders --print_only
#              images --dirn2session --session-name
#              projects --type
#              entities


cli.add_command(dump.dump)
cli.add_command(show.show)
cli.add_command(parse_video.parse_video)
cli.add_command(register.register)
