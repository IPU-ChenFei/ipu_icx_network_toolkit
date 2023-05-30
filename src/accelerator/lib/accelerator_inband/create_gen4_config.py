#!/usr/bin/env python3

# description : This script helps to generate 4xxx config file
#=============================================================
# History
# 1.0.0 : [Alan] Initial Implimentation
# 1.0.1 : [Vijay] Extended to support both PF and VF config
#         for host usage
# 1.0.2 : [Vijay] Adds support for Adi Instances and handling
#         service types
# 1.0.3 : [Vijay] Adds support for poll and process handling

__version__ = '1.0.3'

import argparse
import re

HEADER_HOST_PF = """[GENERAL]
ServicesEnabled = {0}

ConfigVersion = 2

#Default value for FW Auth loading
FirmwareAuthEnabled = 1

#Default values for number of concurrent requests*/
CyNumConcurrentSymRequests = 512
CyNumConcurrentAsymRequests = 64

#Statistics, valid values: 1,0
statsGeneral = 1
statsDh = 1
statsDrbg = 1
statsDsa = 1
statsEcc = 1
statsKeyGen = 1
statsDc = 1
statsLn = 1
statsPrime = 1
statsRsa = 1
statsSym = 1


# Disable public key crypto and prime number
# services by specifying a value of 1 (default is 0)
PkeServiceDisabled = 0

# This flag is to enable device auto reset on heartbeat error
AutoResetOnError = 0

# Default value for power management idle interrrupt delay
PmIdleInterruptDelay = 0

# This flag is to enable power management idle support
PmIdleSupport = 0

# This flag is to enable key protection technology
KptEnabled = 1

# Define the maximum SWK count per function can have
# Default value is 1, the maximum value is 128
KptMaxSWKPerFn = 1

# Define the maximum SWK count per pasid can have
# Default value is 1, the maximum value is 128
KptMaxSWKPerPASID = 1

# Define the maximum SWK lifetime in second
# Default value is 0 (eternal of life)
# The maximum value is 31536000 (one year)
KptMaxSWKLifetime = 31536000

# Flag to define whether to allow SWK to be shared among processes
# Default value is 0 (shared mode is off)
KptSWKShared = 0

##############################################
# Kernel Instances Section
##############################################
[KERNEL]
NumberCyInstances = 0
NumberDcInstances = 0

##############################################
# ADI Section for Scalable IOV
##############################################
[SIOV]
NumberAdis = {1}

##############################################
# User Process Instance Section
##############################################
"""

HEADER_HOST_VF = """[GENERAL]
ServicesEnabled = {0}

ConfigVersion = 2

#Default values for number of concurrent requests*/
CyNumConcurrentSymRequests = 512
CyNumConcurrentAsymRequests = 64
DcNumConcurrentRequests = 512

#Statistics, valid values: 1,0
statsGeneral = 1
statsDh = 1
statsDrbg = 1
statsDsa = 1
statsEcc = 1
statsKeyGen = 1
statsDc = 1
statsLn = 1
statsPrime = 1
statsRsa = 1
statsSym = 1


# Disable public key crypto and prime number
# services by specifying a value of 1 (default is 0)
PkeServiceDisabled = 0

# This flag is to enable device auto reset on heartbeat error
AutoResetOnError = 0

# Disable Address translation services
ATEnabled = 0

##############################################
# Kernel Instances Section
##############################################
[KERNEL]
NumberCyInstances = 0
NumberDcInstances = 0

##############################################
# User Process Instance Section
##############################################
"""

SECTION = """[SSL]
NumberCyInstances = {0}
NumberDcInstances = {1}
NumProcesses = {2}
LimitDevAccess = 0
"""

SERVICE_INSTANCE = "{0}{1}Name = \"SSL{1}\"\n{0}{1}IsPolled = {3}\n{0}{1}CoreAffinity = {2}\n"
FILE_NAME = "/etc/{0}_dev{1}.conf"

def build_core_list(core_range, offset=0, max_core=0):
    if core_range == '0' or not '-' in core_range:
        return None
    cores_list = list()
    cores = core_range.split('-')
    lower_bound = int(cores[0])
    upper_bound = int(cores[1])
    for i in range(lower_bound,upper_bound+1):
        if max_core > 0:
            cores_list.append((i + offset) % max_core)
        else:
            cores_list.append(i)
    return cores_list

if __name__ == '__main__':
    num_cy_instances = 0
    num_dc_instances = 0
    num_adi_instances = 0
    cy_cores_list = list()
    dc_cores_list = list()
    cy_offset = 0
    dc_offset = 0
    services = ""
    supportedService = [
        "asym",
        "asym;dc",
        "asym;sym",
        "dc",
        "dc;sym",
        "dc;asym",
        "sym",
        "sym;dc",
        "sym;asym",
    ]
    supportedPoll = [
        0,
        1,
        2,
    ]

    parser = argparse.ArgumentParser()
    parser.add_argument("num_devices", help="Set of devices in range of a-b, e.g 0-9 for dev 0 to 9", type=str)
    parser.add_argument("cy_instances", help="The number of QAT crypto instances to configure", type=int)
    parser.add_argument("cy_cores", help="Set of cores in range of a-b, e.g 1-10 use cores 1 to 10", type=str)
    parser.add_argument("dc_instances", help="The number of QAT compression instances to configure", type=int)
    parser.add_argument("dc_cores", help="Set of cores in range of a-b, e.g 1-10 use cores 1 to 10", type=str)
    parser.add_argument("service_type", help="Define service as either sym/asym/dc/sym;dc/asym;dc.. etc, default is sym;dc", nargs='?', default="sym;dc", type=str)
    parser.add_argument("file_type", help="Files types 4xxx / 4xxxvf, default is 4xxx", nargs='?', default="4xxx", type=str)
    parser.add_argument("max_core", help="Set 0 to ignore relative core distribution across device, default is 0", nargs='?', default=0, type=int)
    parser.add_argument("adi_instances", help="The number of QAT mdev instances to configure, default is 0", nargs='?', default=0, type=int)
    parser.add_argument("cy_poll", help="Define cy instance poll type 0/1/2, default is 1", nargs='?', default=1, type=int)
    parser.add_argument("dc_poll", help="Define dc instance poll type 0/1/2, default is 1", nargs='?', default=1, type=int)
    parser.add_argument("num_process", help="Define number of process, default is 1", nargs='?', default=1, type=int)
    args = parser.parse_args()
    
    num_adi_instances = args.adi_instances

    services = args.service_type
    if not services in supportedService:
         print("Invalid service_type %s !!Aborting!!" % services)
         exit(1)

    if not args.file_type in ("4xxx", "4xxxvf"):
        print("Invalid file_type %s !!Aborting!!" % args.file_type)
        exit(1)

    if not args.cy_poll in supportedPoll:
        print("Invalid cy_poll %s !!Aborting!!" % args.cy_poll)
        exit(1)

    if not args.dc_poll in supportedPoll:
        print("Invalid dc_poll %s !!Aborting!!" % args.dc_poll)
        exit(1)

    if args.num_process < 1:
        print("Invalid num_process %s !!Aborting!!" % args.num_process)
        exit(1)

    for serv in services.split(";"):
        if serv in ( "dc", ):
            num_dc_instances = args.dc_instances
            continue
        if serv in ( "sym", "asym", ):
            num_cy_instances = args.cy_instances

    #Enhance for mixed MDEV and SSL instance once driver support is enabled
    if num_adi_instances > 0:
        num_cy_instances = 0
        num_dc_instances = 0

    num_devices_list = build_core_list(args.num_devices)

    for d in num_devices_list:
        cy_cores_list = build_core_list(args.cy_cores, cy_offset, args.max_core)
        dc_cores_list = build_core_list(args.dc_cores, dc_offset, args.max_core)
        cy_offset += len(cy_cores_list)
        dc_offset += len(dc_cores_list)
        fileName=FILE_NAME.format(args.file_type, d)
        with open(fileName, 'w') as f:
            if args.file_type == "4xxx":
                print(HEADER_HOST_PF.format(services, num_adi_instances), file=f)
            else:
                print(HEADER_HOST_VF.format(services), file=f)
            print(SECTION.format(num_cy_instances, num_dc_instances, 1), file=f)
            for i in range(0,num_cy_instances):
                print(SERVICE_INSTANCE.format(
                    "Cy",i,cy_cores_list[i%len(cy_cores_list)],args.cy_poll),
                    file=f)
            for i in range(0,num_dc_instances):
                print(SERVICE_INSTANCE.format(
                    "Dc",i,dc_cores_list[i%len(dc_cores_list)],args.dc_poll),
                    file=f)
            print("#Generated using create_gen4_config.py version {0}".format(
                __version__), file=f) 
