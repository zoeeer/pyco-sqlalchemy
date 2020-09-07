import logging
from pprint import pformat
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.attributes import InstrumentedAttribute, flag_modified
from flask_sqlalchemy import SQLAlchemy
import werkzeug.exceptions as errors
from dateutil.parser import parse as parse_date
import flask

db = SQLAlchemy()

if flask.has_app_context():
    logger = flask.current_app.logger
else:
    logger = logging.getLogger("flask.app")


@contextmanager
def db_session_maker(auto_commit=False):
    ## 不要尝试重新手动创建 session, eg: `db.create_scoped_session(options=options)`
    ## 避免ORM对象在不同session中重复Attach
    sess = db.session
    yield sess
    if auto_commit:
        try:
            sess.commit()
        except Exception as e:
            sess.rollback()
            raise e
    sess.close()


def force_remove_multiple(*models, silent=False):
    count = 0
    for m in models:
        if isinstance(m, db.Model):
            db.session.delete(m)
            count += 1
        else:
            msg = "DbModel Not Found:<{}:{}>".format(type(m), m)
            if silent:
                logger.error(msg)
            else:
                db.session.rollback()
                raise errors.NotFound(msg)
    if count > 0:
        db.session.commit()


class BaseModel():
    """ sample:
    >>> class TableName(db.Model, BaseModel):
        pass
    """

    @classmethod
    def columns(cls):
        tbl = getattr(cls, "__table__", None)
        if tbl is None:
            name = cls.__name__
            desc = 'Service Unavailable: DbModel<{}> '.format(name)
            msg = "API-ERROR:{}\nDbModel<{}> must be subclass of db.Model!".format(desc, name)
            logger.error(msg)
            raise errors.ServiceUnavailable(desc)
        else:
            return tbl.columns

    @classmethod
    def primary_keys(cls):
        tbl = cls.__table__
        pks = [m.name for m in tbl.primary_key.columns]
        return pks

    @classmethod
    def _immutable_keys(cls):
        # limit columns should not updated by cls.update(form)
        pks = cls.primary_keys()
        return pks

    @classmethod
    def strict_form(cls, data=None, **kwargs):
        if data is None:
            data = kwargs
        elif isinstance(data, dict):
            data.update(**kwargs)
        else:
            raise TypeError('data value must be dict or None')

        form = {}
        for k, v in data.items():
            col = getattr(cls, k, None)
            if isinstance(col, InstrumentedAttribute):
                if isinstance(v, str):
                    v = v.strip()
                form[k] = v
        return form

    @classmethod
    def initial(cls, data=None, **kwargs):
        form = cls.strict_form(data, **kwargs)
        m = cls(**form)
        return m

    @classmethod
    def insert(cls, data=None, **kwargs):
        m = cls.initial(data, **kwargs)
        m.save()
        return m

    @classmethod
    def _make_query(cls, condition=None, limit=None, offset=None, order_by=None, **condition_kws):
        # NOTE: ERROR raise if call query.[update({})/delete()] after limit()/offset()/distinct()/group_by()/order_by()
        condition = cls.strict_form(condition, **condition_kws)
        qry = cls.query.filter_by(**condition)
        if isinstance(order_by, (list, tuple)):
            qry = qry.order_by(*order_by)
        elif order_by is not None:
            # NOTE: Raise Error if bool(order_by)
            qry = qry.order_by(order_by)
        if isinstance(limit, int):
            qry = qry.limit(limit)
        if isinstance(offset, int) and offset >= 0:
            qry = qry.offset(offset)
        return qry

    @classmethod
    def discard(cls, condition=None, limit=1, **condition_kws):
        # In Case of incorrect operation, default limit 1;
        condition = cls.strict_form(condition, **condition_kws)
        with db_session_maker(auto_commit=False) as db_sess:
            # n = cls.query.filter_by(**condition).delete()
            n = db_sess.query(cls).filter_by(**condition).delete()
            if limit and limit < n:
                db_sess.rollback()
                msg = "You're trying discard {} rows of {}, which is over limit={}".format(n, cls.__name__, limit)
                raise errors.SecurityError(msg)
            else:
                db_sess.commit()
            return n

    @classmethod
    def page_items(cls, condition=None, limit=10, offset=0, order_by=None, **condition_kws):
        qry = cls._make_query(condition, **condition_kws)
        pk = cls.primary_keys()[0]
        total = qry.value(func.count(getattr(cls, pk)))
        if isinstance(order_by, (list, tuple)):
            qry = qry.order_by(*order_by)
        elif order_by is not None:
            qry = qry.order_by(order_by)
        items = qry.limit(limit).offset(offset).all()
        next_offset = offset + len(items)
        has_more = total > next_offset
        return dict(total=total, next_offset=next_offset, has_more=has_more, items=items)

    @classmethod
    def filter_by(cls, condition=None, **condition_kws):
        qry = cls._make_query(condition, **condition_kws)
        ms = qry.all()
        return ms

    @classmethod
    def count(cls, condition=None, **condition_kws):
        # https://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.count
        qry = cls._make_query(condition, **condition_kws)
        pk = cls.primary_keys()[0]
        qry = qry.value(func.count(getattr(cls, pk)))
        return qry

    @classmethod
    def get_or_none(cls, condition=None, **condition_kws):
        cond = cls.strict_form(condition, **condition_kws)
        return cls.query.filter_by(**cond).one_or_none()

    @classmethod
    def upsert_one(cls, condition: dict, **updated_kws):
        m = cls.get_or_none(condition)
        if isinstance(m, cls):
            m.update(updated_kws)
        else:
            m = cls.insert(condition, **updated_kws)
        return m

    @classmethod
    def getOr404(cls, **condition_kws):
        m = cls.get_or_none(condition_kws)
        if isinstance(m, cls):
            return m
        else:
            name = cls.__name__
            msg = "Data Not Found: {}: {}".format(name, pformat(condition_kws))
            raise errors.NotFound(msg)

    def to_dict(self, **kwargs):
        d = dict(
            _type=self.__class__.__name__
        )
        columns = self.columns()
        for col in columns:
            name = col.name
            value = getattr(self, name)
            d[name] = value
        d.update(kwargs)
        return d

    def update(self, form=None, __force=False, **kwargs):
        data = self.strict_form(form, **kwargs)
        keys = self._immutable_keys()
        is_modified = False
        for k, v in data.items():
            is_mutable = k not in keys
            if __force or is_mutable:
                is_modified = True
                setattr(self, k, v)
                if isinstance(v, (dict, list, tuple)):
                    flag_modified(self, k)
        if is_modified:
            db.session.commit()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def remove(self):
        db.session.delete(self)
        db.session.commit()


class CoModel(BaseModel):

    @declared_attr
    def created_time(self):
        return db.Column(db.DateTime, default=datetime.utcnow)

    @declared_attr
    def updated_time(self):
        return db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def initial(cls, data=None, **kwargs):
        form = cls.strict_form(data, **kwargs)
        created_time = form.pop('created_time', None)
        if isinstance(created_time, datetime):
            form['created_time'] = created_time
        elif isinstance(created_time, str):
            form['created_time'] = parse_date(created_time)

        updated_time = form.pop('updated_time', None)
        if isinstance(updated_time, datetime):
            form['updated_time'] = updated_time
        elif isinstance(updated_time, str):
            form['updated_time'] = parse_date(updated_time)
        m = cls(**form)
        return m

    @classmethod
    def lastOrNone(cls, **kwargs):
        qry = cls._make_query(kwargs, limit=1, order_by=cls.created_time.desc())
        return qry.one_or_none()

    @classmethod
    def lastOr404(cls, **kwargs):
        m = cls.lastOrNone(**kwargs)
        if isinstance(m, cls):
            return m
        msg = "Data Not Found: {}: {}".format(cls.__name__, pformat(kwargs))
        raise errors.NotFound(msg)
