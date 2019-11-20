#! /usr/bin/env python3

import copy
import json
import re
import os
import subprocess
import time
import typing
import threading

from typing import List, Optional, Union

# third-party libraries
import requests

# user-defined modules
if __package__:
    from . import color
    from . import logger
else:
    import color
    import logger

HORIZONTAL_BAR = "─"
HORIZONTAL_DASH = "⎯"
VERTICAL_BAR = "│"


def vislen(s: str):
    """Return visible length of a string after removing color codes in it."""
    return len(re.compile(r"\033\[[0-9]+(;[0-9]+)?m").sub("", s))


def squeeze(s, maxlen, tail=0):
    if len(s) <= maxlen:
        return s
    return s[:(maxlen-tail-2)] + ".." + (s[-tail:] if tail else "")

# todo: review usage
def extract(resp: requests.models.Response, key: str, fallback):
    try:
        return json.loads(resp.text)[key]
    except KeyError:
        return fallback


def fetch(data: dict, keys: List[str]) -> dict:
    return dict((k, data[k]) for k in keys)


def get_time(date=True, precision=3, local_time=False, time_zone=False):
    now = time.time()
    fmt = "%H:%M:%S"
    if date:
        fmt = "T".join(["%Y-%m-%d", fmt])
    if precision:
        subsec = int((now - int(now)) * (10 ** precision))
        fmt = ".".join([fmt, f"{subsec:0{precision}d}"])
    if time_zone:
        fmt = " ".join([fmt, "%Z"])
    convert = time.localtime if local_time else time.gmtime
    return time.strftime(fmt, convert(now))


def format_header(header, level: str):
    upper = level.upper()
    if upper == "info":
        return (">>> {}".format(header.title()))
    if upper == "debug":
        return pad(color.black_on_cyan(header), char="-")
    if upper == "trace":
        return pad(header, char="⎯")
    raise RuntimeError("Invalid header level \"{}\"".format(level))


def make_header(header, level="debug"):
    level = str(logger.LogLevel(level))
    if level == "info":
        return (">>> {}".format(header.title()))
    if level == "debug":
        return pad(color.black_on_cyan(header), total=100, left=20, char="-")
    if level == "trace":
        return pad(header, total=100, left=20, char="⎯")
    return header


# to be deprecated
def get_transaction_id(response: requests.models.Response) -> Optional[str]:
    try:
        return json.loads(response.text)["transaction_id"]
    except KeyError:
        return

def format_json(text: str, maxlen=100) -> str:
    data = json.loads(text)
    if maxlen:
        trim(data, maxlen=100)
    return json.dumps(data, indent=4, sort_keys=False)


def format_tokens(amount: int, ndigits=4, symbol="SYS"):
    """
    Doctest
    -------
    >>> print(format_tokens(37.5e6))
    37500000.0000 SYS
    >>> print(format_tokens(1, 3, 'ABC'))
    1.000 ABC
    """
    return "{{:.{}f}} {{}}".format(ndigits).format(amount, symbol)


def optional(x, y):
    return x if y is not None else None


# def override(default_value, value, override_value=None):
#     return override_value if override_value is not None else value if value is not None else default_value

def override(*args):
    """
    Example
    -------
    >>> a, b, c = 1, 2, None
    >>> override(a, b, c)
    2
    >>> default_value = 1
    >>> value = 2
    >>> command_line_value = 3
    >>> value = override(default_value, value, command_line_value)
    >>> value
    3
    """
    for x in reversed(args):
        if x is not None:
            return x
    return None


# --------------- text-related ----------------------------------------------------------------------------------------


def plural(word, count, suffix="s"):
    return word + suffix if count > 1 else  word


def pad(text, total, left=0, char=" ", sep="", textlen=None) -> str:
    """textlen is a hint for visable length of text"""
    textlen = vislen(text) if textlen is None else textlen
    offset = len(text) - textlen
    return (char * left + sep + text + sep).ljust(total + offset, char)


def abridge(data: typing.Union[dict, list], maxlen=79):
    clone = copy.deepcopy(data)
    trim(clone, maxlen=maxlen)
    return clone


def trim(data: typing.Union[dict, list], maxlen=79):
    """
    Summary
    -------
    A helper function for json formatting. This function recursively look
    into a nested dict or list that could be converted to a json string,
    and replace strings that are too long with three dots (...).
    """
    if isinstance(data, dict):
        for key in data:
            if isinstance(data[key], (list, dict)):
                trim(data[key], maxlen=maxlen)
            else:
                if isinstance(data[key], str) and len(data[key]) > maxlen:
                    data[key] = squeeze(data[key], maxlen=maxlen, tail=3)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (list, dict)):
                trim(item, maxlen=maxlen)
            else:
                if isinstance(item, str) and len(item) > maxlen:
                    item = squeeze(item, maxlen=maxlen, tail=3)


# --------------- subprocess-related ----------------------------------------------------------------------------------


def get_cmd_and_args_by_pid(pid: typing.Union[int, str]) -> str:
    return subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True).stdout


def get_pid_list_by_pattern(pattern: str) -> typing.List[int]:
    out = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True).stdout.splitlines()
    return [int(x) for x in out]


def terminate(pid: typing.Union[int, str]):
    subprocess.run(["kill", "-SIGTERM", str(pid)])


# --------------- test ------------------------------------------------------------------------------------------------

def test():
    print("Pass -v in command line for details of doctest.")


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    test()


# def run(args: list):
#     return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout.readlines()

# def timeout_run(args: list, timeout=1):
#     p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
#     out = []
#     def getline():
#         out.append(p.stdout.readline())
#     while True:
#         t = threading.Thread(target=getline, daemon=True)
#         t.start()
#         t.join(timeout=timeout)
#         if t.is_alive() or not out or not out[-1]:
#             break
#     return out




# def pad(text: str, left=20, total=90, right=None, char="-", sep=" ") -> str:
#     """
#     Summary
#     -------
#     This function provides padding for a string.

#     Doctest
#     -------
#     >>> # implied_total (24) < total (25), so total becomes 24.
#     >>> pad("hello, world", left=3, right=3, total=25, char=":", sep=" ~ ")
#     '::: ~ hello, world ~ :::'
#     """
#     if right is not None:
#         implied_total = vislen(char) * (left + right) + vislen(sep) * 2 + vislen(text)
#         total = min(total, implied_total)
#     string = char * left + sep + text + sep
#     offset = len(string) - vislen(string)
#     return string.ljust(total + offset, char)
