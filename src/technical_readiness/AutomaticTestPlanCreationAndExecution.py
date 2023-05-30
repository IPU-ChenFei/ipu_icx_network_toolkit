'''
Copyright (c) 2022, Intel Corporation. All rights reserved.
Intention is to use HSDES query and platform config to generate, trigger and
update results back to HSDES using CommandCenter and HSDES rest APIs

Title          : AutomatingTestPlanCreationAndExecution.py
Author(s)      : Mandar Chandrakant Thorat; Santosh Deshpande

Documentation:
BKM Link               : https://wiki.ith.intel.com/display/DCGBKC/C2C+Automation+Build+Check-in+to+Results+in+Dashboard
HSDES-API Link         : https://hsdes.intel.com/rest/doc/
Artifactory-API Link   : https://www.jfrog.com/confluence/display/JFROG/Artifactory+REST+API
Command Centre API Link: https://api.commandcenter.iind.intel.com/swagger/ui/index
OneBKC API Link        : https://onebkc.intel.com/v2/api-docs/

Command Line to execute:
python AutomaticTestPlanCreationAndExecution.py -f template.json --framework "DPG_Automation_master_212022_1.0.976_E" --rhelPrKit "EGS-SRV-RHEL-22.10.6.165E" --centOSKit "EGS-SRV-CENTOS-STREAM-22.10.6.165D" --win2022Kit "EGS-SRV-WIN2022-22.10.6.165G"

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
from datetime import datetime

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
HSDES_QUERY_TEMPLATE = "<Query xmlns=\"https://hsdes.intel.com/schemas/2012/Query\"><Filter><Parent><WhereClause Operand=\"MATCH ALL\"><Criteria Name=\"R1\"><Subject Value=\"server_platf.{0}\"/><CriteriaField Value=\"id\"/><FieldOperator Value=\"greater than\"/><FieldValue Value=\"\u00270\u0027\"/><FieldType Value=\"bigint\"/></Criteria><Criteria Name=\"R2\"><Subject Value=\"server_platf.{0}\"/><CriteriaField Value=\"{0}.test_cycle\"/><FieldOperator Value=\"in\"/><FieldValue Offset=\"1\" Value=\"\u0027{1}\u0027\"/><FieldType Value=\"multisel\"/></Criteria></WhereClause><Hierarchy/></Parent><Flags/></Filter><Display Displayas=\"shortname\"><DisplayField Visible=\"true\" Shortname=\"id\" Fullname=\"id\"/><DisplayField Visible=\"true\" Shortname=\"title\" Fullname=\"title\"/><DisplayField Visible=\"true\" Shortname=\"command_line\" Fullname=\"server_platf.test_case_definition.command_line\"/></Display><SortOrder/></Query>"
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
    WW = WW + "." + str(buildNumber)
    return WW


def ccGetApi(url):
    '''
    Execute get request using CommandCenter API

    :param url: url for get request'''
    logger.debug("CC Get API")
    logger.debug(url)
    try:
        response = requests.get(url, verify=False, auth=auth, headers=headers)
        logger.info("CC Get status code={0} response={1}".format(response.status_code, response.json()))
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


def createTestScript(execution_config, CCRecords, testCaseToPackageMap, projectName,
                     frameworkBuild, MS_Title_WW, MY_TIMEOUT_IN_SEC):
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
    logger.debug("Create CommandCenter TestScriptID and Fire: ")
    url = 'https://api.commandcenter.iind.intel.com/api/ci/v1/scripts/create?projectName={0}&buildVersion={1}'.format(
        projectName, frameworkBuild)
    logger.debug(url)

    execution_timeout = time.strftime('%H:%M:%S', time.gmtime(MY_TIMEOUT_IN_SEC))

    all_tc_data = []
    for ccElement in CCRecords:
        if ccElement['title'] not in testCaseToPackageMap:
            logger.debug("Title {0} is not found in CC package list".format(ccElement['title']))
            continue

        test_package_name = testCaseToPackageMap[ccElement['title']][0]
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
    return ret['ScriptId']


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


def doScriptProvisioning(systemDetails, provisioningScriptID, frameworkKit, sleepTimeout=2400,
                         pollingDelay=300, execTimeout=3000):
    '''
    Run specific CommandCenter Provisioning TestScript

    :param systemDetails: list of execution configs
    :param provisioningScriptID: CC testScript ID to be used
    :param frameworkKit: framework kit to be used
    '''
    startTime = time.time()
    for i, element in enumerate(systemDetails):
        logger.debug("Setup {}:".format(i + 1))
        epochTime = time.time()
        productKit = element[element['os']]
        if isinstance(provisioningScriptID, dict):
            element['scriptID'] = provisioningScriptID[element['os']]
        else:
            element['scriptID'] = provisioningScriptID

        ###TODO: add method
        runID = runCCTestScripts(element['scriptID'], element['controllerIPName'], frameworkKit, productKit)
        logger.debug("# Trigger time for record {0} with runID {1}: {2} seconds ".format(element["scriptID"],
                                                                                         runID,
                                                                                         time.time() - epochTime))
        addSetup(element['scriptID'], element['controllerIPName'], runID)

    logger.debug(">> Total execution time = {0} seconds <<".format(time.time() - startTime))

    time.sleep(sleepTimeout)
    startTime = time.time()

    while time.time() - startTime < execTimeout:
        if verifySetupReady():
            break
        else:
            time.sleep(pollingDelay)
    else:
        logger.error("Timeout reached for script execution..")


def doProvisioning(DO_PROVISION, systemDetails, CC_COPYDPGBUILD, CC_FW_Only, CC_PROVISIONING_TESTSCRIPT_ID,
                   frameworkKit):
    '''
    Control various CommandCenter Provisioning TestScripts

    :param DO_PROVISION: supports 'no'=framework copy only,
                                  'fwo'=framework copy + firmware flashing or
                                  'all'=framework copy + firmware flashing
    :param systemDetails: list of execution_config controller IPs
    :param CC_COPYDPGBUILD: CC testScriptID for copying framework
    :param CC_FW_Only: CC testScriptID for flashing firmwares(CPLD, IFWI, BMC)
    :param CC_PROVISIONING_TESTSCRIPT_ID: CC testScriptID for OS provisioning(RHEL, CentOS or Windows)
    '''
    if DO_PROVISION.lower() in ['no', 'fwo', 'all']:
        doScriptProvisioning(systemDetails, CC_COPYDPGBUILD, frameworkKit, sleepTimeout=60,
                             pollingDelay=30, execTimeout=300)
    if DO_PROVISION.lower() in ['fwo', 'all']:
        doScriptProvisioning(systemDetails, CC_FW_Only, frameworkKit, sleepTimeout=600,
                             pollingDelay=150, execTimeout=3600)
    if DO_PROVISION.lower() in ['all']:
        doScriptProvisioning(systemDetails, CC_PROVISIONING_TESTSCRIPT_ID, frameworkKit,
                             sleepTimeout=1080, pollingDelay=240, execTimeout=5400)


def getQueryRecordList(hsdesQueryID):
    url = 'https://hsdes-api.intel.com/rest/query/%s?include_text_fields=Y&start_at=1&max_results=10000' % hsdesQueryID
    try:
        response = requests.get(url, verify=False, auth=HTTPKerberosAuth(), headers=headers)
        logger.debug(response.json())
    except Exception as ex:
        logger.error("Unable to get record list: {}".format(ex))
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
    try:
        response = requests.post(url, verify=False, auth=HTTPKerberosAuth(), headers=headers, data=str(data))
        logger.info("HSDES Get status code={0} response={1}".format(response.status_code, response.json()))
    except Exception as ex:
        logger.error("Failed to execute post request : {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()

    return response.json()


def hsdesGetApi(url):
    '''
    Execute get request using HSDES API

    :param url: url for post request
    '''
    try:
        response = requests.get(url, verify=False, auth=HTTPKerberosAuth(), headers=headers)
        logger.info("HSDES Get status code={0} response={1}".format(response.status_code, response.json()))
    except Exception as ex:
        logger.error("Failed to execute get request : {}".format(ex))
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


def createMilestone(milestone_breakdown, eta_ww, owner_team, MY_PROGRAM_NAME):
    logger.debug("Create HSDES Milestone: ")
    FieldValues = {
        "milestone.milestone_breakdown": milestone_breakdown,
        "milestone.eta_request_ww": eta_ww,
        "milestone.owner_team": owner_team,
        "owner": user,
        "release": MY_PROGRAM_NAME,
        "status": "open",
        "tag": "C2C_Automation_Run_VIA_CC"
    }
    return createHSDESEntry(FieldValues, "milestone")


def GetRecordDetails(RecordID, fields):
    url = 'https://hsdes-api.intel.com/rest/article/%s' % RecordID
    url = url + '?fields={0}'.format(fields)
    try:
        response = requests.get(url, verify=False, auth=HTTPKerberosAuth(), headers=headers)
        logger.debug("response status_code: {0}".format(response.status_code))
        data = response.json()['data'][0][fields]
    except Exception as ex:
        logger.error("Unable to get HSDES record details: {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()
    return (data)


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


def updateTestCase(tcId, planned_for, milestone):
    Current_Planned_For = GetRecordDetails(tcId, 'server_platf.test_case.planned_for')
    Current_MileStones = GetRecordDetails(tcId, 'test_case.test_cycle')
    FieldValues = {
        # Planned_for should be same as name of test_plan
        "server_platf.test_case.planned_for": Current_Planned_For + ',' + planned_for,
        # test_cycle should be title of milestone record
        "test_case.test_cycle": Current_MileStones + ',' + milestone
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

def updateTestResult(trId, status, reason, prKit, PreSightingID):
    details = "C2C_Automation_Run_VIA_CC"
    if prKit:
        details = details + "  product Kit: " + prKit
    if (PreSightingID == 0):
        FieldValues = {
            "status": status,
            "reason": reason,
            "test_result.details": details,
        }
    else:
        FieldValues = {
            "status": status,
            "reason": reason,
            "test_result.details": details,
            "test_result.free_tag_1": str(PreSightingID)
        }

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


def createTestCase(title, planned_for, config_title, owner_team, milestone, parent_id):
    logger.debug("Create HSDES Test case: ")
    FieldValues = {
        "title": title,
        "server_platf.test_case.configuration": config_title,
        "owner": user,
        "test_case.owner_team": owner_team,
        "server_platf.test_case.planned_for": planned_for,
        "parent_id": parent_id,
        "relationship": "parent-child",
        "test_case.test_cycle": milestone,
        "tag": "C2C_Automation_Run_VIA_CC"
    }
    return createHSDESEntry(FieldValues, "test_case")


def createTestCaseList(title, planned_for, owner_team, milestone, parent_id, MY_PROGRAM_NAME, PlatformConfigList):
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
    :param owner_team: Test Plan Owner Team
    :param milestone: Milestone(test_cycle) Title
    :param parent_id: TCD ID to add parent-child relation
    :param MY_PROGRAM_NAME: Test Plan release_affected name
    :param PlatformConfigList: Platform config Title list
    :return TC_IDList: Test Case ID list
    '''
    TC_IDList = []
    ConfigList = HaveRecordedConfigParent(parent_id)
    TestCaseList = HaveRecordedConfigParent(parent_id, "test_case")
    for ConfigListElement in ConfigList:
        TC_ID = 0
        ConfigTitle = GetRecordDetails(ConfigListElement, HSDES_TITLE)
        ConfigVersion = GetRecordDetails(ConfigListElement, HSDES_VERSION)
        if ConfigTitle not in PlatformConfigList:
            continue
        UpdatedTitle = title + '_' + ConfigTitle
        for TestCaseListElement in TestCaseList:
            TestCaseTitle = GetRecordDetails(TestCaseListElement, HSDES_TITLE)
            if (TestCaseTitle.find(UpdatedTitle) >= 0):
                TC_ID = TestCaseListElement
                updateTestCase(TC_ID, planned_for, milestone)
                break
        if (TC_ID == 0):
            TC_ID = createTestCase(UpdatedTitle, planned_for, MY_PROGRAM_NAME + "-" + ConfigVersion, owner_team,
                                   milestone, parent_id)
        # add list of Testcase IDs for current run
        TC_IDList.append(TC_ID)
    return TC_IDList


def createTestResult(title, parent_id, milestone):
    logger.debug("Create HSDES Test result: ")
    FieldValues = {
        "title": title,
        "relationship": "parent-child",
        "parent_id": parent_id,
        "status": "open",
        "test_result.test_cycle": milestone,
        "tag": "C2C_Automation_Run_VIA_CC"
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


def createHSDESRecordsForCycle(MY_WW, MY_TEAM, Execution_Run, MY_TITLE, MY_PROGRAM_NAME, buildNumber,
                               PlatformConfigList):
    '''
    Create Milestone, Test Case and Test Results for given cycle and execution_configs

    :return AllCCRecord: Map of platform configs and related test cases for CommandCenter
    :return TEST_CYCLE_TITLE: Milestone record Title
    :return Updated_Title: milestone_breakdown (Test Plan Title, WW, Day and Build number)
    '''
    WW = workWeekDayRetriver(buildNumber)
    Updated_Title = MY_TITLE + "." + WW
    milestoneID = createMilestone(Updated_Title, MY_WW, MY_TEAM, MY_PROGRAM_NAME)
    TEST_CYCLE_TITLE = GetRecordDetails(milestoneID, HSDES_TITLE)
    # The TCD query which needs to be executed per plan based on planned_for
    AllCCRecord = {}

    for Element in Execution_Run:
        Title = Element['title']
        TCD_ID = Element['id']
        # Create test_case for each Test case definition + platform config.
        # Also updated planned_for and Test_cycle for each milestone run
        TC_ID_List = createTestCaseList(Title, MY_TITLE, MY_TEAM, TEST_CYCLE_TITLE, TCD_ID, MY_PROGRAM_NAME,
                                        PlatformConfigList)
        for TCElement in TC_ID_List:
            resultTitle = GetRecordDetails(TCElement, HSDES_TITLE)
            TestCasePlatformConfig = GetRecordDetails(TCElement, HSDES_CONFIGURATION)
            # Create test_result for each test_case
            TR_ID = createTestResult(resultTitle, TCElement, TEST_CYCLE_TITLE)
            CCExecutionRecord = {'cc_id': str(TCElement), 'title': Title, 'test_result': TR_ID,
                                 'Execution_Update_Status': False, 'Execution_test_result': 'NOT_RUN'}

            if TestCasePlatformConfig not in AllCCRecord:
                AllCCRecord[TestCasePlatformConfig] = []

            AllCCRecord[TestCasePlatformConfig].append(CCExecutionRecord)

    logger.debug(AllCCRecord)
    return AllCCRecord, TEST_CYCLE_TITLE, Updated_Title


def ValidateAndUpdateResults(ccRecords, prKit, MS_Title, SIGHTING_DATA_REQUIREMENTS, MY_PROGRAM_NAME):
    flag = []
    for k, v in ccRecords.items():
        result_id = v[0]['cc_id']
        res = readRunResults(result_id)
        logger.debug("run result: {0}".format(res))
        flag.append(res["OverallResult"] != "RUNNING")
        for i, el in enumerate(res['TestScriptItems']):
            pre_sighting_id = 0
            logger.debug("TestScriptItems: {}".format(el))

            if el['Type'] == 'TEST_CASE' and el['Result'] not in ("NOT_RUN", "RUNNING"):
                if v[i - 1]['Execution_Update_Status'] == False:
                    result = el['Result'].lower()
                    if result == "passed":
                        status = "complete"
                        reason = "pass"
                    elif result == "failed":
                        status = "complete"
                        reason = "fail"
                        if prKit:
                            pre_sighting_id = createPresighting(el['Name'] + "+" + MS_Title, result_id,
                                                                SIGHTING_DATA_REQUIREMENTS, MY_PROGRAM_NAME, prKit)
                    else:
                        status = "rejected"
                        reason = "not_valid"

                    logger.debug(
                        "ValidateAndUpdateResults: {} {} {} {} {}".format(v[i - 1]['test_result'], status, reason,
                                                                          prKit, pre_sighting_id))
                    updateTestResult(v[i - 1]['test_result'], status, reason, prKit, pre_sighting_id)
                    v[i - 1]['Execution_Update_Status'] = True
                    v[i - 1]['Execution_test_result'] = reason
    return flag, ccRecords


def getOwnerTeamDetails(TCD_ID):
    owner = GetRecordDetails(TCD_ID, HSDES_OWNERTEAM)
    logger.debug("Onwer Team of the TCD: {0}".format(owner))
    return owner


def getConfigLinkRecord(TCD_ID):
    # for a platform config we will get single SUT for now, use OWNER_TEAM to filter later
    url = "https://hsdes-api.intel.com/rest/trace/tree/record-hierarchy/{0}/test_case_definition?labelFilter=%2Bconfig_version".format(
        TCD_ID)
    logger.debug("ConfigLinkedRecords: {0}".format(url))
    OWNER_TEAM = getOwnerTeamDetails(TCD_ID)
    try:
        response = requests.get(url, verify=False, auth=HTTPKerberosAuth(), headers=headers)
        logger.debug("ConfigLinkedRecords: {0} {1}".format(response.status_code, response.json()))

        nodesList = response.json()['nodes']
    except Exception as ex:
        logger.error("Unable to get ConfigLinkRecords: {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()

    logger.debug("ConfigLinkedRecords nodes: {0}".format(nodesList))

    systemlist = []
    for node in nodesList:
        if node['level'] != "2":
            continue
        # TODO next level of control is via Owner Team Name based on the TCD and pick only relevant machines
        desc = GetRecordDetails(node['id'], "server_platf.config_version.details_json")
        SystemInfo = json.loads(desc)
        SystemInfo['platformConfigID'] = node['tree_parent_id']
        systemlist.append(SystemInfo)
    return systemlist


def main():
    args = setup_arg_parse()
    filePath = args.f

    jsonRecord = readJsonConfigContents(filePath)
    PlatformConfigList = []
    systemDetails = []

    MY_PLAN_ID = jsonRecord['MY_PLAN_ID']
    MY_TITLE = GetRecordDetails(MY_PLAN_ID, 'title')
    MY_TEAM = GetRecordDetails(MY_PLAN_ID, 'test_plan.owner_team')
    MY_PROGRAM_NAME = GetRecordDetails(MY_PLAN_ID, 'release_affected')
    MY_FAMILY_NAME = GetRecordDetails(MY_PLAN_ID, 'family_affected')
    MYQUERY_ID = jsonRecord['MYQUERY_ID']
    MY_RUN_NUMBER = jsonRecord['MY_RUN_NUMBER']
    MY_WW = workWeekRetriver()
    MY_TIMEOUT_IN_SEC = int(jsonRecord['MY_TIMEOUT_IN_SEC'])
    DO_PROVISION = jsonRecord['PROVISION']
    CC_PROJECT_NAME = jsonRecord['CC_PROJECT_NAME']
    CC_COPYDPGBUILD = jsonRecord['CC_COPYDPGBUILD']
    CC_FW_Only = jsonRecord['CC_FW_Only']
    CC_PROVISIONING_TESTSCRIPT_ID = jsonRecord['CC_PROVISIONING_TESTSCRIPT_ID']
    SIGHTING_DATA_REQUIREMENTS = jsonRecord['SIGHTING_DATA_REQUIREMENTS']

    Execution_Run = getQueryRecordList(MYQUERY_ID)
    for element in Execution_Run:
        detail = getConfigLinkRecord(element['id'])
        for el in detail:
            if el not in systemDetails:
                systemDetails.append(el)

    for PlatformConfigElement in systemDetails:
        PlatformConfigTitle = GetRecordDetails(PlatformConfigElement['platformConfigID'], 'title')
        PlatformConfigList.append(PlatformConfigTitle)
        logger.debug("Retriving Platform Config Title: {0}".format(PlatformConfigTitle))

    for i, element in enumerate(systemDetails):
        try:
            if "centos" in element['os'].lower():
                productKit = args.centOSStrPrKit
            elif "rhel" in element['os'].lower():
                productKit = args.rhelPrKit
            elif "win" in element['os'].lower():
                productKit = args.win2022PrKit
        except Exception as ex:
            logger.warning("productKit parsing failed: {}".format(ex))
            productKit = None
            element['os'] = 'None'
        finally:
            element[element['os']] = productKit

    doProvisioning(DO_PROVISION, systemDetails, CC_COPYDPGBUILD, CC_FW_Only, CC_PROVISIONING_TESTSCRIPT_ID,
                   args.frameworkKit)

    for i, element in enumerate(systemDetails):
        controllerIP = element['controllerIPName']
        break

    try:
        getCCTestcaseXml(controllerIP)
        logger.debug("Copied testCases.xml from HOST: {0}".format(controllerIP))
    except Exception as ex:
        logger.error("Unable to get testCases.xml: {}".format(ex))
        logger.error(traceback.format_exc())
        raise Exception()

    ccRecords, MS_Title, MS_Title_WW = createHSDESRecordsForCycle(MY_WW, MY_TEAM, Execution_Run, MY_TITLE,
                                                                  MY_PROGRAM_NAME, MY_RUN_NUMBER, PlatformConfigList)
    createHSDQueries(MS_Title, HSDES_TEST_CASE)
    createHSDQueries(MS_Title, HSDES_TEST_RESULT)

    testCaseToPackageMap = getCCTestPackageList(CC_MAPPING_FILE)
    logger.debug("Got created with Command Centre Package Details: {}".format(testCaseToPackageMap))

    startTime = time.time()
    for i, element in enumerate(systemDetails):
        logger.debug("Setup {0}:".format(i + 1))
        epochTime = time.time()
        productKit = element[element['os']]
        PC_release = GetRecordDetails(element['platformConfigID'], HSDES_RELEASE)
        PC_title = GetRecordDetails(element['platformConfigID'], HSDES_TITLE)
        scriptTitle = PC_release + "-" + PC_title

        if scriptTitle not in ccRecords:
            logger.debug("Platform config {0} is not connected with an TCD".format(scriptTitle))
            continue

        testScriptId = createTestScript(PC_title, ccRecords[scriptTitle], testCaseToPackageMap, CC_PROJECT_NAME,
                                        args.frameworkKit, MS_Title_WW + str(element['controllerIPName']),
                                        MY_TIMEOUT_IN_SEC)

        resultID = runCCTestScripts(testScriptId, element['controllerIPName'], args.frameworkKit, productKit)
        logger.debug("# Trigger time for record {0}: {1} ".format(testScriptId, time.time() - epochTime))
        logger.debug(resultID)
        for el in ccRecords[scriptTitle]:
            el['cc_id'] = resultID

    logger.debug(">> Total execution time = {0} seconds<<".format(time.time() - startTime))
    startTime = time.time()
    time.sleep(600)

    while ((time.time() - startTime) < MY_TIMEOUT_IN_SEC):
        flag, ccRecords = ValidateAndUpdateResults(ccRecords, productKit, MS_Title, SIGHTING_DATA_REQUIREMENTS,
                                                   MY_PROGRAM_NAME)
        if False not in flag:
            break
        else:
            time.sleep(300)
    else:
        logger.error("Timeout reached for script execution..")


if __name__ == "__main__":
    main()
