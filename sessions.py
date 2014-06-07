# coding: u8

import pickle

from tornado.util import ObjectDict as d


class ObjectDict(dict):
    def __getattr__(self, name):
        return self.get(name, ObjectDict())

    def __setattr__(self, name, value):
        self[name] = value


class SetupError(Exception):
    pass


class SessionIdNotExistsError(Exception):
    pass


class SessionManager(dict):
    def __init__(self, handler):
        self['__dict'] = ObjectDict(handler=handler)

        if not hasattr(SessionManager, 'db'):
            raise SetupError('Please call SessionManager.setup() first.')

        self.setup_session_id()

    @classmethod
    def setup(cls, db, tb, cookie_name='session_id', **kwargs):
        """kwargs will be sent to tornado `set_cookie` method"""
        cls.db = db
        cls.tb = tb
        cls.cookie_name = cookie_name

        kwargs.setdefault('expires', None)
        kwargs.setdefault('expires_days', None)
        cls.cookie_settings = kwargs

    def update_last_access(self, s=None):
        import datetime
        s = s or self.db.query(self.tb).filter_by(sid=self['__dict'].sid).first()
        s.last_access = datetime.datetime.now()
        self.db.commit()

    def get(self, key, default=None):
        default = ObjectDict()
        data = self.get_data_dict_from_db()
        value = data.get(key, default)
        if isinstance(value, dict):
            value = ObjectDict(value)
        return value

    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        return self.set(key, value)

    def __contains__(self, key):
        return key in self.get_data_dict_from_db()

    def get_data_dict_from_db(self):
        s = self.db.query(self.tb).filter_by(sid=self['__dict'].sid).first()
        if s is None:
            raise SessionIdNotExistsError('session id is not exists.')
        self.update_last_access(s)
        return ObjectDict(pickle.loads(s.data))

    def set(self, key, value):
        data = self.get_data_dict_from_db()
        s = self.db.query(self.tb).filter_by(sid=self['__dict'].sid).first()
        data[key] = value
        s.data = pickle.dumps(dict(data))
        self.update_last_access(s)

    def clear(self):
        self['__dict'].handler.clear_cookie(self.cookie_name)
        self.db.query(self.tb).filter_by(sid=self['__dict'].sid).delete()
        self.db.commit()

    def generate_sid(self):
        import uuid
        return str(uuid.uuid4()).replace('-', '')

    def setup_session_id(self):
        sid = self['__dict'].handler.get_secure_cookie(self.cookie_name)
        if sid is None:
            sid = self.generate_sid()
            self['__dict'].handler.set_secure_cookie(
                self.cookie_name, sid, **self.cookie_settings)
        if self.db.query(self.tb.sid).filter_by(sid=sid).first() is None:
            from datetime import datetime
            data = pickle.dumps({})
            s = self.tb(sid=sid, last_access=datetime.now(), data=data)
            self.db.add(s)
            self.db.commit()
        self['__dict'].sid = sid


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
