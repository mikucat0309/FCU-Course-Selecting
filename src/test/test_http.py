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


if __name__ == "__main__":
    unittest.main()
