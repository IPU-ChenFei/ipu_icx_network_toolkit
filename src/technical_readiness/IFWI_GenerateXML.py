'''
Copyright (c) 2019-2020, Intel Corporation. All rights reserved.
This is the entry point for all IFWI Pre Build Activities that has to happen 
before the BUILD is triggered
Title      	: IFWI_GenerateXML.py
Author(s)  	: Chandni, Vyas; Santosh, Deshpande
Description	: Things to perform: 
			1. Extracts Payload Binaries from the Zip Package based on the JSON file.
Inputs		: Each function has relevant header details for input and output
Output		: Each function has relevant header details for input and output
Usage		: python IFWI_GenerateXML.py -c iConfigFile.txt -x xmlfile -i InputConfigFilePath -o OutputXMLFilePath
'''
from lxml import etree as ET
import csv, struct, array, sys, operator
import argparse
import os.path
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
	parser.add_argument('-c', help='Config File', required=True, metavar="iConfigFile")
	parser.add_argument('-x', help='Input XML File',required=True,metavar="iXmlFile")
	parser.add_argument('-i', help='Input Config File Path',required=True,metavar="ConfigPath")
	parser.add_argument('-o', help='Output XML File Path',required=True,metavar="oXmlFilePath")
	args = parser.parse_args()
	return args
'''
Performs Creating the Build infrastructure 
Title      	: CreateGoldenConfigFile
Description	:
			Generates XML files based on the Default XML's and config text files. 
			Replaces the parameters based on the text files. 
Inputs		: 
			iConfigFile: Text files that has the parameters to be replaced.
			iXmlFile: This is the Default XML files as an Input. 
Outputs		:
			oXmlFile: Output will be generated XML files acc. to the Default XML files. 		
'''
def GetOutputXMLFileName(iConfigFile):
	newxmltempfile=iConfigFile.split(".")
	return newxmltempfile[0]+"_"+IFWI_PreOSBuildCommonCode.WorkWeekRetriver()+".xml"

def GetConfigDataToApply(iConfigFile, ConfigPath):
	PatchFileData = []
	cwd = os.getcwd()
	os.chdir(ConfigPath)
	with open(iConfigFile, "r") as config_file:
		filereader = csv.DictReader(config_file, delimiter=",")
		for row in filereader: PatchFileData.append(row)
	os.chdir(cwd)
	return PatchFileData

def FixSpaces(a, oXmlFile):
	with open(a, "rb") as aFile, open(oXmlFile,"wb") as bFile:
		for aLine in aFile:
			if (aLine.find(b"<FitData") < 0):
				aLine = aLine.replace(b"/>",b" />")
			else:
				aLine = aLine.replace(b">",b" >")
			bFile.write(aLine)
	os.remove(a)
	
def SetConfigDataInXMLFile(PatchFileData, iXmlFile, oXmlFile):
	iXmlFileTree = ET.parse(iXmlFile)
	for I in PatchFileData:
		SearchString = './/{0}'.format(I['XMLtag'])
		if (I['name'] == ''):
			if(I['XMLtag'] == "FitData"):
				x = iXmlFileTree.getroot()
				FitDataXmlTag = I['XMLtag']
				FitDataXmlSku = I['Value']
				fit_attrib_to_update = I['Value'].split("=")
				x.set(fit_attrib_to_update[0], fit_attrib_to_update[1].strip('\"'))
			else:
				#x = iXmlFileTree.find(SearchString)
				for x in iXmlFileTree.findall(SearchString):
					if(SearchString.upper().find('project'.upper()) >=0 ):
						attrib_to_update = [I['Value']]
						if(I['Value'].find("@") > 0):
							attrib_to_update = I['Value'].split("@")
							if (attrib_to_update[0].upper().find(x.get('ingredient').upper()) >= 0):
								x.set('version', attrib_to_update[1])
								x.set('artifactory', attrib_to_update[2])
					else:
						y = x.attrib
						if(I['Value'].find("=") > 0):
							attrib_to_update=I['Value'].split("=")
							x.set(attrib_to_update[0], attrib_to_update[1])
						else:
							x.set('value', I['Value'])
		else :
			for x in iXmlFileTree.findall(SearchString):
				y = x.attrib
				if (I['name'] == y['name']):
					if(I['Value'].find("=") > 0):
						attrib_to_update=I['Value'].split("=")
						x.set(attrib_to_update[0], attrib_to_update[1])
					else:
						x.set('value', I['Value'])
					break
		iXmlFileTree.write('temp.xml', pretty_print=True, xml_declaration=True, encoding="utf-8")
		FixSpaces('temp.xml', oXmlFile)


def CreateGoldenConfigFile(iConfigFile, iXmlFile, ConfigPath, oXmlFilePath):
	oXmlFile = oXmlFilePath + GetOutputXMLFileName(iConfigFile)
	PatchFileData = GetConfigDataToApply(iConfigFile, ConfigPath)
	SetConfigDataInXMLFile(PatchFileData, ConfigPath+iXmlFile, oXmlFile)
	return oXmlFile

def main():
	args = setup_arg_parse()
	iConfigFile = args.c
	iXmlFile = args.x
	ConfigPath = args.i
	oXmlFilePath = args.o
	CreateGoldenConfigFile(iConfigFile, iXmlFile, ConfigPath, oXmlFilePath)

if __name__ == "__main__":
	main()
