import logging
import time
from random import uniform


class HumanBehaviour():

    def __init__(self):
        self.log_extra = {'action': 'HumanBehaviour'}
        self._logger = logging.getLogger('Instabot')

    def jitter(self, value, delta=0.3):
        jitter = delta * value
        return uniform(value-jitter, value+jitter)

    def sleep(self, seconds, delta=0.3):
        sleep_duration = self.jitter(seconds, delta)

        self._logger.info('Sleep for %s' % (sleep_duration), extra=self.log_extra)
        time.sleep(sleep_duration)

    def action_delay(self, low, high):
        # Waits for random number of seconds between low & high numbers
        longNum = uniform(low, high)
        shortNum = float("{0:.2f}".format(longNum))

        self._logger.info('Wait for %s' % (shortNum), extra=self.log_extra)
        time.sleep(shortNum)
