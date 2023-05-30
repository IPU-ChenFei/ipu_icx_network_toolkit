"""
Wrapper for DTAF PTG - PCIe Traffic Generator
"""

import os
import sys
import random
import argparse
import subprocess
from time import sleep
import multiprocessing
from datetime import datetime

FASTPATH = "FP"
PHY = "PHY"
DP = "downstream_port"
RP = "root_port"

TEST_PATTERNS = [
    "rd96", "rd256", "rd512", "rd1024",
    "wr96", "wr256", "wr512", "wr1024",
    "rdwr96", "rdwr256", "rdwr512",  # "rdwr1024"
]

READ_PATTERNS = [
    "rd96", "rd256", "rd512", "rd1024",
]

WRITE_PATTERNS = [
    "wr8", "wr96", "wr256", "wr512",
]

PHY_DID = ["0d52"]
FP_DID = ["0501"]
DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "new_linear", "new_linear")


def main(image, vectors, ranged, tests, addr_offset, addr_diff, testpath, targets, iterations, test_duration, bw_file,
         sbr_flag, alltest_flag, bdf):
    if testpath and alltest_flag:
        all_files = os.listdir(testpath)
        tests = [test for test in all_files if test.endswith(".txt")]
    if not tests[0].endswith(".txt"):
        temp_tests = get_list(tests)
        tests = []
        for test in temp_tests:
            tests.append(f"{test}_linear-1.txt")
    procs = []
    if type(targets) == dict:
        for bus, info in targets.items():
            if info["image"] == FASTPATH:
                procs.append(multiprocessing.Process(target=execute_fp, args=(ranged, tests, addr_offset, addr_diff,
                                                                              bus, iterations, test_duration,
                                                                              bw_file, sbr_flag, testpath, bdf,)))
            elif info["image"] == PHY:
                procs.append(multiprocessing.Process(target=execute_phy, args=(vectors, tests[0], addr_offset, bus,
                                                                               test_duration, bw_file, testpath)))

    else:
        for target in targets:
            if image == FASTPATH:
                procs.append(multiprocessing.Process(target=execute_fp, args=(ranged, tests, addr_offset, addr_diff,
                                                                              target, iterations, test_duration,
                                                                              bw_file, sbr_flag, testpath, bdf,)))
            elif image == PHY:
                procs.append(multiprocessing.Process(target=execute_phy, args=(vectors, tests[0], addr_offset, target,
                                                                               test_duration, bw_file, testpath,)))

    print(f"{len(procs)} process(es) ready. Starting in 3 seconds.")
    sleep(3)

    for proc in procs:
        proc.start()
    print(f"{len(procs)} process(es) started..")
    sleep(1)

    print("Waiting for processes to complete..")
    for proc in procs:
        proc.join()


def execute_fp(ranged, tests, addr_offset, addr_diff, target, iterations, test_duration, bw_file, sbr_flag, testpath,
               bdf):
    address_range = [hex(addr_offset)]
    if ranged:
        for i in range(1, 11):
            addr1 = addr_offset + (addr_diff * i)
            address_range.append(hex(addr1))
            addr2 = addr_offset - (addr_diff * i)
            address_range.append(hex(addr2))
        print(f"Range of addresses to run test on: {address_range}")

    def _execute_fp():
        subprocess.run(command)

    def prepare(t):
        print(f"DEBUG 1 - {t}")
        test_file = os.path.join(testpath, t)
        if sbr_flag:
            perform_sbr(bdf)
        address = random.choice(address_range)
        c = f"./ptg5_beta5_static 1 {test_file} -A -E -a {address} -p 0x{target} -t {test_duration} -o {bw_file}"
        print(f"Executing command -> {c}")
        return c.split(" ")

    if iterations <= 0:
        while True:
            for test in tests:
                command = prepare(test)
                _execute_fp()
    else:
        for iteration in range(1, iterations + 1):
            test = random.choice(tests)
            print(f"Executing iteration# : {iteration}")
            command = prepare(test)
            _execute_fp()


def execute_phy(vectors, test, addr_offset, target, test_duration, bw_file, testpath):
    def _execute_phy():
        retval = subprocess.run(command.split())  # , stdout=logfile, stderr=logfile_e)
        return retval

    test_file = os.path.join(testpath, test)
    command = f"./ptg5_beta5_static {vectors} {test_file} {test_file} {test_file} {test_file} {test_file}" \
              f" {test_file} -A -E -a {hex(addr_offset)} -p 0x{target} -t {test_duration} -o {bw_file}"
    print(f"Executing command -> {command}")
    _execute_phy()
    sleep(test_duration)
    print("Test completed.")
    sys.exit(0)


def check_image(bdf):
    retval = subprocess.run(["setpci", "-s", bdf, "0x2.w"], stdout=subprocess.PIPE)
    retval = retval.stdout.decode().strip()
    for did in PHY_DID:
        if did == retval:
            return PHY
    for did in FP_DID:
        if did == retval:
            return FASTPATH

def detect_cards():
    """
    Returns the bus list in the format -
    key : "bus"
        value : key : "bdf"     - as seen in lspci. type - list
                key : "image"   - phy / fastpath
    """
    print("Detecting cards ...\n")
    bus_list = {}
    proc = subprocess.run(["lspci", "-d", f":{PHY_DID[0]}"], stdout=subprocess.PIPE)
    retval = proc.stdout.decode().strip()

    if retval == "":
        proc = subprocess.run(["lspci", "-d", f":{FP_DID[0]}"], stdout=subprocess.PIPE)
        retval = proc.stdout.decode().strip()

    if retval == "":
        raise Exception("Could not find any known card! Try adding bus number manually. Or update the script with "
                        "new DID")

    devices = retval.split('\n')
    for device in devices:
        bdf = device.split(' ')[0]
        if bdf.count(":") == 2:
            bus = bdf.split(":")[1]
        else:
            bus = bdf.split(":")[0]
        image = check_image(bdf)
        if bus not in bus_list.keys():
            bus_list[bus] = {"bdf": [bdf], "image": image}
        else:
            bus_list[bus]["bdf"].append(bdf)
    return bus_list


def perform_sbr(endpoint, silent=False):
    def clean_up(content):
        i = 0
        for i, l in enumerate(content):
            if l.isnumeric():
                break
        return content[i:].strip()

    def get_downstream_port(ep, target=None):
        if target is None:
            target = [DP, RP]
        dp = None
        retval = subprocess.run(["pcicrawler", "-t"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # I don't want to the whole big parse JSON :p Can check at later date if that actually helps in some way.
        dev_list = retval.stdout.decode().split("\n")[1:]
        n_minus_1_dev = None
        for i, device in enumerate(dev_list):
            if ep in device:
                dp = dev_list[i]
                for t in target:
                    if t in dp:
                        dp = dp.split()[0]
                        dp = clean_up(dp)
                        break

        if not dp:
            raise RuntimeError("Could not fetch port details.")
        return dp

    downstream_port = get_downstream_port(endpoint)
    print(f"Performing SBR on {endpoint}") if not silent else print()
    os.system(rf"setpci -s {downstream_port} 3E.b=0x43")
    sleep(1)
    os.system(rf"setpci -s {downstream_port} 3E.b=0x03;")
    sleep(2)
    cmd = "echo 1" + " > /sys/bus/pci/devices/" + "0000" + "\:" + endpoint.split(":")[0] + "\:" + \
          endpoint.split(":")[1].split(".")[0] + "." + endpoint.split(".")[1] + "/remove"
    os.system(cmd)
    os.system(r"echo 1 >/sys/bus/pci/rescan")
    os.system(rf"setpci -s {endpoint} 04.l=0x000001FF")
    print(f"SBR done on {endpoint}") if not silent else print()


def get_list(user_input):
    """
    Helper function.
    Used for -
        1. Creating list of test filenames.
        2. Bus list from string format.
    """
    # For test filenames.
    if user_input == "all":
        tests = []
        for test in TEST_PATTERNS:
            for i in range(1, 11, 1):
                tests.append(f"{test}_linear-{i}.txt")
        return tests
    # Just split user_input and return as list.
    elif type(user_input) is str:
        if "," in user_input:
            user_input = user_input.split(",")
        else:
            user_input = [user_input]
    return user_input

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DTAF PTG WRAPPER")
    parser.add_argument("-f", "--fastpath", action="store_true")
    parser.add_argument("-p", "--phy", action="store_true")
    parser.add_argument("--vm", default=1, help="Enter 1 for FP and up to 6 for PHY")
    parser.add_argument("-a", "--address", default="0x400000000")
    parser.add_argument("-r", "--ranged", action="store_true")
    parser.add_argument("-d", "--diff", default="0x10000000")
    parser.add_argument("-t", "--test", default=TEST_PATTERNS)
    parser.add_argument("-ta", "--testall", action="store_true")
    parser.add_argument("-tp", "--testpath", default=DEFAULT_PATH, help="Override default test files folder")
    parser.add_argument("-b", "--bus")
    parser.add_argument("-i", "--iterations", default=1)
    parser.add_argument("-s", "--seconds", default=10, help="Time in seconds to run each iteration")
    parser.add_argument("-sbr", "--sbr", action="store_true", help="Requires --bdf argument.")
    parser.add_argument("-bdf", "--bdf", help="Used in executing SBR.")
    _output_file = f"py_ptg_bw_" \
                   f"{str(datetime.now()).replace('-', '_').replace(' ', '_').replace('.', '_').replace(':', '_')}.log"
    parser.add_argument("-o", "--output", default=_output_file)

    _image = None
    args = parser.parse_args()
    if args.fastpath:
        _image = FASTPATH
    elif args.phy:
        _image = PHY

    if args.testpath != DEFAULT_PATH:
        if not os.path.exists(args.testpath):
            raise NotADirectoryError(f"Invalid path - {args.testpath}")

    if args.bus == "auto":
        _b = detect_cards()
    else:
        _b = get_list(args.bus)

    main(image=_image, vectors=int(args.vm), ranged=args.ranged, tests=args.test, addr_offset=int(args.address, 16),
         addr_diff=int(args.diff, 16), testpath=args.testpath, targets=_b, iterations=int(args.iterations),
         test_duration=args.seconds, bw_file=args.output, sbr_flag=args.sbr, alltest_flag=args.testall, bdf=args.bdf)
