### tornado-sqlalchemy-session

    $ pip instal sqlalchemy tornado

    $ python models.py

    $ python example.py

http://127.0.0.1:8888


### Usage

1. `python models.py` to generate the models

2. In your handler:

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
            self.session.user = {'userid': 9527}  # this will auto commit
            self.write(self.session.user.userid)
