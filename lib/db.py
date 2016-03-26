#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time, uuid, functools, threading, logging

class Dict(dict):

    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

def next_id(t=None):
    if t is None:
        t = time.time()
    return '%015d%s000' % (int(t * 1000), uuid.uuid4().hex)

def _profiling(start, sql=''):
    t = time.time() - start
    if t > 0.1:
        logging.warning('[PROFILING] [DB] %s: %s' % (t, sql))
    else:
        logging.info('[PROFILING] [DB] %s: %s' % (t, sql))


class _Engine(object):

    def __init__(self, connect):
        self._connect = connect

    def connect(self):
        return self._connect()

def create_engine(user, password, database, host='127.0.0.1', port=3306, **kw):
    params = dict(user=user, password=password, database=database, host=host, port=port)
    defaults = dict(use_unicode=True, charset='utf8', collation='utf8_general_ci', autocommit=False)
    for k, v in defaults.iteritems():
        params[k] = kw.pop(k, v)
    params.update(kw)
    params['buffered'] = True

    import mysql.connector
    return _Engine(lambda: mysql.connector.connect(**params))

def create_engine_MySQLdb(host, user, pw, db, port=3306):
    import MySQLdb
    return _Engine(lambda: MySQLdb.connect(host, user, pw, db, port, charset = 'utf8'))

engine = None


class _DbCtx(threading.local):

    def __init__(self):
        self.connection = None
        self.connection_count = 0
        self.transaction_count = 0

    def init(self):
        if self.connection is None:
            self.connection = "init"
            self.connection_count = 0
            self.transaction_count = 0

    def cursor(self):
        if self.connection is None:
            raise Exception('self.connection is None')
        elif self.connection is "init":
            global engine
            connection = engine.connect()
            self.connection = connection
            return self.connection.cursor()
        else:
            return self.connection.cursor()

    def commit(self):
        if self.connection:
            if self.connection is not "init":
                try:
                    self.connection.commit()
                except:
                    self.connection.rollback()
                    print('commit failed and rollback...')

    def rollback(self):
        if self.connection:
            if self.connection is not "init":
                self.connection.rollback()

    def cleanup(self):
        if self.connection is None:
            raise Exception('self.connetion is None')
        elif self.connection is "init":
            raise Exception('self.connection is "init"')
        else:
            connection = self.connection
            connection.close()
            self.connection = None

_db_ctx = _DbCtx()


class _ConnectionCtx(object):

    def __enter__(self):
        global _db_ctx
        _db_ctx.init()
        _db_ctx.connection_count += 1
        return self

    def __exit__(self, exctype, excvalue, traceback):
        global _db_ctx
        _db_ctx.connection_count -= 1
        if _db_ctx.connection_count == 0:
            _db_ctx.cleanup()

def connection():
    return _ConnectionCtx()

def with_connection(func):
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        with _ConnectionCtx():
            return func(*args, **kw)
    return _wrapper


class _TransactionCtx(object):

    def __enter__(self):
        global _db_ctx
        _db_ctx.init()
        _db_ctx.transaction_count += 1
        return self

    def __exit__(self, exctype, excvalue, traceback):
        global _db_ctx
        _db_ctx.transaction_count -= 1
        if _db_ctx.transaction_count == 0:
            if exctype is None:
                _db_ctx.commit()
            else:
                _db_ctx.rollback()
            _db_ctx.cleanup()

def transaction():
    return _TransactionCtx()

def with_transaction(func):
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        _start = time.time()
        with _TransactionCtx():
            return func(*args, **kw)
        _profiling(_start)
    return _wrapper


@with_connection
def _select(sql, first, *args):
    cursor = None
    try:
        global _db_ctx
        cursor = _db_ctx.cursor()
        sql = sql.replace('?', '%s')
        cursor.execute(sql, args)
        if cursor.description:
            names = [x[0] for x in cursor.description]
        else:
            raise Exception('cursor.description is None')
        if first:
            value = cursor.fetchone()
            if value:
                return Dict(names, value)
            else:
                return None
        else:
            values = cursor.fetchall()
            return [Dict(names, x) for x in values]
    finally:
        if cursor:
            cursor.close()

def select_one(sql, *args):
    return _select(sql, True, *args)

def select_int(sql, *args):
    d = _select(sql, True, *args)
    if len(d)!=1:
        raise Exception('Expect only one column.')
    return d.values()[0]

def select(sql, *args):
    return _select(sql, False, *args)


@with_connection
def _update(sql, *args):
    cursor = None
    try:
        global _db_ctx
        cursor = _db_ctx.cursor()
        sql = sql.replace('?', '%s')
        cursor.execute(sql, args)
        r = cursor.rowcount
        if _db_ctx.transaction_count == 0:
            _db_ctx.connection.commit()
        return r
    finally:
        if cursor:
            cursor.close()

def update(sql, *args):
    return _update(sql, *args)

def insert(table, **kw):
    cols, args = zip(*kw.iteritems())
    sql = 'insert into `%s` (%s) values (%s)' % (table, ','.join(['`%s`' % col for col in cols]), ','.join(['?' for i in range(len(cols))]))
    return _update(sql, *args)


if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    engine = create_engine('root', 'password', 'app_ymtx')
    update('drop table if exists user')
    update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
    import doctest
    doctest.testmod()