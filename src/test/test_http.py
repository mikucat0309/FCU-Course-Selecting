import unittest

from src.main import error
from src.main import http


class TestHttp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.course = http.Course()

    def tearDown(self):
        self.course.reset()

    def test_login(self):
        username = "D0888011"
        password = "Correct"
        self.course.login(username, password)

    def test_login_failed(self):
        username = "D0888011"
        password = "Wrong"
        with self.assertRaises(error.LoginError):
            self.course.login(username, password)


if __name__ == "__main__":
    unittest.main()
