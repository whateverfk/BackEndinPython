from datetime import datetime


class TimeProvider:
    def now(self) -> datetime:
        return datetime.now().astimezone()
