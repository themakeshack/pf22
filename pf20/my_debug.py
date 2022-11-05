from datetime import datetime

from pfconfig import DEBUGLEVEL


def printdebug(level: int, message: str):
    # Set DEBUGLEVEL higher for more granularity; Set DEBUGLEVEL to 0 to turn debug off
    if level >= DEBUGLEVEL:
        print(datetime.now().replace(microsecond=0), ":: DEBUG", level, "::", message)
    return


if __name__ == "__main__":
    printdebug(1, "this is the message")
    printdebug(3, "this is another message")
