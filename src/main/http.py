import logging
from typing import *

from bs4 import BeautifulSoup
from requests import Session, Response
from requests.cookies import RequestsCookieJar

from .error import *
from .util import *

proxy = {
    "http": "127.0.0.1:8086",
    "https": "127.0.0.1:8086"
}


class Crawler:
    logon: bool = False
    __host = ""
    __guid = ""
    __wmap: Dict[int, int] = {}  # cid -> position
    __logger = None
    __session = Session()
    __post_data: Dict[str, str] = None

    def __init__(self):
        ft = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        sh = logging.StreamHandler()
        sh.setFormatter(ft)
        self.__logger = logging.getLogger("fcu")
        self.__logger.addHandler(sh)
        self.__logger.level = logging.DEBUG
        self.__init()

    def __init(self):
        self.__session.cookies = RequestsCookieJar()
        r = self.__session.get("https://course.fcu.edu.tw")
        self.__post_data = get_hidden_values(r.text)

    def reset(self):
        self.close()
        self.__init()

    def close(self):
        self.__session.close()

    def __post_back(self, url: str = "", data: Dict = None) -> Response:
        url = f"http://{self.__host}/NetPreSelect.aspx?guid={self.__guid}&lang=zh-tw" if not url else url
        if data:
            self.__post_data.update(data)
        r = self.__session.post(url, data=self.__post_data)
        self.__logger.debug(f"{url} {r.status_code}")
        [self.__logger.debug(f"\t{k}: {v[:40]}") for k, v in self.__post_data.items()]
        [self.__logger.debug(f"\t{k}: {v}") for k, v in data.items()]
        self.__post_data = get_hidden_values(r.text)
        return r

    def login(self, username: str, password: str):
        self.__session.get("https://course.fcu.edu.tw/validateCode.aspx")
        postdata = {
            "__EVENTTARGET": "ctl00$Login1$LoginButton",
            "ctl00$Login1$RadioButtonList1": "zh-tw",
            "ctl00$Login1$UserName": username,
            "ctl00$Login1$Password": password,
            "ctl00$Login1$vcode": self.__session.cookies.get("CheckCode"),
        }
        r = self.__post_back("https://course.fcu.edu.tw/Login.aspx", postdata)
        if "service" not in r.url:
            raise LoginError
        self.logon = True
        self.__host, self.__guid = parse_url(r.url)
        self.__post_data = get_hidden_values(r.text)
        return r

    def query(self, cid: int) -> Dict[int, int]:
        if not self.logon:
            raise RuntimeError("Please login first")
        postdata = {
            "__EVENTTARGET": "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$btnSearchOther",
            "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$cbOtherCondition1": "on",
            "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$tbSubID": str(cid)
        }
        r = self.__post_back(data=postdata)
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find("table", id="ctl00_MainContent_TabContainer1_tabCourseSearch_wcCourseSearch_gvSearchResult")
        mapping = {}
        cnt = 2
        if table is not None:
            trs = table.find_all("tr")
            for tr in trs[1:]:
                tds = tr.find_all("td")
                cid = int(tds[1].font.string)
                mapping[cid] = cnt
                cnt += 1
        return mapping
