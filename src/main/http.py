import logging
from typing import *

from bs4 import BeautifulSoup
from requests import Session, Response
from requests.cookies import RequestsCookieJar

from .error import *
from .util import *


class Crawler:
    __logon: bool = False
    __host = ""
    __guid = ""
    __wishmap: Dict[int, int] = {}  # cid -> position
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

    def checklogin(self):
        if not self.__logon:
            raise RuntimeError("Please login first")

    def __post_back(self, url: str = "", data: Dict = None) -> Response:
        url = f"http://{self.__host}/NetPreSelect.aspx?guid={self.__guid}&lang=zh-tw" if not url else url
        self.__logger.debug(url)
        [self.__logger.debug(f"\t{k}: {v[:40]}") for k, v in self.__post_data.items()]
        [self.__logger.debug(f"\t{k}: {v}") for k, v in data.items()]
        if data:
            self.__post_data.update(data)
        r = self.__session.post(url, data=self.__post_data)
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
        self.__logon = True
        self.__host, self.__guid = parse_url(r.url)
        self.__post_data = get_hidden_values(r.text)
        self.updatewish(r.text)
        return r

    def query(self, cid: int) -> Dict[int, int]:
        self.checklogin()
        postdata = {
            "__EVENTTARGET": "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$btnSearchOther",
            "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$cbOtherCondition1": "on",
            "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$tbSubID": str(cid)
        }
        r = self.__post_back(data=postdata)
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find("table", id="ctl00_MainContent_TabContainer1_tabCourseSearch_wcCourseSearch_gvSearchResult")
        if table is None:
            raise RuntimeError(f"Nothing found")
        trs = table.find_all("tr")
        querymap = {}
        pos = 2
        for tr in trs[1:]:
            tds = tr.find_all("td", limit=2)
            cid = int(tds[1].font.string)
            querymap[cid] = pos
            pos += 1
        return querymap

    def addwish(self, cid: int):
        self.checklogin()
        m = self.query(cid)
        pos = m[cid]
        postdata = {
            f"ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$gvSearchResult$ctl{pos:02d}$btnAdd": "%E9%97%9C%E6%B3%A8"
        }
        r = self.__post_back(data=postdata)
        self.updatewish(r.text)

    def removewish(self, cid: int):
        self.checklogin()
        if cid not in self.__wishmap:
            raise RuntimeError(f"course id {cid} is not in your wish list")
        pos = self.__wishmap[cid]
        postdata = {
            "__EVENTTARGET": f"ctl00$MainContent$TabContainer1$tabSelected$gvWishList$ctl{pos:02d}$btnRemoveItem"
        }
        r = self.__post_back(data=postdata)
        self.updatewish(r.text)

    def updatewish(self, html: str):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", id="ctl00_MainContent_TabContainer1_tabSelected_gvWishList")
        m = {}
        if table:
            trs = table.find_all("tr")
            pos = 2
            for i in range(1, len(trs), 2):
                tds = trs[i].find_all("td", limit=2)
                cid = int(tds[1].font.string)
                m[cid] = pos
                pos += 2
        self.__wishmap = m

    def get_wishmap(self):
        return self.__wishmap.copy()
