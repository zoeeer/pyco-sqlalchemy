import json
from datetime import datetime
from collections import OrderedDict
from sqlalchemy import types
import sqlalchemy.exc as sqlerrors
from . import utils
from . import regex


class CustomParameterError(Exception, sqlerrors.DontWrapMixin):

    def __init__(self, msg, *args):
        self.description = msg
        self.args = args

    def __str__(self):
        return "{}: {} {}".format(self.__class__.__name__, self.description, self.args if self.args else "")


class DateTime(types.TypeDecorator):
    """
    # sample 1:
    @declared_attr
    def created_time(self):
        return db.Column(DateTime, default=datetime.utcnow)
    ## note: DateTime 不校验时区, 使用`datetime.utcnow`容易得到错误的时间戳, 需要在后端业务代码重新处理 tz_offset

    # sample 2:
    updated_time = db.Column(DateTime, default=datetime.now, onupdate=datetime.now)
    ## 如果有国际化需求, 建议使用时间戳替代日期, 或者统一使用 `DatetimeTZUtc`
    """
    impl = types.DateTime

    def process_bind_param(self, value, dialect):
        if isinstance(value, datetime):
            return value
        elif isinstance(value, str):
            return utils.parse_datestr(value)
        elif isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        else:
            return value


class DateTimeTZLocal(types.TypeDecorator):
    """
    # sample 1:
    @declared_attr
    def created_time(self):
        return db.Column(DateTime, default=utils.now)

    # sample 2:
    updated_time = db.Column(DateTime, default=utils.now, onupdate=utils.now)
    """
    impl = types.DateTime

    def process_bind_param(self, value, dialect):
        return utils.parse_date(value, tz=utils.TZ_LOCAL)


class DatetimeTZUtc(types.TypeDecorator):
    impl = types.DateTime

    def process_bind_param(self, value, dialect):
        return utils.parse_date(value, tz=utils.TZ_UTC)


class BoolField(types.TypeDecorator):
    impl = types.Boolean
    # NOTE: origin `sqltypes.Boolean` use _strict_bools = frozenset([None, True, False])

    BoolStrings = {
        ""     : False,
        "0"    : False,
        "false": False,
        "null" : False,
        "none" : False,
        "no"   : False,
        "n"    : False,
        "f"    : False,

        ### 支持部分英文单词语义化
        "error"  : False,
        "not_ok" : False,
        "not ok" : False,
        "invalid" : False,
        "incorrect" : False,
        "undefined" : False,

        ### 支持部分中文语义化
        "无"    : False,
        "否"    : False,
        "错"    : False,
        "空"    : False,
        "错误"    : False,
        "无效"    : False,
        "空白"    : False,
        # "1"    : True,
        # "true" : True,
        # "yes"  : True,
        # "ok"   : True,
        # "y"    : True,
        # "t"    : True,
    }

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            v = value.strip().lower()
            return self.BoolStrings.get(v, True)
        else:
            return bool(value)


class TrimString(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            value = value.strip()
        elif value is None:
            return ""
        else:
            value = str(value)
        if self.impl.length > 0 and len(value) > self.impl.length:
            value = value[-self.impl.length:]
        return value


class SnakeField(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is None:
            return ""
        elif isinstance(value, (str, int)):
            return regex.snake_case(str(value))
        else:
            raise CustomParameterError(f"invalid ${type(value)}:'{value}', Column<SnakeField> require [0-9a-zA-Z_]")


class StringTags(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        if value and isinstance(value, str):
            return ','.join(map(lambda x: x.strip(), value.split(',')))
        if isinstance(value, (list, tuple, set)):
            return ','.join(map(str, value))
        return ""


class SortedTags(types.TypeDecorator):
    impl = types.JSON

    def process_bind_param(self, value, dialect):
        if isinstance(value, (list, tuple, set)):
            return sorted(set(map(str, value)))
        elif isinstance(value, str):
            return sorted(set(map(lambda x: x.strip(), value.split(','))))
        elif not value:
            return []
        else:
            return [str(value)]


SortedTagsArray = SortedTags


class OrderedJson(types.TypeDecorator):
    impl = types.JSON

    def process_result_value(self, value, dialect):
        if isinstance(value, str):
            return json.JSONDecoder(object_pairs_hook=OrderedDict).decode(value)
        return value


class JsonText(types.TypeDecorator):
    # NOTE: actually it supports `sqltypes.JSON`
    # https://docs.sqlalchemy.org/en/13/core/custom_types.html#sqlalchemy.types.TypeDecorator
    impl = types.Text
    JSONDecoder = json.JSONDecoder
    JSONEncoder = json.JSONEncoder

    def process_bind_param(self, value, dialect):
        return json.dumps(value, indent=2, cls=self.JSONEncoder)

    def process_result_value(self, value, dialect):
        return json.loads(value, cls=self.JSONDecoder)
