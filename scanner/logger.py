from colorlog import ColoredFormatter
import logging

class Logger:
    def __init__(self, name='', log_level = 'WARNING', log_colored=True):
        self.name = name
        self.log_colored = log_colored
        self.level = log_level
        self._setup_logger()

    def _setup_logger(self):
        if self.log_colored:
            formatter = ColoredFormatter(
                "%(asctime)s %(log_color)s[%(action)s]%(reset)s %(message_log_color)s%(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                reset=True,
                log_colors={
                    'DEBUG': 'yellow',
                    'INFO': 'cyan',
                    'WARNING': 'green',
                    'ERROR': 'red',
                    'CRITICAL': 'red',
                },
                secondary_log_colors={
                    'message': {
                        'DEBUG': 'white',
                        'INFO': 'white',
                        'WARNING': 'white',
                        'ERROR': 'red',
                        'CRITICAL': 'red',
                    }
                }
            )
        else:
            formatter = logging.Formatter('%(asctime)s [%(action)s] %(message)s', "%Y-%m-%d %H:%M:%S")

        # Display the logging on the Terminal
        self.logger = logging.getLogger(self.name)
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        level = logging.getLevelName(self.level)
        self.logger.setLevel(level)
        self.logger.propagate = False
        return self.logger