from Messages import Messages


ROLE_DEFAULT = 0
ROLE_LOCKED = 1
ROLE_ADMIN = 2
LOGIN_MAX_ATTEMPTS = 3
SENDING_INTERVAL_MS = 10

class BotUser:
    def __init__(self, id) -> None:
        self.ID = id
        self.Role = ROLE_DEFAULT
        self.LoginAttempts : int = 0
        self.PreviousSendTime = None

        # Admin data
        self.CurrentChatID = None
        self.CurrentMessageIndex : int = None
        self.CurrentMessages : Messages = None


    def AttemptLoginFail(self) -> None:
        self.LoginAttempts += 1
        if self.LoginAttempts >= LOGIN_MAX_ATTEMPTS:
            self.Role = ROLE_LOCKED

    def LoginPass(self) -> None:
        self.Role = ROLE_ADMIN