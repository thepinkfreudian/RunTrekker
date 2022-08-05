from datetime import datetime, timedelta


def get_refresh_range(days: int = 7):
    end = datetime.today()
    start = end - timedelta(days=days)

    return start, end
