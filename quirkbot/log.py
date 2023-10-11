from logging import (
    Formatter,
    StreamHandler,
    getLogger,
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    CRITICAL,
)


class CustomFormatter(Formatter):
    grey = "\x1b[38m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    bold_red = "\x1b[1;31m"
    reset = "\x1b[0m"
    log_fmt = "%(levelname)s: %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        DEBUG: f"{grey}{log_fmt}{reset}",
        INFO: f"{grey}{log_fmt}{reset}",
        WARNING: f"{yellow}{log_fmt}{reset}",
        ERROR: f"{red}{log_fmt}{reset}",
        CRITICAL: f"{bold_red}{log_fmt}{reset}",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = Formatter(log_fmt)
        return formatter.format(record)


LOGGER = getLogger("quirkbot")
ch = StreamHandler()
ch.setLevel(DEBUG)
ch.setFormatter(CustomFormatter())
LOGGER.addHandler(ch)
