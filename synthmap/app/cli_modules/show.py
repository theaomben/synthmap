from collections import defaultdict
import pprint

import rich_click as click  # import click

from synthmap.db import manager as db_man


@click.group()
def show():
    """Prints Items for humans"""


@show.command()
@click.pass_context
def entities(ctx):
    with db_man.mk_conn(ctx.obj["db_path"], read_only=True) as db:
        data = db_man.list_entities(db)
    keys = data[0].__fields__.keys()
    print("\t".join(keys))
    stats = {k: defaultdict(int) for k in keys}
    for row in data:
        dr = dict(row)
        print(", ".join([str(i) for i in dr.values() if i]))
        for k, v in dr.items():
            stats[k][v] += 1
    print("#################################################\nStats:")
    for k, v in stats.items():
        if k in ["entity_id", "label", "detail", "way_number"]:
            continue
        print(k)
        for val, score in sorted(v.items(), key=lambda x: x[-1], reverse=True)[:3]:
            if score > 1 and val:
                print(f"\t{val}:\t{score}")


@show.command()
@click.pass_context
def entity_tree(ctx):
    with db_man.mk_conn(ctx.obj["db_path"], read_only=True) as db:
        data = db_man.list_entities(db)
    pp = pprint.PrettyPrinter()
    tree = {}
    for entity in data:
        tree = entity.to_tree(tree=tree)
    pp.pprint(tree)
