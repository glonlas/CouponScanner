from scanner.human_behaviour import HumanBehaviour
from scanner.human_sleep_schedule import HumanSleepSchedule
from scanner.logger import Logger
from tinydb import TinyDB, Query
import datetime
import json
import requests
import logging
import yaml
import atexit
import signal

import pprint

class Scanner:

    counters = {
        "tested": 0,
        "found": 0,
        "last_id": 0
    }

    request = {
        "response": None,
        "json": None
    }

    user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36  "
                  "(KHTML, like Gecko) Chrome/53.0.2785.101 Safari/537.36")
    accept_language = 'fr-FR,fr;q=0.8,en-US;q=0.6,en;q=0.4'

    session = None

    def __init__(self, config_path = 'config/config.yml'):
        self.start_time = datetime.datetime.now()

        # Process the config
        self.config_path = config_path
        self._process_config(config_path = self.config_path)

        # Init Logger
        self._setup_logger()

        log_extra = {'action': 'Init'}
        log_string = 'Coupon Scanner v1.0 started at: %s' % \
                     (self.start_time.strftime("%d.%m.%Y %H:%M"))
        self.logger.warning(log_string, extra=log_extra)

        log_string = 'Config file: %s' % (config_path)
        self.logger.warning(log_string, extra=log_extra)

        # Init DB for Unfollow
        db_path = './dbs/' + self.service_name + '.json'
        self.coupon_db = TinyDB(db_path)
        log_string = 'DB file: %s' % (db_path)
        self.logger.warning(log_string, extra=log_extra)

        # Init sub-systems
        self.human_behaviour = HumanBehaviour()
        self.human_sleep_schedule = HumanSleepSchedule(self.sleep_schedule)

        # Init session
        self._setup_session(
            self.service_host,
            self.user_agent,
            self.accept_language,
            self.proxy
        )

        signal.signal(signal.SIGTERM, self.stop_worker)
        atexit.register(self.stop_worker)

    def start_worker(self):
        log_extra = {'action': 'Worker'}

        for id in range(self.service_start, self.service_end):
            log_string = "Testing coupon #%s" % (id)
            self.logger.info(log_string, extra={'action': 'Coupon'})

            if self._send_request(self.service_url % (id)):

                if 'Status' in self.request['json'].keys() and \
                   self.request['json']['Status'] == 0:

                    # Coupon found
                    self.counters['found'] += 1
                    self._save_coupon(self.request['json'])

            self.counters['last_id'] = id
            self.counters['tested'] += 1
            self.human_behaviour.action_delay(1,5)

            if self.human_sleep_schedule.work():
                # Reload the config when after a break
                # Allow to refresh your configuration if you have changed it
                self._wakeup_process()

    def stop_worker(self):
        self._status()

        work_time = datetime.datetime.now() - self.start_time
        log_string = 'Coupon scanner worked for: %s' % (work_time)
        self.logger.warning(log_string, extra={'action': 'Worker'})


    def _process_config(self, config_path):
        def list_from_file(file):
            with open(file, 'r', encoding = 'utf-8') as f:
                lines = f.read().splitlines()
            return lines

        def yaml_from_file(file):
            with open(file, 'r') as ymlfile:
                return yaml.load(ymlfile)

        config = yaml_from_file(config_path)

        ## Services
        self.service_name = config['service']['name']
        self.service_host = config['service']['host']
        self.service_url = config['service']['url']
        self.service_step = config['service']['step']
        self.service_start = config['service']['start']
        self.service_end = config['service']['end']

        ## Sleep Schedule
        self.sleep_schedule = config['sleep_schedule']

        ## User agent & Proxy
        self.user_agent = config['browser']['user_agent']
        self.accept_language = config['browser']['accept_language']
        self.proxy = config['browser']['proxy']

        ## Logs
        self.log_mod = config['logs']['mode']
        self.log_colored = config['logs']['colored']
        self.log_level = config['logs']['level']
        self.log_full_path = '%s%s_%s.log' % (config['logs']['path'],
                                              self.service_name,
                                              self.start_time.strftime("%Y.%m.%d_%H%M"))

    def _setup_logger(self):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s [%(levelname)s] %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename=self.log_full_path,
                            filemode='w')

        if self.log_mod == 1:
            logSystem = Logger(name = '', log_level = self.log_level, log_colored = self.log_colored)
            self.logger = logSystem.logger
        else:
            self.logger = logging.getLogger('')

    def _wakeup_process(self):
        self._process_config(config_path=self.config_path)
        self.logger.warning("Config reloaded", extra={'action': 'Config'})
        self._status()

    def _status(self):
        log_string = '%i tested, %i found. Last ID: %i.' % \
                     (self.counters['tested'],
                      self.counters['found'],
                      self.counters['last_id'])
        self.logger.warning(log_string, extra={'action': 'Status'})


    def _setup_session(self, host, user_agent, accept_language, proxy):
        self.session = requests.Session()
        self.session.headers.update({'Accept-Encoding': 'gzip, deflate',
                                     'Accept-Language': accept_language,
                                     'Connection': 'keep-alive',
                                     'Content-Length': '0',
                                     'Host': host,
                                     'Origin': 'https://' + host,
                                     'Referer': 'https://' + host + '/',
                                     'User-Agent': user_agent,
                                     'X-Instagram-AJAX': '1',
                                     'X-Requested-With': 'XMLHttpRequest'})

        ## Setup the proxy if needed
        # if you need proxy make something like this:
        # self.session.proxies = {"https" : "http://proxyip:proxyport"}
        if proxy != "":
            proxies = {
                'http': 'http://' + proxy,
                'https': 'http://' + proxy,
            }
            self.session.proxies.update(proxies)

    def _send_request(self, endpoint):
        try:
            response = self.session.get(endpoint)

            if response.status_code == 200:
                self.request['response'] = response
                self.request['json'] = json.loads(response.text)
                return True

        except:
            logging.info("Error on req!", extra={'action': 'Request'})

        return False

    def _save_coupon(self, json):
        # Coupon name
        code = ''
        if 'Code' in json.keys():
            code = json['Code']

        # Coupon expiration
        expires = 0
        if 'Tags' in json.keys() and \
                        'ExpiresOn' in json['Tags'].keys():
            expires = json['Tags']['ExpiresOn']

        # Coupon name
        name = ''
        if 'Name' in json.keys():
            name = json['Name']

        # Add the follower to the DB
        self.coupon_db.insert({'coupon_id': code, 'expires': expires, 'name': name})
        log_string = "Coupon #%s: %s" % (code, name)
        self.logger.warning(log_string, extra={'action': 'Coupon'})

        return True
