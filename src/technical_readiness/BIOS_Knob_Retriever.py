'''
Copyright (c) 2022, Intel Corporation. All rights reserved.
This is the entry point for all IFWI Pre Build Activities that has to happen 
before the BUILD is triggered
Title      	: BIOS_Knob_Release_Report.py
Author(s)  	: Santosh, Deshpande
Description	: Things to perform, report generation: 
			1. Converts consolidated each IFWI XML changes into Tabified XLS file.
			2. Gives IP Payload version, OWR links, and what changed from previous release.
			3. Strap Overrides if any used.
Inputs		: IFWI Binary
Output		: XML file for all the BIOS Knobs and the XLSX file with segregration
Usage		: python BIOS_Knob_Release_Report.py  -b IFWI.BIN

'''
import os, glob, sys, shutil, json
import argparse, csv
from lxml import etree as ET

def CleanupOut(path=r'.\\'):
	shutil.rmtree(path+r'pysvtools\xmlcli\out\\*.*', True)

def GenerateBIOSSetupOptionXMLFile(IFWIBIOSBinary, VariablestHeader = None):
	BIOSSetupOptionXMLFile = None
	print("GenerateBIOSSetupOptionXMLFile: BIOS/IFWI BIOS Setup options report out started")
	CleanupOut()
	sys.path.append(".")
	import pysvtools.xmlcli.XmlCli as MyBiosCli
	abc = MyBiosCli.savexml(0, IFWIBIOSBinary)
	XMLFileList = glob.glob(r'.\pysvtools\xmlcli\out\\' + r'*.xml')
	BIOSSetupOptionXMLFile =  XMLFileList[0]
	CheckIfFilePathIsCorrect = os.path.isfile(BIOSSetupOptionXMLFile)
	if (CheckIfFilePathIsCorrect):
		print("GenerateBIOSSetupOptionXMLFile: XML got Created Continuing further", BIOSSetupOptionXMLFile, "    ", len(XMLFileList))
		shutil.copyfile(BIOSSetupOptionXMLFile, IFWIBIOSBinary.replace(".bin",".xml"))
	
	if (VariablestHeader == None):
		return IFWIBIOSBinary.replace(".bin",".xml")
	else:
		#CleanupOut()
		return GetKnobList(IFWIBIOSBinary.replace(".bin",".xml"), VariablestHeader)

def GetKnobList(XMLFile, VariablestHeader):
	xp = []
	Count = 0

	iXmlFileTree = ET.parse(XMLFile)
	for Element in iXmlFileTree.findall('.//knob'):
		OptionList = ''
		for SubElement in Element.findall('.//option'):
			OptionList = OptionList + SubElement.get('text')+'-'+SubElement.get('value')+', '
		if (OptionList == ''):
			if (Element.get('min') != None):
				OptionList = 'Min:'+Element.get('min')+'- Max:'+Element.get('max')+'), '
		if (OptionList == ''):
			OptionList = 'NA, '
			
		t = {}
		for VElement in VariablestHeader:
			if (VElement.upper().find('Sl.No'.upper()) >=0):
				t[VElement] = Count
			elif (VElement.upper().find('AllOptions'.upper()) >=0):
				t[VElement] = OptionList[0:-2]
			else:
				t[VElement] = Element.get(VElement).strip().strip('=')
		t['found']=False
		xp.append(t)
		Count = Count + 1
	return xp