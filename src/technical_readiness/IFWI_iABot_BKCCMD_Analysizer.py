'''
Copyright (c) 2019-2020, Intel Corporation. All rights reserved.
Program meant for understanding the command received and invoke appropriate functionality.
Major Commands are Engineering, Rebase and Release
Under this sub-commands are for Binaries, visible straps and invisible straps, harness update overrides.
Title      	: Supported_Command_List.py
Author(s)  	: Chandni, Vyas, Ansari MND
Description	: Things to perform: 
			1. Reads from the Command_List.csv to prepare the list of commands and usage
			2. Sends output to user as email.
Inputs		: Each function has relevant header details for input and output
Output		: Each function has relevant header details for input and output
Usage		: Refer to Readme.txt
'''

import os
import errno
import shutil
import argparse
import json
from collections import OrderedDict
from importlib import import_module
import IFWI_PreOSBuildCommonCode
import glob
import IFWI_GenerateXML
import win32com.client
import subprocess
import IFWI_7ZIPPackage_Creator
outlook = win32com.client.Dispatch("Outlook.Application")
inbox = outlook.GetNamespace("MAPI").GetDefaultFolder(6)

'''
Validates all the command line options if users have entered appropriately and all the mandatory values are passed
Title      	: setup_arg_parse
Description	: This function handles all the command line arguments 
Inputs		: user input from the command line.
Outputs		: args has all the arguments stored with commandline option names
'''	
def setup_arg_parse():
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', help='Command Subject String',required=True,metavar="CmdSubjStr")
	parser.add_argument('-b', help='Command Body String',required=False,metavar="CmdBodyStr")
	args = parser.parse_args()
	return args
	
def CreateBuildDetails(BuildFolderPath, Subject, Submitter):
    with open(BuildFolderPath+"\\Requestor.txt","w") as submitter:
        submitter.writelines("Submitter: " + Submitter)
        submitter.writelines("\nCommand : " + str(Subject))

def BackUpFolderStruct(src, dest):
	print (src, dest)
	try:
		shutil.copytree(src, dest)
	except shutil.Error as e:
		print('Directory not copied. Error: %s' % e)
	except OSError as e:
		if e.errno == errno.ENOTDIR:
			shutil.copy(src, dest)
		else:
			print('Directory not copied. Error: %s' % e)


def HiddenOverrideStraps(ConfigPath, ConfigFile, userOverride):
    Command_List = []
    FHSO = ['Value', 'Offset', 'Start Bit', 'Comments', 'Strap Size']
    for row in userOverride:
        Command_List.append(OrderedDict(row))
    print (Command_List)
    IFWI_PreOSBuildCommonCode.WriteBackConfigContentsInMemory(ConfigPath+ConfigFile,Command_List, FHSO)

def CallingCleanupFolders(XMLCLIBaseFolder, PayloadFolder):
    try :
        FileList = glob.glob(PayloadFolder+"*.exe")
        for ExecutablesToDelete in FileList:
            os.remove(ExecutablesToDelete)
    except:
        print ("Payload Folder is cleann at this point")
    try :
        shutil.rmtree(PayloadFolder+"TempDir")
    except:
        print("Temp Dir not created yet")
    try :
        XMLCLIPathOutPath = XMLCLIBaseFolder + r'\pysvtools\xmlcli\Out'
        shutil.rmtree(XMLCLIPathOutPath)
    except:
        print ("XMLCLI Out folder is clean")
    try :
        FileList = glob.glob(PayloadFolder+"*.ffs")
        for ExecutablesToDelete in FileList:
            os.remove(ExecutablesToDelete)
    except:
        print ("Payload Folder is cleann at this point")
    try :
        FileList = glob.glob(PayloadFolder+"*.sec")
        for ExecutablesToDelete in FileList:
            os.remove(ExecutablesToDelete)
    except:
        print ("Payload Folder is cleann at this point")
    try :
        FileList = glob.glob(PayloadFolder+"*.raw")
        for ExecutablesToDelete in FileList:
            os.remove(ExecutablesToDelete)
    except:
        print ("Payload Folder is cleann at this point")
    

'''
Validates all the command line options if users have entered appropriately and all the mandatory values are passed
Title      	: ParseUpdateActions
Description	: This function handles all the command line arguments 
Inputs		: user input from the command line.
Outputs		: args has all the arguments stored with commandline option names
'''	
def ParseUpdateActions(CmdSubjStr, BOTPath, UserName):
    FH = []
    Root = ''
    BaseFolder = ''
    ColumnName = ''
    RootNetworkPath = ''
    Data = ''
    CmdFail = False
    Contents = []
    ZipFileName = ""


    for key, value in CmdSubjStr.items():
        if (key.upper().find('ProgramName'.upper()) >= 0):
            ProgramName = CmdSubjStr['ProgramName']
        if (key.upper().find('Action'.upper()) >= 0):
            CommandName = CmdSubjStr['Action']
        if (key.upper().find('Base'.upper()) >= 0):
            BaseFolder = CmdSubjStr['Base']
        if (key.upper().find('Contents'.upper()) >= 0):
            Contents = CmdSubjStr['Contents']
        if (key.upper().find('Ifwi'.upper()) >= 0):
            InputIFWI = CmdSubjStr['IFWI']
    print ("Program Name: ", ProgramName, "Command: ", CommandName, "Contents: ", Contents, "User Base: ", BaseFolder)


    Command_List = IFWI_PreOSBuildCommonCode.ReadConfigContentsInMemory(BOTPath+r'\BotConfig.txt', FH, ';')
    for row in Command_List:
        if (row['ProgramName'] == ProgramName):
            Root = row['RootFolder']
            RootNetworkPath = row['RootNetworkPath']
            platformName =  row['PlatformConfigName']
            XMLCLIBaseFolder = row['XMLCLIBaseFolder']
            if (BaseFolder == ''):
                BaseFolder = row['BaseFolder']
            break
    if (Root == ''):
        Data = Data + "This BOT is not configured for : " + ProgramName + ". Please talk to Program IFWI Lead\n"

    elif (CommandName.upper().find("BKCBKMBuild".upper()) >=0):
        WWFolderName = IFWI_PreOSBuildCommonCode.WorkWeekRetriver(23)
        os.mkdir(Root+"\\"+WWFolderName)
        IFWI_PreOSBuildCommonCode.SetEnvVariables(Root, WWFolderName)
        BackUpFolderStruct(BOTPath+r'\Downloads\\' , IFWI_PreOSBuildCommonCode.PAYLOADS)

        DeleteAttachmentFiles = glob.glob(BOTPath+r'\Downloads\*.*')
        for AFilesInList in DeleteAttachmentFiles:
            os.remove(AFilesInList)

        DownloadedFiles = glob.glob(IFWI_PreOSBuildCommonCode.PAYLOADS+r'\*.7z')
        print (DownloadedFiles)
        CurrentWorkingDir = os.getcwd()
        os.chdir(IFWI_PreOSBuildCommonCode.PAYLOADS)
        IFWIBinary = IFWI_7ZIPPackage_Creator.ExtractIFWIZipPackage (DownloadedFiles[0])
        os.remove(DownloadedFiles[0])
        os.chdir(CurrentWorkingDir)
        
        
        CreateBuildDetails(IFWI_PreOSBuildCommonCode.WORKSPACE_PATH, CmdSubjStr, UserName)
        if (len(Contents) != 0):
            Data = ""
            for key, value in Contents.items():
                if (key.upper().find('Binary'.upper()) >= 0):
                    '''
                    
                    BinaryDetails = value
                    Update_ConfigMasters = getattr(__import__("IFWI_iABot_Update_MasterConfigs", fromlist=["Update_ConfigMasters"]), "Update_ConfigMasters")
                    Update_ConfigMasters(IFWI_PreOSBuildCommonCode.CONFIG, BinaryDetails, ConfigFileDetails)
                    for fullFilename in DownloadedFiles:
                        fullFilenametemp = fullFilename.split('\\')
                        f = fullFilenametemp[len(fullFilenametemp)-1]
                        if (os.path.isfile(IFWI_PreOSBuildCommonCode.PAYLOADS+f) == True):
                            os.remove(IFWI_PreOSBuildCommonCode.PAYLOADS+f)
                        shutil.move(fullFilename, IFWI_PreOSBuildCommonCode.PAYLOADS)

                    Update_LocalManifest_Payloads = getattr(__import__("IFWI_iABot_Update_LocalManifest_Payloads", fromlist=["Update_LocalManifest_Payloads"]), "Update_LocalManifest_Payloads")
                    Update_LocalManifest_Payloads(IFWI_PreOSBuildCommonCode.PAYLOADS, BinaryDetails)
                    '''
                    Data = Data + "TO BE IMPLEMENTED...   FITm does support decompose YET :( Command Name: " + key.upper()

                elif (key.upper().find('BIOS_Knob_Override'.upper()) >= 0):
                    ApplyBiosKnobs = getattr(__import__("IFWI_ApplyKnobs", fromlist=["ApplyBiosKnobs"]), "ApplyBiosKnobs")
                    Data = Data + ApplyBiosKnobs(value, XMLCLIBaseFolder, IFWI_PreOSBuildCommonCode.PAYLOADS+IFWIBinary[0])

                elif (key.upper().find('BIOS_Patch_Override'.upper()) >= 0):
                    uCode_Patch_update = getattr(__import__("IFWI_iABot_SubsystemInt_uCode", fromlist=["uCode_Patch_update"]), "uCode_Patch_update")
                    Data = Data + uCode_Patch_update(value, XMLCLIBaseFolder, IFWI_PreOSBuildCommonCode.PAYLOADS, IFWI_PreOSBuildCommonCode.PAYLOADS+IFWIBinary[0])

                elif (key.upper().find('Strap_Override_Hidden'.upper()) >= 0):
                    HiddenOverrideStraps(IFWI_PreOSBuildCommonCode.PAYLOADS, 'HiddenOverrideStraps.csv', value)
                    OverrideStrapBits = getattr(__import__("IFWI_StrapsOverrideBits", fromlist=["OverrideStrapBits"]), "OverrideStrapBits")
                    Data = Data + OverrideStrapBits(IFWI_PreOSBuildCommonCode.PAYLOADS+IFWIBinary[0], IFWI_PreOSBuildCommonCode.PAYLOADS+'HiddenOverrideStraps.csv')
                    print (Data)

                elif (key.upper().find('Get_BIOS_KnobDiffList'.upper()) >= 0):
                    GenerateBIOSKnobDIFFReport = getattr(__import__("IFWI_BIOS_Knob_Diff_Report", fromlist=["GenerateBIOSKnobDIFFReport"]), "GenerateBIOSKnobDIFFReport")
                    print (IFWIBinary, "SANTOSH FOUND THE ISSUE")
                    Data = GenerateBIOSKnobDIFFReport(IFWI_PreOSBuildCommonCode.PAYLOADS+IFWIBinary[0], IFWI_PreOSBuildCommonCode.PAYLOADS+IFWIBinary[1], BOTPath, IFWI_PreOSBuildCommonCode.PAYLOADS+value[0]['ResultsXLSX'], XMLCLIBaseFolder)

                elif (key.upper().find('Get_BIOS_Knoblist'.upper()) >= 0):
                    GenerateBIOSKnobReportOut = getattr(__import__("IFWI_BIOS_Knob_Release_Report", fromlist=["GenerateBIOSKnobReportOut"]), "GenerateBIOSKnobReportOut")
                    Data = Data + GenerateBIOSKnobReportOut(IFWI_PreOSBuildCommonCode.PAYLOADS+IFWIBinary[0], BOTPath, IFWI_PreOSBuildCommonCode.PAYLOADS+value[0]['ResultsXLSX'], XMLCLIBaseFolder)

                elif (key.upper().find('Get_SPS_DLND_Link'.upper()) >= 0):
                    RetrieveSPSVerionDetails = getattr(__import__("IFWI_SPS_VersionRetriever", fromlist=["RetrieveSPSVerionDetails"]), "RetrieveSPSVerionDetails")
                    JsonData = RetrieveSPSVerionDetails(IFWI_PreOSBuildCommonCode.PAYLOADS+IFWIBinary[0])
                    Data = Data + json.dumps(JsonData)

                elif (key.upper().find('BIOS_FV_Override'.upper()) >= 0):
                    UpdateBiosFVForNonUEFI = getattr(__import__("IFWI_BIOSFV_Update", fromlist=["UpdateBiosFVForNonUEFI"]), "UpdateBiosFVForNonUEFI")
                    shutil.copy(IFWI_PreOSBuildCommonCode.PAYLOADS+IFWIBinary[0], IFWI_PreOSBuildCommonCode.PAYLOADS+IFWIBinary[0]+".orig")
                    for ActionListNumber in range (0, len(value)):
                        JsonData = UpdateBiosFVForNonUEFI(IFWIBinary[0], BOTPath, value[ActionListNumber]['Label'], value[ActionListNumber]['PayloadName'], IFWI_PreOSBuildCommonCode.PAYLOADS+r'TempDir', IFWI_PreOSBuildCommonCode.PAYLOADS, Root+r'\Base\Payloads\Tools')
                        shutil.copy(IFWI_PreOSBuildCommonCode.PAYLOADS+"tIFWI_Modified.BIN", IFWI_PreOSBuildCommonCode.PAYLOADS+IFWIBinary[0])
                        Data = Data + json.dumps(JsonData)
                    try:
                        print ("Update the files back to send back")
                        shutil.copy(IFWI_PreOSBuildCommonCode.PAYLOADS+"tIFWI_Modified.BIN", IFWI_PreOSBuildCommonCode.PAYLOADS+"OutputIFWIBin.bin")
                        shutil.copy(IFWI_PreOSBuildCommonCode.PAYLOADS+IFWIBinary[0]+".orig", IFWI_PreOSBuildCommonCode.PAYLOADS+IFWIBinary[0])
                        os.remove(IFWI_PreOSBuildCommonCode.PAYLOADS+"tIFWI_Modified.BIN")
                        os.remove(IFWI_PreOSBuildCommonCode.PAYLOADS+IFWIBinary[0]+".orig")
                    except:
                        print("Error during build might be the reasone for non-existance of files")

                else:
                    Data = "Unsupported Content Action for the Build"
                    break
                
            print("ZIP the contents to send it out")
            CallingCleanupFolders(XMLCLIBaseFolder, IFWI_PreOSBuildCommonCode.PAYLOADS)
            
            IFWI_7ZIPPackage_Creator.CreateIFWIZipPackage (IFWI_PreOSBuildCommonCode.WORKSPACE_PATH+'TEST.7Z', IFWI_PreOSBuildCommonCode.PAYLOADS)
            
            Data = Data + "\n Full IFWI is attached as 7z file\n"

    else:
        Data = "Unsupported Action Sent"
        
    print (Data)
    ReturnData = [Data, IFWI_PreOSBuildCommonCode.WORKSPACE_PATH+'TEST.7Z']
    return (ReturnData)

def main():
	args = setup_arg_parse()
	CmdSubjStr = args.s
	BinaryFullPath = args.b
	ParseAndListActions(CmdSubjStr, BinaryFullPath)

if __name__ == "__main__":
	main()
