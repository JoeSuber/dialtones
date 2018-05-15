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

http://adbshell.com/commands

"""

import subprocess
import time
import os
from chamcodes import dial_codes, carriers
from psycon import iconograph
from blobs import scry
import cv2

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
        self.lb_data = self.keyevent + ["KEYCODE_POUND", "KEYCODE_POUND", "KEYCODE_3", "KEYCODE_2",
                                        "KEYCODE_8", "KEYCODE_2", "KEYCODE_POUND"]
        self.lb_diag = self.keyevent + ["KEYCODE_POUND", "KEYCODE_POUND", "KEYCODE_3", "KEYCODE_4",
                                        "KEYCODE_2", "KEYCODE_4", "KEYCODE_POUND"]
        self.longpress1 = self.keyevent + ["--longpress", "KEYCODE_1", "KEYCODE_1", "KEYCODE_1", "KEYCODE_1", "KEYCODE_1"]
        self.dialpad = self.shell + ["am", "start", "-a", "android.intent.action.DIAL"]
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

    def swipe(self, x1, y1, x2, y2, delay=None):
        """ inputs are ratios from zero to 1 of max screen dimension """
        if delay is None:
            delay = ""
        else:
            delay = str(int(delay))
        xa = str(int(self.x_max * x1))
        ya = str(int(self.y_max * y1))
        xb = str(int(self.x_max * x2))
        yb = str(int(self.y_max * y2))
        return self.swipe_front + [xa, ya, xb, yb, delay]

    def tap(self, x, y):
        """ x and y are screen coordinate integers """
        return self.tapper + [str(x), str(y)]

    def screenshot(self, pic_name):
        pic_path = "/sdcard/" + self.device + "_" + self.OEM + "_" + self.alpha[0] + "_" + pic_name
        self.pic_paths.append(pic_path)
        return self.shell + ["screencap", "-p", pic_path]

    def download(self, pic_name):
        """ note pic_name should have the device and OEM built into it's front """
        return self.pull + ["/sdcard/" + self.device + "_" + self.OEM + "_" + self.alpha[0] + "_" + pic_name,
                            self.outputdir]

    def pc_pics(self, keyword):
        localpic = [os.path.join(self.outputdir, fn.split("/")[-1]) for fn in self.pic_paths
                    if (keyword in fn) and (self.device in fn)]
        return localpic[0]

    def text(self, txt):
        return self.shell + ["input", "text", str(txt)]

    def dial(self, code):
        return self.shell + ["am", "start", "-a", "android.intent.action.CALL", "-d", "tel:{}".format(code)]

    def no_dial(self, code):
        return self.shell + ["service", "call", "phone", "1", "s16", "{}".format(code)]

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


def get_email_info(acct_name="testing_email_info.txt"):
    email_path = os.path.join(os.getcwd(), acct_name)
    if os.path.exists(email_path):
        with open(email_path, "r") as efob:
            email, password = efob.readline().split("::")
        return email, password
    print("*>*>*>*>*  Test Email Account Needed!  *<*<*<*<*<*<")
    email = input("Please input the full email account for testing: ")
    password = input("Please input the password for this account: ")
    print("\n Thank you. If you need to change it, delete this file--> {}".format(email_path))
    with open(email_path, "w") as efob:
        efob.write(email + "::" + password)
    return email, password


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
    time.sleep(0.5)


def download_all_pics(cmd_instance):
    """ gets all the pics from paths stored in local device-instance.
    DOES NOT check the the actual device's storage areas! """
    print("downloading pics for {} {}:".format(cmd_instance.OEM, cmd_instance.device))
    for path in cmd_instance.pic_paths:
        print(path)
        localname = path.split("/")[-1]
        print("-    {}".format(localname))
        ask(cmd_instance.download(localname))


def examine_screen(device, searched_for_text, photo="temp.png", DEBUG=False):
    """ find location of a particular bit of text in a screen shot"""
    ask(device.screenshot(photo))
    pic_on_device_path = device.pic_paths[-1].split("/")[-1]
    ask(device.download(pic_on_device_path))
    time.sleep(0.8)
    texts = scry(os.path.join(device.outputdir, pic_on_device_path))
    for t in texts:
        if DEBUG: print(t.text)
        if searched_for_text in " ".join(t.text):
            return t.center_x, t.center_y
    print("'{}' not found on {}".format(searched_for_text, device.device))
    return None, None

##################################################
###########  Scripts for Chameleon ###############
##################################################
if __name__ == "__main__":
    cmds = init_devices()
    email, password = get_email_info()

    for dev in cmds:
        print("Working on Device: {}".format(dev.device))
        ask(dev.home)
        time.sleep(0.5)

        print("lockscreen {} {}".format(dev.alpha, dev.device))
        ask(dev.screenshot("lockscreen.png"))
        ask(dev.download("lockscreen.png"))

        print("homescreen {} {}".format(dev.alpha, dev.device))
        homescreen(dev)
        ask(dev.swipe(0.2, 0.8, 0.9, 0.8))
        ask(dev.screenshot("homescreen.png"))
        ask(dev.download("homescreen.png"))

        print("Notification Tray for {} {}".format(dev.alpha, dev.device))
        homescreen(dev)
        ask(dev.swipe(0.5, 0.01, 0.5, 0.8))     # swipe down from top
        time.sleep(1)
        ask(dev.screenshot("notificationtray.png"))
        ask(dev.download("notificationtray.png"))

        ###   app tray   ###
        print("App Tray for {} {}".format(dev.alpha, dev.device))
        screen_fn = dev.pc_pics("homescreen.png")
        homescreen(dev)
        print("checking local pic:  {}".format(screen_fn))
        icon_fn = os.path.join(dev.icon_dir, 'apps_tiny.png')
        x, y = iconograph(screen_fn, icon_fn, icon_source_size=(720, 1280), DEBUG=False)
        time.sleep(1)       # wait for home screen
        ask(dev.tap(x, y))
        time.sleep(1)       # change screens
        for n in range(3):  # move it back to page 1
            ask(dev.swipe(0.1, 0.8, 0.9, 0.8))
        for n in range(3):
            time.sleep(0.4)   # wait for app tray
            ask(dev.screenshot("apptray-{}.png".format(n)))
            ask(dev.download("apptray-{}.png".format(n)))
            ask(dev.swipe(0.9, 0.8, 0.1, 0.8))
        for n in range(3):  # move it back to page 1
            ask(dev.swipe(0.1, 0.8, 0.9, 0.8))


        ###   CONTACTS   ###
        print("## Contacts ##")
        homescreen(dev)
        print("looking for 'Messages'")
        x, y = examine_screen(dev, "Messages", photo="homescreen.png")
        if (x is None) or (y is None):
            print("!!! device {} is lacking a 'Messages' button! breaking !!!")
            homescreen(dev)
            exit(1)
        ask(dev.tap(x, y))
        time.sleep(1.5)
        print(" -- first contact screen...")
        ask(dev.screenshot("msg_contacts.png"))
        ask(dev.download("msg_contacts.png"))
        x, y = examine_screen(dev, "CONTACTS", photo="msg_contacts.png")
        if x and y:
            ask(dev.tap(x, y))
        print(" -- target contact screen")
        ask(dev.screenshot("Contacts.png"))
        ask(dev.download("Contacts.png"))
        time.sleep(1)

        ###   playstore   ###
        homescreen(dev)
        print("## Playstore ##")
        print("playstore for {} {}".format(dev.alpha, dev.device))
        x, y = examine_screen(dev, "Play", photo="homescreen.png", DEBUG=True)
        if x is not None:
            ask(dev.tap(x, y))
            print("waiting for playstore icon press...")
            time.sleep(2)
            ask(dev.screenshot("google_app_store.png"))
            ask(dev.download("google_app_store.png"))
            time.sleep(0.5)
        else:
            print("No Play Store button found! stopping!")
            exit(1)
        print("looking for APPS, as if acct already active")
        x, y = examine_screen(dev, "APPS", photo="google_app_store.png")
        if x is not None:
            ask(dev.tap(x, y))
        else:
            print("No APPS found")
            print("signing in using email and pass")
            ask(dev.screenshot("accept.png"))
            ask(dev.download("accept.png"))
            print("looking for email blank")
            x, y = examine_screen(dev, "Email", photo="accept.png")
            if x is not None:
                print("entering email: {}".format(email))
                ask(dev.tap(x, y))
                ask(dev.text(email))
                ask(dev.enter_key())
                print("waiting for password screen")
                time.sleep(2.3)
                # password entry
                ask(dev.screenshot("password.png"))
                ask(dev.download("password.png"))
                print("looking for 'Password'")
                x, y = examine_screen(dev, "Password", photo="password.png")
                if x is not None:
                    print("entering password")
                    ask(dev.tap(x, y))
                    ask(dev.text(password))
                    ask(dev.enter_key())
                    time.sleep(2)
                else:
                    print("No password blank found")
                    exit(1)
                print("looking for ACCEPT to go on to store")
                ask(dev.screenshot("pass_accept.png"))
                ask(dev.download("pass_accept.png"))
                x, y = examine_screen(dev, "ACCEPT", photo="pass_accept.png", DEBUG=True)
                if x is not None:
                    print("tapping 'ACCEPT'")
                    ask(dev.tap(x, y))
                    time.sleep(3.6)
                else:
                    print("No 'ACCEPT' button after password entry!")
                print("looking for Google Services screen")
                ask(dev.screenshot("google_services.png"))
                ask(dev.download("google_services.png"))
                x, y = examine_screen(dev, "Services", photo="pass_accept.png", DEBUG=True)
                if x is not None:
                    print("Services found.")
                    ask(dev.swipe(0.95, 0.95, 0.97, 0.97 ))
                    time.sleep(1)
                print("looking for NEXT to go on to store")
                ask(dev.screenshot("pass_next.png"))
                ask(dev.download("pass_next.png"))
                x, y = examine_screen(dev, "NEXT", photo="pass_nextaccept.png", DEBUG=True)
                if x is not None:
                    print("tapping 'NEXT'")
                    ask(dev.tap(x, y))
                    time.sleep(2)
                else:
                    print("No 'NEXT' button after password entry!")
        print("waiting for appstore to appear")
        time.sleep(2)
        ask(dev.screenshot("appstore.png"))
        ask(dev.download("appstore.png"))

        ###  Hotspot, Tethering, Network, Legal Info Screens  ###
        print("## Hotspot, Tethering, Network, Legal Info,  ##")
        print("Hotspot, Tethering Network & Legal info for {} {}".format(dev.alpha, dev.device))
        homescreen(dev)
        print("swipe down")
        ask(dev.swipe(0.5, 0.01, 0.5, 0.8)) #swipe down the app tray
        icon_fn = os.path.join(dev.icon_dir, 'gear_tiny.png')
        time.sleep(0.5)
        print("finding gear icon")
        ask(dev.screenshot("gear.png"))
        ask(dev.download("gear.png"))
        screen_fn = dev.pc_pics("gear.png")
        print(screen_fn)
        time.sleep(2)
        x, y = iconograph(screen_fn, icon_fn, icon_source_size=(720, 1280), DEBUG=False)
        ask(dev.tap(x, y))
        time.sleep(0.7)
        print("tapped 'gear' at: x={}, y={}".format(x,y))
        ask(dev.screenshot("gear.png"))
        ask(dev.download("gear.png"))

        print("looking for 'Connections' on menu")
        x, y = examine_screen(dev, "Connections", photo="gear.png")
        if x is not None:
            ask(dev.tap(x,y))
            print("tapped 'Connections")
            time.sleep(0.7)
            ask(dev.screenshot("Connections.png"))
            ask(dev.download("Connections.png"))
            ask(dev.back)
        else:
            print("no 'Connections' menu item found ")
        time.sleep(0.7)
        print("looking for 'Hotspot' on menu")
        x, y = examine_screen(dev, "Hotspot", photo="gear.png")
        if x is not None:
            ask(dev.tap(x,y))
            print("tapped 'Hotspot")
            time.sleep(0.7)
            ask(dev.screenshot("Hotspot.png"))
            ask(dev.download("Hotspot.png"))
            ask(dev.back)
        else:
            print("no 'Hotspot' menu item found ")

        print("swipeing down ")
        ask(dev.swipe(0.5, 0.8, 0.5, 0.1))
        ask(dev.screenshot("about_device.png"))
        ask(dev.download("about_device.png"))
        x, y = examine_screen(dev, "About", photo="about_device.png")
        if x is None:
            print("looking for 'About' 2nd time, now below swipe")
            ask(dev.swipe(0.5, 0.1, 0.5, 0.8))
            ask(dev.screenshot("about_device.png"))
            ask(dev.download("about_device.png"))
            x, y = examine_screen(dev, "About", photo="about_device.png")
        print("'About device' at: {}, {}".format(x,y))
        if x is not None:
            print("tapping {}, {}".format(x, y))
            ask(dev.tap(x, y))
        else:
            print("About Device not found!!!!")
        print("---waiting for legal info tap to materialize----")
        time.sleep(2)
        ask(dev.screenshot("legal_info.png"))
        ask(dev.download("legal_info.png"))
        x, y = examine_screen(dev, "Legal", photo="legal_info.png", DEBUG=True)
        if x is not None:
            print("tapping 'Legal'")
            ask(dev.tap(x, y))
            time.sleep(1)
        else:
            print("Legal information not found!!!")
        print("--privacy--")
        ask(dev.screenshot("privacy.png"))
        ask(dev.download("privacy.png"))
        x, y = examine_screen(dev, "Privacy", photo="privacy.png", DEBUG=True)
        if x is not None:
            ask(dev.tap(x, y))
            time.sleep(1)
        else:
            print("Privacy Alert not found!!!! stopping!")
            exit(1)
        ask(dev.screenshot("privacy_proceed.png"))
        ask(dev.download("privacy_proceed.png"))
        x, y = examine_screen(dev, "PROCEED", photo="privacy_proceed.png", DEBUG=True)
        if x is not None:
            print("tapping Proceed")
            ask(dev.tap(x, y))
            time.sleep(0.5)
        else:
            print("privacy 'PROCEED' not found!!!")
        print("taking privacy alert screenshot1")
        ask(dev.screenshot("privacy_alert_p1.png"))
        ask(dev.download("privacy_alert_p1.png"))
        ask(dev.swipe(0.5, 0.8, 0.5, 0.1))
        time.sleep(0.5)
        print("taking privacy alert screenshot2")
        ask(dev.screenshot("privacy_alert_p2.png"))
        ask(dev.download("privacy_alert_p2.png"))
        time.sleep(0.5)
        x, y = examine_screen(dev, "OK", photo="privacy_alert_p2.png", DEBUG=True)
        if x is not None:
            print("tapping 'OK' on privacy alert")
            ask(dev.tap(x, y))
        else:
            print("couldn't find 'OK' on legal privacy screen!!!")
        print("going back to home")
        homescreen(dev)


        ###    ##3282# -> View -> MMSC -> URL, Proxy, Proxy Port   ###
        print("##3282# -> View -> MMSC -> URL, Proxy, Proxy Port")
        ask(dev.dialpad)
        time.sleep(0.6)
        print("keying in ##DATA#")
        ask(dev.lb_data)
        time.sleep(1.6)
        ask(dev.screenshot("MMSC_view.png"))
        ask(dev.download("MMSC_view.png"))
        time.sleep(0.5)
        print("looking for MMSC-View")
        x, y = examine_screen(dev, "View", photo="MMSC_view.png", DEBUG=True)
        if x is not None:
            print("tapping MMSC-View")
            ask(dev.tap(x,y))
        else:
            print("NO MMSC-View! exiting")
            exit(1)
        time.sleep(0.5)
        print("taking mmsc screenshot")
        ask(dev.screenshot("MMSC_mmsc.png"))
        ask(dev.download("MMSC_mmsc.png"))
        time.sleep(0.5)
        x, y = examine_screen(dev, "MSL", photo="MMSC_mmsc.png", DEBUG=True)
        #if x is not None:
        #    print("entering MSL {}".format(dev.msl))
        #    ask(dev.text("{}".format(dev.msl)))
        #    ask(dev.tap(167, 358))
        #    time.sleep(0.6)
        #else:
        #   print("'MSL' not found, maybe no MSL entry opportunity?")
        ask(dev.screenshot("MMSC_mmsc2.png"))
        ask(dev.download("MMSC_mmsc2.png"))
        print("looking for 'MMSC'")
        x, y = examine_screen(dev, "MMSC", photo="MMSC_mmsc2.png", DEBUG=True)
        if x is not None:
            print("tapping MMSC")
            ask(dev.tap(x,y))
        else:
            print("NO 'MMSC' found, exiting")
            exit(1)
        time.sleep(0.5)
        ask(dev.screenshot("MMSC_info.png"))
        ask(dev.download("MMSC_info.png"))
        time.sleep(0.5)
        print("looking for MMSC final menu items")
        highx, highy = examine_screen(dev, "URL", photo="MMSC_info.png", DEBUG=True)
        lowx, lowy = examine_screen(dev, "Port", photo="MMSC_info.png", DEBUG=True)
        if not all([highy, lowy]):
            print("WARNING NOT ALL MMSC MENU SPOTS FOUND")
            midx, midy = 40, None
        else:
            midx = int((lowx + highx) / 2)
            midy = int((lowy + highy) / 2)
        print("highy = {}, midy = {}, lowy = {}".format(highy, midy, lowy))
        print("taking screen shots of MMSC menu items")
        ask(dev.tap(highx, highy))
        time.sleep(0.5)
        print("url")
        ask(dev.screenshot("MMSC_url.png"))
        ask(dev.download("MMSC_url.png"))
        ask(dev.back)
        time.sleep(0.5)
        ask(dev.tap(midx, midy))
        time.sleep(0.5)
        print("gateway")
        ask(dev.screenshot("MMSC_proxygateway.png"))
        ask(dev.download("MMSC_proxygateway.png"))
        ask(dev.back)
        time.sleep(0.5)
        ask(dev.tap(lowx, lowy))
        time.sleep(0.5)
        print("port")
        ask(dev.screenshot("MMSC_proxyport.png"))
        ask(dev.download("MMSC_proxyport.png"))
        ask(dev.back)
        ask(dev.back)
        ask(dev.back)
        ask(dev.back)
        homescreen(dev)
        time.sleep(1)
        print("MMSC items DONE!")

        ###    ##DIAG# & MSL entry   ###
        print("###  ##DIAG# & MSL entry")
        ask(dev.dialpad)
        time.sleep(0.5)
        ask(dev.lb_diag)
        time.sleep(2)
        ask(dev.screenshot("DIAG_view.png"))
        ask(dev.download("DIAG_view.png"))
        time.sleep(0.5)
        x, y = 167, 358 ## hack for 'OK'
        print("entering MSL {}".format(dev.msl))
        ask(dev.text("{}".format(dev.msl)))
        ask(dev.tap(x,y))
        time.sleep(0.9)
        ask(dev.screenshot("DIAG_msl.png"))
        ask(dev.download("DIAG_msl.png"))
        time.sleep(0.5)

        ###   Call Intercept  dial 1 for Voicemail? ###
        print("###   call intercept, voicemail #### ")
        homescreen(dev)
        ask(dev.dialpad)
        time.sleep(0.7)
        ask(dev.screenshot("dialpad.png"))
        ask(dev.download("dialpad.png"))
        ask(dev.longpress1)
        time.sleep(2)
        print("taking screenshots of voicemail call inprogress")
        ask(dev.screenshot("voicemail.png"))
        ask(dev.download("voicemail.png"))
        ask(dev.hangup)


        print("############ Finished ###################")
        print("#####    {}    ########".format(dev.device))
        print("#########################################")
        exit(1)


