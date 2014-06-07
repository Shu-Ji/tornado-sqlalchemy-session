# coding: u8

import tornado.web

from sessions import SessionManager, SessionMixin
from models import TornadoSqlaSession, db

SessionManager.setup(db, TornadoSqlaSession, 'sid')


class BaseHandler(tornado.web.RequestHandler, SessionMixin):
    def prepare(self):
        """if you want generate session id while"""
        self.write(self.session.get('user'))


class LogoutHandler(BaseHandler):
    def get(self):
        self.session.clear()


class MainHandler(BaseHandler):
    def get(self):
        self.write('hello world')
        self.write('<br>')
        self.write('<a href="/logout">Logout</a>')


if __name__ == '__main__':
    import tornado.ioloop
    TORNADO_SETTINGS = {
        'cookie_secret': '^X@s6GwwfdZ#BM]54sWf@@!f\cv\Nd:f=>:)$',
        'debug': True,
    }

    tornado.web.Application([
        (r'/', MainHandler),
        (r'/logout', LogoutHandler),
    ], **TORNADO_SETTINGS).listen(8888)
    tornado.ioloop.IOLoop.instance().start()
