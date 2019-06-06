
# pyco-sqlalchemy

Easy ORM for Flask and Django Based on SqlAlchemy.ORM


## Tips:
- use `charset=UTF8MB4 collate utf8_general_ci`
  (https://stackoverflow.com/questions/766809/whats-the-difference-between-utf8-general-ci-and-utf8-unicode-ci)
- use `ext.TrimColumn instead Columns.Text`

## Samples

- flask

```python
from pyco_sqlalchemy._flask import BaseModel, db

class User(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(32))
    email = db.Column(db.String(64), unique=True)
     

form = dict(name="dev")
u1 = User.insert(form, email="dev@pypi.com")
u3 = User.upsert_one(form, email="dev@oncode.cc")
assert u1.id == u3.id
```

## Todos
- SQLALchemy-ORM
- django-ORM

## Change Logs
#### v1.0

- support `flask-sqlalchemy`

