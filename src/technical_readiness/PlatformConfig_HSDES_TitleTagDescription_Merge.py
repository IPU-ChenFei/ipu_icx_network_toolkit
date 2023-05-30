'''
Copyright (c) 2022, Intel Corporation. All rights reserved.
Intention is the find the %age linkage between TCD and FR also classify against each Owner teams...
Finding Automation Status from HSDES and sanity per team
Readiness for running directly from HSDES via scheduler (CC or TCF)

Title      	: PlatformConfig_Updates_Score_V2.py
Author(s)  	: Santosh, Deshpande
Description	: Uses connected records of config_version subject only and performs 
			  following:
				Concatnates the Title
				Concatnates the Tags
				Concatnates the Description
Inputs		: Each function has relevant header details for input and output
Output		: Each function has relevant header details for input and output
Sample Cmd	: python PlatformConfig_HSDES_TitleTagDescription_Merge.py -q 160161472690d0 -r 16016464285 (Keep only query Valid)
'''
import argparse
import os
import sys
import base64
import requests
from requests_kerberos import HTTPKerberosAuth
import urllib3
import time
import json

headers = { 'Content-type': 'application/json' }
proxy = {'http': '', 'https': ''}
# this is to ignore the ssl insecure warning as we are passing in 'verify=false'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def setup_arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', help='Update the Platform Configs based on the Query 0 to ignore', required=True, metavar="PCQ")
    parser.add_argument('-r', help='Update for specific Platform Config Record 0 to ignore', required=True, metavar="PCR")
    args = parser.parse_args()
    return args

def HaveRecordedConfigParent(hsdesRecordID):
	ConnectedList = []
	url = 'https://hsdes-api.intel.com/rest/trace/tree/related/%s' % hsdesRecordID
	url = url + '/config_version?labelFilter=%2Bconfig_version'
	response = requests.get(url, verify=False, auth=HTTPKerberosAuth(), headers = headers)
	NodesList = response.json()['nodes']
	#print (url)
	#print (NodesList)
	if (len(NodesList) > 1):
		for Elements in NodesList:
			if (len(Elements) == 2):
				#print(Elements)
				for IDList in Elements:
					if (IDList['id'] != int(hsdesRecordID)):
						ConnectedList.append(IDList['id'])
	#print (ConnectedList)
	return (ConnectedList)

def GetQueryRecordList(hsdesQueryID):
	url = 'https://hsdes-api.intel.com/rest/query/%s?include_text_fields=Y&start_at=1&max_results=500' % hsdesQueryID
	response = requests.get(url, verify=False, auth=HTTPKerberosAuth(), headers = headers)
	#print(response)
	#print(url)
	for var,val in response.json().items():
		if (var.upper().find("DATA") >=0 ):
			return (val)
	return None

def GetRecordDetails(RecordID):
	url = 'https://hsdes-api.intel.com/rest/article/%s' %RecordID
	url = url + '?fields=title%2Cdescription%2Ctag'
	response = requests.get(url, verify=False, auth=HTTPKerberosAuth(), headers = headers)
	#print (response)
	#print(url)
	data = response.json()['data'][0]
	return (data)

def UpdateRecordWithMergedData (Title, Description, Tags, RecordID):
	url='https://hsdes-api.intel.com/rest/article/%s' %RecordID
	url=url+'?fetch=false&debug=false'
	ValueFields = {'title': Title, 'description':Description, 'tag': Tags}
	PayloadData = {'subject': 'config_version', 'tenant': 'server_platf', 'fieldValues': [ValueFields]}
	PayloadData = json.dumps(PayloadData)
	# print(PayloadData)
	#exit()
	response = requests.put(url, verify=False, auth=HTTPKerberosAuth(), headers = headers, data=PayloadData)
	print(response)
	return

def UpdateSinglePlatformRecord(EachPlatformConfig):
	ParentConfigList = GetRecordDetails(EachPlatformConfig)
	Title_Temp = ParentConfigList['title'].split(":")
	Title = [None,None,None,None]
	Description_Index = ParentConfigList['description'].find('DETAILS *****')
	Description_TXT = ''
	#print (Description_Index)
	if (-1 != Description_Index):
		Description_Index = Description_Index+35
		Description_TXT = ParentConfigList['description'][0:Description_Index]
	#print(Description_Temp)
	Description= [None,None,None,None]
	Tags = [None,None,None,None]
	Index = -100
	
	ParentConfigList = HaveRecordedConfigParent(EachPlatformConfig)
	for ParentConfigListElement in ParentConfigList:
		RecordDetailsListToUpdate = GetRecordDetails(ParentConfigListElement)
		Index = -1
		if (None != RecordDetailsListToUpdate['tag']):
			if ('CONFIG_MEMORY' in RecordDetailsListToUpdate['tag']):
				Index = 0
			if ('CONFIG_IO' in RecordDetailsListToUpdate['tag']):
				Index = 1
			if ('CONFIG_UPI' in RecordDetailsListToUpdate['tag']):
				Index = 3
			if ('CONFIG_STORAGE' in RecordDetailsListToUpdate['tag']):
				Index = 2
			if ('CONFIG_NETWORK' in RecordDetailsListToUpdate['tag']):
				Index = 1
			Tags[Index] = RecordDetailsListToUpdate['tag']

		if (None != RecordDetailsListToUpdate['title']):
			Title[Index] = RecordDetailsListToUpdate['title']
		if (None !=RecordDetailsListToUpdate['description']):
			Description[Index] = RecordDetailsListToUpdate['description']

	Title_TXT = Title_Temp[0]+ ': '
	#Description_TXT = Description_Temp [0] + ' DETAILS *****</span><br></p> \n'
	Tags_TXT = ''
	for Index in range(0,4):
		if (None != Title[Index]):
			Title_TXT = Title_TXT + ' ' + Title[Index]
		if (None != Tags[Index]):
			Tags_TXT = Tags_TXT + ',' + Tags[Index]
		if (None != Description[Index]):
			Description_TXT = Description_TXT + Description[Index]
	
	#print (Title_TXT)
	#print (Description_TXT)
	#print (Tags_TXT)
	UpdateRecordWithMergedData(Title_TXT, Description_TXT, Tags_TXT, EachPlatformConfig)

def UpdatePlatformRecord(QueryID):
	Initial_Time = time.time()
	EGSApprovedQueryList = GetQueryRecordList(QueryID)
	print ("Records fetched time:  ", time.time()-Initial_Time)
	Initial_Time = time.time()
	for EachPlatformConfig in EGSApprovedQueryList:
		UpdateSinglePlatformRecord(EachPlatformConfig['id'])
	print ("Records fetched time:  ", time.time()-Initial_Time)
	
def main():
    args = setup_arg_parse()
    QueryID = args.q
    SinglePlatformRecord = args.r
    if (int(QueryID) != 0):
        UpdatePlatformRecord(QueryID)
    if (int(SinglePlatformRecord) != 0):
        UpdateSinglePlatformRecord(SinglePlatformRecord)
    

if __name__ == "__main__":
    main()