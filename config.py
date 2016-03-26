#!/usr/bin/env python
# -*- coding: utf-8 -*-

def _create_db():
    host =  '127.0.0.1'
    port = 3306
    user = 'root'
    pw = 'password'
    db = 'ymtx'

    try:
        import sae.const
        host = sae.const.MYSQL_HOST
        port = int(sae.const.MYSQL_PORT)
        user = sae.const.MYSQL_USER
        pw = sae.const.MYSQL_PASS
        db = sae.const.MYSQL_DB

        #override
        # host = 'w.rdc.sae.sina.com.cn'
        # port = 3307
        # user = '0l40xoz51k'
        # pw = 'lk3i1im0h2hh5l330lk4wz334myy220wzywxwlk1'
        # db = 'app_ymtx'
    except ImportError:
        pass

    configs = {
        'db':{
            'host':host,
            'port':port,
            'user':user,
            'password':pw,
            'database':db,
            },
        'session':{
            'secret':'YmTx'
            }
        }
    return configs


class Dict(dict):
    '''
    Simple dict but support access as x.y style.
    '''
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


def merge(defaults, override):
    r = {}
    for k, v in defaults.iteritems():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r


def toDict(d):
    D = Dict()
    for k, v in d.iteritems():
        D[k] = toDict(v) if isinstance(v, dict) else v
    return D


configs = _create_db()
configs = toDict(configs)
