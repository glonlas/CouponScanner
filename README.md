# Domino Pizza Coupon Scanner
Coupon scanner is a small script to list the available Domino Pizza coupons.
This scanner was build to be gentle and scan slowly. The goal is not
to overload Domino Pizza servers and neither to ban your IP, because at 
the end you want to buy your Pizza.


# Requirements
`Python 3`, `PIP`

## 1. Packages to install (Debian/Ubuntu)
```bash
apt-get install -y python3 python3-pip build-dep
pip install tox
```

## 2. Configuration
To setup the project you must start by creating your config file.
Copy the file `config/config.yml.dist` to `config/config.yml` and edit it. 
```bash
cp config/config.yml.dist config/config.yml
```

## 3. Run the project
```bash
tox
```

## 4. Run the project with different config file
```bash
tox -- run.py --config path/to/my/config.yml
```

## 5. Want to refresh the packages
```bash
tox -r
```

# FAQ
## How fast is this scanner?
This scanner is made to be gentle. It send a request every 10 sec, and
the mecanism of sleep_schedule is made to stop the scan during peak
periods to not overload the servers.

## How it works?
The public Domino Pizza coupon looks to be a 4 digit code. This scanner
will call the Domino Pizza API and try all the permutation until it finds
valid coupons. This script takes pause between each call and can even be
configure to take long break, like between 11:30am and 2pm or 5pm to 10pm
to not load servers during peak time.

## Need more detail during the scan?
Change the logging level in the config file from 'WARNING' to 'INFO'

