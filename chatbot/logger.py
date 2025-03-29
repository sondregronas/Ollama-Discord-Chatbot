import logging
from logging import getLogger, StreamHandler, INFO

logger = getLogger("chatbot")
logger.setLevel(INFO)


class ColorFormatter(logging.Formatter):
    _colors = {
        logging.CRITICAL: "\033[91m",  # Red
        logging.ERROR: "\033[91m",  # Red
        logging.WARNING: "\033[93m",  # Yellow
        logging.INFO: "\033[92m",  # Green
        logging.DEBUG: "\033[95m",  # Magenta
    }
    _marks = {
        logging.CRITICAL: "!",
        logging.ERROR: "E",
        logging.WARNING: "W",
        logging.INFO: "*",
        logging.DEBUG: "D",
    }
    _reset = "\033[0m"
    _blue = "\033[94m"
    _bold = "\033[1m"

    def format(self, rec):
        marks, colors = self._marks, self._colors
        return (
            f"{self._blue}{self._bold}[{colors[rec.levelno]}{marks[rec.levelno]}"
            f"{self._blue}]{self._reset} {super().format(rec)}"
        )


stream_formatter = ColorFormatter(
    "[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
streamhandler = StreamHandler()
streamhandler.setFormatter(stream_formatter)
logger.addHandler(streamhandler)
