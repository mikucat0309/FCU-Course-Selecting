import logging

from bs4 import BeautifulSoup
from requests import Session, Response
from requests.cookies import RequestsCookieJar

from .util import *


class Crawler:
    __logger: logging.Logger = None
    __session: Session = None
    __post_data: Dict[str, str] = None
    __logon: bool = False
    __host: str = ""
    __guid: str = ""
    __wishmap: Dict[int, int] = None  # cid -> position
    __selected: Set[int] = None  # cid

    def __init__(self):
        ft = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        sh = logging.StreamHandler()
        sh.setFormatter(ft)
        self.__logger = logging.getLogger("fcu")
        self.__logger.addHandler(sh)
        self.__logger.level = logging.DEBUG
        self.__init()

    def __init(self) -> None:
        self.__session = Session()
        self.__session.cookies = RequestsCookieJar()
        self.__logon = False
        self.__wishmap = {}
        self.__selected = set()
        r = self.__session.get("https://course.fcu.edu.tw")
        self.__post_data = get_hidden_values(r.text)

    def reset(self) -> None:
        self.close()
        self.__init()

    def close(self) -> None:
        self.__session.close()

    def checklogin(self) -> None:
        if not self.__logon:
            raise RuntimeError("Please login first")

    def __postback(self, url: str = "", data: Dict = None) -> Response:
        url = f"http://{self.__host}/NetPreSelect.aspx?guid={self.__guid}&lang=zh-tw" if not url else url
        self.__logger.debug(url)
        [self.__logger.debug(f"\t{k}: {v[:40]}") for k, v in self.__post_data.items()]
        [self.__logger.debug(f"\t{k}: {v}") for k, v in data.items()]
        if data:
            self.__post_data.update(data)
        r = self.__session.post(url, data=self.__post_data)
        self.__post_data = get_hidden_values(r.text)
        return r

    def login(self, username: str, password: str) -> Response:
        self.__session.get("https://course.fcu.edu.tw/validateCode.aspx")
        postdata = {
            "__EVENTTARGET": "ctl00$Login1$LoginButton",
            "ctl00$Login1$RadioButtonList1": "zh-tw",
            "ctl00$Login1$UserName": username,
            "ctl00$Login1$Password": password,
            "ctl00$Login1$vcode": self.__session.cookies.get("CheckCode"),
        }
        r = self.__postback("https://course.fcu.edu.tw/Login.aspx", postdata)
        if "service" not in r.url:
            raise RuntimeError("Wrong username/password")
        self.__logon = True
        self.__host, self.__guid = parse_url(r.url)
        self.__post_data = get_hidden_values(r.text)
        self.wishupdate(r.text)
        self.courseupdate(r.text)
        return r

    def __wishaction(self, cid: int, action: str) -> Response:
        self.checklogin()
        if cid not in self.__wishmap:
            raise RuntimeError(f"course id {cid} not in your wish list")
        pos = self.__wishmap[cid]
        postdata = {
            "__EVENTTARGET": f"ctl00$MainContent$TabContainer1$tabSelected$gvWishList$ctl{pos:02d}$"
        }
        if action == "add":
            postdata["__EVENTTARGET"] += "btnAdd"
        elif action == "del":
            postdata["__EVENTTARGET"] += "btnRemoveItem"
        elif action == "quota":
            postdata["__EVENTTARGET"] += "btnQuota"
        else:
            raise RuntimeError("Unknown action")
        return self.__postback(data=postdata)

    def wishmap(self) -> Dict[int, int]:
        self.checklogin()
        return self.__wishmap.copy()

    def wishupdate(self, html: str) -> None:
        self.checklogin()
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

    def wishquery(self, cid: int) -> Dict[int, int]:
        self.checklogin()
        postdata = {
            "__EVENTTARGET": "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$btnSearchOther",
            "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$cbOtherCondition1": "on",
            "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$tbSubID": f"{cid:04d}"
        }
        r = self.__postback(data=postdata)
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

    def wishadd(self, cid: int) -> None:
        self.checklogin()
        if cid in self.__wishmap:
            raise RuntimeError(f"course id {cid} already in your wish list")
        m = self.wishquery(cid)
        pos = m[cid]
        postdata = {
            f"ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$gvSearchResult$ctl{pos:02d}$btnAdd": "關注"
        }
        r = self.__postback(data=postdata)
        self.wishupdate(r.text)

    def wishremove(self, cid: int) -> None:
        r = self.__wishaction(cid, "btnRemoveItem")
        self.wishupdate(r.text)

    def wish_addcourse(self, cid: int) -> None:
        r = self.__wishaction(cid, "btnAdd")
        self.wishupdate(r.text)

    def wish_register(self, cid: int) -> Tuple[int, int]:
        r = self.__wishaction(cid, "btnQuota")
        result = re.search(r'開放人數： *(\d+) */ *(\d+)', r.text)
        return int(result[1]), int(result[2])

    def __courseaction(self, cid: int, action: str) -> Response:
        self.checklogin()
        self.coursequery(cid)
        postdata = {
            "__EVENTTARGET": "ctl00$MainContent$TabContainer1$tabSelected$"
        }
        if action == "add":
            postdata["__EVENTTARGET"] += "gvToAdd"
            postdata["__EVENTARGUMENT"] = "addCourse$0"
        elif action == "del":
            postdata["__EVENTTARGET"] += "gvToDel"
            postdata["__EVENTARGUMENT"] = "delCourse$0"
        else:
            raise RuntimeError("Unknown action")
        return self.__postback(data=postdata)

    def selected(self) -> Set[int]:
        return self.__selected.copy()

    def courseupdate(self, html: str) -> None:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", id="ctl00_MainContent_TabContainer1_tabSelected_TabContainer2_perSubTab_gvPerSelPg")
        trs = table.find_all("tr")
        self.__selected = set([int(tr.find("td").a.string) for tr in trs[1:]])

    def coursequery(self, cid: int) -> None:
        self.checklogin()
        postdata = {
            "ctl00$MainContent$TabContainer1$tabSelected$tbSubID": f"{cid:04d}",
            "ctl00$MainContent$TabContainer1$tabSelected$btnGetSub": "查詢"
        }
        self.__postback(data=postdata)

    def courseadd(self, cid: int) -> None:
        if cid in self.__selected:
            raise RuntimeError("course id {cid} already in selected courses")
        r = self.__courseaction(cid, "add")
        self.courseupdate(r.text)

    def coursedel(self, cid: int) -> None:
        if cid not in self.__selected:
            raise RuntimeError(f"course id {cid} not in selected courses")
        r = self.__courseaction(cid, "del")
        self.courseupdate(r.text)
