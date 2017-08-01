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
43e1cef8
"""
import subprocess
import time
import sys
import os
import glob
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
        print("WARNING! not a valid path: {}".format(local_path))
        return []

    def getprop(self):
        return self.start + ["getprop"]


def devicelist():
    """ return a list of device codes for the usb-plugged-in devices
     in the order they are given by calling 'adb devices' """
    raw = subprocess.run(["adb", "devices"], stdout=subprocess.PIPE).stdout.decode("utf-8").split(os.linesep)[1:]
    return [entry.split('\t')[0] for entry in raw if "\t" in entry]


def ask(cmd_str):
    """ run an adb command string and return the terminal text output """
    return subprocess.run(cmd_str, stdout=subprocess.PIPE).stdout.decode("utf-8").split(os.linesep)


if __name__ == "__main__":
    path = os.path.join('C:\\', 'Users', '2053_HSUF', 'Desktop')
    cmds = [Adb(device) for device in devicelist()]
    for num, cmd in enumerate(cmds):
        print("#{:3}            *********************  {}  **********************".format(num + 1, cmd.device))
        junk = ask(cmd.getprop())
        print([j for j in junk if 'gsm.operator.numeric' in j])
#