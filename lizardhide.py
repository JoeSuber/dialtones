"""
automate chameleon and hidden menu device tests.

Lock Screen (look for SKU)
Home Screen (if no app drawer screenshots of all apps)
App Drawer Screens
Contacts (Boost has 3 preloaded)
Recent Calls/Call History
Voicemail
##DATA# MMSC (URL, Proxy, Proxy Port)
##DIAG# (if lock screen 2 screenshots)
Mobile Networks in Settings
Roaming Menu
All Hotspot Menus (hotpsot, more)
Legal Information
Google Legal
Privacy Alerts (click proceed)
Messaging
Signature EMail - Yahoo Royals2406 royals06 (settings of email)dvtandctest/donotchange
Play Store - OEM Logo (No logo whne Wholesale and inactive)
Gallery

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
http://sprintdd.com/android/chameleon/

# adb shell input keyevent --longpress KEYCODE_L
"""
import subprocess
import time
import os
import csv
from chamcodes import dial_codes, carriers
from psycon import iconograph
from blobs import scry


def ask(cmd_str):
    """ run an adb command string, return the terminal text output as a list of lines"""
    return subprocess.run(cmd_str, stdout=subprocess.PIPE).stdout.decode("utf-8").split(os.linesep)


class Adb(object):
    """ return properly formatted 'adb' command strings for subprocess to call when multiple devices are hooked up.
        Instances provide a place to stick the unique data for each device"""
    def __init__(self, device):
        self.device = device
        self.msl = None
        self.boiler_plate = ['adb', '-s', '{}'.format(device), 'wait-for-device']
        self.shell = self.boiler_plate + ['shell']
        self.android_id = self.shell + ['content', 'query' ' --uri',
                                        '\"content://settings/secure/android_id\"', '--projection', 'value']
        self.window = self.shell + ['dumpsys', 'window']
        self.pull = self.boiler_plate + ['pull']
        self.swipe_front = self.shell + ["input", "swipe"]
        self.tapper = self.shell + ["input", "touchscreen", "tap"]
        self.keyevent = self.shell + ["input", "keyevent"]
        self.back = self.keyevent + ["KEYCODE_BACK"]
        self.home = self.keyevent + ["KEYCODE_HOME"]
        self.hangup = self.keyevent + ["KEYCODE_ENDCALL"]
        self.getprop = self.shell + ["getprop"]
        self.mfgr = self.getprop + ["ro.product.manufacturer"]
        self.uri = self.shell + ['content', 'query' ' --uri', '\"content://settings/system/\"']
        self.display_density = None
        self.OEM = None
        self.alpha = None
        self.testplan = None
        self.MSL = None
        self.pic_paths = []
        self.gen = ()
        self.current_code = ""
        self.time_on = 0        # zero will turn on the execution of commands
        self.delay = 10         # seconds
        self.finished = False
        self.outputdir = os.path.join(os.getcwd(), "pics")
        self.icon_dir = os.path.join(os.getcwd(), "icons")
        if not os.path.exists(self.outputdir):
            os.mkdir(self.outputdir)
        if not os.path.exists(self.icon_dir):
            os.mkdir(self.icon_dir)
        print("Screenshot storage: {}".format(self.outputdir))
        print("Icon storage: {}".format(self.icon_dir))

    def swipe(self, x1, y1, x2, y2):
        """ inputs are ratios from zero to 1 of max screen dimension """
        xa = str(int(self.x_max * x1))
        ya = str(int(self.y_max * y1))
        xb = str(int(self.x_max * x2))
        yb = str(int(self.y_max * y2))
        return self.swipe_front + [xa, ya, xb, yb]

    def tap(self, x, y):
        """ x and y are screen coordinate integers """
        return self.tapper + [str(x), str(y)]

    def screenshot(self, pic_name):
        pic_path = "/sdcard/" + self.device + "_" + self.OEM + "_" + self.alpha[0] + "_" + pic_name
        self.pic_paths.append(pic_path)
        return self.shell + ["screencap", "-p", pic_path]

    def download(self, pic_name):
        """ note pic_name should have the device and OEM built into it's front """
        return self.pull + ["/sdcard/" + pic_name, self.outputdir]

    def pc_pics(self, keyword):
        localpic = [os.path.join(self.outputdir, fn.split("/")[-1]) for fn in cmd.pic_paths
                    if (keyword in fn) and (self.device in fn)]
        if len(localpic) > 1:
            print("Warning! Multiple pics include '{}' in dir: {}".format(keyword, self.outputdir))
            return []
        return localpic[0]

    def text(self, txt):
        return self.shell + ["input", "text", str(txt)]

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

    def display_config(self):
        if self.display_density is None:
            self.display_density = int(ask(self.getprop + ['ro.sf.lcd_density'])[0].strip())
            print("display density: {}".format(self.display_density))
        stuff = ask(self.window)
        for line in stuff:
            if ('mUnrestrictedScreen' in line) and ("Original" not in line):
                res = line.split(" ")[-1]
                x, y = res.split("x")
                self.x_max, self.y_max = int(x), int(y)
                print("x max, y max = ({}, {})".format(self.x_max, self.y_max))
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


def assign_msl(devices, msl_file="_msl.txt"):
    for device in devices:
        if not os.path.exists(device.icon_dir):
            os.mkdir(device.icon_dir)
        fn = os.path.join(device.icon_dir, device.device + msl_file)
        if os.path.exists(fn):
            with open(fn, "r") as fob:
                device.msl = fob.read().strip()
                print("msl for {} = {}".format(device.device, device.msl))
        if not device.msl:
            print("Please assign the correct MSL to this device: {}".format(device.device))
            homescreen(device)
            device.msl = str(input("(it should have just blinked on) : ").strip())
            try:
                int(device.msl)
                with open(fn, "w") as fob:
                    fob.write(device.msl)
            except ValueError:
                device.msl = None
                print("MSL should be all numeric digits. Try again!")
                assign_msl(devices, msl_file=msl_file)


def init_devices():
    """ initialize plugged-in devices and assign test plans """
    cmds = [Adb(device) for device in devicelist()]
    for num, cmd in enumerate(cmds):
        print("#{:3}            *********************  {}  **********************".format(num + 1, cmd.device))
        cmd.display_config()
        ask(cmd.home)
        cmd.OEM = ask(cmd.mfgr)[0].replace("\\r", "").replace("\r", "")
        print("OEM:      {}".format(cmd.OEM))
        cmd.alpha = [assign_carrier(j) for j in ask(cmd.getprop) if 'ro.home.operator' in j]
        if not cmd.alpha:
            cmd.alpha = ['NA']
        cmd.testplan = dial_codes['All'] + dial_codes[cmd.alpha[0]]
        print("Carrier: {}".format(cmd.alpha[0]))
        cmd.gen = (c for c in cmd.testplan)
    assign_msl(cmds)
    return cmds


def homescreen(cmd_instance):
    """ moves device interface to home start position """
    ask(cmd_instance.home)
    ask(cmd_instance.swipe(0.1, 0.8, 0.9, 0.8))     # swipe right
    ask(cmd_instance.home)
    time.sleep(0.8)


def download_all_pics(cmd_objects):
    """ gets all the pics from paths stored in each local device-instance.
    DOES NOT check the the actual device's storage areas! """
    for cmd_instance in cmd_objects:
        print("downloading pics for {} {}:".format(cmd_instance.OEM, cmd_instance.device))
        for path in cmd_instance.pic_paths:
            localname = path.split("/")[-1]
            print("-    {}".format(localname))
            ask(cmd_instance.download(localname))


def examine_screen(device, photo="temp.png"):
    """ find locations of text in a screen shot"""
    ask(device.screenshot(photo))
    pic_on_device_path = device.pic_paths[-1].split("/")[-1]
    ask(device.download(pic_on_device_path))
    print("obtaining {}".format(pic_on_device_path))
    time.sleep(1)
    print("download wait over, starting scry()...")
    return scry(os.path.join(device.outputdir, pic_on_device_path))


if __name__ == "__main__":
    cmds = init_devices()

    # home screens
    for cmd in cmds:
        ask(cmd.home)
        time.sleep(0.8)
        print("homefront {} {}".format(cmd.alpha, cmd.device))
        ask(cmd.screenshot("homefront.png"))
        homescreen(cmd)
        print("homescreen {} {}".format(cmd.alpha, cmd.device))
        ask(cmd.screenshot("homescreen.png"))

    # Notification Tray
    for cmd in cmds:
        print("Notification Tray for {} {}".format(cmd.alpha, cmd.device))
        homescreen(cmd)
        ask(cmd.swipe(0.5, 0.01, 0.5, 0.8))     # swipe down from top
        time.sleep(1)
        ask(cmd.screenshot("notificationtray.png"))

    # app tray
    for cmd in cmds:
        print("App Tray for {} {}".format(cmd.alpha, cmd.device))
        screen_fn = cmd.pc_pics("homescreen.png")
        icon_fn = os.path.join(cmd.icon_dir, 'apps_tiny.png')
        homescreen(cmd)
        x, y = iconograph(screen_fn, icon_fn, icon_source_size=(720, 1280), DEBUG=False)
        time.sleep(1)       # wait for home screen
        ask(cmd.tap(x, y))
        time.sleep(1)       # change screens
        for n in range(3):  # move it back to page 1
            ask(cmd.swipe(0.1, 0.8, 0.9, 0.8))
        for n in range(3):
            time.sleep(0.8)   # wait for app tray
            ask(cmd.screenshot("apptray-{}.png".format(n)))
            ask(cmd.swipe(0.9, 0.8, 0.1, 0.8))
        for n in range(3):  # move it back to page 1
            ask(cmd.swipe(0.1, 0.8, 0.9, 0.8))

    # playstore
    for cmd in cmds:
        print("playstore for {} {}".format(cmd.alpha, cmd.device))
        screen_fn = cmd.pc_pics("homescreen.png")
        icon_fn = os.path.join(cmd.icon_dir, 'playstore_tiny.png')
        homescreen(cmd)
        x, y = iconograph(screen_fn, icon_fn)
        ask(cmd.tap(x, y))
        time.sleep(3)
        texts = examine_screen(cmd)
        for t in texts:
            if "ACCEPT" in t.text:
                ask(cmd.tap(t.center_x, t.center_y))
                print("ACCEPT!!!")

        for t in texts:
            if "your account" in " ".join(t.text).lower():
                print("YAYAY")

    # download all pics
    download_all_pics(cmds)

"""
    # run ADCs and call-intercepts
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
"""