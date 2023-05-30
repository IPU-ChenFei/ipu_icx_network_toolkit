'''
Copyright (c) 2022, Intel Corporation. All rights reserved.
Intention is to use HSDES query and platform config to generate, trigger and
update results back to HSDES using CommandCenter and HSDES rest APIs

Title          : volume_validation_business_logic_deployment.py
Author(s)      : Mandar Chandrakant Thorat; Santosh Deshpande

Documentation:
BKM Link               : https://wiki.ith.intel.com/display/DCGBKC/C2C+Automation+Build+Check-in+to+Results+in+Dashboard
HSDES-API Link         : https://hsdes.intel.com/rest/doc/
Artifactory-API Link   : https://www.jfrog.com/confluence/display/JFROG/Artifactory+REST+API
Command Centre API Link: https://api.commandcenter.iind.intel.com/swagger/ui/index
OneBKC API Link        : https://onebkc.intel.com/v2/api-docs/

Command Line to execute:
python volume_validation_business_logic_deployment.py -f template.json --framework "DPG_Automation_master_272022_1.0.1413_E" --rhelPrKit "EGS-SRV-RHEL-22.24.2.15A" --centOSKit "EGS-SRV-CENTOS-STREAM-22.24.2.15B" --win2022Kit "EGS-SRV-WIN2022-22.24.2.15E"

Dependency Files:
Additional packages needed: src/technical_readiness/atpce_requirements.txt
Tool Configuration File   : src/technical_readiness/template.json

External File requirement:
Command Centre file: TestCases.XML (from any execution NUC, \\$NUC\DPG_Automation\dtaf_content\testCases.xml)
'''

import argparse
import getpass
import json
import logging
import time
import shutil
import traceback
import random
from datetime import datetime

import socket
import requests
import urllib3
from lxml import etree as ET
from requests_kerberos import HTTPKerberosAuth
from requests_ntlm import HttpNtlmAuth

# create formatter
formatter = logging.Formatter('%(asctime)s - %(funcName)20s - %(levelname)s - %(message)s')
# create first logger
logger = logging.getLogger('first logger')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(filename=datetime.now().strftime('ctc_%d_%m_%Y__%H_%M.log'))
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

qlogger = logging.getLogger('query logger')
qlogger.setLevel(logging.INFO)
query_logger = logging.FileHandler(filename=datetime.now().strftime('ctc_queries_%d_%m_%Y__%H_%M.log'))
query_logger.setFormatter(formatter)
qlogger.addHandler(query_logger)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

headers = {'Content-type': 'application/json'}
proxy = {'http': '', 'https': ''}

# this is to ignore the ssl insecure warning as we are passing in 'verify=false'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

user = getpass.getuser()
password = getpass.getpass()
auth = HttpNtlmAuth(user, password)

CC_MAPPING_FILE = "c:\\temp\\testCases.xml"
HSDES_CONFIGURATION = 'server_platf.test_case.configuration'
HSDES_TITLE = 'title'
HSDES_VERSION = 'config_version.version'
HSDES_OWNERTEAM = 'test_case_definition.owner_team'
HSDES_RELEASE = 'release'
HSDES_QUERY_TEMPLATE = "<Query xmlns=\"https://hsdes.intel.com/schemas/2012/Query\"><Filter><Parent><WhereClause Operand=\"MATCH ALL\"><Criteria Name=\"R1\"><Subject Value=\"server_platf.test_case\"/><CriteriaField Value=\"id\"/><FieldOperator Value=\"greater than\"/><FieldValue Value=\"'0'\"/><FieldType Value=\"bigint\"/></Criteria><Criteria Name=\"R2\"><Subject Value=\"server_platf.test_case\"/><CriteriaField Value=\"server_platf.test_case.planned_for\"/><FieldOperator Value=\"contains\"/><FieldValue Offset=\"1\" Value=\"\u0027{0}\u0027\"/><FieldType Value=\"multisel\"/></Criteria><Criteria Name=\"R3\"><Subject Value=\"server_platf.test_case\"/><CriteriaField Value=\"status\"/><FieldOperator Value=\"not in\"/><FieldValue Offset=\"1\" Value=\"'rejected','blocked','future'\"/><FieldType Value=\"singlesel\"/></Criteria><Criteria Name=\"R4\"><Subject Value=\"server_platf.test_case\"/><CriteriaField Value=\"title\"/><FieldOperator Value=\"does not start with\"/><FieldValue Offset=\"1\" Value=\"'Testrecord'\"/><FieldType Value=\"varchar\"/></Criteria></WhereClause><Hierarchy/></Parent><Flags/></Filter><Display Displayas=\"shortname\"><DisplayField Visible=\"true\" Shortname=\"id\" Fullname=\"id\"/><DisplayField Visible=\"true\" Shortname=\"parent_id\" Fullname=\"parent_id\"/><DisplayField Visible=\"true\" Shortname=\"title\" Fullname=\"title\"/><DisplayField Visible=\"true\" Shortname=\"configuration\" Fullname=\"server_platf.test_case.configuration\"/><DisplayField Visible=\"true\" Shortname=\"planned_for\" Fullname=\"server_platf.test_case.planned_for\"/><DisplayField Visible=\"true\" Shortname=\"test_cycle\" Fullname=\"test_case.test_cycle\"/><DisplayField Visible=\"true\" Shortname=\"owner_team\" Fullname=\"test_case.owner_team\"/><DisplayField Visible=\"true\" Shortname=\"status\" Fullname=\"status\"/><DisplayField Visible=\"true\" Shortname=\"tag\" Fullname=\"tag\"/><DisplayField Visible=\"true\" Shortname=\"notify\" Fullname=\"notify\"/></Display><SortOrder/></Query>"

      
HSDES_TEST_CASE = "test_case"
HSDES_TEST_RESULT = "test_result"

d = {}


def setup_arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', help='Path to Commandcenter Config file', required=True, metavar="PathToCCConfigFile")
    parser.add_argument('--framework', action="store", dest="frameworkKit",
                        default="DPG_Automation_testing_global_rhel_path_112022_1.0.333_E",
                        help="DTAF automation Framework Kit")
    parser.add_argument('--rhelPrKit', action="store", dest="rhelPrKit",
                        default="EGS-SRV-RHEL-22.10.6.165E",
                        help="RHEL Product Kit")
    parser.add_argument('--centOSKit', action="store", dest="centOSStrPrKit",
                        default="EGS-SRV-CENTOS-STREAM-22.10.6.165D",
                        help="CentOS Stream product Kit")
    parser.add_argument('--win2022Kit', action="store", dest="win2022PrKit",
                        default="EGS-SRV-WIN2022-22.10.6.165G",
                        help="windows 2022 OS product Kit")

    args = parser.parse_args()
    return args


def readJsonConfigContents(jsonConfigFile):
    with open(jsonConfigFile) as handle:
        config_file_data = json.loads(handle.read())
    logger.debug("ConfigContents: {0}".format(config_file_data))
    return config_file_data


def workWeekRetriver():
    WW = str(datetime.utcnow().isocalendar()[0]) + str(datetime.utcnow().isocalendar()[1])
    return WW


def workWeekDayRetriver(buildNumber=1):
    WW = str(datetime.utcnow().isocalendar()[0]) + "WW" + str(
        datetime.utcnow().isocalendar()[1]) + "." + str(datetime.utcnow().isocalendar()[2])
    #WW = WW + "." + str(buildNumber)
    return WW


def ccGetApi(url):
    '''
    Execute get request using CommandCenter API

    :param url: url for get request'''
    logger.debug(url)
    try:
        response = requests.get(url, verify=False, auth=auth, headers=headers)
        # logger.info("CC Get status code={0} response={1}".format(response.status_code, response.json()))
    except Exception as ex:
        logger.error("Failed to execute get request : {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()

    return response.json()


def ccPostApi(url, data):
    '''
    Execute post request using CommandCenter API

    :param url: url for post request
    :param data: payload for post request
    '''
    try:
        logger.debug("url:{0} data:{1}".format(url, json.dumps(data, indent=4)))
        response = requests.post(url, verify=False, auth=auth, headers=headers, data=str(data))
        logger.info("CC Get status code={0} response={1}".format(response.status_code, response.json()))
    except Exception as ex:
        logger.error("Failed to execute post request : {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()

    return response.json()


def runCCTestScripts(scriptID, controllerIPName, frameworkKit, productKit):
    url = 'https://api.commandcenter.iind.intel.com/api/ci/v1/scripts/run'
    test_setup = {
        "Controller": controllerIPName,
        "RemoteInstance": "Bangalore"
    }
    payload_data = {"ScriptId": str(scriptID),
                    "Tag": "Autorun_CC_Script_ID",
                    "ProductVersion": productKit,
                    "BlockReschedules": "true",
                    "WaitForAllComponents": "false",
                    "DelayBetweenRetriesInMinutes": "30",
                    "FrameworkVersionsList": ["DTAF", frameworkKit],
                    "Force": "false",
                    "TestSetups": [test_setup]
                    }
    payload_data = json.dumps(payload_data)
    logger.debug(payload_data)

    ret = ccPostApi(url, payload_data)
    return ret['ResultId']


def readRunResults(resultID):
    logger.debug("Read RunResults for {0}".format(resultID))
    url = 'https://api.commandcenter.iind.intel.com/api/ci/v1/scripts/result/%s' % resultID
    return ccGetApi(url)


def getControllerStatus(controllerIP):
    logger.debug("Get controller status for {0}".format(controllerIP))
    url = 'https://api.commandcenter.iind.intel.com/api/ci/v1/testSetups?controller={0}&remoteInstance=Bangalore'.format(
        controllerIP)
    ret = ccGetApi(url)
    return ret['Status'], ret['UsedBy'], ret['IsConnected']


def getCCTestcaseXml(controllerIP):
    source_path = r"\\{0}\c$\DPG_Automation\dtaf_content".format(controllerIP)
    file_name = "\\testCases.xml"
    shutil.copyfile(source_path + file_name, CC_MAPPING_FILE)


def getCCTestPackageList(testCasesXml):
    '''
    Generate map of CommandCenter package to test case

    :param testCasesXml: file required by CommandCenter
    :return testCaseToPackageMap: map of package and test cases
    '''
    iXmlFileTree = ET.parse(testCasesXml)
    SearchString = './/{0}'.format("TestCase")
    testCaseToPackageMap = {}
    for XmlTag in iXmlFileTree.findall(SearchString):
        PackageName = ""
        TestCaseName = ""
        for SubElement in XmlTag:
            if (SubElement.tag.upper().find("PackageName".upper()) >= 0):
                PackageName = SubElement.text
            if (SubElement.tag.upper().find("TestCaseName".upper()) >= 0):
                TestCaseName = SubElement.text

        if TestCaseName not in testCaseToPackageMap:
            testCaseToPackageMap[TestCaseName] = []
        testCaseToPackageMap[TestCaseName].append(PackageName)
    return testCaseToPackageMap


def createTestScript(execution_config, CCRecordsTRList, testCaseToPackageMap, projectName,
                     frameworkBuild, MS_Title_WW, MY_TIMEOUT_IN_SEC, ownerTeamToMilestoneList, productKit):
    '''
    Prepare CommandCenter TestScript using HSDES TCD query data

    :param execution_config: execution config name
    :param CCRecords: dictionary containing details on execution config to testcase mapping
    :param testCaseToPackageMap: Map of testcase to testpackage in CC
    :param projectName: CommandCenter project name
    :param frameworkBuild: framework kit to be used
    :param MS_Title_WW: Milestone Title appended with WW
    :param MY_TIMEOUT_IN_SEC: TestScript Execution timeout
    :return ScriptId - created CC TestScript ID
    '''
    CCRecordsTRList_exec = []
    logger.debug("Create CommandCenter TestScriptID and Fire: ")
    url = 'https://api.commandcenter.iind.intel.com/api/ci/v1/scripts/create?projectName={0}&buildVersion={1}'.format(
        projectName, frameworkBuild)
    logger.debug(url)

    execution_timeout = time.strftime('%H:%M:%S', time.gmtime(MY_TIMEOUT_IN_SEC))

    all_tc_data = []
    for ccElement in CCRecordsTRList:
        if ccElement['title'] not in testCaseToPackageMap:
            logger.debug("Title {0} is not found in CC package list".format(ccElement['title']))
            continue
        details = {"ProductKit":productKit,
                   "Execution Type": "C2C Framework",
                   "OS Variant":ccElement['OS'],
                   "SUT Execution Config HSDES ID": execution_config,
                   "RASP_ID": "TBI"
                   }
        test_package_name = testCaseToPackageMap[ccElement['title']][0]
        ccElement['TR_id'] = 0 #stubbed createTestResult(ccElement['testResultTitle'], ccElement['tc_id'], ownerTeamToMilestoneList[ccElement['Owner_Team']]['TestCycleTitle'], json.dumps(details))
        ## TODO: verify with commandline to uniquely run related test script

        tc_data = {
            "FrameworkPackageName": test_package_name,
            "IsEvent": 'false',
            "Type": "TEST_CASE",
            "Name": ccElement['title'],
            "Properties": {
                "RepeatsIfFail": 0  # right one
            },
        }
        all_tc_data.append(tc_data)
        CCRecordsTRList_exec.append(ccElement)

    data = {
        "Type": "TEST_SCRIPT",
        "Name": MS_Title_WW,
        "Properties": {
            "ExecutionTimeout": execution_timeout
        },
        "ChildrenComponents": [
            {
                "Type": "TEST_PACKAGE",
                "Name": execution_config,
                "ChildrenComponents": all_tc_data
            }
        ]
    }
    ret = ccPostApi(url, data)
    return ret['ScriptId'], CCRecordsTRList_exec


def addSetup(scriptID, controllerIP, runID):
    if controllerIP not in d:
        d[controllerIP] = {scriptID: runID}
    else:
        logger.debug("Incorrect controllerIP:{0}, scriptID:{1} and runID{2}".format(controllerIP, scriptID, runID))


def verifySetupReady():
    d1 = d.copy()
    logger.debug(d1)
    for element, val in enumerate(d.items()):
        status, user, isConnected = getControllerStatus(val[0])
        logger.debug("status:{0}, User:{1}, isConnected:{2}".format(status, user, isConnected))
        if status == 'Free' and user == "" and isConnected == True:
            d1.pop(val[0])
    return True if len(d1) == 0 else False


def getQueryRecordList(hsdesQueryID):
    url = 'https://hsdes-api.intel.com/rest/query/%s?include_text_fields=Y&start_at=1&max_results=10000' % hsdesQueryID
    try:
        response = requests.get(url, verify=False, auth=HTTPKerberosAuth(), headers=headers)
        logger.debug(response.json())
    except Exception as ex:
        logger.error("Unable to get record list: {}".format(ex, url))
        logger.error(traceback.format_exc())
        raise Exception()

    for var, val in response.json().items():
        if (var.upper().find("DATA") >= 0):
            return (val)
    return None


def hsdesPostApi(url, data):
    '''
    Execute post request using HSDES API

    :param url: url for post request
    :param data: payload for post request
    '''
    logger.debug("url:{0} data:{1}".format(url, json.dumps(data, indent=4)))
    try:
        response = requests.post(url, verify=False, auth=HTTPKerberosAuth(), headers=headers, data=str(data))
        logger.info("HSDES Get status code={0} response={1}".format(response.status_code, response.json()))
    except Exception as ex:
        logger.error("Failed to execute post request : {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()

    return response.json()


def createHSDQueries(milestone_title, tenant, magazineId=2207261098):
    queryXml = HSDES_QUERY_TEMPLATE.format(tenant, milestone_title)

    fields = {
        "title": "{0}_{1}".format(milestone_title, tenant),
        "magazineId": magazineId,
        "queryXml": queryXml
    }
    fields = json.dumps(fields)
    url = 'https://hsdes-api.intel.com/rest/query'

    res = hsdesPostApi(url, fields)
    qlogger.info("{0}: https://hsdes.intel.com/appstore/community/#/{1}?queryId={2}".format(tenant, magazineId,
                                                                                            res['newId']))

def createHSDTestPlanBasedQuery(testPlanId='16017351889', magazineId=16013412367):
    planned_for = GetRecordDetails(testPlanId, HSDES_TITLE)
    queryXml = HSDES_QUERY_TEMPLATE.format(planned_for)

    fields = {
        "title": "{0}_{1}".format(planned_for, workWeekRetriver()),
        "magazineId": magazineId,
        "category": "public",
        "queryXml": queryXml
    }
    fields = json.dumps(fields)
    url = 'https://hsdes-api.intel.com/rest/query'

    res = hsdesPostApi(url, fields)
    qlogger.info(" https://hsdes.intel.com/appstore/community/#/{0}?queryId={1}".format(magazineId, res['newId']))
    print(" https://hsdes.intel.com/appstore/community/#/{0}?queryId={1}".format(magazineId, res['newId']))
    return res['newId']

def createHSDESEntry(FieldValues, subject, url='https://hsdes-api.intel.com/rest/article?fetch=false&debug=false'):
    payload_data = {
        "tenant": "server_platf",
        "subject": subject,
        "fieldValues": [FieldValues]
    }
    payload_data = json.dumps(payload_data)
    logger.debug(payload_data)
    try:
        response = requests.post(url, verify=False, auth=HTTPKerberosAuth(), headers=headers, data=str(payload_data))
        logger.info("createHSDESEntry: {0} {1}".format(response.status_code, response.json()))
        record_id = response.json()["new_id"]
    except Exception as ex:
        logger.error("Unable to post HSDES request: {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()
    return record_id


def createTestPlan(title, owner_team, MY_PROGRAM_NAME, MY_FAMILY_NAME):
    logger.debug("Create HSDES Testplan: ")
    FieldValues = {
        "title": title,
        "family_affected": MY_FAMILY_NAME,
        "status": "open",
        "test_plan.nodetype": "test_plan",
        "test_plan.owner_team": owner_team,
        "release_affected": MY_PROGRAM_NAME,
        "tag": "C2C_Automation_Run_VIA_CC"
    }
    return createHSDESEntry(FieldValues, "test_plan")


def createMilestone(milestone_breakdown, eta_ww, owner_team, MY_PROGRAM_NAME, description=''):
    logger.debug("Create HSDES Milestone: ")
    FieldValues = {
        "milestone.milestone_breakdown": milestone_breakdown,
        "milestone.eta_request_ww": eta_ww,
        "milestone.owner_team": owner_team,
        "owner": user,
        "release": MY_PROGRAM_NAME,
        "status": "open",
        "tag": "C2C_Automation_Run_VIA_CC",
		"description": description
    }
    return createHSDESEntry(FieldValues, "milestone")


def GetRecordDetails(RecordID, fields):
    url = 'https://hsdes-api.intel.com/rest/article/%s' % RecordID
    url = url + '?fields={0}'.format(fields)
    try:
        response = requests.get(url, verify=False, auth=HTTPKerberosAuth(), headers=headers)
        #logger.debug("response status_code: {0}".format(response.status_code))
        if (fields.find(',') < 0):
            data = response.json()['data'][0][fields]
        else:
            data = response.json()['data'][0]
    except Exception as ex:
        logger.error("Unable to get HSDES record details: {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()
    return (data)


def SetRecordDetails(RecordID, subject, fields):
    payload_data = {
        "tenant": "server_platf",
        "subject": subject,
        "fieldValues": [{'description':json.dumps(fields, indent=4)}]
    }

    payload_data = json.dumps(payload_data)

    url = 'https://hsdes-api.intel.com/rest/article/%s' % RecordID
    url = url + '?fields={0}'.format('description')
    try:
        response = requests.put(url, verify=False, auth=HTTPKerberosAuth(), headers=headers, data=str(payload_data))
        logger.debug("response status_code: {0} {1}".format(response.status_code, response.json()))
    except Exception as ex:
        logger.error("Unable to get HSDES record details: {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()


def safeSetRecordDetails(RecordID, subject, fields):

    description = GetRecordDetails(RecordID, 'description')
    print(description)
    x = description.replace('&quot;', '"')
    print(x)
    if x != '':
        description_Json = json.loads(x)
    else:
        description_Json = {}
    print(description_Json)
    print('****')

    for k,v in description_Json.items():
        if k in fields.keys():
            description_Json[k] = description_Json[k] + ',' + fields[k]

    for k,v in fields.items():
        if k not in description_Json.keys():
            description_Json[k] = fields[k]

    SetRecordDetails(RecordID, subject, description_Json)

def HaveRecordedConfigParent(hsdesRecordID, RecordType="config_version"):
    ConnectedList = []
    url = 'https://hsdes-api.intel.com/rest/trace/tree/related/%s' % hsdesRecordID
    url = url + '/test_case_definition?labelFilter=%2B' + RecordType
    try:
        response = requests.get(url, verify=False, auth=HTTPKerberosAuth(), headers=headers)
        NodesList = response.json()['nodes']
    except Exception as ex:
        logger.error("Unable to get HSDES request: {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()
    if (len(NodesList) > 1):
        for Elements in NodesList:
            if (len(Elements) == 2):
                for IDList in Elements:
                    if (IDList['id'] != int(hsdesRecordID)):
                        ConnectedList.append(IDList['id'])
    return (ConnectedList)


def updateTestCase(tcId, current_mileStones, milestone):
    updated_milestone = milestone
    if len(current_mileStones) > 0:
        updated_milestone = current_mileStones + ',' + milestone
    FieldValues = {
        # test_cycle should be title of milestone record
        "test_case.test_cycle": updated_milestone
    }
    url = 'https://hsdes-api.intel.com/rest/article/{0}?fetch=false&debug=false'.format(tcId)
    payload_data = {
        "tenant": "server_platf",
        "subject": "test_case",
        "fieldValues": [FieldValues]
    }

    payload_data = json.dumps(payload_data)
    logger.debug(payload_data)

    try:
        response = requests.put(url, verify=False, auth=HTTPKerberosAuth(), headers=headers, data=str(payload_data))
        logger.debug("updateTestCase: {0} {1}".format(response.status_code, response.json()))
    except Exception as ex:
        logger.error("Unable to update test_case: {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()

def updateTestResult(el, trId, status, reason, prKit): #, PreSightingID):
    detailsstr = GetRecordDetails(trId, 'test_result.details')
    details = json.loads(detailsstr)
    details['Test_Result'] = 'complete'
    details['start_time'] = el['StartTime']
    details['stop_time'] = el['StopTime']
    from datetime import datetime
    date_format = "%Y-%m-%dT%H:%M:%S"
    start_time = datetime.strptime(el['StartTime'].split('.')[0], date_format)
    stop_time = datetime.strptime(el['StopTime'].split('.')[0], date_format)
    details['duration'] = str(stop_time - start_time)
    details['log_files'] = el['LogFiles']

    if prKit:
        details['product_kit'] = prKit

    # if (PreSightingID == 0):
    FieldValues = {
        "status": status,
        "reason": reason,
        "test_result.details": json.dumps(details, indent=4),
    }
    # else:
    #     FieldValues = {
    #         "status": status,
    #         "reason": reason,
    #         "test_result.details": json.dumps(details),
    #         "test_result.free_tag_1": str(PreSightingID)
    #     }

    url = 'https://hsdes-api.intel.com/rest/article/{0}?fetch=false&debug=false'.format(trId)
    payload_data = {
        "tenant": "server_platf",
        "subject": "test_result",
        "fieldValues": [FieldValues]
    }

    payload_data = json.dumps(payload_data)
    logger.debug("updateTestResult: {0}".format(payload_data))

    try:
        response = requests.put(url, verify=False, auth=HTTPKerberosAuth(), headers=headers, data=str(payload_data))
        logger.debug("updateTestResult: {0} {1}".format(response.status_code, response.json()))
    except Exception as ex:
        logger.error("Unable to update test_result: {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()


def createTestCase(title, planned_for, config_title, owner_team, TCDid):
    logger.debug("Create HSDES Test case: ")
    FieldValues = {
        "title": title,
        "server_platf.test_case.configuration": config_title,
        "owner": user,
        "test_case.owner_team": owner_team,
        "server_platf.test_case.planned_for": planned_for,
        "parent_id": TCDid,
        "relationship": "parent-child",
        "tag": "C2C_Automation_Run_VIA_CC"
    }
    return createHSDESEntry(FieldValues, "test_case")


def getPlatformConfigLinkedRecords(TCD_ID):
    # for a platform config we will get single SUT for now, use OWNER_TEAM to filter later
    url = "https://hsdes-api.intel.com/rest/trace/tree/record-hierarchy/{0}/test_case_definition?labelFilter=%2Bconfig_version".format(
        TCD_ID)
    logger.debug("ConfigLinkedRecords: {0}".format(url))
    try:
        response = requests.get(url, verify=False, auth=HTTPKerberosAuth(), headers=headers)
        logger.debug("ConfigLinkedRecords: {0} {1}".format(response.status_code, response.json()))
        nodesList = response.json()['nodes']
    except Exception as ex:
        logger.error("Unable to get ConfigLinkRecords: {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()

    logger.debug("ConfigLinkedRecords nodes: {0}".format(nodesList))

    platformConfigList = []
    for node in nodesList:
        if node['level'] != "1":
            continue
        platformConfigList.append(node['id'])
    return platformConfigList

'''
Go over full TCD List create new test case or update the Test Case as appropriate
Return the Test Case List and Platform Config List those are interconnected
Each PlatformConfig will have associated Test Cases
'''
def createUpdateTestCaseList(MY_PLAN_ID, TCDQueryId=0):
    fullPlatformConfigList = []
    fullTCPCConnectedList = {}
    ownerTeamList = []
    TestRecordConnectedData = {}

    ##Make sure to update the list with OwnerTeam

    if (TCDQueryId != 0):
        planned_for = GetRecordDetails(MY_PLAN_ID, HSDES_TITLE)
        TCDList = getQueryRecordList(TCDQueryId)
        for TCDElement in TCDList:
            platformConfigList = getPlatformConfigLinkedRecords(TCDElement['id'])
            Owner_Team = GetRecordDetails(TCDElement['id'], "test_case.owner_team")
            if Owner_Team not in ownerTeamList:
                ownerTeamList.append(Owner_Team)
            #Generate unique list of fullPlatformConfigList
            for platformConfigElement in platformConfigList:
                if platformConfigElement not in fullPlatformConfigList:
                    fullPlatformConfigList.append(platformConfigElement)
                    fullTCPCConnectedList[platformConfigElement]=[]
            createTestCaseList(planned_for, TCDElement, platformConfigList, fullTCPCConnectedList)
    else:
        TCQueryId = createHSDTestPlanBasedQuery(MY_PLAN_ID)
        configuratationInTestCaseMatch = {}
        TCRecordListPerPlan = getQueryRecordList(str(TCQueryId))
        #This is hardcoded for list of Platform configs that are available for people consume as of today...
        #Parameterize this static value 1 time.
        PCRecordList = getQueryRecordList('16017438636')
        for PCRecordElement in PCRecordList:
            #if Platform Config is not activated disable deployment of test cases....
            if (PCRecordElement['status'] != 'active'):
                print ("This Platform Config is not deployed please reach out to platform validation architect")
                continue
            configuratationInTestCaseMatch[PCRecordElement['release']+'-'+PCRecordElement['version']] = PCRecordElement['id']
            fullPlatformConfigList.append(PCRecordElement['id'])
            fullTCPCConnectedList[PCRecordElement['id']] = []
        print (configuratationInTestCaseMatch)

        for TCRecordListElement in TCRecordListPerPlan:
            TestRecordConnectedData[TCRecordListElement['id']] = {}
            TestRecordConnectedData[TCRecordListElement['id']]['title'] = TCRecordListElement['title']
            TestRecordConnectedData[TCRecordListElement['id']]['parent_id'] = TCRecordListElement['parent_id']
            TestRecordConnectedData[TCRecordListElement['id']]['configuration'] = TCRecordListElement['configuration']
            TestRecordConnectedData[TCRecordListElement['id']]['planned_for'] = TCRecordListElement['planned_for']
            TestRecordConnectedData[TCRecordListElement['id']]['test_cycle'] = TCRecordListElement['test_cycle']
            TestRecordConnectedData[TCRecordListElement['id']]['owner_team'] = TCRecordListElement['owner_team']
            TestRecordConnectedData[TCRecordListElement['id']]['status'] = TCRecordListElement['status']
            TestRecordConnectedData[TCRecordListElement['id']]['tag'] = TCRecordListElement['tag']
            TestRecordConnectedData[TCRecordListElement['id']]['notify'] = TCRecordListElement['notify']
            TestCaseDefinitionData = GetRecordDetails(TCRecordListElement['parent_id'], "title,server_platf.test_case_definition.operating_system,server_platf.test_case_definition.pre_condition,server_platf.test_case_definition.automation_framework,server_platf.test_case_definition.automation_status,server_platf.test_case_definition.command_line,id")

            TestRecordConnectedData[TCRecordListElement['id']]['TCD_title'] = TestCaseDefinitionData['title']
            TestRecordConnectedData[TCRecordListElement['id']]['OSList'] = TestCaseDefinitionData['server_platf.test_case_definition.operating_system']
            TestRecordConnectedData[TCRecordListElement['id']]['Pre_Condition'] = TestCaseDefinitionData['server_platf.test_case_definition.pre_condition']
            TestRecordConnectedData[TCRecordListElement['id']]['Automation_Framework'] = TestCaseDefinitionData['server_platf.test_case_definition.automation_framework']
            TestRecordConnectedData[TCRecordListElement['id']]['Automation_Status'] = TestCaseDefinitionData['server_platf.test_case_definition.automation_status']
            TestRecordConnectedData[TCRecordListElement['id']]['Command_Line'] = TestCaseDefinitionData['server_platf.test_case_definition.command_line']

            #Check if platform config is deoplyed or not if not skip activity...
            if TCRecordListElement['configuration'] not in configuratationInTestCaseMatch.keys():
                continue
            fullTCPCConnectedList[configuratationInTestCaseMatch[TCRecordListElement['configuration']]].append(TCRecordListElement['id'])
            if TCRecordListElement['owner_team'] not in ownerTeamList:
                ownerTeamList.append(TCRecordListElement['owner_team'])
        print (fullTCPCConnectedList)
        print (configuratationInTestCaseMatch)

    return fullTCPCConnectedList, ownerTeamList, TestRecordConnectedData


'''
ExecutionType: 
    0 - New Run
    1 - Resume
    next step is split by OS
    sort on Owner_team within OS
    Get PreCondition information for any updates into IFWI, or content_config*.xml file for NUC prepration
    HW Config based matching (future)
'''
def createTestResultList(fullTCPCConnectedList, TestRecordConnectedData, test_cycle, ExecutionType=0):
    ExecutionConfigToTR = {}
    if ExecutionType == 0:
        for PlatformConfigElement, TCList in fullTCPCConnectedList.items():
            OSArrangedList = {}
            for TCElement in TCList:
                #stubbed updateTestCase(TCElement, TestRecordConnectedData[TCElement]['test_cycle'], test_cycle)
                OSListStr = TestRecordConnectedData[TCElement]['OSList']
                if (OSListStr == None):
                    logger.debug("Skipped TC ", TCElement, " TCD DIDN't HAVE OS LISTED ", TestRecordConnectedData[TCElement]['parent_id'])
                else:
                    #Create Multiple Test Results and start putting it in different queues.. For now use only 1
                    #With-OS sort by Owner team as well...
                    OSList = OSListStr.split(',')
                    for OS in OSList:
                        TRDataContent = {}
                        if OS not in OSArrangedList.keys():
                            OSArrangedList[OS] = []
                        TRDataContent['testResultTitle'] = TestRecordConnectedData[TCElement]['title']
                        TRDataContent['title'] = TestRecordConnectedData[TCElement]['TCD_title']
                        TRDataContent['OS'] = OS
                        TRDataContent['test_result'] = 'NOT_RUN'
                        TRDataContent['Owner_Team'] = TestRecordConnectedData[TCElement]['owner_team']
                        TRDataContent['tc_id'] = TCElement
                        TRDataContent['TR_id'] = 0
                        OSArrangedList[OS].append(TRDataContent)
            OSArrangedList_Ordered = {}
            for OS, TCOSList  in OSArrangedList.items():
                OSArrangedList_Ordered[OS] = sorted(TCOSList, key=lambda OwnerTeam: OwnerTeam['Owner_Team'])
            ExecutionConfigToTR[PlatformConfigElement] = OSArrangedList_Ordered
    else:
        print("Create the TR Query for this TestCycleMilestone and filter only on test_result.resaon_other = NOT_RUN")
    return ExecutionConfigToTR


def createOrchestratorSpecificExecutionList(TRList, testCycleMilestone):
    for TRElement in TRList:
        resultTitle = GetRecordDetails(TRElement, HSDES_TITLE)
        # TODO: FIx 'cc_id'
        CCExecutionRecord = {'cc_id': str(TRElement), 'title': resultTitle, 'test_result': TRElement,
                             'Execution_Update_Status': False, 'Execution_test_result': 'NOT_RUN'}
    return None


def stopOrchestratorSpecificExecution(executionConfigResultId):
    return None


def resumeOrchestratorExecution(testCycleMilestone):
    return None



def createTestCaseList(planned_for, TCDid, ConfigList, fullTCPCConnectedList):
    '''
    TCD + platform Config creates a test case if it doesn't exist
    If a config link is removed, then it won't be considered for execution
    if a new config is added new testcases should be created
    Every testcase created always gets linked to TCD
        For a given TCD; identify all applicable configs
        For a given TCD & all applicable configs; return list of connected testcases
        Identify matching TCs for current execution
            if there are no testcases linked to TCD then create TestCase and link to TCD

    :param title: TCD Title
    :param planned_for: Test Plan Title
    :param milestone: Milestone(test_cycle) Title
    :param TCDid: TCD ID to add parent-child relation
    :param MY_PROGRAM_NAME: Test Plan release_affected name
    :param PlatformConfigList: Platform config Title list
    :return TC_IDList: Test Case ID list
    '''
    TestCaseList = HaveRecordedConfigParent(TCDid, "test_case")
    title = GetRecordDetails(TCDid, HSDES_TITLE)
    owner_team = GetRecordDetails(TCDid, "owner_team")  # TODO TCD owner team""
    for ConfigListElement in ConfigList:
        TC_ID = 0
        ConfigRelease = GetRecordDetails(ConfigListElement, HSDES_RELEASE)
        ConfigVersion = GetRecordDetails(ConfigListElement, HSDES_VERSION)

        UpdatedTitle = title + '_' + ConfigRelease + '-' + ConfigVersion
        for TestCaseListElement in TestCaseList:
            TestCaseTitle = GetRecordDetails(TestCaseListElement, HSDES_TITLE)
            if (TestCaseTitle.find(UpdatedTitle) >= 0):
                TC_ID = TestCaseListElement
                updateTestCase(TC_ID, planned_for)
                break
        if (TC_ID == 0):
            TC_ID = createTestCase(UpdatedTitle, planned_for, ConfigRelease + "-" + ConfigVersion, owner_team, TCDid)
        # add list of Testcase IDs for current run into the associated Platform Config List
        fullTCPCConnectedList[ConfigListElement].append(TC_ID)
    return None


def createTestResult(title, parent_id, milestone, details):
    logger.debug("Create HSDES Test result: ")
    FieldValues = {
        "title": title,
        "relationship": "parent-child",
        "parent_id": parent_id,
        "status": "open",
        "test_result.test_cycle": milestone,
        "reason_other":"NOT_RUN",
        "tag": "C2C_Automation_Run_VIA_CC",
        "test_result.details": details
    }
    return createHSDESEntry(FieldValues, "test_result")


def createPresighting(title, runID, SIGHTING_DATA_REQUIREMENTS, MY_PROGRAM_NAME, bkc):
    logger.debug("Create HSDES Pre-sighting: ")
    FieldValues = {
        "title": title,
        "description": runID,
        "bug.exposure": "4-low",
        "bug.team_found": SIGHTING_DATA_REQUIREMENTS['team_found'],
        "server_platf.bug.phase_found": SIGHTING_DATA_REQUIREMENTS['phase_found'],
        "bug.report_type": "presighting",
        "bug.platform": SIGHTING_DATA_REQUIREMENTS['bug.platform'],
        "server_platf.bug.product_found": SIGHTING_DATA_REQUIREMENTS['product_found'],
        "bug.how_found": "testing",
        "release": MY_PROGRAM_NAME,
        "bug.to_reproduce": runID,
        "server_platf.bug.configuration": runID,
        "server_platf.bug.suspect_area": SIGHTING_DATA_REQUIREMENTS['suspect_area'],
        "server_platf.bug.bkc_version": bkc,
        "bug.reproducibility": "once",
        "server_platf.bug.soc_family": SIGHTING_DATA_REQUIREMENTS['soc_family'],
        "server_platf.bug.soc_version": SIGHTING_DATA_REQUIREMENTS['soc_version'],
        "tag": "C2C_Automation_Run_VIA_CC"
    }
    return createHSDESEntry(FieldValues, "bug")


def getOwnerTeamDetails(TCD_ID):
    owner = GetRecordDetails(TCD_ID, HSDES_OWNERTEAM)
    logger.debug("Onwer Team of the TCD: {0}".format(owner))
    return owner


def getHWConfigList(fullTCPCConnectedList):
    # for a platform config we will get single SUT for now, use OWNER_TEAM to filter later
    platformConfigToSUTExecutionConfigList = {}

    try:
        for platformConfigElement, TCList in fullTCPCConnectedList.items():
            url = "https://hsdes-api.intel.com/rest/trace/tree/record-related-hierarchy/{0}/config_version?maxLevel=1&labelFilter=%2Bconfig_version".format(
                platformConfigElement)
            print (url)
            logger.debug("ConfigLinkedRecords: {0}".format(url))
            response = requests.get(url, verify=False, auth=HTTPKerberosAuth(), headers=headers)
            logger.debug("ConfigLinkedRecords: {0} {1}".format(response.status_code, response.json()))
            print("ConfigLinkedRecords: {0} {1}".format(response.status_code, response.json()))
            nodesList = response.json()['nodes']
            SUTCount = 0

            for node in nodesList:
                if node['level'] != "1":
                    continue
                # List out all the SUTExecutionConfig and connect it to Platform Config.
                if (SUTCount == 0):
                    platformConfigToSUTExecutionConfigList[platformConfigElement] = []
                #Check if SUTExecutionConfig is deployed by checking if Execution Machine is active for VV
                DeploymentStatus = GetRecordDetails(node['id'], 'status')
                if (DeploymentStatus == 'active'):
                    platformConfigToSUTExecutionConfigList[platformConfigElement].append({node['id']:socket.gethostbyname(GetRecordDetails(node['id'], HSDES_TITLE))})
                SUTCount += 1

    except Exception as ex:
        logger.error("Unable to get ConfigLinkRecords: {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()

    logger.debug("ConfigLinkedRecords nodes: {0}".format(nodesList))

    return platformConfigToSUTExecutionConfigList

def provisionNUCSetup(HWToSUTConnectedConfigList, scriptID='831910805', frameworkKit = 'DPG_Automation_master_272022_1.0.1413_E', executionTimeOut=60, poolingDelay=10):
    ExecutionConfigCount = 0

    for PlatformConfigElement, ExecutionConfigList in HWToSUTConnectedConfigList.items():
        for ExecutionConfigElement in ExecutionConfigList:
            for ExecutionConfigHSDID, NUCIPAddr in ExecutionConfigElement.items():
                runID = runCCTestScripts(scriptID, NUCIPAddr, frameworkKit, None)
                print ("SANTOSH https://commandcenter.iind.intel.com/Results/SummaryReport/", runID)
                addSetup(scriptID, NUCIPAddr, runID)
            ExecutionConfigCount += 1

    # wait for Commpletion of all the SUT updates with Framekwork build.
    print ("Total Execution system ", ExecutionConfigCount)
    startTime = time.time()
    while time.time() - startTime < executionTimeOut:
        if verifySetupReady():
            break
        else:
            time.sleep(poolingDelay)
    else:
        logger.error("Timeout reached for script execution..")


def getSUTExecutionStatus(ccRecord, prKit, MS_Title):
    res = readRunResults(ccRecord['result_id'])
    ccRecord["OverallResult"] =res["OverallResult"]
    logger.debug("run result: {0}".format(res))
    for i, el in enumerate(res['TestScriptItems']):
        # pre_sighting_id = 0
        logger.debug("TestScriptItems: {}".format(el))
        status = "open"
        reason = ""
        if i==0 :
            continue

        if el['Type'] == 'TEST_CASE' and el['Result'] not in ("NOT_RUN", "RUNNING"):
            if ccRecord['TR_list'][i-1]['test_result'] == 'NOT_RUN':
                ccRecord['TR_list'][i-1]['test_result'] = 'complete'
                result = el['Result'].lower()
                if result == "passed":
                    status = "complete"
                    reason = "pass"
                elif result == "failed":
                    status = "complete"
                    reason = "fail"
                    # if prKit:
                    #     pre_sighting_id = createPresighting(el['Name'] + "+" + MS_Title, result_id, prKit)

                logger.debug("ValidateAndUpdateResults: {} {} {} {}".format(ccRecord['TR_list'][i-1]['TR_id'], status, reason,
                                                                      prKit)) #, pre_sighting_id))
                #stubbed
                # for retry in range(2):
                #     updateTestResult(el, ccRecord['TR_list'][i-1]['TR_id'], status, reason, prKit) #, pre_sighting_id)
    return ccRecord

def getOverallExecutionStatus(ccRecordsList, prKit, MS_Title):
    all_machine_status = len(ccRecordsList)
    for i, ccRecord in enumerate(ccRecordsList):
        if ccRecord['OverallResult'] not in ('RUNNING', 'NOT_RUN'):
            all_machine_status -= 1
            continue
        getSUTExecutionStatus(ccRecord, prKit, MS_Title)

    return all_machine_status, ccRecordsList


def main():
    args = setup_arg_parse()
    filePath = args.f

    jsonRecord = readJsonConfigContents(filePath)
    MY_PLAN_ID = jsonRecord['MY_PLAN_ID']
    MY_TIMEOUT_IN_SEC = int(jsonRecord['MY_TIMEOUT_IN_SEC'])
    CC_PROJECT_NAME = jsonRecord['CC_PROJECT_NAME']
    CC_COPYDPGBUILD = jsonRecord['CC_COPYDPGBUILD']
    MY_WW = workWeekRetriver()
    MY_PROGRAM_NAME = GetRecordDetails(MY_PLAN_ID, 'release_affected')

    # Planning from TCD->TC.
    #Create/Update/Get Test Case List connected to appropriate Platform Config per HSDES
    fullTCPCConnectedList, ownerTeamList, TestRecordConnectedData = createUpdateTestCaseList(MY_PLAN_ID)

    #Get All SUT Configs that are connected all Platform Configs in HSDES
    HWToSUTConnectedConfigList = getHWConfigList(fullTCPCConnectedList)
    
    #Invoke Command Center action to fix all machines with NUC Provisioning parallelly
    provisionNUCSetup(HWToSUTConnectedConfigList, CC_COPYDPGBUILD)

    # Execution from TC->TR.
    # create Cycle Per team
    WW = workWeekDayRetriver()
    Updated_Title =  GetRecordDetails('22015547471', 'title') #GetRecordDetails(MY_PLAN_ID, 'title') + "." + WW + str(18)
    ownerTeamToMilestoneList = {}
    for ownerTeamElement in ownerTeamList:
        milestoneID = '22015547471' #stubbed out createMilestone(Updated_Title, MY_WW, ownerTeamElement, MY_PROGRAM_NAME)
        ownerTeamToMilestoneList[ownerTeamElement] = {'TestCycleTitle':GetRecordDetails(milestoneID, HSDES_TITLE),
                                                      'TestCycleID':milestoneID}
    Master_milestoneID = '22015547471' #stubbed out createMilestone(Updated_Title, MY_WW, GetRecordDetails(MY_PLAN_ID, 'test_plan.owner_team'),
                                         # MY_PROGRAM_NAME, json.dumps(ownerTeamToMilestoneList))

    testResultList = createTestResultList(fullTCPCConnectedList, TestRecordConnectedData, Updated_Title)

    testCaseToPackageMap = getCCTestPackageList(CC_MAPPING_FILE)
    logger.debug("Got created with Command Centre Package Details: {}".format(testCaseToPackageMap))

    ccRecordsList = []
    time.sleep(60)
    startTime = time.time()

    productKit = 'EGS-SRV-CENTOS-STREAM-22.24.2.15B'  # element[element['os']]
    for pc_id, ec_list in HWToSUTConnectedConfigList.items():
        OSCount = 0
        for ec_element in ec_list:
            ccRecords = {}
            epochTime = time.time()
            ccRecords['NUC'] = list(ec_element.values())[0]
            if (OSCount == 0): ccRecords['TR_list'] = testResultList[pc_id]['CentOS']
            if (OSCount == 1): ccRecords['TR_list'] = testResultList[pc_id]['RHEL']
            if (OSCount == 2): ccRecords['TR_list'] = testResultList[pc_id]['Windows']
            OSCount += 1
            ccRecords['ec_id'] = str(list(ec_element.keys())[0])
            testScriptId, ccRecords['TR_list'] = createTestScript(ccRecords['ec_id'], ccRecords['TR_list'],
                                                 testCaseToPackageMap, CC_PROJECT_NAME,
                                                 args.frameworkKit,
                                                 GetRecordDetails(Master_milestoneID, HSDES_TITLE) + ccRecords['NUC'] +'a'+str(
                                                 int(random.random() * 100000)),
                                                 MY_TIMEOUT_IN_SEC, ownerTeamToMilestoneList, productKit)
            resultID = runCCTestScripts(testScriptId, ccRecords['NUC'], args.frameworkKit, productKit)
            logger.debug("# Trigger time for record {0}: {1} ".format(testScriptId, time.time() - epochTime))
            logger.debug(resultID)
            description = "https://commandcenter.iind.intel.com/Results/DetailedRunReport/{0}".format(resultID)
            safeSetRecordDetails(Master_milestoneID, 'milestone',
                                 {"description": description})
            ccRecords['result_id'] = resultID
            ccRecords['testScriptId'] = testScriptId
            ccRecords['OverallResult'] = 'RUNNING'
            ccRecordsList.append(ccRecords)

    time.sleep(30)

    while ((time.time() - startTime) < MY_TIMEOUT_IN_SEC):
        all_machine_status, ccRecordsList = getOverallExecutionStatus(ccRecordsList, productKit, GetRecordDetails(Master_milestoneID, HSDES_TITLE))
        if all_machine_status == 0:
            break
        else:
            time.sleep(60)
    else:
        logger.error("Timeout reached for script execution..")


if __name__ == "__main__":
    main()
