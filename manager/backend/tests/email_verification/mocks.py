class TOTPMock:
    time = 0

    def __init__(self, key, step, digits):
        pass

    def t(self):
        # Return random time
        return 123456

    def token(self):
        return 123456

    def verify(self, token, tolerance):
        return token == self.token()


class EmailMessageMock:
    def __init__(self, subject, body, to):
        pass

    def send(self):
        return 1
