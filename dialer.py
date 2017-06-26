import subprocess
import time
import sys
import re
import os

"""Use android debugger to dial phones and hang them up.
    This is for saving some time in the device testing process.
    (assumes android debugger is available) 
    
    https://forum.xda-developers.com/showthread.php?t=2141817
    http://www.linuxtopia.org/online_books/android/devguide/guide/developing/tools/android_adb_commandsummary.html
    
    "%23" == "#" in strings
    """

class Dialer(object):
    """ init with quantity of dial tests and duration of call"""

    def __init__(self, reps=10, duration=35, timeout=20, callers=None, logbook=None):
        self.devices = self.devicelist()
        self.phonebook = dict()
        self.repetitions = reps
        self.duration = duration
        self.timeout = timeout
        self.callers = callers
        self.log_fn = logbook or os.path.join(os.getcwd(), "logbook.txt")
        self.current_caller = None

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

    def teardown_call(self, hangups, wait=6):
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
        print(" fin ")

    def call(self):
        """ needs to log results
        1) 20 second no pickup
        2) successful call-pickup-listen-hangup
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
                    print('*** Begin call {}  to device {} ***'.format(self.repetitions - countdown, callee))
                    subprocess.call(
                        'adb -s {} wait-for-device shell am start -a android.intent.action.CALL -d tel:{}'.format(
                            caller, phone_number), shell=True)
                    self.call_found, self.call_answered = False, False
                    for i in range(self.duration, 0, -1):  # caller will maintain call for duration
                        sys.stdout.write("\r")
                        sys.stdout.write("{:2d}".format(i))
                        sys.stdout.flush()
                        time.sleep(1)
                        if not self.call_found:
                            self.call_found = self.lookforcall(callee)
                            if i < (self.duration - self.timeout):
                                print(" Call Timeout expired! device {} failed to call {}".format(caller, callee))
                        if self.call_found and (not self.call_answered):
                            self.answer_call(callee)
                            self.call_answered = True

                    self.teardown_call([caller, callee])
        print("Finished the call list!")

    def lookforcall(self, device):
        cmds = ['adb', '-s', '{}'.format(device), 'wait-for-device', 'shell', 'dumpsys', 'telephony.registry']
        blather = subprocess.run(cmds, stdout=subprocess.PIPE).stdout.decode("utf-8")
        incoming = [i for i in blather.split(os.linesep) if 'mCallIncomingNumber' in i][0].split('=')
        if len(incoming[1]) > 6:
            print("  incoming on {} device: {}".format(device, incoming))
            return incoming[1]
        return False

    def answer_call(self, device):
        subprocess.call('adb -s {} wait-for-device shell input keyevent KEYCODE_CALL'.format(device), shell=True)
        print(" device {} answers".format(device))

# main
if __name__ == "__main__":
    dialup = Dialer()
    dialup.obtain_number()
    dialup.call()
