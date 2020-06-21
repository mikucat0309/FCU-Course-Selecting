import logging

from requests import Session, Response
from requests.cookies import RequestsCookieJar

from . import error
from .util import get_hidden_values


class Course:
    def __init__(self):
        ft = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        sh = logging.StreamHandler()
        sh.setFormatter(ft)
        self.__logger = logging.getLogger("fcu")
        self.__logger.addHandler(sh)
        self.__logger.level = logging.DEBUG
        self.url = ""
        self.__init()

    def __post_back(self, url: str = "", data=None, eventarg: str = "") -> Response:
        url = url if url else self.url
        if data:
            self.__post_data.update(data)
        r = self.__session.post(url, data=self.__post_data)
        self.__post_data = get_hidden_values(r.text)
        return r

    def login(self, username: str, passwd: str):
        self.__session.get("https://course.fcu.edu.tw/validateCode.aspx")
        login_data = {
            "__EVENTTARGET": "ctl00$Login1$LoginButton",
            "ctl00$Login1$RadioButtonList1": "zh-tw",
            "ctl00$Login1$UserName": username,
            "ctl00$Login1$Password": passwd,
            "ctl00$Login1$vcode": self.__session.cookies.get("CheckCode"),
        }
        response = self.__post_back("https://course.fcu.edu.tw/Login.aspx", login_data)
        self.url = response.url
        self.__logger.debug(self.url)
        if "service" not in self.url:
            raise error.LoginError
        return response

    def __init(self):
        self.__session = Session()
        self.__session.cookies = RequestsCookieJar()
        r = self.__session.get("https://course.fcu.edu.tw")
        self.__post_data = get_hidden_values(r.text)

    def reset(self):
        self.close()
        self.__init()

    def close(self):
        self.__session.close()
