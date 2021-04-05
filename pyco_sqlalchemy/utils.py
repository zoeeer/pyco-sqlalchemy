import json
import uuid
import time
from pprint import pformat
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse as parse_datestr

TZ_UTC = timezone.utc
TZ_LOCAL = timezone(timedelta(seconds=-time.timezone))


def now(tz=None):
    # 使用datetime.now, 使得到的日期, 不管时间区是多少, 时间戳都是一致的.
    # 返回等同于: datetime.utcnow().replace(tz_info=TZ_UTC)
    # eg: now(TZ_UTC).timestamp() == now(TZ_LOCAL).timestamp())
    if not tz:
        tz = TZ_LOCAL
    return datetime.now(tz=tz)


def parse_date(val, nullable=True, tz=TZ_LOCAL, **parse_kws):
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=tz)
    elif isinstance(val, str):
        return parse_datestr(val, **parse_kws)
    elif isinstance(val, datetime):
        # 注意: 如果 val 是使用 datetime.utcnow() 获取的日期, 如果 tz 不为 TZ_UTC, 其时间戳会被更改
        # 假设当地北京, 使用 tz=TZ_LOCAL, 则返回日期的时间戳会减少 8 小时 (28800s)
        return val.replace(tzinfo=tz)
    elif val is None:
        if nullable:
            return None
    raise ValueError(f"Unknown DateValue{val}")


class BaseJSONEncoder(json.JSONEncoder):
    @classmethod
    def stringify(cls, obj, strict=False):
        if isinstance(obj, datetime):
            # default use TZ-LOCAL, eg: "2021-03-22 20:32:02.271068+08:00"
            return str(obj.astimezone())
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif hasattr(obj, 'to_json') and callable(obj.to_json):
            return obj.to_json()
        elif hasattr(obj, 'to_dict') and callable(obj.to_dict):
            return obj.to_dict()
        elif hasattr(obj, 'json'):
            if callable(obj.json):
                return obj.json()
            else:
                return obj.json

        text = pformat(obj, indent=2)
        msg = f"{type(obj)}::{text}"
        if not strict:
            return msg
        else:
            raise TypeError(f"BaseJSONEncoder: Object is not serializable. \n{msg}")

    def default(self, obj):
        return self.stringify(obj, strict=True)


###
# json_dumps 可能会抛出 TypeError
json_dumps = lambda obj: json.dumps(obj, indent=2, cls=BaseJSONEncoder)
# json_stringify 总能返回字符串结果, 不会抛出 TypeError
json_stringify = lambda obj: json.dumps(obj, indent=2, default=BaseJSONEncoder.stringify)
