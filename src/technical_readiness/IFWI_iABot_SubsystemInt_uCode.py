'''
Copyright (c) 2019-2020, Intel Corporation. All rights reserved.
This is the entry point for all IFWI Post Build Activities to verify the Straps Changes in the Knobs.
Title      	: IFWI_iABot_SubsystemInt_uCode.py
Author(s)  	: Ansari MND; B, Smitha; B R, Vijay
Description	: Things to perform: 
			  Applies the MCU patch on BIOS ROM and generates update BIOS .
Inputs		: Each function has relevant header details for input and output
Output		: Each function has relevant header details for input and output
Usage		:
'''
import argparse
import csv,sys
from lxml import etree as ET
import os.path
import glob, os, shutil
import fnmatch
from collections import OrderedDict

import IFWI_GenerateXML
import IFWI_PreOSBuildCommonCode

'''
Validates all the command line options if users have entered appropriately and all the mandatory values are passed
Title      	: setup_arg_parse
Description	: This function handles all the command line arguments 
Inputs		: user input from the command line.
Outputs		: args has all the arguments stored with commandline option names
'''
def setup_arg_parse():
	parser = argparse.ArgumentParser()
	parser.add_argument('-r', help = 'Root Path to create workspace', required= True, metavar= "RootPathWorkSpace")
	parser.add_argument('-b', help = 'BIOS ROM File to be Updated with MCU Patch', required= True, metavar= "BIOSROMFile")
	parser.add_argument('-m', help = 'New MCU Patch to use', required= True, metavar= "MCUPatchFile")
	args = parser.parse_args()
	return args

'''
Apply the ucode patch into the BIOS Binary File.
Title      	: uCode_Patch_update
Description	: This function updates ucode patch into the BIOS Binary File  
Inputs		: Requestor,Data,ConfigFileDetails,XMLCLIBaseFolder
Outputs		: BIOS ROM file
'''
def uCode_Patch_update(Data, XMLCLIBaseFolder, PayloadsPath, IFWI):
    sys.path.append(XMLCLIBaseFolder)
    import pysvtools.xmlcli.XmlCli as cli
    xmlCLIOutFolder = XMLCLIBaseFolder + "\pysvtools\\xmlcli\out"

    for row in Data:
        uCodeName = row['PayloadName']
    uCodeFilePath = PayloadsPath+uCodeName

    if os.path.isfile(uCodeFilePath):
        print("uCode Filepath is ", uCodeFilePath)

    ROMFilePath = IFWI

    # XMLCLI Function call to update BIOS patch
    cli.ProcessUcode("update", ROMFilePath, uCodeFilePath)

    BiosROMName, BiosROMExt = os.path.splitext(os.path.basename(ROMFilePath))
    uCodeBin, uCodeExt = os.path.splitext(uCodeName)
    updatedBiosROM = BiosROMName+"_newUc_"+uCodeBin[5:]

    for basename in os.listdir(xmlCLIOutFolder):
        if (basename.lower().find(updatedBiosROM.lower()) >= 0):
            pathname = os.path.join(xmlCLIOutFolder, basename)
            if os.path.isfile(pathname):
                shutil.copy2(pathname, ROMFilePath)
                cli.ProcessUcode("read",ROMFilePath)
                break;
    print("Output BIOS ROM generated successfully: ",ROMFilePath)
    print("****uCode Patch settings done****")
    return "uCode Patch successfully completed\n"

def main():
	args = setup_arg_parse()
	RootPathWorkSpace = args.r
	BIOSROMFile = args.b
	MCUPatchFile = args.m
	#uCode_Patch_update(PathToXMLCliFolder,Interface,ConfigFileDetails,XMLCLIBaseFolder,".")
	
if __name__ == "__main__":
    main()

