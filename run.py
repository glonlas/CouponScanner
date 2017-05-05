from scanner.scanner import Scanner
import sys
import argparse
import os

def main(argv):
    config_file = 'config/config.yml'

    parser = argparse.ArgumentParser()
    parser.add_argument("-c",
                        "--config",
                        help="Override the default config file. By default: config/config.yml")

    args = parser.parse_args()
    if args.config:
        if os.access(args.config, os.R_OK):
            config_file = args.config
        else:
            print("ERROR: '", args.config, "' is not readable, please check the path")
            exit(0)

    # Init the scanner
    scanner = Scanner(config_path=config_file)

    # Start the scanner
    scanner.start_worker()

if __name__ == '__main__':
    main(sys.argv[1:])
