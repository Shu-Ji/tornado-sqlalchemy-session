# coding: u8

import tornado.web

from sessions import SessionManager, SessionMixin
from models import TornadoSqlaSession, db

SessionManager.setup(db, TornadoSqlaSession, 'sid')


class BaseHandler(tornado.web.RequestHandler, SessionMixin):
    def prepare(self):
        # if you want generate session id while tornado start no matter
        # the user logged in or not:
        self.session.setup_session_id()


class LogoutHandler(BaseHandler):
    def post(self):
        self.session.clear()
        self.redirect('/')


class MainHandler(BaseHandler):
    def get(self):
        self.write_p('user' in self.session)
        self.write_p('last_access' in self.session)
        
        self.write_p('<hr>')
        
        self.session.user = {'userid': 9527}  # this will auto commit
        self.session.last_access = '2014-05-12'  # again
  
        self.write_p(self.session.user.userid)
        self.write_p(self.session.last_access)
        self.write_p('user' in self.session)
        
        self.write_p('<hr>')
        
        self.write_p('<a href="/">Reload Page</a>')
        self.write('<form action="/logout" method="post">'
                   '<input type="submit" value="Logout">'
                   '</form>')
        
    def write_p(self, text):
        self.write('<p>%s</p>' % text)


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
