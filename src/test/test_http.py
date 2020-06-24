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
        m = self.course.wishquery(1411)
        self.assertNotEqual(m, {})

    def test_wish_add_remove_update(self):
        self.test_login()
        m = self.course.wishmap()
        l1 = list(m.keys())
        l1.append(1411)

        self.course.wishadd(1411)
        m2 = self.course.wishmap()
        l2 = list(m2.keys())
        self.assertListEqual(l1, l2)

        self.course.wishremove(1411)
        m3 = self.course.wishmap()
        self.assertDictEqual(m, m3)

    def test_wish_addcourse(self):
        self.test_login()
        m1 = self.course.wishmap()
        l1 = list(m1.keys())
        l1.append(1411)

        self.course.wishadd(1411)
        l2 = list(self.course.wishmap().keys())
        self.assertListEqual(l1, l2)

        self.course.wish_addcourse(1411)
        m3 = self.course.wishmap()
        self.assertDictEqual(m1, m3)

    def test_wish_register(self):
        self.test_login()
        self.course.wishadd(1411)
        total, opened = self.course.wish_register(1411)
        self.assertIs(type(total), int)
        self.assertIs(type(opened), int)

    def test_coursequery(self):
        self.test_login()
        self.course.coursequery(1411)

    def test_course_add_del(self):
        self.test_login()
        s1 = self.course.selected()

        self.course.coursedel(1411)
        s2 = self.course.selected()
        self.assertSetEqual(s1 - {1411}, s2)

        self.course.courseadd(1411)
        s3 = self.course.selected()
        self.assertSetEqual(s1, s3)


if __name__ == "__main__":
    unittest.main()
