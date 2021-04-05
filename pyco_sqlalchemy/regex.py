import re


def alphanumeric(s: str, sep='_'):
    """
    # refer: https://stackoverflow.com/a/12985459/6705684
    # Note that \W is equivalent to [^a-zA-Z0-9_] only in Python 2.x.
    # In Python 3.x, \W+ is equivalent to [^a-zA-Z0-9_] only if re.ASCII / re.A flag is used.
    >>> alphanumeric('h^&ell`.,|o w]{+orld')
    'h_ell_o_w_orld'
    """
    return re.sub('[^0-9a-zA-Z]+', sep, s.strip())


def simple_case(s: str):
    """
    # better pathname/filename, accept only alpha numbers and [_-.]
    >>>simple_case("xxasdfIS _asdkf ks. asfx - dkasx"))
    'xxasdfIS_asdkfks.asfx-dkasx'
    >>>simple_case("xxasdfIS ÓÔÔLIasdf_asdkf中文ks. asfx - dkasx"))
    'xxasdfISLIasdf_asdkfks.asfx-dkasx'
    """
    return re.sub(r"[^0-9a-zA-Z_\-\.]+", '', s)


def snake_case(s: str):
    """
    # refer: https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    # smarter than ''.join(['_' + c.lower() if c.isupper() else c for c in s]).lstrip('_')
    >>> snake_case('getHTTPResponseCode')
    'get_http_response_code'
    >>> snake_case('get2HTTPResponseCode')
    'get2_http_response_code'
    >>> snake_case('get2HTTPResponse123Code')
    'get2_http_response123_code'
    >>> snake_case('HTTPResponseCode')
    'http_response_code'
    >>> snake_case('HTTPResponseCodeXYZ')
    'http_response_code_xyz'
    """
    s = alphanumeric(s, '_')
    a = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')
    return a.sub(r'_\1', s).lower()


def camel_case(s: str):
    """
    # suggest to preprocess $s with $simple_case or $alphanumeric
    >>> camel_case("Some rise ^升起^. Some fade ª••º.")
    'SomeRise ^升起^. SomeFade ª••º.'
    >>> camel_case("Some live to die another day.")
    'SomeLiveToDieAnotherDay.'
    >>> camel_case("I’ll live to die another day.")
    'I’llLiveToDieAnotherDay.'
    """
    return re.sub(r"[\-_\.\s]([a-z])", lambda mo: mo.group(1).upper(), s)


def title_case(s: str):
    """
    # refer: https://docs.python.org/3/library/stdtypes.html#str.title
    >>> title_case("they're bill's friends.")
    "They're Bill's Friends."
    """
    return re.sub(r"[A-Za-z]+('[A-Za-z]+)?", lambda mo: mo.group(0).capitalize(), s)
