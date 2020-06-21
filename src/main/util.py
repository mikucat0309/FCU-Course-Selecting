import re


def get_hidden_values(raw: str) -> dict:
    return {
        "__VIEWSTATE": getvalue("__VIEWSTATE", raw),
        "__VIEWSTATEGENERATOR": getvalue("__VIEWSTATEGENERATOR", raw),
        "__EVENTVALIDATION": getvalue("__EVENTVALIDATION", raw)
    }


def getvalue(id: str, raw: str):
    result = re.search(f'id="{id}" value="(.*?)"', raw)
    return result[1] if result else ""
