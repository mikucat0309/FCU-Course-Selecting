import re
from typing import *


def get_hidden_values(raw: str) -> Dict[str, str]:
    return {
        "__VIEWSTATE": getvalue("__VIEWSTATE", raw),
        "__VIEWSTATEGENERATOR": getvalue("__VIEWSTATEGENERATOR", raw),
        "__EVENTVALIDATION": getvalue("__EVENTVALIDATION", raw)
    }


def getvalue(key: str, raw: str) -> str:
    result = re.search(f'id="{key}" value="(.*?)"', raw)
    return result[1] if result else ""


def parse_url(url: str) -> Tuple[str, str]:
    r = re.match(r'https?://([\-.\w]+)/.+guid=(\w+)', url)
    return r[1], r[2]
