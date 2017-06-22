import subprocess
import time
import sys
import re
import os, codecs

"""Use android debugger to dial phones and hang them up.
    This is for saving some time in the device testing process.
    (assumes android debugger is available) 

    http://www.linuxtopia.org/online_books/android/devguide/guide/developing/tools/android_adb_commandsummary.html
    """


class Dialer(object):
    """ init with quantity of dial tests and duration of call"""

    def __init__(self, reps=10, duration=35, callers=None):
        self.devices = self.devicelist()
        self.phonebook = dict()
        self.repetitions = reps
        self.duration = duration
        self.callers = callers
        self.log_fn = os.path.join(os.getcwd(), "logcat.txt")

    def devicelist(self):
        """ return a list of device codes for the usb-plugged-in devices
         in the order they are given by calling 'adb devices' """
        raw = subprocess.run(["adb", "devices"], stdout=subprocess.PIPE).stdout.decode("utf-8").split(os.linesep)[1:]
        return [entry.split('\t')[0] for entry in raw if "\t" in entry]

    def obtain_number(self):
        """ user manually puts in dut phone numbers """
        print("{} device{} plugged in and registered with Android debugger.".format(len(self.devices),
                                                                                    " is" if len(
                                                                                        self.devices) == 1 else "s are"))
        print("Put in phone numbers for the devices below.\n "
              "Leave blank the single device you want to place all the calls,\n"
              "or, to make all the devices call each other, give them all valid phone numbers.")
        for device in self.devices:
            if len(device) > 3:  # ignore the stray linefeeds and tabs, keep the device serial numbers
                self.phonebook[device] = input("{}: ".format(device)).strip().replace("-", "").replace(".", "")
                entry_len = len(self.phonebook[device])
                if (entry_len > 11) or len(re.findall(r'\D', self.phonebook[device])):
                    print("The above does not appear to be a valid phone number: {}".format(self.phonebook[device]))
                    print(" ----  starting over -------")
                    self.obtain_number()
                    break
        return 1

    def assign_callers(self):
        for device, phone_number in self.phonebook.items():
            if phone_number is "":
                return [device]
        return self.phonebook.keys()

    def teardown_call(self, hangups, wait=5):
        """ hangups is a list of serial-ids to send the hangup message to via adb  """
        if type(hangups) is not list:
            hangups = list((hangups,))
        sys.stdout.write("\r")
        for device in hangups:
            subprocess.call('adb -s {} wait-for-device shell input keyevent KEYCODE_ENDCALL'.format(device), shell=True)
        for j in range(wait, 0, -1):
            sys.stdout.write("\r")
            sys.stdout.write("Call teardown:{:2d}".format(j))
            sys.stdout.flush()
            time.sleep(1)

    def operate_callee(self, id, seconds_to_go):
        """ check the phone to see if it should answer """
        call_keeps_going = True
        print("opening logfile")
        with open(self.log_fn, "w") as logfob:
            logfob.write(subprocess.run(['adb', '-s {}'.format(id), 'wait-for-device', 'logcat', 'InCall:I', '*:S']))
        print("logfile closed")
        # check status for active call
        # if not active call check for incoming call
        # if incoming call, answer
        # if active call, check seconds_to_go
        return call_keeps_going

    def call(self):
        """ needs to log results 1) 20 second no pickup 2) successful call-pickup-listen-hangup
        3) failure to ring  --  bonus! record gps of failure!
        $ adb shell dumpsys <service> """
        if self.callers is None:
            self.callers = self.assign_callers()
        for caller in self.callers:
            for callee, phone_number in self.phonebook.items():
                if caller == callee:
                    continue
                countdown = self.repetitions
                while countdown:
                    countdown -= 1
                    print('Begin call {}  to device {}'.format(self.repetitions - countdown, callee))
                    subprocess.call(
                        'adb -s {} wait-for-device shell am start -a android.intent.action.CALL -d tel:{}'.format(
                            caller, phone_number), shell=True)
                    for i in range(self.duration, 0, -1):  # caller will maintain call for duration
                        sys.stdout.write("\r")
                        sys.stdout.write("{:2d}".format(i))
                        sys.stdout.flush()
                        # if
                        time.sleep(1)
                        if not self.operate_callee(callee, i):
                            break
                    self.teardown_call([caller, callee])
        print("Finished the call list!")


def dumpty():
    """ for parsing this dang logcat file generated with 'adb logcat > adblogcat.txt' """
    with codecs.open("C:\\Users\\2053_HSUF\\Desktop\\adblogcat.txt", 'rU', 'utf-16') as fob:
        for linenum, line in enumerate(fob.readlines()):
            parts = line.strip().split(":")
            try:
                print(linenum, " : ", parts[2].split(' ')[-1])
            except:
                print("badline_____________________")


# main
if __name__ == "__main__":
    dialup = Dialer()
    dialup.obtain_number()
    dialup.call()
