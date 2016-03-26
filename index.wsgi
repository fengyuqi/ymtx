#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import sae
    sae.add_vendor_dir('vendor')
except ImportError:
    pass

from lib import db
from lib.web import WSGIApplication, Jinja2TemplateEngine
from config import configs

import os, time
from datetime import datetime

db.engine = db.create_engine_MySQLdb(configs.db.host, configs.db.user, configs.db.password, configs.db.database, configs.db.port)
wsgi=WSGIApplication(os.path.dirname(os.path.abspath(__file__)))

template_engine=Jinja2TemplateEngine(os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates'))


def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    elif delta < 3600:
        return u'%s分钟前' % (delta // 60)
    elif delta < 86400:
        return u'%s小时前' % (delta // 3600)
    elif delta < 604800:
        return u'%s天前' % (delta // 86400)
    else:
        dt = datetime.fromtimestamp(t)
        return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)

template_engine.add_filter('datetime', datetime_filter)
wsgi.template_engine = template_engine

import urls
wsgi.add_interceptor(urls.user_interceptor)
wsgi.add_interceptor(urls.manage_interceptor)
wsgi.add_module(urls)

if __name__ == '__main__':
    wsgi.run(9000, host='0.0.0.0')
else:
    # application = wsgi.get_wsgi_application()
    app = wsgi.get_wsgi_application()
    import sae
    application = sae.create_wsgi_app(app)
