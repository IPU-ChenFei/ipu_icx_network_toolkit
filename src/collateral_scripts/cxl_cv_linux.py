# will be copied to /root/cxl_cv-0.1.0-Linux/cxl_cv-0.1.0-Linux/bin/cxl_cv_linux.py
#######################################################################################################################
# This file triggers CXL_CV_CLI app.
# Select the cxl device for the given bdf
# select the given test numbers
# run the selected test
# return the json file output
#######################################################################################################################
import pexpect
import re
import sys, time
import os
import glob


args = sys.argv
print(args)
if not args:
   raise Exception('not enough arguments. Example python script.py "value" "value" "value"............')
command = "./CXL_CV_CLI"

process = pexpect.spawnu(command, timeout=72000, encoding='utf-8')
process.logfile = sys.stdout
print(process.before)
print(process.after)
process.expect("CXL Compliance", timeout=30)
time.sleep(1)
process.send("%s\n" % "lscxl")
time.sleep(1)
process.expect("CXL Compliance", timeout=30)
time.sleep(1)
print(process.before)
output = process.before
regex_output=re.findall("(\d+)\s+{}\d+[0]".format(args[1]), output)
if not regex_output:
   process.send("%s\n" % "add_device {}:00.0".format(args[1][2:]))
   time.sleep(2)
   process.expect("CXL Compliance", timeout=30)
   time.sleep(1)
   print(process.before)
   output = process.before
   regex_output = re.findall("(\d+)\s+{}\d+[0]".format(args[1]), output)
   if not regex_output:
      raise Exception("CXL device not listed in the tool even after adding it manually")
print("{} cxl device is at {}".format(args[1], regex_output[0]))
process.send("%s\n" % "select_device {}".format(regex_output[0]))
time.sleep(2)
process.send("%s\n" % "select_test {}".format(args[2]))
time.sleep(2)
process.send("%s\n" % "run_selected")
time.sleep(60)
process.expect("CXL Compliance", timeout=30)
print(process.before)
print(process.after)
process.send("%s\n" % "exit")
time.sleep(2)
process.close()
print(process.exitstatus, process.signalstatus)

list_of_files = glob.glob('./*.json') # * means all if need specific format then *.csv
latest_file = max(list_of_files, key=os.path.getctime)
print("latest file - \n{}".format(latest_file))
