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
take screenshot

-- parse results --

http://adbshell.com/commands

"""
import subprocess
import time
import sys
import os
import glob
from chamcodes import dial_codes, carriers


class Adb(object):
    """ return properly formatted command strings for subprocess to call when multiple devices are hooked up.
        Instances provide a place to stick the unique data for each device"""
    def __init__(self, device):
        self.device = device
        self.shell = ['adb', '-s', '{}'.format(device), 'wait-for-device', 'shell']
        self.alpha = None
        self.testplan = None

    def android_id(self):
        return self.shell + ['content', 'query' ' --uri', '\"content://settings/secure/android_id\"', '--projection', 'value']

    def tel_reg(self):
        return self.shell + ['dumpsys', 'telephony.registry']

    def uri(self):
        return self.shell + ['content', 'query' ' --uri', '\"content://settings/system/\"']

    def getprop(self):
        return self.shell + ["getprop"]

    def screenshot(self):
        return self.shell + [""]

    def install(self, local_path):
        print(local_path)
        if os.path.exists(local_path):
            return ['adb', '-s', '{}'.format(self.device), 'install', '-r', '{}'.format(local_path)]
        print("WARNING! not a valid path: {}".format(local_path))
        return []


def devicelist():
    """ return a list of device codes for the usb-plugged-in devices
     in the order they are given by calling 'adb devices' """
    raw = subprocess.run(["adb", "devices"], stdout=subprocess.PIPE).stdout.decode("utf-8").split(os.linesep)[1:]
    return [entry.split('\t')[0] for entry in raw if "\t" in entry]


def ask(cmd_str):
    """ run an adb command string, return the terminal text output """
    return subprocess.run(cmd_str, stdout=subprocess.PIPE).stdout.decode("utf-8").split(os.linesep)


def assign_carrier(clue):
    """ string search to map the correct testplan key to a device's clue-string """
    clue = clue.lower()
    for k in carriers:
        for matcher in carriers[k]:
            if matcher.lower() in clue:
                return k
    print("No good guess for {}".format(clue))
    return ""


if __name__ == "__main__":
    path = os.path.join('C:\\', 'Users', '2053_HSUF', 'Desktop')
    cmds = [Adb(device) for device in devicelist()]
    for num, cmd in enumerate(cmds):
        print("#{:3}            *********************  {}  **********************".format(num + 1, cmd.device))
        cmd.alpha = [assign_carrier(j) for j in ask(cmd.getprop()) if 'ro.home.operator' in j]
        if not cmd.alpha:
            continue
        print(cmd.alpha)
        cmd.testplan = dial_codes['All'] + dial_codes[cmd.alpha]
