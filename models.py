#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time,uuid

from lib.db import next_id
from lib.orm import Model, StringField, BooleanField, FloatField, TextField

class Blog(Model):
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    name = StringField(ddl='varchar(50)')
    content = TextField()
    created_at = FloatField(updatable=False, default=time.time)

class User(Model):
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    email = StringField(updatable=False, ddl='varchar(50)')
    password = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    created_at = FloatField(updatable=False,default=time.time)

def init():
    try:
        from lib import db
        from config import configs
        db.engine = db.create_engine_MySQLdb(configs.db.host, configs.db.user, configs.db.password, configs.db.database, configs.db.port)
        Blog.create_table()
        User.create_table()
    except:
        raise Exception('init failed')

if __name__ == "__main__":
    init()

    


