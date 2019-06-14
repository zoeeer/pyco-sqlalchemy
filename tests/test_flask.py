import os
import pytest
import tempfile
from flask import Flask
from pyco_sqlalchemy._flask import BaseModel, db

cwd = os.path.dirname(__file__)


@pytest.fixture
def app():
    app = Flask(__name__)
    # db_file = 'sqlite:///test.sqlite.db'
    db_fd, db_file = tempfile.mkstemp(suffix="sqlite.db", dir=cwd)
    print(db_fd, db_file)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///'.format_map(db_file)
    app.config["SQLALCHEMY_ECHO"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

    with app.app_context():
        db.init_app(app)
        db.create_all()
        yield app

    os.close(db_fd)
    os.unlink(db_file)


class User(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(32))
    email = db.Column(db.String(64), unique=True)


def test_user(app):
    form = dict(name="dev")
    u1 = User.insert(form, email="dev@pypi.com")
    u2 = User.upsert_one(form, email="dev@oncode.cc")
    assert u1.id == u2.id
    print(u1.to_dict())
    print(u2.to_dict())

    u3 = User.insert(name='dev3')
    assert u3.name == "dev3"
    n = User.discard(name="dev3")
    assert n == 1

    u4 = User.insert(name="dev4")
    try:
        n = User.discard()
    except Exception as e:
        assert e.__class__.__name__ == "SecurityError"
        print(e)
    n = User.discard(limit=None)
    us = User.filter_by()
    assert len(us) == 0
