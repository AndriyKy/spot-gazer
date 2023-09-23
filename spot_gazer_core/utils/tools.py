import pendulum


def parse_time(hour: int = 0, minute: int = 0, second: int = 0, human_readable: bool = False) -> str | int:
    for time in (hour, minute, second):
        assert time >= 0 and time <= 60, "Time must be in range [0, 60]"

    if human_readable:
        return pendulum.duration(hours=hour, minutes=minute, seconds=second)
    return hour*3600 + minute*60 + second
