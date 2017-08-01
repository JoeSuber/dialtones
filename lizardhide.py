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


class Adb(object):
    """ return properly formatted command strings for subprocess to call """
    def __init__(self, device):
        self.device = device
        self.start = ['adb', '-s', '{}'.format(device), 'wait-for-device', 'shell']

    def android_id(self):
        return self.start + ['content', 'query' ' --uri', '\"content://settings/secure/android_id\"', '--projection', 'value']

    def tel_reg(self):
        return self.start + ['dumpsys', 'telephony.registry']

    def uri(self):
        return self.start + ['content', 'query' ' --uri', '\"content://settings/system/\"']

    def install(self, local_path):
        print(local_path)
        if os.path.exists(local_path):
            return ['adb', '-s', '{}'.format(self.device), 'install', '-r', '{}'.format(local_path)]
        print("WARNING! not a path: {}".format(local_path))
        return []


def devicelist():
    """ return a list of device codes for the usb-plugged-in devices
     in the order they are given by calling 'adb devices' """
    raw = subprocess.run(["adb", "devices"], stdout=subprocess.PIPE).stdout.decode("utf-8").split(os.linesep)[1:]
    return [entry.split('\t')[0] for entry in raw if "\t" in entry]


def carrier_detect():
    devices = devicelist()
    # check service state
    for num, device in enumerate(devices):
        cmds = Adb(device)
        path = os.path.join('C:/', 'Users', '2053_HSUF', 'Desktop', 'SprintAdminTest.apk')
        print("#{:3}            *********************  {}  **********************".format(num + 1, device))
        raw = subprocess.run(cmds.uri(), stdout=subprocess.PIPE).stdout.decode("utf-8").split(os.linesep)
        #entry = [blurb for blurb in raw if "network" in blurb.lower()]
        entry = raw
        for e in entry:
            if e:
                print(e)


if __name__ == "__main__":
    carrier_detect()


