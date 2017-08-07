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


def ask(cmd_str):
    """ run an adb command string, return the terminal text output as a list of lines"""
    return subprocess.run(cmd_str, stdout=subprocess.PIPE).stdout.decode("utf-8").split(os.linesep)


class Adb(object):
    """ return properly formatted 'adb' command strings for subprocess to call when multiple devices are hooked up.
        Instances provide a place to stick the unique data for each device"""
    def __init__(self, device):
        self.device = device
        self.boiler_plate = ['adb', '-s', '{}'.format(device), 'wait-for-device']
        self.shell = self.boiler_plate + ['shell']
        self.pull = self.boiler_plate + ['pull']
        self.display_density = None
        self.display_multiplier = 1
        self.alpha = None
        self.testplan = None
        self.pic_paths = {}
        self.gen = ()
        self.current_code = ""
        self.time_on = 0    # zero will turn on the execution of commands
        self.delay = 10      # seconds
        self.finished = False
        self.outputdir = os.path.join(os.getcwd(), "pics")
        if not os.path.exists(self.outputdir):
            os.mkdir(self.outputdir)

    def android_id(self):
        return self.shell + ['content', 'query' ' --uri', '\"content://settings/secure/android_id\"', '--projection', 'value']

    def telephony_registry(self):
        return self.shell + ['dumpsys', 'telephony.registry']

    def uri(self):
        return self.shell + ['content', 'query' ' --uri', '\"content://settings/system/\"']

    def getprop(self):
        return self.shell + ["getprop"]

    def hangup(self):
        return self.shell + ["input", "keyevent", "KEYCODE_ENDCALL"]

    def screenshot(self, test, sd_path):
        self.pic_paths[test] = sd_path
        return self.shell + ["screencap", "/sdcard/" + self.pic_paths[test]]

    def download(self, path):
        return self.pull + ["/sdcard/" + path, self.outputdir]

    def dial(self, code):
        return self.shell + ["am", "start", "-a", "android.intent.action.CALL", "-d", "tel:{}".format(code)]

    def enter_key(self, code=None):
        if code is None:
            code = '66'
        return self.shell + ["input", "keyevent", str(code)]

    def install(self, local_path):
        print(local_path)
        if os.path.exists(local_path):
            return ['adb', '-s', '{}'.format(self.device), 'install', '-r', '{}'.format(local_path)]
        print("WARNING! not a valid path: {}".format(local_path))
        return []

    def display_config(self, xyxy=None):
        if self.display_density is None:
            self.display_density = int(ask(self.getprop() + ['ro.sf.lcd_density'])[0].strip())
            print("display density: {}".format(self.display_density))
            self.display_multiplier = self.display_density / 320
        return self.display_density


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


def init_devices():
    """ initialize plugged-in devices and assign test plans """
    cmds = [Adb(device) for device in devicelist()]
    for num, cmd in enumerate(cmds):
        print("#{:3}            *********************  {}  **********************".format(num + 1, cmd.device))
        cmd.display_config()
        cmd.alpha = [assign_carrier(j) for j in ask(cmd.getprop()) if 'ro.home.operator' in j]
        if not cmd.alpha:
            print("-- no recognized carrier --")
            continue
        print(cmd.alpha[0])
        cmd.testplan = dial_codes['All'] + dial_codes[cmd.alpha[0]]
        cmd.pic_paths = {k: cmd.alpha[0].replace(" ", '') + "_" + str(k[0]) + "_scrn.png" for k in cmd.testplan}
        cmd.gen = (c for c in cmd.testplan)
    return cmds

if __name__ == "__main__":
    cmds = init_devices()
    path = os.path.join('C:\\', 'Users', '2053_HSUF', 'Desktop')

    """ run test-plans """
    while True:
        devices_finished = 0
        # activate the next command
        for num, cmd in enumerate(cmds):
            if cmd.gen:
                try:
                    if not cmd.time_on:
                        cmd.current_code = cmd.gen.__next__()
                        print("{}: {} ".format(cmd.device, cmd.current_code))
                        ask(cmd.dial(cmd.current_code[0]))
                        cmd.time_on = time.time()

                except Exception as e:
                    print("device {} {} is done".format(cmd.device, cmd.alpha))
                    print(e)
                    cmd.finished = True
                    devices_finished += 1
            else:
                devices_finished += 1

        # use the timer to activate screen shot, download it, and then tear down call
        for num, cmd in enumerate(cmds):
            if cmd.gen and (not cmd.finished):
                current_wait = time.time() - cmd.time_on
                if current_wait > cmd.delay:
                    print("tearing down {} cmd: {} pic: {}"
                          .format(cmd.device, cmd.current_code, cmd.pic_paths[cmd.current_code]))
                    ask(cmd.screenshot(cmd.current_code, cmd.pic_paths[cmd.current_code], ))
                    ask(cmd.download(cmd.pic_paths[cmd.current_code]))
                    ask(cmd.hangup())
                    cmd.time_on = 0


        if devices_finished >= num:
            print(" ****   all done!  ****")
            break
