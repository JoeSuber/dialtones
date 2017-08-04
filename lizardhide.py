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
    """ return properly formatted 'adb' command strings for subprocess to call when multiple devices are hooked up.
        Instances provide a place to stick the unique data for each device"""
    def __init__(self, device):
        self.device = device
        self.boiler_plate = ['adb', '-s', '{}'.format(device), 'wait-for-device']
        self.shell = self.boiler_plate + ['shell']
        self.pull = self.boiler_plate + ['pull']
        self.alpha = None
        self.testplan = None
        self.pic_paths = {}
        self.gen = ()

    def android_id(self):
        return self.shell + ['content', 'query' ' --uri', '\"content://settings/secure/android_id\"', '--projection', 'value']

    def tel_reg(self):
        return self.shell + ['dumpsys', 'telephony.registry']

    def uri(self):
        return self.shell + ['content', 'query' ' --uri', '\"content://settings/system/\"']

    def getprop(self):
        return self.shell + ["getprop"]

    def screenshot(self, test, sd_path):
        self.pic_paths[test] = sd_path
        return self.shell + ["screencap", sd_path]

    def download(self, path):
        return self.pull + [path]

    def dial(self, code):
        return self.shell + ["am", "start", "-a", "android.intent.action.CALL", "-d", "tel:{}".format(code)]

    def install(self, local_path):
        print(local_path)
        if os.path.exists(local_path):
            return ['adb', '-s', '{}'.format(self.device), 'install', '-r', '{}'.format(local_path)]
        print("WARNING! not a valid path: {}".format(local_path))
        return []


def ask(cmd_str):
    """ run an adb command string, return the terminal text output """
    return subprocess.run(cmd_str, stdout=subprocess.PIPE).stdout.decode("utf-8").split(os.linesep)


def devicelist():
    """ return a list of device codes for the usb-plugged-in devices
     in the order they are given by calling 'adb devices' """
    raw = ask(["adb", "devices"])[1:]
    return [entry.split('\t')[0] for entry in raw if "\t" in entry]


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
    """ initialize devices and assign test plans """
    path = os.path.join('C:\\', 'Users', '2053_HSUF', 'Desktop')
    sd_path = "/sdcard/screen.png"
    cmds = [Adb(device) for device in devicelist()]
    for num, cmd in enumerate(cmds):
        print("#{:3}            *********************  {}  **********************".format(num + 1, cmd.device))
        cmd.alpha = [assign_carrier(j) for j in ask(cmd.getprop()) if 'ro.home.operator' in j]
        if not cmd.alpha:
            print("-- no recognized carrier --")
            continue
        print(cmd.alpha[0])
        cmd.testplan = dial_codes['All'] + dial_codes[cmd.alpha[0]]
        cmd.pic_paths = {k: cmd.alpha[0].replace(" ", '') + "_" + str(k[0]) + "_scrn.png" for k in cmd.testplan}
        cmd.gen = (c[0] for c in cmd.testplan)

    """ run test-plan """
    while True:
        devices_finished = 0
        for num, cmd in enumerate(cmds):
            if cmd.gen:
                try:
                    code = cmd.gen.__next__()
                    print("{}: {} ".format(cmd.device, code))
                    ask(cmd.dial(code))

                except Exception as e:
                    print("device {} is done".format(cmd.device))
                    print(e)
                    devices_finished +=1
            else:
                devices_finished += 1

        ## short delay
        ## screen shots
        ## call teardowns
        ## error notation

        if devices_finished >= num:
            print(" ****   all done!  ****")
            break


