#!/usr/bin/env python3

import subprocess, time
from toolbox.logger import Log

help = "module to run external scripts or commands as needed"

def setup_args(subparser):
    subparser.add_argument(
        "-c", "--command",
        help='command or external script to execute',
        required=True,
        dest='COMMAND'
        )

def main(args):
    RESULTS = run_command(args.COMMAND)
    Log.info("command results are: ", output=True)
    for RESULT in RESULTS:
        print(RESULT, end='')
    return RESULTS

def run_command(command):
    RESULTS = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    for line in iter(RESULTS.stdout.readline, b''):
        if line:
            yield line.decode("UTF-8")
    while RESULTS.poll() is None:
        time.sleep(.1)
    ERR = RESULTS.stderr.read()
    if RESULTS.returncode != 0:
        Log.critical("please verify options and try again: " + str(ERR))
    else:
        return True

if __name__ == "__main__":
    main()
