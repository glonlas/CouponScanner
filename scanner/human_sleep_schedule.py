import logging
from datetime import datetime, timedelta
from time import sleep
from random import uniform

"""
# Config Format Expected
sleep_schedule:
  enabled: True
  enable_reminder: True
  reminder_interval: 600
  entries:
    # Night
    - enabled: True
      # When the sleep should start (24h format hh:mm)
      start_time: '23:40'
      # How long is the sleep (hh:mm)
      duration: '8:30'
      ## Random offset
      # Add at the initial start time a random extra time (between 00:00 and XXX_random_offset)
      # Ex: 23:40 + 15
      start_time_random_offset: '0:20'
      duration_random_offset: '0:20'
"""

class HumanSleepSchedule(object):

    SCHEDULING_MARGIN = timedelta(minutes=10)    # Skip if next sleep is SCHEDULING_MARGIN from now

    def __init__(self, config):
        # Logs
        self.log_extra = {'action': 'HumanSleepSchedule'}
        self._logger = logging.getLogger('CouponChecker')
        self._last_index = -1
        self._next_index = -1
        self._process_config(config)
        self._schedule_next_sleep()

    def work(self):
        if self._should_sleep_now():
            self._sleep()
            self._schedule_next_sleep()
            return True
        return False

    def get_next_sleep_schedule(self):
        now = datetime.now()

        times = []
        for index in range(len(self.entries)):
            next_time = now.replace(hour=self.entries[index]['start_time'].hour, minute=self.entries[index]['start_time'].minute)
            next_time += timedelta(seconds=self._get_random_offset(self.entries[index]['start_time_random_offset']))

            next_duration = self._get_next_duration(self.entries[index])

            next_end = next_time + timedelta(seconds=next_duration)

            prev_day_time = next_time - timedelta(days=1)
            prev_day_end = next_end - timedelta(days=1)

            diff = next_time - now

            # Edge case if sleep time has started previous day
            if (prev_day_time <= now and now < prev_day_end):
                self._next_index = index
                return prev_day_time, next_duration, prev_day_end, True
            # If sleep time is passed or time to sleep less than SCHEDULING_MARGIN then add one day
            elif (next_time <= now and now > next_end) or (diff > timedelta(0) and diff < self.SCHEDULING_MARGIN):
                next_time += timedelta(days=1)
                next_end += timedelta(days=1)
                diff = next_time - now
            # If now is sleeping time
            elif next_time <= now and now < next_end:
                if index == self._last_index:  # If it is still the same sleep entry, but now < next_end because of random offset
                    next_time += timedelta(days=1)
                    next_end += timedelta(days=1)
                    diff = next_time - now
                else:
                    self._next_index = index
                    return next_time, next_duration, next_end, True

            prepared = {'index': index, 'start_time': next_time, 'duration': next_duration, 'end': next_end, 'diff': diff}
            times.append(prepared)

        closest = min(times, key=lambda x: x['diff'])
        self._next_index = closest['index']

        return closest['start_time'], closest['duration'], closest['end'], False

    def _process_config(self, config):
        def testkey(entry, key, offset=False, defval=''):
            if not key in entry:
                index = config.index(entry) + 1
                if not offset:
                    raise ValueError('HumanSleepSchedule: No "%s" key found in entry %d' % (key, index))
                else:
                    self._logger.debug('No "%s" key found in entry %d, using default value (%s)' % (key, index, defval), extra=self.log_extra)

        self.entries = []

        if 'enabled' in config and config['enabled'] == False: return

        if 'enable_reminder' in config and config['enable_reminder'] == True:
            self._enable_reminder = True
            self._reminder_interval = config['reminder_interval'] if 'reminder_interval' in config else 600
        else:
            self._enable_reminder = False

        # Entries
        if not 'entries' in config:
            self._logger.debug('SleepSchedule is disabled.', extra=self.log_extra)
            return False

        for entry in config['entries']:
            if 'enabled' in entry and entry['enabled'] == False:
                continue

            prepared = {}

            # Start time
            testkey(entry, 'start_time')
            prepared['start_time'] = datetime.strptime(entry['start_time'], '%H:%M')

            # Duration
            testkey(entry, 'duration')
            raw_duration = datetime.strptime(entry['duration'], '%H:%M')
            prepared['duration'] = int(timedelta(hours=raw_duration.hour, minutes=raw_duration.minute).total_seconds())

            # Random Offset on start time
            testkey(entry, 'start_time_random_offset', offset=True, defval='01:00')
            raw_time_random_offset = datetime.strptime(
                entry['start_time_random_offset'] if 'start_time_random_offset' in entry else '01:00', '%H:%M')
            prepared['start_time_random_offset'] = int(
                timedelta(
                    hours=raw_time_random_offset.hour, minutes=raw_time_random_offset.minute).total_seconds())

            # Random Offset on duration
            testkey(entry, 'duration_random_offset', offset=True, defval='00:30')
            raw_duration_random_offset = datetime.strptime(
                entry['duration_random_offset'] if 'duration_random_offset' in entry else '00:30', '%H:%M')
            prepared['duration_random_offset'] = int(
                timedelta(
                    hours=raw_duration_random_offset.hour, minutes=raw_duration_random_offset.minute).total_seconds())

            # Add the config
            self.entries.append(prepared)

        if not len(self.entries):
            self._logger.debug('SleepSchedule is disabled.', extra=self.log_extra)
            return False
        else:
            return True

    def _get_next_duration(self, entry):
        duration = entry['duration'] + self._get_random_offset(entry['duration_random_offset'])
        return duration

    def _get_random_offset(self, max_offset):
        offset = uniform(-max_offset, max_offset)
        return int(offset)


    def _schedule_next_sleep(self):
        if not len(self.entries):
            return False

        self._next_sleep, self._next_duration, self._next_end, sleep_now = self.get_next_sleep_schedule()

        if not sleep_now:
            time = self._time_fmt(self._next_sleep)
            duration = self._time_fmt(self._next_duration)
            log_string = 'Next sleep at %s, for a duration of %s' % \
                         (time,
                          duration)
            self._logger.warning(log_string, extra=self.log_extra)

            if self._enable_reminder:
                self._last_reminder = datetime.now()

    def _should_sleep_now(self):
        if not len(self.entries):
            return False
        now = datetime.now()

        if now >= self._next_sleep and now < self._next_end:
            self._next_duration = (self._next_end - now).total_seconds()
            return True

        if self._enable_reminder:
            diff = now - self._last_reminder
            if (diff.total_seconds() >= self._reminder_interval):
                time = str(self._next_sleep.strftime("%H:%M:%S"))
                duration = str(timedelta(seconds=self._next_duration))

                log_string = 'Next sleep at %s, for a duration of %s' % \
                             (time,
                              duration)
                self._logger.warning(log_string, extra=self.log_extra)
                self._last_reminder = now

        return False

    def _time_fmt(self, value):
        ret = ""
        if isinstance(value, datetime):
            ret = value.strftime("%H:%M:%S")
        elif isinstance(value, (int, float)):
            h, m = divmod(value, 3600)
            m, s = divmod(m, 60)
            ret = "%02d:%02d:%02d" % (h, m, s)
        return ret

    def _sleep(self):
        now = datetime.now()

        sleep_to_go = self._next_duration
        sleep_hms = self._time_fmt(self._next_duration)
        wakeup_at = self._time_fmt(now + timedelta(seconds=sleep_to_go))

        log_string = 'Sleeping for: %s, wake at %s' % \
                     (sleep_hms,
                      wakeup_at)
        self._logger.error(log_string, extra=self.log_extra)

        sleep(sleep_to_go)
        self._last_index = self._next_index
