class LoginError(Exception):
    def __init__(self):
        pass


class CourseError(Exception):
    def __init__(self, msg: str):
        self.msg = msg
