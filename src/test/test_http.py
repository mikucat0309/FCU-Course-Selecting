import unittest

from src.main import error
from src.main import http


class TestHttp(unittest.TestCase):
    course = None

    @classmethod
    def setUpClass(cls):
        cls.course = http.Crawler()

    def tearDown(self):
        self.course.reset()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.course.close()

    def test_login(self):
        username = "D0888011"
        password = "Correct"
        self.course.login(username, password)

    def test_login_failed(self):
        username = "D0888011"
        password = "Wrong"
        with self.assertRaises(error.LoginError):
            self.course.login(username, password)

    def test_query(self):
        self.test_login()
        m = self.course.query(1411)
        self.assertNotEqual(m, {})

    def test_add_remove_wish(self):
        self.test_login()
        m = self.course.get_wishmap()
        l1 = list(m.keys())
        l1.append(1141)

        self.course.addwish(1141)
        m2 = self.course.get_wishmap()
        l2 = list(m2.keys())
        self.assertListEqual(l1, l2)

        self.course.removewish(1141)
        m3 = self.course.get_wishmap()
        self.assertDictEqual(m, m3)


if __name__ == "__main__":
    unittest.main()
