'''
Copyright (c) 2019-2020, Intel Corporation. All rights reserved.
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
from openpyxl import Workbook
from openpyxl.styles import *
from lxml import etree as ET
import BIOS_Knob_Retriever

'''
Validates all the command line options if users have entered appropriately and all the mandatory values are passed
Title      	: setup_arg_parse
Author(s)  	: Santosh, Deshpande
Description	: This function handles all the command line arguments 
Inputs		: user input from the command line.
Outputs		: args has all the arguments stored with commandline option names
'''	
def setup_arg_parse():
	parser = argparse.ArgumentParser()
	parser.add_argument('-b', help = 'IFWI.BIN or BIOS.ROM', required= True, metavar= "IFWIBIOSBinary")
	args = parser.parse_args()
	return args	
	
def UpdateXLSXFileContent(VariablestHeader, ConfigDataRow, InsertCount, SheetHandle):
	iCount = 0
	InsertCount = InsertCount + 1
	InsertCount_Text = '{0}'.format(InsertCount)
	if (InsertCount == 1):
		for HeaderLabel in VariablestHeader:
			RowName = chr(ord('A')+iCount)
			SheetHandle[RowName+InsertCount_Text] = HeaderLabel
			SheetHandle[RowName+InsertCount_Text].font = Font(bold=True)
			iCount = iCount+1
	else:
		for HeaderLabel in VariablestHeader:
			RowName = chr(ord('A')+iCount)
			SheetHandle[RowName+InsertCount_Text] = ConfigDataRow[HeaderLabel]
			iCount = iCount+1
	return InsertCount

def CheckCondition(FilterList, DataRow):
	MatchFound = False
	for FilterElement in FilterList:
		MatchFoundForSingle = False
		for ColumnName, SearchString in FilterElement.items():
			ColumnNm = ColumnName.strip('-')
			if (DataRow[ColumnNm].upper().find(SearchString.upper()) >=0):
				MatchFoundForSingle = True
			if ColumnName.find('-') >=0:
				MatchFound = MatchFoundForSingle and MatchFound
			else:
				MatchFound = MatchFoundForSingle or MatchFound
	return MatchFound

def GenerateXLSXFileBaseOnXML(XMLFile, xp, jsondata):
	SheetHandleAndRowCount = []
	Count = 0

	XLSXFileName = XMLFile.replace(".bin",".xlsx")
	print (XLSXFileName)
	XLSXFile = Workbook()
	SummarySheet = XLSXFile.active
	SummarySheet.title ="SUMMARY"

	for JsonDataElement in jsondata['Filters']:
		SheetHandleAndRow = {'SheetName':JsonDataElement['SheetName'], 'InsertCount': 0, 'FilterList' : JsonDataElement['FilterList'], 'SheetHandle': XLSXFile.create_sheet(JsonDataElement['SheetName'])}
		SheetHandleAndRowCount.append(SheetHandleAndRow)
	print (SheetHandleAndRowCount)
	
	for ConfigDataRow in xp:
		Found = False
		Count = 0
		SheetIndex= 0
		for SheetHandleAndRow in SheetHandleAndRowCount:
			if (SheetHandleAndRow['SheetName'].upper().find('FullKnobList'.upper()) >=0):
				SheetHandleAndRow['InsertCount'] = UpdateXLSXFileContent(jsondata['Header'], ConfigDataRow, SheetHandleAndRow['InsertCount'], SheetHandleAndRow['SheetHandle'])
			elif (SheetHandleAndRow['SheetName'].upper().find('OTHERS_UNKNOWN'.upper()) >=0):
				SheetIndex = Count
			else:
				if (CheckCondition(SheetHandleAndRow['FilterList'], ConfigDataRow)): 
					Found = Found or True
					SheetHandleAndRow['InsertCount'] = UpdateXLSXFileContent(jsondata['Header'], ConfigDataRow, SheetHandleAndRow['InsertCount'], SheetHandleAndRow['SheetHandle'])
			Count = Count + 1
		if (Found == False):
				SheetHandleAndRowCount[SheetIndex]['InsertCount'] = UpdateXLSXFileContent(jsondata['Header'], ConfigDataRow, SheetHandleAndRowCount[SheetIndex]['InsertCount'], SheetHandleAndRowCount[SheetIndex]['SheetHandle'])
			
	SummarySheet['A1'] = "Sheet Name"
	SummarySheet['B1'] = "Total Records"
	Count = 2
	for SummaryUpdate in SheetHandleAndRowCount:
		InsertCount_Text = '{0}'.format(Count)
		SummarySheet['A'+InsertCount_Text] = SummaryUpdate['SheetName']
		SummarySheet['B'+InsertCount_Text] = SummaryUpdate['InsertCount']
		Count = Count + 1
	XLSXFile.save(XLSXFileName)
	XLSXFile.close()	

def GenerateBIOSKnobReportOut(IFWIBIOSBinary):
	print("GenerateBIOSKnobReportOut: BIOS/IFWI BIOS Setup options report out started")
	jsondata = {}
	with open(r'BIOS_Knob_Release_Report.json', "r", newline = '') as jsonfile:
		jsonstring = jsonfile.read()
		jsondata = json.loads (jsonstring)
	if (os.path.isfile(IFWIBIOSBinary)):
		print("GenerateBIOSKnobReportOut: IFWIBIOSBinary Continuing further")
		KnobList = BIOS_Knob_Retriever.GenerateBIOSSetupOptionXMLFile(IFWIBIOSBinary, jsondata['Header'])
	if (len(KnobList) > 0):
		XLSXFileReportOut = GenerateXLSXFileBaseOnXML(IFWIBIOSBinary, KnobList, jsondata)

def main():
	args = setup_arg_parse()
	IFWIBIOSBinary = args.b
	GenerateBIOSKnobReportOut(IFWIBIOSBinary)

if __name__ == "__main__":
    main()