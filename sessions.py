# coding: u8

import pickle

from tornado.util import ObjectDict


class SetupError(Exception):
    pass


class SessionIdNotExistsError(Exception):
    pass


class SessionManager(object):
    def __init__(self, handler):
        self.handler = handler

        if not hasattr(SessionManager, 'db'):
            raise SetupError('Please call SessionManager.setup() first.')

        self.__setup_session_id()

    @classmethod
    def setup(cls, db, tb, cookie_name='session_id', **kwargs):
        """kwargs will be sent to tornado `set_cookie` method"""
        cls.db = db
        cls.tb = tb
        cls.cookie_name = cookie_name

        kwargs.setdefault('expires', None)
        kwargs.setdefault('expires_days', None)
        cls.cookie_settings = kwargs

    @property
    def data(self):
        return getattr(self.tb, 'data')

    def __update_last_access(self, s=None):
        import datetime
        s = s or self.db.query(self.tb).filter_by(sid=self.session_id).first()
        s.last_access = datetime.datetime.now()
        self.db.commit()

    def get(self, key, default=None):
        s = self.db.query(self.data).filter_by(sid=self.session_id).first()
        if s is None:
            raise SessionIdNotExistsError('session id is not exists.')
        self.__update_last_access()
        data = pickle.loads(s.data)
        return data.get(key, default)

    def set(self, key, value):
        s = self.db.query(self.tb).filter_by(sid=self.session_id).first()
        if s is None:
            raise SessionIdNotExistsError('session id is not exists.')
        data = pickle.loads(s.data)
        data[key] = value
        s.data = pickle.dumps(data)
        self.__update_last_access(s)

    def clear(self):
        self.handler.clear_cookie(self.cookie_name)
        self.db.query(self.tb).filter_by(sid=self.session_id).delete()
        self.db.commit()

    def __generate_sid_cookie(self):
        import uuid
        return str(uuid.uuid4()).replace('-', '')

    def __setup_session_id(self):
        sid = self.handler.get_secure_cookie(self.cookie_name)
        if sid is None:
            sid = self.__generate_sid_cookie()
            self.handler.set_secure_cookie(
                self.cookie_name, sid, **self.cookie_settings)
            from datetime import datetime
            data = pickle.dumps({})
            s = self.tb(sid=sid, last_access=datetime.now(), data=data)
            self.db.add(s)
            self.db.commit()
        self.session_id = sid


class SessionMixin(object):
    '''
    This mixin must be included in the request handler inheritance list, so that
    the handler can support sessions.

    Example:
    >>> db = scoped_session(sessionmaker(bind=engine))
    >>> class TornadoSqlaSession(Base):
        ...    __tablename__ = 'tornado_sqla_session'
        ...    sid = Column(Integer, primary_key=True)
        ...    last_access = Column(DateTime)
        ...    data = Text()

    >>> from sessions import SessionManager, SessionMixin
    >>> SessionManager.setup(db, TornadoSqlaSession, 'sid')
    >>> class MyHandler(tornado.web.RequestHandler, SessionMixin):
    ...    def get(self):
    ...        print type(self.session) # SessionManager

    Refer to SessionManager documentation in order to know which methods are
    available.
    '''

    @property
    def session(self):
        '''
        Returns a SessionManager instance
        '''

        return self.create_mixin(self, '__session_manager', SessionManager)

    def create_mixin(self, context, manager_property, manager_class):
        if not hasattr(context, manager_property):
            setattr(context, manager_property, manager_class(context))
        return getattr(context, manager_property)
