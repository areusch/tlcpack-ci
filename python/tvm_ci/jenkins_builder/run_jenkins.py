import argparse
import logging
import time

from . import jenkins_lib


def main():
    parser = argparse.ArgumentParser(description="Run Jenkins locally")
    jenkins_lib.add_arguments(parser)
    args = parser.parse_args()
    logging.basicConfig(level="INFO")

    with jenkins_lib.launch_jenkins(args, []):
        print("Press Ctrl+C to exit Jenkins")
        while True:
            time.sleep(1)


if __name__ == "__main__":
    main()
