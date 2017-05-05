# Requirements
`Python 3`, `PIP`

# 1. Packages to install (Debian/Ubuntu)
```bash
apt-get install -y python3 python3-pip ttf-ancient-fonts tesseract-ocr libjpeg8 libjpeg62-dev libfreetype6 libfreetype6-dev build-dep python-imaging
pip install tox
```

# 2. Configuration
## Setup the project
Copy the file `config/config.yml.dist` to `config/config.yml` and edit it.  

# 3. Run the project
```bash
tox
```

# 4. Run the project with different config file
```bash
tox -- runBot.py --config path/to/my/config.yml
```

# 5. Want to refresh the packages
```bash
tox -r
```

# Need more detail during the scan?
Change the logging level in the config file from 'WARNING' to 'INFO'