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
from openpyxl import Workbook
from openpyxl.styles import *
from lxml import etree as ET
import BIOS_Knob_Retriever

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

def GenerateBIOSKnobDIFFReport(IFWIBIOSBinary1, IFWIBIOSBinary2):
	print("GenerateBIOSKnobReportOut: BIOS/IFWI BIOS Setup options report out started")
	jsondata = {}
	with open(r'BIOS_Knob_Diff_Report.json', "r", newline = '') as jsonfile:
		jsonstring = jsonfile.read()
		jsondata = json.loads (jsonstring)
	KnobList1 = []
	KnobList2 = []
	print(jsondata['Header'])
	if (os.path.isfile(IFWIBIOSBinary1)):
		print("GenerateBIOSKnobReportOut: IFWIBIOSBinary Continuing further")
		KnobList1 = BIOS_Knob_Retriever.GenerateBIOSSetupOptionXMLFile(IFWIBIOSBinary1, jsondata['Header'])
	print (len(KnobList1), KnobList1[0]['prompt'])
	if (os.path.isfile(IFWIBIOSBinary2)):
		print("GenerateBIOSKnobReportOut: IFWIBIOSBinary Continuing further")
		KnobList2 = BIOS_Knob_Retriever.GenerateBIOSSetupOptionXMLFile(IFWIBIOSBinary2, jsondata['Header'])
	
	KnobDelta = []
	HeaderList = ['prompt','name','SetupPgPtr','CurrentVal___'+IFWIBIOSBinary1,'CurrentVal___'+IFWIBIOSBinary2,'default___'+IFWIBIOSBinary1,'default___'+IFWIBIOSBinary2]
	for KnobValueIn1 in KnobList1:
		KnobDeltaValue = {'prompt':KnobValueIn1['prompt'],'name':KnobValueIn1['name'],'SetupPgPtr':KnobValueIn1['SetupPgPtr'],'CurrentVal___'+IFWIBIOSBinary1:KnobValueIn1['CurrentVal'],'CurrentVal___'+IFWIBIOSBinary2:'MISSING','default___'+IFWIBIOSBinary1:KnobValueIn1['default'],'default___'+IFWIBIOSBinary2:'MISSING'}
		FoundMatch = 0
		for KnobValueIn2 in KnobList2:
			if ((KnobValueIn1['name'].upper().find((KnobValueIn2['name'].upper())) == 0) and (len(KnobValueIn1['name']) == len(KnobValueIn2['name']))): #True
				if (KnobValueIn1['CurrentVal'].upper().find((KnobValueIn2['CurrentVal'].upper())) != 0): #False
					KnobDeltaValue['CurrentVal___'+IFWIBIOSBinary2] = KnobValueIn2['CurrentVal']
					KnobDeltaValue['default___'+IFWIBIOSBinary2] = KnobValueIn2['default']
					KnobDelta.append(KnobDeltaValue)
				KnobValueIn2['found']=True
				FoundMatch = 1
				break

		if (FoundMatch == 0):
			KnobDelta.append(KnobDeltaValue)
			
	XLSXFileName = "DeltaKnobOutput.xlsx"
	print (XLSXFileName)
	XLSXFile = Workbook()
	SummarySheet = XLSXFile.active
	SummarySheet.title ="SUMMARY"
	Count = 0
	
	for x in KnobDelta:
		Count = UpdateXLSXFileContent(HeaderList, x, Count, SummarySheet)
					
	XLSXFile.save(XLSXFileName)
	XLSXFile.close()	

def setup_arg_parse():
	parser = argparse.ArgumentParser()
	parser.add_argument('-C1', help = 'IFWI.BIN or BIOS.ROM', required= True, metavar= "IFWIBIOSBinary")
	parser.add_argument('-C2', help = 'IFWI.BIN or BIOS.ROM', required= True, metavar= "IFWIBIOSBinary")
	args = parser.parse_args()
	return args	

def main():
	args = setup_arg_parse()
	IFWIBIOSBinary1 = args.C1
	IFWIBIOSBinary2 = args.C2
	GenerateBIOSKnobDIFFReport(IFWIBIOSBinary1, IFWIBIOSBinary2)

if __name__ == "__main__":
    main()