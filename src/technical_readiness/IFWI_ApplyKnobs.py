'''
Copyright (c) 2019-2020, Intel Corporation. All rights reserved.
This is the entry point for all IFWI Post Build Activities to verify the Straps Changes in the Knobs.
Title      	: IFWI_ApplyKnobs.py
Author(s)  	: Himani, Patel; Vijay, B R; Chandni, Vyas; Ansari MND
Description	: Things to perform: 
              This python file will automate the XMLCli and generate new Binary File with the specified Knob changes.
Inputs		: Each function has relevant header details for input and output
Output		: Each function has relevant header details for input and output
Usage		: python IFWI_KnobsVerify -x PathToXMLCliFolder -i Interface -b InputBinFileOrROMFile -k InputKnobFile 
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
    parser.add_argument('-x', help='Path to XMLCli',required=False,metavar="PathToXMLCliFolder")
    parser.add_argument('-i', help='Interface',required=True,metavar="Interface")
    parser.add_argument('-b', help='Input Bin File or ROM File',required=True,metavar="InputBinFileOrROMFile")
    parser.add_argument('-k', help='Input Knob File',required=True,metavar="InputKnobFile")
    args = parser.parse_args()
    return args
  
'''
Automatically Generate XML Using XMLCli commands.
Title      	: GenerateXMLUsingXMLCli
Description	: This function generate the XML using XMLCli and Binary File or BIOS ROM file.
Inputs		: PathToXMLCliFolder,Interface,InputBinFileOrROMFile
Outputs		: XML file
'''  
def GenerateXMLUsingXMLCli(PathToXMLCliFolder,Interface,InputBinFileOrROMFile):
    import pysvtools.xmlcli.XmlCli as cli
    cli.clb._setCliAccess(Interface)
    abc = cli.savexml(0, InputBinFileOrROMFile)
    print ("************************************")
    print ("XML Created using XMLCli, ....   ", abc)
    print ("************************************")

'''
Set the Knob changes according to the user inputed CSV file and generate new XML file. 
Title      	: SetBiosDataInXMLFile
Description	: This function generate the XML using XMLCli with the Knob changes given by user.
Inputs		: PatchFileData, iXmlFile, oXmlFile
Outputs		: XML file
'''  
def SetBiosDataInXMLFile(PatchFileData, iXmlFile, oXmlFile):
    iXmlFileTree = ET.parse(iXmlFile)
    KnobArray=[]
    for I in PatchFileData:
        SearchString = './/{0}'.format(I['XMLtag'])
        print ("Current Knob being worked on: ", I, "  in file: ", iXmlFile)
        for x in iXmlFileTree.findall(SearchString):
            y = x.attrib
            if (y['prompt'].strip().upper().find(I['Prompt'].strip().upper()) >= 0):
                #print("My changes here reached:    ", I)
                if (I['DefaultValue']== ''):
                    #print("My changes here reached:    Defai;t Valie os Blank")
                    oldval=y['CurrentVal']
                    x.set('CurrentVal', I['CurrentValue'])
                    print ("Knob:--> ",I['Prompt'], "," ,"Old CurrentVal:",oldval, "," , "New CurrentVal:",I['CurrentValue'])
                    KnobArray.append("=".join([y['name'], I['CurrentValue']]))
                elif (I['CurrentValue']== ''):
                    print("My changes here reached:    Current Valie os Blank")
                    oldval=y['default']
                    print ("Knob:--> ",I['Prompt'], "," ,"Old DefaultVal:",oldval, "," , "New DefaultVal:",I['DefaultValue'])
                    x.set('default', I['DefaultValue'])
                    KnobArray.append("=".join([y['name'], I['DefaultValue']]))

    iXmlFileTree.write('temp.xml', pretty_print=True, xml_declaration=True, encoding="utf-8")
    IFWI_GenerateXML.FixSpaces('temp.xml', oXmlFile)
    return KnobArray

'''
Automatically Program the Knob changes into the Binary File.
Title      	: GenerateBinaryUsingKnobChanges
Description	: This function program the Knob changes using XMLCli and generate the Binary File or BIOS ROM File
Inputs		: PathToXMLCliFolder,Interface,InputBinFileOrROMFile
Outputs		: Binary File or BIOS ROM file
'''  
def GenerateBinaryUsingKnobChanges(PathToXMLCliFolder,Interface,InputBinFileOrROMFile,KnobArray):
    import pysvtools.xmlcli.XmlCli as cli
    cli.clb._setCliAccess(Interface)
    s = ",".join(KnobArray)
    print ("************************************")
    print ("Program Knobs into Binary File")
    print ("************************************")
    cli.CvProgKnobs(s, InputBinFileOrROMFile)


def CreateKnobChangesFile(PathToXMLCliFolder,InputKnobFile,Interface,InputBinFileOrROMFile):
    oXmlFile = PathToXMLCliFolder +"\\"+ IFWI_GenerateXML.GetOutputXMLFileName(InputKnobFile)
    PatchFileData = IFWI_GenerateXML.GetConfigDataToApply(InputKnobFile,PathToXMLCliFolder)
    CWD = os.getcwd()
    os.chdir(PathToXMLCliFolder+ "\out")
    for file in glob.glob("*.xml"):
        print ("XML File generated by XMLCli: "+(file))
    KnobData=SetBiosDataInXMLFile(PatchFileData,PathToXMLCliFolder+"\\out\\"+ file, oXmlFile)
    GenerateBinaryUsingKnobChanges(PathToXMLCliFolder,Interface,InputBinFileOrROMFile,KnobData)
    os.chdir(CWD)
    return oXmlFile

def AutomateKnobChanges(PathToXMLCliFolder,Interface,InputBinFileOrROMFile,InputKnobFile):

    GenerateXMLUsingXMLCli(PathToXMLCliFolder,Interface,InputBinFileOrROMFile)
    CreateKnobChangesFile(PathToXMLCliFolder,InputKnobFile,Interface,InputBinFileOrROMFile)

'''
Read the Knob changes and apply them into the BIOS Binary File.
Title      	: ApplyBiosKnobs
Description	: This function program the Knobs into the BIOS ROM  
Inputs		: Requestor,Data,ConfigFileDetails,XMLCLIPATH
Outputs		: BIOS ROM file
'''
def ApplyBiosKnobs(Data, XMLCLIBaseFolder, ROMFilePath):
    sys.path.append(XMLCLIBaseFolder)
    XMLCLIPath = XMLCLIBaseFolder + "\pysvtools\\xmlcli"
    xmlCLIOutFolder = XMLCLIPath + "\out"
    KNOBFilePath = XMLCLIPath + "\knob.csv"
    FHSO = ['XMLtag', 'Prompt', 'DefaultValue', 'CurrentValue', 'Comments']
    RowElement = {'XMLtag':'knob', 'Prompt':'', 'DefaultValue':'', 'CurrentValue':'', 'Comments':''}
    Command_List = []

    for row in Data:
        RowElement['Prompt'] = row['XMLtag']
        RowElement['CurrentValue'] = row['Value']
        Command_List.append(OrderedDict(RowElement))


    #Generating the knob file from the input params
    IFWI_PreOSBuildCommonCode.WriteBackConfigContentsInMemory(KNOBFilePath, Command_List, FHSO, ',')
    KNOBFileName = os.path.basename(KNOBFilePath)
    BiosROM = os.path.basename(ROMFilePath)
    print("BIOS ROM name : ", ROMFilePath)


    AutomateKnobChanges(XMLCLIPath, 'stub', ROMFilePath, KNOBFileName)

    BiosROMName, BiosROMExt = os.path.splitext(os.path.basename(ROMFilePath))
    print("BiosROMExt",BiosROMExt)


    for basename in os.listdir(xmlCLIOutFolder):
        if basename.startswith(BiosROMName) and basename.endswith("New"+BiosROMExt):
            pathname = os.path.join(xmlCLIOutFolder, basename)
            if os.path.isfile(pathname):
                print("SANT", pathname, ROMFilePath)
                shutil.copy2(pathname, ROMFilePath)

    print("****BIOS Knob Settings Applied Successfuly ****")
    print("BIOS outfile generated at ", ROMFilePath)
    return "BIOS Knob Settings Applied Successfully \n"



def main():
    args = setup_arg_parse()
    PathToXMLCliFolder=args.x
    Interface=args.i
    InputBinFileOrROMFile=args.b
    InputKnobFile=args.k
    AutomateKnobChanges(PathToXMLCliFolder,Interface,InputBinFileOrROMFile,InputKnobFile)

if __name__ == "__main__":
    main()

