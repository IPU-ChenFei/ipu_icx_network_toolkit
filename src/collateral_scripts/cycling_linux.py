import pexpect
import re
import sys, time
from collections import OrderedDict

args = OrderedDict([arg.split('=') for arg in sys.argv[1:]])

print (args)
command = "./setupcycle.sh"
process = pexpect.spawnu(command, timeout=72000, encoding='utf-8')
process.logfile = sys.stdout

unexpected_expects = []
if args:
    for key, value in args.items():
        print ("Expecting: %s" % key)
        try:
            process.expect(key, timeout=30)
            time.sleep(1)
            process.send("%s\n" % value)
            print (process.before)
            print (process.after)
            time.sleep(1)
        except:
            unexpected_expects.append(key)
print(process.after)
for lin in process:
   print(lin)
if unexpected_expects:
    print ("unexpected expects: %s" % unexpected_expects)

process.close()
