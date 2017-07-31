""" automate chameleon and hidden menu device tests.

psuedo:

- setup -
detect devices
for each device detect carrier
based on carrier, use chamcodes to assign appropriate testing regime to each device
check each device for apk installation
if needed, locate local apk and install to device
    find local apk filename
create local screenshot directory
create local test-results directory
create and assign filenames for each test result and screenshot

- begin testing -
dial the test
wait for connect (or timeout)
check response
record apk response
take screenshot

-- parse results --
"""
import subprocess
import time
import sys
import os
from chamcodes import dial_codes


def devicelist():
    """ return a list of device codes for the usb-plugged-in devices
     in the order they are given by calling 'adb devices' """
    raw = subprocess.run(["adb", "devices"], stdout=subprocess.PIPE).stdout.decode("utf-8").split(os.linesep)[1:]
    return [entry.split('\t')[0] for entry in raw if "\t" in entry]


def carrier_detect():
    devices = devicelist()
    # check service state
    for device in devices:
        cmds = ['adb', '-s', '{}'.format(device), 'wait-for-device', 'shell', 'dumpsys', 'telephony.registry']
        raw = subprocess.run(cmds, stdout=subprocess.PIPE).stdout.decode("utf-8").split(os.linesep)
        print("*********************************")
        entry = [blurb for blurb in raw if "sprint" in blurb.lower()]
        for e in entry:
            if e:
                print(e)


if __name__ == "__main__":
    print(dial_codes['All'])


