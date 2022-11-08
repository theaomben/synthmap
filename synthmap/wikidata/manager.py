from collections import defaultdict
from dateutil import parser
import json
import random
import time

import requests

from synthmap.db import manager as db_man
from synthmap.log.logger import getLogger


schema_entity = """CREATE TABLE WikiEntities(entity_id TEXT UNIQUE NOT NULL,
    modified TEXT NOT NULL,
    type TEXT NOT NULL,
    label_en TEXT,
    label_fr TEXT,
    json_data TEXT NOT NULL)"""

schema_entity_links = """CREATE TABLE WikiEntityLinks(parent_id TEXT NOT NULL,
    property_id TEXT NOT NULL,
    child_id TEXT NOT NULL)"""


def save_entity(db, entity_data):
    insert_stmt = """INSERT INTO WikiEntities
    (entity_id, modified, type, label_en, label_fr, json_data)
    VALUES (?, ?, ?, ?, ?, ?)"""
    json_data = json.dumps(entity_data, indent=None, separators=(',', ':'))
    db.execute(insert_stmt,
              [entity_data['id'],
               entity_data['modified'],
               entity_data['type'],
               entity_data['labels'].get('en', {'value': ""})['value'],
               entity_data['labels'].get('fr', {'value': ""})['value'],
               json_data])

def get_entity_by_id(db, entity_id):
    return db.execute("""SELECT * FROM WikiEntities WHERE entity_id=? ORDER BY modified DESC LIMIT 1""",
                     [entity_id]).fetchone()

def get_entity_data(db, entity_id, subquery=False):
    db_entity = get_entity_by_id(db, entity_id)
    if db_entity:
        if not subquery:
            return json.loads(db_entity['json_data'])
    time.sleep(2)
    r = requests.get(f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json")
    j = r.json()
    raw_data = j['entities'][entity_id]
    save_entity(db, raw_data)
    for k in raw_data['claims'].keys():
        get_entity_data(db, k)
    return raw_data

def link_entities(db):
    for entity in db.execute("""SELECT * FROM Entities"""):
        d = get_entity_data(db, entity['entity_id'])
        cnt = 0
        for prop_id, snaks in d['claims'].items():
            for v in snaks:
                dv = v['mainsnak'].get('datavalue')
                if not dv:
                    continue
                elif dv['type'] == 'wikibase-entityid':
                    dv_id = dv['value']['id']
                    db.execute("""INSERT INTO EntityLinks
    (parent_id, property_id, child_id)
    VALUES (?, ?, ?)""",
                               [d['id'], prop_id, dv_id])
                    cnt += 1
        print(f"Done {d['id']}, {cnt} items")

def fetch_entity_details(db, entity_id):
    d = get_entity_data(db, entity_id)
    for k, snaks in d['claims'].items():
        for v in snaks:
            try:
                dv = v['mainsnak']['datavalue']
                if dv['type'] == 'wikibase-entityid':
                    dv_id = dv['value']['id']
                    get_entity_data(db, dv_id)
            except Exception as e: 
                print(e)
                continue
        db.commit()

def query_has_bordering(db):
    linked_entities = defaultdict(int)
    for row in db.execute("""SELECT entity_id, json_extract(json_data, '$.claims.P47') AS shares_border
    FROM WikiEntities
    WHERE  json_extract(json_data, '$.claims.P47') IS NOT NULL"""):
        row_data = json.loads(row['shares_border'])
        for snak in row_data:
            if snak['mainsnak']['snaktype'] == "novalue":
                continue
            linked_entities[snak['mainsnak']['datavalue']['value']["id"]] += 1
    return dict(sorted(linked_entities.items(), key=lambda item: item[-1], reverse=True))

def query_neighborhood(db, place_id, done_entities=None, depth=3):
    if not depth:
        return None
    if not done_entities:
        done_entities = set()
    for row in db.execute("""SELECT entity_id, label_en, json_extract(json_data, '$.claims.P47') AS shares_border
    FROM WikiEntities
    WHERE json_extract(json_data, '$.claims.P47') IS NOT NULL
        AND entity_id =?""", [place_id]):
        #AND json_extract(json_data, '$.claims.P131') LIKE '%Q90%'
        print(f"processing {row['label_en']}, {row['entity_id']}, depth: {depth}")
        done_entities.add(row['entity_id'])
        row_data = json.loads(row['shares_border'])
        to_do = []
        for snak in row_data:
            if snak['mainsnak']['snaktype'] == "novalue":
                continue
            neighbour_id = snak['mainsnak']['datavalue']['value']["id"]
            if neighbour_id in done_entities:
                continue
            fetch_entity_details(db, neighbour_id)
            to_do.append(neighbour_id)
        random.shuffle(to_do)
        for i in to_do:
            query_neighborhood(db, i, done_entities, depth=depth-1)