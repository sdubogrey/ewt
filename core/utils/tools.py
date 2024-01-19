import datetime
import io
import json
import logging
import os
import re
import uuid
from typing import Optional

logger = logging.getLogger('gunicorn.access')


def serializer(o):
    if isinstance(o, uuid.UUID):
        return str(o)
    elif isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


def serialize(data: dict or list, indent=None, ensure_ascii=True) -> str:
    return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii, default=serializer)


def deserialize(jsn: str) -> dict or list:
    try:
        data = json.loads(jsn)
    except (json.JSONDecodeError, TypeError):
        data = jsn
    return data

def uid_hex():
    return uuid.uuid4().hex


def dt_to_str(dt: datetime.datetime, fmt='%Y-%m-%dT%H:%M:%S') -> Optional[str]:
    if not dt:
        return None
    return dt.strftime(fmt)


def is_digit(sign):
    if sign is not None:
        if type(sign) is not int and type(sign) is not float:
            if not str(sign).isdigit():
                return False
            else:
                return True
        else:
            return True
    else:
        return False


def is_device_id(possible_device_id: str) -> bool:
    """
    Device ID is a value that contains at least four digits
    """
    if not possible_device_id:
        return False

    if not isinstance(possible_device_id, str):
        possible_device_id = str(possible_device_id)

    if len(re.sub('[^0-9]', '', possible_device_id)) >= 3:
        return True
    else:
        return False


def is_jsonable(obj):
    if not isinstance(obj, (list, dict)):
        return False
    try:
        json.dumps(obj)
        return True
    except (TypeError, OverflowError):
        return False
