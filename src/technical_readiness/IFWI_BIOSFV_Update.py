'''
Copyright (c) 2021-2022, Intel Corporation. All rights reserved.
Retrieves the FIT and SPS/CSME Version from the IFWI Image.
Title      	: IFWI_BIOSFV_Update.py
Author(s)  	: Santosh, Deshpande
Description	:
Inputs		: Each function has relevant header details for input and output
Output		: Each function has relevant header details for input and output
'''

import os
from lxml import etree as ET
import csv, struct, array, sys, operator
import argparse, shutil, glob
import os.path
import subprocess

def GetFVLabel(results, FVLabel):
	FVname = None
	resulttxt = str(results)
	resultlist = resulttxt.upper().split(FVLabel.upper())
	if (len(resultlist) > 1):
		TopHalf = resultlist[0]
		CloserToFVNum = TopHalf.split(" :")
		GetLastSection = CloserToFVNum[-2]
		NowAtFV = GetLastSection.split("\"")
		FVnameBreak = NowAtFV[-1]
		FvNamed = FVnameBreak.split("N")
		FVname = FvNamed[-1]

	print (FVname)
	return (FVname)

def ReplaceVars(UpdatedCommand, TeD, PD, TD, FVID, UISection, GUID, IFWIBIOS, InputBin):
	UpdatedCommandLocal = (((((UpdatedCommand.replace("$FVID", FVID)).replace("$UISection", UISection)).replace("$GUID", GUID)).replace("$InIFWI.BIN", IFWIBIOS)).replace("$InputBin", InputBin))
	return UpdatedCommandLocal
	
def CopyTools (src, Dest):

    Listed = glob.glob(src+"\\*.exe")
    for FileList in Listed:
        BaseFileNameList = FileList.split("\\")
        shutil.copy (FileList, Dest+BaseFileNameList[len(BaseFileNameList)-1])
    
def UpdateBiosFVForNonUEFI(IFWIBIOS, iXmlFile, UpdateBiosSection, InputBin, TeD, PD, TD):
	CommandArrayList = []
	iXmlFileTree = ET.parse(iXmlFile+r'\IFWI_ConfigBIOSSubFV.xml')
	#os.mkdir(TeD)
	FVID = ""
	#Find All supported Sections in the XML file
	nowDir = os.getcwd()
	os.chdir(PD)
	CopyTools(TD, PD)
	for Element in iXmlFileTree.findall('.//IntelDriver'):
		LABEL = Element.attrib.get('label')
		#Match with User Request??? This function () is called repetatively so once found do the work and return from here..
		if (LABEL.upper().find(UpdateBiosSection.upper()) >=0 ):
			for SubElement in Element: 
				if (SubElement.tag.upper().find("UISection".upper()) >= 0):
					UISection = SubElement.attrib.get('value')
					print (UISection)
				if (SubElement.tag.upper().find("GUID".upper()) >= 0):
					GUID = SubElement.attrib.get('value')
				for Leaflet in SubElement:
					CommandToExecute = Leaflet.attrib.get('value')
					CommandToExecute = ReplaceVars(CommandToExecute,  TeD, PD, TD, FVID, UISection, GUID, IFWIBIOS, InputBin[0:len(InputBin)-4])
					CommandArrayList.append(CommandToExecute)
					print (CommandToExecute)
					results = subprocess.check_output(CommandToExecute)
					if (CommandToExecute.upper().find("FMMT") >=0):
						if (CommandToExecute.upper().find(" -V") >=0):
							FVID = GetFVLabel(results, GUID)
							if (None == FVID):
								print ("Wrong TAG RETURNING ERROR")
								break
				print (CommandArrayList)
			#exit the ELEMENT FOR
			break

	os.chdir(nowDir)
	print (CommandArrayList, "\n", len(CommandArrayList))
	return str(results)
			
def main():
	RootPath = os.getcwd()
	Temp = os.path.join(RootPath, "Temp")
	Payloads = os.path.join(RootPath, "Payloads")
	Tools = os.path.join(RootPath, "Tools")
	UpdateBiosFVForNonUEFI("EGSDCRB.SYS.OR.64.2021.03.4.05.1800_SPR_EBG_SPS.bin", r'C:\DPEA_XPIV\Experiments_Delete_Whenever\DROP6_Working\Scripts\IFWI_Scripts\\', "IfwiId", Temp, Payloads, Tools)
	
if __name__ == "__main__":
    main()