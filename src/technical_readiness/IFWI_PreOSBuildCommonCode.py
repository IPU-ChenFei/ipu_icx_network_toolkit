'''
Copyright (c) 2019-2020, Intel Corporation. All rights reserved.
This is the entry point for all IFWI Pre Build Activities that has to happen 
before the BUILD is triggered. Common code in one place to reuse.
Title      	: IFWI_PreOSBuildCommonCode.py
Author(s)  	: Chandni, Vyas; Santosh, Deshpande
Description	: Things to perform: 
            1. Create A workspace as of date workweek with build number in the root directory
            2. Creates all the sub-folders and
            3. Sets Variables for the path to all folders
Inputs		: Each function has relevant header details for input and output
Output		: Each function has relevant header details for input and output
'''
import struct, os, sys, shutil
import csv,operator,argparse
import datetime
import IFWI_logger
WORKSPACE_PATH = ''
WWDIR=''
CONFIG=''
SCRIPTS=''
PAYLOADS=''
IFWI=''
TOOLS=''
DOCS=''
IFWI_XMLMap=''
IFWI_XMLMap=''
WW=''
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
    parser.add_argument('-b', help = 'Build Number Of the Date', required= True, metavar= "BuildNumber")
    args = parser.parse_args()
    return args
'''
Performs Creating the Build infrastructure 
Title      	: CreateWorkSpace
Description	:
            1. Create A workspace as of date workweek with build number in the root directory
            2. Creates all the sub-folders and sets the path to all folders
Inputs		: 
            BuildNumber: Build Number of the day (Always Starts with 1)
            RootDir: Network share root location where Work Space to Build IFWI and download the IP payload package
Outputs		:
            WWFolderName: Work Space based on WorkWeek Folder Name.			
'''
def CreateWorkSpace(BuildNumber, RootDir):
    WWDIR = WorkWeekRetriver(BuildNumber)
    SetEnvVariables(RootDir, WWDIR)
    if (os.path.exists(WORKSPACE_PATH) == True):
        IFWI_logger.IFWILOGGER("info", ("Folder Already Exists... Deleting it"))
        shutil.rmtree(WORKSPACE_PATH)
    os.mkdir(WORKSPACE_PATH)
    os.mkdir(CONFIG)
    os.mkdir(SCRIPTS)
    os.mkdir(PAYLOADS)
    os.mkdir(DOCS)
    os.mkdir(TOOLS)
    os.mkdir(IFWI)
    os.mkdir(IFWI_XMLMap)
    return WWDIR
'''
Performs Creating the Build infrastructure 
Title      	: SetEnvVariables
Description	:
            1. Sets up Environment variables for rest of the code to work.
Inputs		: 
            RootDir: Network share root location where Work Space to Build IFWI and download the IP payload package
            WWFolderName: Work Space based on WorkWeek Folder Name.			
Outputs		:
            None
'''
def SetEnvVariables(RootDir, WWFolderName):
	global CONFIG
	global SCRIPTS
	global PAYLOADS
	global IFWI
	global TOOLS
	global IFWI_XMLMap
	global WWDIR
	global DOCS
	global WORKSPACE_PATH
	global SIGNING
	WWDIR = WWFolderName
	WORKSPACE_PATH = RootDir+'\\'+WWDIR+'\\'
	CONFIG = WORKSPACE_PATH+'Config\\'
	SCRIPTS=WORKSPACE_PATH+'Scripts\\'
	DOCS=WORKSPACE_PATH+'Docs\\'
	PAYLOADS=WORKSPACE_PATH+'Payloads\\'
	IFWI=WORKSPACE_PATH+'IFWI\\'
	TOOLS=PAYLOADS+'Tools\\'
	IFWI_XMLMap=IFWI+'XMLMap\\'
	SIGNING = WORKSPACE_PATH+'Signing\\'
	
def WorkWeekRetriver(BuildNumber=1):
	global WW
	WW = str(datetime.datetime.utcnow().isocalendar()[0])+"WW"+str(datetime.datetime.utcnow().isocalendar()[1])+"."+str(datetime.datetime.utcnow().isocalendar()[2])
	BldNum = 0
	if (None == BuildNumber):
		BuildNumber = 1
	if (os.path.isfile(WW)):
		with open(WW, "r", newline = '') as BldNumFile:
			for Data in BldNumFile:
				BldNum = int(Data)		
	if (BuildNumber != 1):
		BldNum = 1 + int(BldNum)
		with open(WW, "w", newline = '') as BldNumFile:
			BldNumFile.write(str(BldNum))
	BuildNumber = BldNum
	WW = WW +"."+str(BuildNumber)
	return WW

def ReadConfigContentsInMemory(iConfigFile, FieldNameHeader=None, dlmtr=","):
    ConfigFileData = []
    IFWI_logger.IFWILOGGER("info", (iConfigFile))
    with open(iConfigFile, "r", newline = '') as config_file:
        filereader = csv.DictReader(config_file, delimiter=dlmtr)
        for row in filereader: 
            ConfigFileData.append(row)
            #IFWI_logger.IFWILOGGER("info", (filereader.fieldnames))
        if (FieldNameHeader != None):
            for HeaderLabel in filereader.fieldnames:
                #IFWI_logger.IFWILOGGER("info", (HeaderLabel))
                FieldNameHeader.append(HeaderLabel)
    return ConfigFileData

def WriteBackConfigContentsInMemory(iConfigFile, ConfigFileData, FieldNameHeader=None, dlmtr=","):
    with open(iConfigFile, 'w', newline = '') as OutputFile:
        ConfigFileWriter = csv.DictWriter(OutputFile, delimiter=dlmtr, fieldnames=FieldNameHeader)
        ConfigFileWriter.writeheader()
        ConfigFileWriter.writerows(ConfigFileData)
    return

def ConvertStringToListArray(StringToList):
    Command_List = []
    VSOL = StringToList.split(',')
    for StringTo in VSOL:
        UserInput = {}
        ElementList = StringTo.strip(']').strip('"').strip(' ')
        IFWI_logger.IFWILOGGER("info", (ElementList))
        UserInputs = ElementList.split(";")
        for UI in UserInputs:
            UserInputs1 = UI.split(":")
            UserInput[UserInputs1[0]] = UserInputs1[1]
        Command_List.append(UserInput)
    for row in Command_List:
        IFWI_logger.IFWILOGGER("info", (row))
    return (Command_List)
def Read_Offset(Type,Filename):
    if (str(os.path.exists(Filename)) == "True" ):
        file = open(Filename,"r")
        for line in file:
            fields = line.split(",")
            Name = fields[0]; Offset = fields[1]
            if (Name==Type):
                IFWI_logger.IFWILOGGER("info", (Type,Offset))
                return Offset
    IFWI_logger.IFWILOGGER("info", ("SPI 0x0"))

    return 0
def CheckIFWIType(FullIFWIBinNamePath):
    SPISignature1 = 0
    SPISignature2 = 0
    IFWI_logger.IFWILOGGER("info", (FullIFWIBinNamePath))
    with open (FullIFWIBinNamePath,'rb') as ifwi_file:
        BufferLoc = bytearray(4)
        ifwi_file.readinto(BufferLoc)
        SPISignature1 = ( (BufferLoc[3] << 24) + (BufferLoc[2] << 16)+ (BufferLoc[1] << 8) + BufferLoc[0] )
        IFWI_logger.IFWILOGGER("info", (hex(SPISignature1)))
        BufferLoc = bytearray(4)
        ifwi_file.readinto(BufferLoc)
        SPISignature2 = ( (BufferLoc[3] << 24) + (BufferLoc[2] << 16)+ (BufferLoc[1] << 8) + BufferLoc[0] )
        IFWI_logger.IFWILOGGER("info", (hex(SPISignature2)))
    if ((SPISignature1 == 0xFFFFFFFF) and (SPISignature2 == 0xFFFFFFFF)):
        IFWI_logger.IFWILOGGER("info", ("Working on UFS IFWI Image"))
        return "UFS"
    elif ((SPISignature1 == 0x44504324) and (SPISignature2 == 0x5)):
        IFWI_logger.IFWILOGGER("info", ("Working on DNX IFWI Image expecting $CPD at the top, Hack for now"))
        return "DNX"
    else:
        IFWI_logger.IFWILOGGER("info", ("Working on SPI IFWI Image"))
        return "SPI"

def main():
    args = setup_arg_parse()
    RootPathWorkSpace = args.r
    BuildNumber = args.b
    CreateWorkSpace(BuildNumber, RootPathWorkSpace)

if __name__ == "__main__":
    main()