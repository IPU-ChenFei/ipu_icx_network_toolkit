import pexpect
import re
import sys, time
from collections import OrderedDict

if sys.argv[1].split('=')[0] == "cmd":
    args = OrderedDict([arg.split('=') for arg in sys.argv[2:]])
    command = sys.argv[1].split('=',1)[1]
else:
    args = OrderedDict([arg.split('=') for arg in sys.argv[1:]])
    command = "./mprime -m"

if not args:
   raise Exception('not enough arguments. Example python script.py "question"="answer" "question"="answer"..')

_REGEX_ERR = "Torture Test completed \d+ tests in .* - 0 errors, 0 warnings."

print (args)
if not args:
    command = "./mprime -t"
    print("Assuming torture test with default config")
process = pexpect.spawnu(command, timeout=72000, encoding='utf-8')
process.logfile = sys.stdout
print (process.before)
print (process.after)

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

if unexpected_expects:
    print ("unexpected expects: %s" % unexpected_expects)

successful_tests = []
tests_status = []
for line in process:
    #try:
    #    line = line.rstrip().decode("utf-8").strip()
    #except Exception as e:
    #    print("message parse error: %s" % str(e))
    if "Torture Test completed " in line.strip():
        tests_status.append(line.strip())
    if re.search(_REGEX_ERR, line.strip()):
        successful_tests.append(line.strip())

print ("Tests status: %s" % tests_status)
print ("Successful tests: %s" % successful_tests)

process.close()
print(process.exitstatus, process.signalstatus)
