ROLE_NORMAL = 0
ROLE_LOCKED = 1
ROLE_ADMIN = 2
LOGIN_MAX_ATTEMPTS = 3

class BotUser:
    def __init__(self, id) -> None:
        self.ID = id
        self.Role = ROLE_NORMAL
        self.LoginAttempts = 0


    def AttemptLoginFail(self) -> None:
        self.LoginAttempts += 1
        if self.LoginAttempts >= LOGIN_MAX_ATTEMPTS:
            self.Role = ROLE_LOCKED

    def LoginPass(self) -> None:
        self.Role = ROLE_ADMIN