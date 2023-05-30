import json, re

import requests
from requests_ntlm2 import HttpNtlmAuth
from django.core.paginator import Paginator
from requests_kerberos import HTTPKerberosAuth
import os
from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import Platform, TestCase, TestCaseExcel, BKCReport, User, TestStepsExcel
from collections import OrderedDict
from django.db import connection
from django.core import serializers
import email
import smtplib
#from email.MIMEMultipart import MIMEMultipart
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import hsdes

TEST_CASE_ID_PREFIX_DICT = {
	"EGS" : {
		"BKC": "EGS_BKC_",
		"PV": "EGS_PV_"
	}
}

EMAIL_SERVER = "SMTPAuth.intel.com"
EMAIL_ADDRESS = "xpiv_bkc_automation@intel.com"
EMAIL_PASSWORD = os.environ['EMAIL_PWD']#"Gar!Intel1234567890@@"
EMAIL_PORT = 587
_AUTOMATION_LEADS = ["divya.al@intel.com", "Mandar.Chandrakant.Thorat@intel.com", "sovan.bhunia@intel.com",
                    "mangu.venkata.krishna.kalyan@intel.com"]
#_AUTOMATION_LEADS = ["kasaiah.bogineni@intel.com"]
_CW_AUTOMATION_TEAM_LEADS = ["deepakx.ramesh@intel.com"]
_CW_AUTOMATION_TEAM = ["dl_piv_automation_lnt@intel.com"]
_USER_ROLES = ["cw_developer", "cw_lead", "lead", "manager", "cw_manager", "user","administrator"]
_ADMIN_ROLES = ["lead", "manager", "developer"]
_SYNC_ROLES= ["administrator"]
_CW_LEADS_ROLES = ["cw_lead", "cw_manager"]
_CW_DEVELOPER_ROLES = ["cw_developer", "user"]
#_CW_AUTOMATION_TEAM = ["kasaiah.bogineni@intel.com"]
from dpgautomation.settings import BASE_URL

_TC_EDIT_LINK = "http://"+BASE_URL+":8080/automation/testcases/%s/%s/"

_CONTACT_EMAIL = "divya.al@intel.com"
ACCESS_DENIED_PAGE = "You don't have access to this page, please send email to %s" % _CONTACT_EMAIL
_AUTOMATION_ADMINS = ["lead", "author"]
_REQUIRED_COMPONENTS = ["TestScriptComponentExecutionResultsId",
						"Name",
						"TestPackageDisplayedName",
						"Result",
						"DurationSeconds",
						"StartTime",
						"StopTime",
						"Duration",
                        "Comments",
						"LogFiles",
						"TestScriptComponentId",
						"TestScriptId",
						"GroupId",
						"FailureReason"]

_SUPPRESSED_COLUMNS = ["TestScriptComponentExecutionResultsId",  "DurationSeconds",  "GroupId", "TestScriptId", "TestScriptComponentId"]
_TABLE_HEADERS = ["S.No",  "TestPackageDisplayedName", "Name", "Result", "FailureReason",  "LogFiles_Path", "Duration", "LogFiles_Dir", "Comments", "StartTime", "StopTime"]

_CURRENT_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ex.txt")

_KEY = "TestScriptComponentExecutionResultsId"
_USERNAME = "gar\\lab_bdcpilab"
_PASSWORD = os.environ['PWD']
#dpgpivbdcsrr4mega2021@"


_AUTOMATION_BLOCK_CATEGORIES = ["", "EXPLORATION", "BLOCK_HARDWARE", "BLOCK_CONTENT_TEAM", "BLOCK_DEFECT", "BLOCK_DTAF"]
_HEADERS={'Content-Type':'application/json'}
_ERROR_KEYWORD = " ERROR    "
_PROJECT = "BKC-EGS"
_BKC_DATABASE_SOURCE = "HPLM"
_PV_DATABASE_SOURCE = "GLASGOW"
_DB_SOURCES = {
	"PV": _PV_DATABASE_SOURCE,
	"BKC": _BKC_DATABASE_SOURCE
}
YES = "yes"
NO = "no"
SERVER_TYPE = "REMOTE"



_URL = "https://api.commandcenter.iind.intel.com/api/v2/BKC-EGS/resultsapi/SummaryReportResults?executionResultId=%s"
_HSDES_QUERY_TD_URL = "https://hsdes-api.intel.com/rest/query/%s?include_text_fields=Y&start_at=1&max_results=%s"
_HSDES_USER_DETAILS_URL = "https://hsdes-api.intel.com/rest/user/%s?expand=personal"
_HSDES_QUERY_TD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "td.txt")
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
_PROXIES={"http": "http://proxy-chain.intel.com:911", "https": "http://proxy-chain.intel.com:911"}

_HSDES_TESTS = {
	"EGS": 16012605144,
}
_HSDES_QUERY_TCD_COLUMNS = ["row_num", "id", "title", "ext_id", "domain", "feature_group", "owner"]


class AUTOMATION_CATEGORIES:
	FULLY_AUTOMATE = "Fully Automate"
	MANUAL = "Manual"
	PARTIAL_AUTOMATE = "Partial Automate"

class BKC_CANDIDATE:
	SILVER = "Silver"
	GOLD = "Gold"
	BRONZE = "Bronze"
	BKC = "BKC"
	PV = "PV"

YES_OR_NO = [YES.capitalize(), NO.capitalize()]
BOOL_VALUES = ["True", "False"]
AUTO_CATEGORIES = [AUTOMATION_CATEGORIES.FULLY_AUTOMATE, AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE]
PLATFORM_CATEGORIES = [BKC_CANDIDATE.BKC, BKC_CANDIDATE.PV]
BKC_CANDIDATES = [BKC_CANDIDATE.SILVER, BKC_CANDIDATE.GOLD, BKC_CANDIDATE.BRONZE, BKC_CANDIDATE.BKC, BKC_CANDIDATE.PV]

class AutomationStatus:
	PASSED = 'PASSED'
	FAILED = "FAILED"

class PARENT_TABLE_CONTENTS:
	TOTAL_TESTS = "Total Tests (A+B)"
	TOTAL_AUTOMATABLE = "Total Automatable (A)"
	PENDING_TO_AUTOMATE = "Pending To Automate (A-C)"
	TOTAL_AUTOMATED = "Total Automated (C)"
	MANUAL = "Manual (B)"
	DEPLOYED = "Automation Deployed (D)"
	YET_TO_DEPLOY = "Yet to Deploy (C-D)"
	AUTOMATION_BLOCKED = "Automation Blockers"
	EXPLORATION = "Exploration"
	DEPRECATED_TCS = "Deprecated TCs"
	REWORK = "Rework"


NEW_TCS = "New TCs"
# DEPRECATED_TCS = "Deprecated TCs"

class AUTOMATION_DEV_CATEGORIES:
	CODEREVIEW = "CODE_REVIEW"
	NEW = "NEW"
	OTHERS = "OTHERS"
	REWORK = "REWORK"
	AUTOMATED = "AUTOMATED"
	CLOSED = "CLOSED"
	VALIDATION = "VALIDATION"
	IN_DEVELOPMENT = "IN_DEVELOPMENT"


_AUTOMATION_DEV_CATEGORIES = [AUTOMATION_DEV_CATEGORIES.NEW, AUTOMATION_DEV_CATEGORIES.CLOSED, AUTOMATION_DEV_CATEGORIES.VALIDATION,
							  AUTOMATION_DEV_CATEGORIES.AUTOMATED, AUTOMATION_DEV_CATEGORIES.IN_DEVELOPMENT, AUTOMATION_DEV_CATEGORIES.CODEREVIEW, AUTOMATION_DEV_CATEGORIES.REWORK,
							  AUTOMATION_DEV_CATEGORIES.OTHERS, ""]
_AUTOMATION_CATEGORIES = [AUTOMATION_CATEGORIES.FULLY_AUTOMATE, AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE]
_BKC_CATEGORIES = [BKC_CANDIDATE.SILVER, BKC_CANDIDATE.GOLD, BKC_CANDIDATE.BRONZE, BKC_CANDIDATE.BKC]
_PV_CANDIDATES = [BKC_CANDIDATE.PV]

_FILTERS = [PARENT_TABLE_CONTENTS.TOTAL_TESTS, PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE,
			PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE, PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED, PARENT_TABLE_CONTENTS.MANUAL,
			PARENT_TABLE_CONTENTS.DEPLOYED, PARENT_TABLE_CONTENTS.YET_TO_DEPLOY]

_BKC_CANDIDATES = [BKC_CANDIDATE.SILVER, BKC_CANDIDATE.BRONZE, BKC_CANDIDATE.GOLD, BKC_CANDIDATE.BKC]


def get_steps_from_hsdes(hsdes_id):
	pass

def is_athenticated(username):
	try:
		obj = User.objects.get(user=username)
		if obj.user:
			return True
	except User.DoesNotExist:
		obj = None
	return False

def get_username(request):
	client_ip = request.META['REMOTE_ADDR']
	username = ""
	idsid = ""
	try:
		import subprocess
		output = subprocess.getoutput("nslookup %s" % client_ip)
		idsid = output.split("Name:")[-1].split("\n")[0].strip().split("-")[0]
		print("Logged in: %s" % idsid)
		if idsid:
			username = user_info(idsid)
	except:
		pass
	return username, idsid


def send_mail(subject, body, to, cc):
	msg = MIMEMultipart()

	msg['Subject'] = subject
	msg['From'] = EMAIL_ADDRESS
	msg['To'] = ','.join(to)
	msg['Cc'] = ','.join(cc)
	try:
		msg.attach(MIMEText(body, 'html'))
	except Exception as e:
		print("Exception ocurred %s" % str(e))
	try:
		server = smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT)
		server.starttls()
		server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
		text = msg.as_string()
		server.sendmail(EMAIL_ADDRESS, cc, text)
		server.quit()
		#print('Mail has been sent successfully...........')
		return True
	except Exception as e:
		print('Failed to send email.. %s' % e)
		print('Trying to send a mail again...')
	return False



def get_cc_results(execution_ids, path):
	data = {}
	final_results = OrderedDict()
	for execution_id in execution_ids:
		# response = requests.get(_URL % execution_id, auth=None, headers=_HEADERS, verify=False, proxies=_PROXIES)
		response = requests.get(_URL % execution_id, auth=HttpNtlmAuth(_USERNAME, _PASSWORD), headers=_HEADERS, verify=False, proxies=_PROXIES)
		if response.status_code != 200:
			return data
		with open(path, "w") as f:
			f.write(response.text)
		with open(path) as f:
			data = json.load(f)
		os.remove(path)
		results = data["Results"]  # list type

		for result in results:
			if result[_KEY] not in final_results.keys():
				final_results[result[_KEY]] = {}
			for key in _REQUIRED_COMPONENTS:
				if key not in _SUPPRESSED_COLUMNS:
					if key.lower() == "logfiles":
						final_results[result[_KEY]][key + "_Dir"] = result[key][0]["Dir"] if len(result[key]) else ""
						final_results[result[_KEY]][key + "_Path"] = result[key][0]["Path"] if len(result[key]) else ""
						if final_results[result[_KEY]][key + "_Path"]:
							# response = requests.get(final_results[result[_KEY]][key + "_Path"], auth=None,
							# 						headers=_HEADERS, verify=False, proxies=_PROXIES)
							response = requests.get(final_results[result[_KEY]][key + "_Path"], auth=HttpNtlmAuth(_USERNAME, _PASSWORD), headers=_HEADERS, verify=False, proxies=_PROXIES)
							error_logs = ""
							if 'Traceback (most recent call last):' in response.text:
								rx = re.compile(r"Traceback \(most recent call last\):(?:\n.*)+?\n(.*?(?:Exception|Error):)\s*(.+)")
								error = ""
								if rx.findall(response.text):
									error = str(rx.findall(response.text))
								error_logs = error_logs + error + "</br></br>"
							for line in response.text.splitlines():
								if _ERROR_KEYWORD in line:
									error_logs = error_logs + line.split(_ERROR_KEYWORD)[-1].split("] ")[-1].strip() + "</br></br>"
							final_results[result[_KEY]][key + "_Path"] = error_logs
					else:
						final_results[result[_KEY]][key] = "" if result[key] is None else result[key]

	return final_results

def get_query_results(url):
	data = {}
	response = requests.get(url , auth=HTTPKerberosAuth(), verify=False,
							proxies=_PROXIES)
	if response.status_code != 200:
		return data
	with open(_HSDES_QUERY_TD_PATH, "w") as f:
		f.write(response.text)
	with open(_HSDES_QUERY_TD_PATH) as f:
		data = json.load(f)
	return data

def get_count_of_query_records(query_id):
	records = get_query_results(_HSDES_QUERY_TD_URL % (query_id, 0))
	if "total" in records.keys():
		return records["total"]

def get_tcd_records(query_id):
	data = []
	num_rows = get_count_of_query_records(query_id)
	if num_rows:
		records = get_query_results(_HSDES_QUERY_TD_URL % (query_id, num_rows))
		data = records["data"]
	return data

def user_info(idsid):
	records = get_query_results(_HSDES_USER_DETAILS_URL % idsid)
	try:
		if records['data']:
			return records['data'][0]['sys_user.name'] + ":" + records['data'][0]['sys_user.wwid']
	except Exception:
		return idsid
	return idsid

def user_email(idsid):
	records = get_query_results(_HSDES_USER_DETAILS_URL % idsid)
	#print(records["data"])
	try:
		if records['data']:
			return records['data'][0]['sys_user.email']
	except Exception:
		return _CONTACT_EMAIL
	return _CONTACT_EMAIL

def parse_cc_results(platform):
	reports = BKCReport.objects.filter(platform_name_short=platform)
	reports_dict = {}
	for report in reports:
		execution_ids = [report_id.strip() for report_id in report.run_ids.split(",") if
						 report_id.strip().isdigit() and report_id.strip() != '']
		final_results = get_cc_results(execution_ids, _CURRENT_JSON_PATH)
	reports_dict[report.report] = final_results
	return reports_dict


def check_login(request):
	try:
		if request.session['username'] != "":
			pass
		if request.session['idsid'] != "":
			pass
		if is_athenticated(request.session['idsid']):
			return True
	except KeyError:
		if SERVER_TYPE == "LOCAL":
			return True
		else:
			return False

def login(request):
	if not check_login(request):
		username, idsid = get_username(request)
		# import pdb; pdb.set_trace()
		# print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
		# print("{}{}".format(username,idsid))
		request.session['username'] = username
		request.session['idsid'] = idsid
		request.session['email'] = user_email(idsid)
	if check_login(request):
		return True

def logout(request):
	try:
		del request.session['username']
		del request.session['idsid']
		del request.session['email']
	except KeyError:
		pass
	return render(request, "automation/logout.html", context={})

def reports(request):
	if not login(request):
		return render(request, "automation/login.html", context={})
	platforms = Platform.objects.all()
	return render(request, "automation/reports.html", context={"platforms": platforms, "username": request.session["username"]})


def automation_dev_trackers(request):
	if not login(request):
		return render(request, "automation/login.html", context={})
	platforms = Platform.objects.all()
	categories_raw = TestCaseExcel.objects.values("platform_tc_category").distinct()
	categories = []
	for c in categories_raw:
		if c["platform_tc_category"].strip() not in categories:
			categories.append(c["platform_tc_category"].strip())
	return render(request, "automation/automation_dev_reports.html", context={"platforms": platforms, "username": request.session["username"], "categories": categories})

def platform_reports(request, platform, bkc):
	if not login(request):
		return render(request, "automation/login.html", context={})

	reports =parse_cc_results(platform)
	results_dict = {}
	for report, execution_results in reports.items():
		if report not in results_dict.keys():
			results_dict[report] = {AutomationStatus.PASSED: 0, AutomationStatus.FAILED: 0}
		for key, value in execution_results.items():
			if value["Result"].lower() == AutomationStatus.PASSED.lower():
				results_dict[report][AutomationStatus.PASSED] = results_dict[report][AutomationStatus.PASSED] + 1
			elif value["Result"].lower() == AutomationStatus.FAILED.lower():
				results_dict[report][AutomationStatus.FAILED] = results_dict[report][AutomationStatus.FAILED] + 1

	return render(request, "automation/platform_reports.html", context={"results": results_dict, "platform": platform, "username": request.session["username"], "bkc": bkc})

def platform_report(request, platform, bkc):
	if not login(request):
		return render(request, "automation/login.html", context={})
	reports = parse_cc_results(platform)
	#print (bkc)
	if bkc not in reports.keys():
		reports[bkc] = {}
	#print (reports)
	return render(request, "automation/platform_report.html", context={"results": reports[bkc], "platform": platform, "bkc": bkc, "username": request.session["username"]})



# Create your views here.
def triage_report(request, execution_id):
	#execution_id = "59845"
	if not login(request):
		return render(request, "automation/login.html", context={})
	cc_results = get_cc_results(execution_id)
	results = {}
	for key, value in cc_results.items():
		for k, v in value.items():
			if key not in results.keys():
				results[key] = {}
			if k not in _SUPPRESSED_COLUMNS:
				results[key][k] = v
	return render(request, "automation/triage_report.html", context={"results": results, "username": request.session["username"]})

def reports(request):
	if not login(request):
		return render(request, "automation/login.html", context={})
	platforms = Platform.objects.all()
	categories_raw = TestCaseExcel.objects.values("platform_tc_category").distinct()
	categories = []
	for c in categories_raw:
		if c["platform_tc_category"].strip() not in categories:
			categories.append(c["platform_tc_category"].strip())
	#print(platforms)
	return render(request, "automation/reports.html", context={"platforms": platforms, "username": request.session["username"], "categories": categories})


def testcases(request):
	if not login(request):
		return render(request, "automation/login.html", context={})
	platforms = Platform.objects.all()
	categories_raw = TestCaseExcel.objects.values("platform_tc_category").distinct()
	categories = []
	for c in categories_raw:
		if c["platform_tc_category"].strip() not in categories:
			categories.append(c["platform_tc_category"].strip())
	return render(request, "automation/testcases.html", context={"platforms": platforms, "categories": categories, "username": request.session["username"]})

def test_plan_hsdes(request, platform):
	if not login(request):
		return render(request, "automation/login.html", context={})
	if platform not in _HSDES_TESTS.keys():
		return HttpResponse("Query of %s is not found" % platform)
	raw_test_plan_details = get_tcd_records(_HSDES_TESTS[platform])
	db_columns = ["automation_completion", "automation_eta", "automation_potential", "automation_owner", "egs_blocked",
				  "automation_script", "non_automatable_reason", "automation_comments", "automation_remarks"]
	test_plan_details = {}
	for item in raw_test_plan_details:
		test_plan_details[item["id"]] = item

	query = """INSERT IGNORE INTO automation_testcase (hsdes_id, platform_name_short) VALUES """

	for key, value in test_plan_details.items():
		query = query + '(%s, "%s")' % (key, platform) + ","
	with connection.cursor() as cursor:
		cursor.execute(query.strip(', '))
	tcid_details = TestCase.objects.filter(platform_name_short=platform).order_by('id')
	#print(tcid_details)
	for obj in tcid_details:
		for column in db_columns:
			test_plan_details[obj.hsdes_id][column] = eval("obj.%s" % column)
	details = []
	hsdes_columns = _HSDES_QUERY_TCD_COLUMNS + db_columns
	for key, value in test_plan_details.items():
		sub_dict = OrderedDict()
		for column in hsdes_columns:
			sub_dict[column] = value[column]
		details.append(sub_dict)


	return render(request, "automation/testplan.html", context={"test_plan_details": details, "platform": platform, "hsdes_columns": hsdes_columns, "username": request.session["username"]})


def test_plan(request, platform, bkc):
	#raw_test_plan_details = get_tcd_records(_HSDES_TESTS[platform]
	if not login(request):
		return render(request, "automation/login.html", context={})
	db_columns = ['temp_test_case_id', 'phoenix_id', 'test_case_id', 'title','is_new_tc', 'is_deprecated', 'developer_comments', 'database_source','feature_group','domain', 'operating_system', 'hw_config','milestone','bkc_candidate','automation_potential','automation_eta','automation_completion',
				  'automation_deployed','automation_deployment_eta', 'automation_developer', 'egs_blocked','automation_category','automation_remarks','automation_block_category','source_patch_link','non_automatable_remarks', 'platform_tc_category']
	tcid_details = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, automation_applicable=YES).order_by('id')

	test_plan_details = []
	for item in tcid_details:
		#print (item.test_case_id)
		sub_dict = {}
		for column in db_columns:
			sub_dict[column] = eval("item.%s" % column)
		test_plan_details.append(sub_dict)
	#print (test_plan_details)

	return render(request, "automation/filter_query.html", context={"test_plan_details": test_plan_details,  "platform": platform, "hsdes_columns": db_columns, "username": request.session["username"]})

def test_steps(request, platform, tcid):
	#raw_test_plan_details = get_tcd_records(_HSDES_TESTS[platform])
	if not login(request):
		return render(request, "automation/login.html", context={})
	db_columns = ['title', 'step_number', 'step','expected_result']
	tcid_details = TestStepsExcel.objects.filter(platform=platform, test_case_id=tcid).order_by('id')
	test_plan_details = []
	for item in tcid_details:
		sub_dict = {}
		for column in db_columns:
			sub_dict[column] = eval("item.%s" % column)
		test_plan_details.append(sub_dict)
	#print (test_plan_details)

	return render(request, "automation/test_steps.html", context={"test_plan_details": test_plan_details,  "platform": platform, "hsdes_columns": db_columns, "username": request.session["username"], "tcid": tcid})


def testcase_details(request, platform, tcid):
	if not login(request):
		return render(request, "automation/login.html", context={})
	results = TestCaseExcel.objects.get(test_case_id=tcid, platform=platform, automation_applicable=YES)
	u_obj = User.objects.get(user=request.session["idsid"])
	# u_obj =
	if u_obj.role.lower() in ["user"]:
		return render(request, "automation/authentication.html",
					  context={ "username": request.session["username"]})
	developers_raw = User.objects.filter(role__contains="developer")
	developers = []
	for obj in developers_raw:
		developers.append(user_info(obj.user).split(":")[0].strip())

	return render(request, "automation/edit_testcase_details.html", context={"results": results,
																			 "platform":platform,
																			 "user_role":u_obj.role,
																			 "developers": developers,
																			 "username": request.session["username"],
																			 "blocked_categories": _AUTOMATION_BLOCK_CATEGORIES,
																			 "automation_dev_catgories": _AUTOMATION_DEV_CATEGORIES,
																			 "yes_or_no": YES_OR_NO,
																			 "bool_values": BOOL_VALUES,
																			 "auto_categories": AUTO_CATEGORIES,
																			 "bkc_candidates": BKC_CANDIDATES,
																			 "platform_categories": PLATFORM_CATEGORIES})

def create_report(request):
	if not login(request):
		return render(request, "automation/login.html", context={})
	platforms_list = []
	platforms = Platform.objects.all()
	for p in platforms:
		platforms_list.append(p.platform_name_short)
	return render(request, "automation/create_report.html", context={"platforms": platforms_list, "username": request.session["username"]})

def add_user(request):
	if not login(request):
		return render(request, "automation/login.html", context={})
	if request.session["idsid"] in _ADMIN_ROLES:
		return render(request, "automation/authentication.html", context={"username": request.session["username"]})
	return render(request, "automation/add_user.html", context={"roles": _USER_ROLES, "username": request.session["username"]})


def sync(request):
    if not login(request):
        return render(request, "automation/login.html", context={})

    #return render(request, "automation/add_user.html", context={"roles": _USER_ROLES, "username": request.session["username"]})

    obj=User.objects.get(user=request.session["idsid"])
    print("Logged in: %s" % request.session["idsid"])
    if obj.role.lower() in _SYNC_ROLES:

        if request.method =="POST":
            result1 = request.POST.get('automation_potential')
            # result2 = request.POST.get('automation_eta')
            # result3 = request.POST.get('automation_current')
            if result1 =="on":
                query_filter = TestCaseExcel.objects.filter(platform_tc_category="BKC", is_new_tc="No",automation_applicable="Yes").exclude(is_deprecated="Yes").values('phoenix_id', 'automation_potential')
    #
    #             # query_filter = TestCaseExcel.objects.filter(platform_tc_category="BKC",
    #             #
    #             #                                                     is_new_tc="No",
    #             #                                                     automation_applicable="Yes",automation_potential="Fully Automate").exclude(automation_deployed="").exclude(is_deprecated="Yes").exclude(phoenix_id="0").values('phoenix_id')
    #             # print(query_filter.count())
                my_dict = {d["phoenix_id"]: d["automation_potential"] for d in query_filter}
                print(my_dict)
                # l = ['16015822825','16015878221']
                # n = {k: my_dict[k] for k in my_dict.keys() & set(l)}
                # print(n)

                # for k in my_dict.keys():
                #     run_update(k, my_dict[k])
                run_update("16015822825","Fully Automate")

                messages.info(request, "Updated Total BKC TCs into Phoenix Fields Successfully")
                return redirect('sync')


            else:
                messages.info(request, "Please select option to update in HSD-ES")
                return  redirect('sync')
        return render(request, "automation/sync.html",
                          context={"roles": _SYNC_ROLES, "username": request.session["username"]})

    return render(request, "automation/authentication.html", context={"username": request.session["username"]})



def update_user(request):
	if not login(request):
		return render(request, "automation/login.html", context={})
	if not request.POST:
		return HttpResponse("Failed to add user")
	idsid = request.POST.get("user")
	role = request.POST.get("role")
	email = user_email(idsid)
	full_name = user_info(idsid)
	full_name = full_name.split(":")[0].strip()
	try:
		obj = User.objects.get(user=idsid)
		if obj:
			obj.role= role
			obj.full_name = full_name
			obj.email = email
			obj.save()
		else:
			User.objects.create(user=idsid, role=role, full_name=full_name, email=email)
	except User.DoesNotExist:
		User.objects.create(user=idsid, role=role, full_name=full_name, email=email)
	return HttpResponse("User has been added successfully!")

def generate_report(request):
	if not login(request):
		return render(request, "automation/login.html", context={})
	if not request.POST:
		return HttpResponse("Failed to create report")
	bkc = request.POST.get("bkc")
	platform = request.POST.get("platform")
	run_id = request.POST.get("run_id")
	try:
		obj = BKCReport.objects.get(platform_name_short=platform, report=bkc)
	except BKCReport.DoesNotExist:
		obj = None
	if obj:
		return HttpResponse("Report exists already, please update the report")
	BKCReport.objects.create(report=bkc, platform_name_short=platform, run_ids=run_id)
	return HttpResponse("Report has been created successfully")

def update_testcase(request, platform, tcid):
	if not login(request):
		return render(request, "automation/login.html", context={})
	if not request.POST:
		return HttpResponse("Failed to update the test case")
	#print(request.POST)
	domain = request.POST.get("domain")
	temp_test_case_id = request.POST.get("temp_test_case_id")
	phoenix_id = request.POST.get("phoenix_id")
	title = request.POST.get("title")
	automation_current = request.POST.get("automation_current")
	automation_potential = request.POST.get("automation_potential")
	automation_eta = request.POST.get("automation_eta")
	automation_applicable = request.POST.get("automation_applicable")
	is_new_tc = request.POST.get("is_new_tc")
	is_deprecated = request.POST.get("is_deprecated")
	automation_completion = request.POST.get("automation_completion")
	automation_deployed = request.POST.get("automation_deployed")
	automation_deployment_eta = request.POST.get("automation_deployment_eta")
	deployed_result = request.POST.get("deployed_result")
	script_path = request.POST.get("script_path")
	automation_developer = request.POST.get("automation_developer")
	egs_blocked = request.POST.get("egs_blocked")
	automation_category = request.POST.get("automation_category")
	developer_comments = request.POST.get("developer_comments")
	automation_remarks = request.POST.get("automation_remarks")
	automation_blocked_category = request.POST.get("automation_blocked_category")
	non_automatable_remarks = request.POST.get("non_automatable_remarks")
	platform_tc_category = request.POST.get("platform_tc_category")
	source_patch_link = request.POST.get("source_patch_link")
	subject = ""

	try:
		record = TestCaseExcel.objects.get(test_case_id=tcid)
		url = _TC_EDIT_LINK % (platform, tcid)
		body = """
						<a href="%s">%s</a></br></br>
						<table border="1">
							<tr><th>Test</th><th>Old Value</th><th>New Value</th></tr>
							<tr><th>Test Case Id</th><td>%s</td><td>%s</td></tr>
							<tr><th>Title</th><td>%s</td><td>%s</td></tr>
							<tr><th>Automation Developer</th><td>%s</td><td>%s</td></tr>
							<tr><th>Automation Category</th><td>%s</td><td>%s</td></tr>
							<tr><th>Blocked Category</th><td>%s</td><td>%s</td></tr>
							<tr><th>Developer Comments</th><td><pre>%s</pre></td><td><pre>%s</pre></td></tr>
						</table>

						""" % (url, url, tcid, tcid, title, title, record.automation_developer, automation_developer, record.automation_category, automation_category, record.automation_block_category, automation_blocked_category, record.developer_comments, developer_comments.replace('"', r'\"').replace("'", r"\'"))
		record.domain = domain
		record.automation_current = automation_current
		record.automation_potential = automation_potential
		record.automation_completion = automation_completion
		record.automation_eta = automation_eta
		record.deployed_result = deployed_result
		record.automation_applicable = automation_applicable
		record.is_new_tc = is_new_tc
		record.is_deprecated = is_deprecated
		record.automation_deployed = automation_deployed
		record.script_path = script_path
		record.automation_developer = automation_developer
		record.egs_blocked = egs_blocked.capitalize()
		record.automation_category = automation_category
		record.platform_tc_category = platform_tc_category
		record.temp_test_case_id = temp_test_case_id
		record.phoenix_id = phoenix_id
		if record.developer_comments != developer_comments.replace('"', r'\"').replace("'", r"\'"):
			subject = "DPG_AUTOMATIONLAB_UPDATE: TC Update -  developer_comments"
		record.developer_comments = developer_comments.replace('"', r'\"').replace("'", r"\'")
		record.automation_remarks = automation_remarks
		record.automation_block_category = automation_blocked_category
		record.source_patch_link = source_patch_link
		record.automation_deployment_eta = automation_deployment_eta
		record.non_automatable_remarks = non_automatable_remarks.replace('"', r'\"').replace("'", r"\'")
		record.save()
		if subject != "":

			user_emails =[]
			try:
				obj = User.objects.get(full_name=automation_developer)
				user_emails.append(obj.email)
				obj = User.objects.get(full_name=record.automation_developer)
				if obj.email not in user_emails:
					user_emails.append(obj.email)
			except Exception as e:
				print(str(e))
			url = _TC_EDIT_LINK % (platform, tcid)
			head_body = """
			<h3>%s is updated: </br></h3>
			""" % request.session["username"]
			if user_emails:
				send_mail(subject, head_body + body , to= user_emails + [request.session["email"]], cc=_CW_AUTOMATION_TEAM_LEADS + _AUTOMATION_LEADS)
			else:
				send_mail(subject, head_body + body, to= _CW_AUTOMATION_TEAM + [request.session["email"]], cc=_CW_AUTOMATION_TEAM_LEADS + _AUTOMATION_LEADS)
	except Exception as e:
		print(str(e))
		return HttpResponse("Error in updating the test case")

	return HttpResponse("Updated sucessfully")

def statistics(request):
	if not login(request):
		return render(request, "automation/login.html", context={})
	platforms = Platform.objects.all()
	categories_raw = TestCaseExcel.objects.values("platform_tc_category").distinct()
	categories = []
	for c in categories_raw:
		if c["platform_tc_category"].strip() not in categories:
			categories.append(c["platform_tc_category"].strip())
	return render(request, "automation/statistics.html", context={"platforms": platforms, "username": request.session["username"], "categories": categories})

def create_candidate():
	return {PARENT_TABLE_CONTENTS.TOTAL_TESTS: 0, PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE: 0, PARENT_TABLE_CONTENTS.MANUAL: 0,
											   PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED: 0, PARENT_TABLE_CONTENTS.DEPLOYED: 0,
											   PARENT_TABLE_CONTENTS.YET_TO_DEPLOY: 0, PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE: 0,
											   PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED: 0, PARENT_TABLE_CONTENTS.EXPLORATION: 0,
											   PARENT_TABLE_CONTENTS.REWORK: 0, PARENT_TABLE_CONTENTS.DEPRECATED_TCS: 0, NEW_TCS:0}

def platform_statistics(request, platform, bkc):
	if not login(request):
		return render(request, "automation/login.html", context={})
	results = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, automation_applicable=YES).order_by("id")

	enable_results = TestCaseExcel.objects.filter(platform=platform, egs_blocked="False", platform_tc_category=bkc, automation_applicable=YES).order_by("id")
	results_dict = {}
	for obj in results:
		if obj.bkc_candidate not in results_dict.keys():
			results_dict[obj.bkc_candidate] = create_candidate()

		_is_new_tc = obj.is_new_tc.lower()
		_oauto_potential = obj.automation_potential.lower()
		_oauto_applicable = obj.automation_applicable.lower()
		_oauto_block_category = obj.automation_block_category.lower()
		_oauto_completion = obj.automation_completion.lower()
		_oauto_deployed = obj.automation_deployed.lower()

		_total_tests = PARENT_TABLE_CONTENTS.TOTAL_TESTS
		_total_automatable = PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE
		_total_automated = PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED
		_deployed = PARENT_TABLE_CONTENTS.DEPLOYED
		_manual = PARENT_TABLE_CONTENTS.MANUAL
		_auto_blocked = PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED
		_exploration = PARENT_TABLE_CONTENTS.EXPLORATION
		_pending = PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE
		_rework = PARENT_TABLE_CONTENTS.REWORK

		_auto_cat_rework = AUTOMATION_DEV_CATEGORIES.REWORK.lower()
		_auto_cat_partial_auto = AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE.lower()
		_auto_cat_fully_auto = AUTOMATION_CATEGORIES.FULLY_AUTOMATE.lower()


		if obj.is_new_tc.lower() == NO and obj.is_deprecated.lower() != YES:
			results_dict[obj.bkc_candidate][_total_tests] = results_dict[obj.bkc_candidate][_total_tests] + 1

		if _oauto_potential == _auto_cat_fully_auto and obj.is_new_tc.lower() != YES and _oauto_applicable == YES and obj.is_deprecated.lower() != YES and not (_oauto_potential == AUTOMATION_CATEGORIES.MANUAL.lower() or _oauto_potential == _auto_cat_partial_auto):
			results_dict[obj.bkc_candidate][_total_automatable] = results_dict[obj.bkc_candidate][_total_automatable] + 1
		elif obj.is_new_tc.lower() != YES and obj.automation_potential.lower() != "manual":
			print("{} : {} -> {}".format(obj.title, obj.automation_potential, obj.automation_applicable))

		if _oauto_potential == _auto_cat_fully_auto and _oauto_completion.strip() != "" and obj.is_new_tc.lower() != YES and _oauto_applicable == YES and obj.is_deprecated.lower() != YES:
			results_dict[obj.bkc_candidate][_total_automated] = results_dict[obj.bkc_candidate][_total_automated] + 1

		if _oauto_potential == _auto_cat_fully_auto and _oauto_completion.strip() != "" and obj.is_new_tc.lower() != YES and _oauto_applicable == YES and _oauto_deployed.strip() != "" and obj.is_deprecated.lower() != YES and obj.automation_category.lower() != _auto_cat_rework:
			results_dict[obj.bkc_candidate][_deployed] = results_dict[obj.bkc_candidate][_deployed] + 1

		if (_oauto_potential == AUTOMATION_CATEGORIES.MANUAL.lower() or _oauto_potential == _auto_cat_partial_auto) and obj.is_new_tc.lower() != YES and _oauto_applicable == YES and obj.is_deprecated.lower() != YES:
			results_dict[obj.bkc_candidate][_manual] = results_dict[obj.bkc_candidate][_manual] + 1

		if _oauto_block_category not in ["", _exploration.lower()] and obj.is_new_tc.lower() != YES and _oauto_applicable == YES and _oauto_completion == "" and obj.automation_potential != AUTOMATION_CATEGORIES.MANUAL and obj.automation_potential != AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE and obj.is_deprecated.lower() != YES:
			results_dict[obj.bkc_candidate][_auto_blocked] = results_dict[obj.bkc_candidate][_auto_blocked] + 1

		if _oauto_block_category == _exploration.lower() and obj.is_new_tc.lower() != YES and _oauto_applicable == YES and _oauto_completion == "" and obj.automation_potential != AUTOMATION_CATEGORIES.MANUAL and obj.automation_potential != AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE and obj.is_deprecated.lower() != YES:
			results_dict[obj.bkc_candidate][_exploration] = results_dict[obj.bkc_candidate][_exploration] + 1

		if obj.automation_category.lower() == _auto_cat_rework and obj.is_deprecated.lower() != YES:
			results_dict[obj.bkc_candidate][_rework] = results_dict[obj.bkc_candidate][_rework] + 1

		if obj.is_new_tc.lower() == YES and obj.is_deprecated.lower() != YES:
			results_dict[obj.bkc_candidate][NEW_TCS] = results_dict[obj.bkc_candidate][NEW_TCS] + 1

		if obj.is_deprecated.lower() == YES:
			results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.DEPRECATED_TCS] = results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.DEPRECATED_TCS] + 1

	for key in results_dict.keys():
		results_dict[key][_pending] = results_dict[key][_total_automatable] - results_dict[key][_total_automated] - results_dict[key][_exploration] - results_dict[key][_auto_blocked]
		results_dict[key][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY] = results_dict[key][_total_automated] - results_dict[key][_deployed]

	results_dict["Total"] = {_total_tests: 0, _total_automatable: 0,
							 _manual: 0, _total_automated: 0,_deployed: 0,
							 PARENT_TABLE_CONTENTS.YET_TO_DEPLOY: 0, _pending: 0, _auto_blocked: 0, _exploration: 0, _rework: 0, PARENT_TABLE_CONTENTS.DEPRECATED_TCS: 0, NEW_TCS:0}
	for obj in results_dict.keys():
		if obj != "Total":
			results_dict["Total"][_total_tests] = results_dict["Total"][_total_tests] + results_dict[obj][_total_tests]
			# print("{} + {} = {}".format(results_dict["Total"][_total_tests], results_dict[obj][_total_tests],results_dict["Total"][_total_tests]))
			results_dict["Total"][_total_automatable] = results_dict["Total"][_total_automatable] + results_dict[obj][_total_automatable]
			results_dict["Total"][_pending] = results_dict["Total"][_pending] + results_dict[obj][_pending]
			results_dict["Total"][_total_automated] = results_dict["Total"][_total_automated] + results_dict[obj][_total_automated]
			results_dict["Total"][_manual] = results_dict["Total"][_manual] + results_dict[obj][_manual]
			results_dict["Total"][_deployed] = results_dict["Total"][_deployed] + results_dict[obj][_deployed]
			results_dict["Total"][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY] = results_dict["Total"][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY] + results_dict[obj][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY]
			results_dict["Total"][_auto_blocked] = results_dict["Total"][_auto_blocked] + results_dict[obj][_auto_blocked]
			results_dict["Total"][_exploration] = results_dict["Total"][_exploration] + results_dict[obj][_exploration]
			results_dict["Total"][_rework] = results_dict["Total"][_rework] + results_dict[obj][_rework]
			results_dict["Total"][PARENT_TABLE_CONTENTS.DEPRECATED_TCS] = results_dict["Total"][PARENT_TABLE_CONTENTS.DEPRECATED_TCS] + results_dict[obj][PARENT_TABLE_CONTENTS.DEPRECATED_TCS]
			results_dict["Total"][NEW_TCS] = results_dict["Total"][NEW_TCS] + results_dict[obj][NEW_TCS]
	enable_results_dict = {}
	for obj in enable_results:
		if obj.bkc_candidate not in enable_results_dict.keys():
			enable_results_dict[obj.bkc_candidate] = create_candidate()

		if obj.is_new_tc.lower() == NO and obj.is_deprecated.lower() != YES:
			enable_results_dict[obj.bkc_candidate][_total_tests] = enable_results_dict[obj.bkc_candidate][_total_tests] + 1

		if obj.automation_potential.lower() == AUTOMATION_CATEGORIES.FULLY_AUTOMATE.lower() and obj.is_new_tc.lower() != YES and obj.automation_applicable.lower() == YES and obj.is_deprecated.lower() != YES:
			enable_results_dict[obj.bkc_candidate][_total_automatable] = enable_results_dict[obj.bkc_candidate][_total_automatable] + 1

		if obj.automation_potential.lower() == AUTOMATION_CATEGORIES.FULLY_AUTOMATE.lower()  and obj.is_new_tc.lower() != YES and obj.automation_applicable.lower() == YES and obj.automation_completion.lower().strip() != "" and obj.is_deprecated.lower() != YES:
			enable_results_dict[obj.bkc_candidate][_total_automated] = enable_results_dict[obj.bkc_candidate][_total_automated] + 1
		if obj.automation_potential.lower() == AUTOMATION_CATEGORIES.FULLY_AUTOMATE.lower()  and obj.is_new_tc.lower() != YES and obj.automation_applicable.lower() == YES and obj.automation_completion.lower().strip() != "" and obj.automation_deployed.lower().strip() != "" and obj.is_deprecated.lower() != YES and obj.automation_category.lower() != _auto_cat_rework.lower():
			enable_results_dict[obj.bkc_candidate][_deployed] = enable_results_dict[obj.bkc_candidate][_deployed] + 1
		if (obj.automation_potential.lower() == AUTOMATION_CATEGORIES.MANUAL.lower() or obj.automation_potential.lower() == AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE.lower()) and obj.is_new_tc.lower() != YES and obj.is_deprecated.lower() != YES:
			enable_results_dict[obj.bkc_candidate][_manual] = enable_results_dict[obj.bkc_candidate][_manual] + 1
		if obj.automation_block_category.lower() not in ["", _exploration.lower()] and obj.is_new_tc.lower() != YES and obj.automation_applicable.lower() == YES and obj.automation_completion.lower() == "" and obj.automation_potential != AUTOMATION_CATEGORIES.MANUAL and obj.automation_potential != AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE and obj.is_deprecated.lower() != YES:
			enable_results_dict[obj.bkc_candidate][_auto_blocked] = enable_results_dict[obj.bkc_candidate][_auto_blocked] + 1

		if obj.automation_block_category.lower() == _exploration.lower() and obj.is_new_tc.lower() != YES and obj.automation_applicable.lower() == YES and obj.automation_completion.lower() == "" and obj.automation_potential != AUTOMATION_CATEGORIES.MANUAL and obj.automation_potential != AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE and obj.is_deprecated.lower() != YES:
			enable_results_dict[obj.bkc_candidate][_exploration] = enable_results_dict[obj.bkc_candidate][_exploration] + 1

		if obj.automation_category.lower() == _auto_cat_rework.lower() and obj.is_deprecated.lower() != YES:
			print("Rewok found : {} {}".format(obj.automation_category, obj.title))
			enable_results_dict[obj.bkc_candidate][_rework] = enable_results_dict[obj.bkc_candidate][_rework] + 1

		if obj.is_deprecated.lower() == YES:
			enable_results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.DEPRECATED_TCS] = enable_results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.DEPRECATED_TCS] + 1

		if obj.is_new_tc.lower() == YES and obj.is_deprecated.lower() != YES:
			enable_results_dict[obj.bkc_candidate][NEW_TCS] = enable_results_dict[obj.bkc_candidate][NEW_TCS] + 1

	for key, value in enable_results_dict.items():
		enable_results_dict[key][_pending] = enable_results_dict[key][_total_automatable] - enable_results_dict[key][_total_automated] - enable_results_dict[key][_auto_blocked] - enable_results_dict[key][_exploration]
		enable_results_dict[key][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY] = enable_results_dict[key][_total_automated] - enable_results_dict[key][_deployed]

	enable_results_dict["Total"] = {_total_tests: 0,_total_automatable: 0,_manual: 0,
													   _total_automated: 0, _deployed: 0,
													   PARENT_TABLE_CONTENTS.YET_TO_DEPLOY: 0, _pending: 0,
													   _auto_blocked: 0, _exploration: 0,
													   _rework: 0, PARENT_TABLE_CONTENTS.DEPRECATED_TCS: 0, NEW_TCS:0}
	for obj in enable_results_dict.keys():
		if obj != "Total":
			enable_results_dict["Total"][_total_tests] = enable_results_dict["Total"][_total_tests] + enable_results_dict[obj][_total_tests]
			enable_results_dict["Total"][_total_automatable] = enable_results_dict["Total"][_total_automatable] + enable_results_dict[obj][_total_automatable]
			enable_results_dict["Total"][_pending] = enable_results_dict["Total"][_pending] + enable_results_dict[obj][_pending]
			enable_results_dict["Total"][_total_automated] = enable_results_dict["Total"][_total_automated] + enable_results_dict[obj][_total_automated]
			enable_results_dict["Total"][_manual] = enable_results_dict["Total"][_manual] + enable_results_dict[obj][_manual]
			enable_results_dict["Total"][_deployed] = enable_results_dict["Total"][_deployed] + enable_results_dict[obj][_deployed]
			enable_results_dict["Total"][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY] = enable_results_dict["Total"][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY] + enable_results_dict[obj][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY]
			enable_results_dict["Total"][_auto_blocked] = enable_results_dict["Total"][_auto_blocked] + enable_results_dict[obj][_auto_blocked]
			enable_results_dict["Total"][_exploration] = enable_results_dict["Total"][_exploration] + enable_results_dict[obj][_exploration]
			enable_results_dict["Total"][_rework] = enable_results_dict["Total"][_rework] + enable_results_dict[obj][
				_rework]
			enable_results_dict["Total"][PARENT_TABLE_CONTENTS.DEPRECATED_TCS] = enable_results_dict["Total"][PARENT_TABLE_CONTENTS.DEPRECATED_TCS] + enable_results_dict[obj][PARENT_TABLE_CONTENTS.DEPRECATED_TCS]

			enable_results_dict["Total"][NEW_TCS] = enable_results_dict["Total"][NEW_TCS] + enable_results_dict[obj][
				NEW_TCS]
	doman_results_dict = {}
	for obj in results:
		if obj.domain not in doman_results_dict.keys():
			doman_results_dict[obj.domain] = create_candidate()

		if obj.is_new_tc.lower() == NO and obj.is_deprecated.lower() != YES:
			doman_results_dict[obj.domain][_total_tests] = doman_results_dict[obj.domain][_total_tests] + 1
		if obj.automation_potential.lower() == AUTOMATION_CATEGORIES.FULLY_AUTOMATE.lower() and obj.is_new_tc.lower() != YES and obj.automation_applicable.lower() == YES and obj.is_deprecated.lower() != YES:
			doman_results_dict[obj.domain][_total_automatable] = doman_results_dict[obj.domain][_total_automatable] + 1
		if obj.automation_potential.lower() == AUTOMATION_CATEGORIES.FULLY_AUTOMATE.lower() and obj.is_new_tc.lower() != YES and obj.automation_applicable.lower() == YES and obj.automation_completion.lower().strip() != "" and obj.is_deprecated.lower() != YES:
			doman_results_dict[obj.domain][_total_automated] = doman_results_dict[obj.domain][_total_automated] + 1
		if obj.automation_potential.lower() == AUTOMATION_CATEGORIES.FULLY_AUTOMATE.lower() and obj.is_new_tc.lower() != YES and obj.automation_applicable.lower() == YES and obj.automation_completion.lower().strip() != "" and obj.automation_deployed.lower().strip() != "" and obj.is_deprecated.lower() != YES and obj.automation_category.lower() != _auto_cat_rework:
			doman_results_dict[obj.domain][_deployed] = doman_results_dict[obj.domain][_deployed] + 1
		if obj.automation_potential.lower() == AUTOMATION_CATEGORIES.MANUAL.lower() and obj.is_new_tc.lower() != YES and obj.automation_applicable.lower() == YES or obj.automation_potential.lower() == AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE.lower() and obj.is_deprecated.lower() != YES:
			doman_results_dict[obj.domain][_manual] = doman_results_dict[obj.domain][_manual] + 1
		if obj.automation_block_category.lower() not in ["", _exploration.lower()] and obj.is_new_tc.lower() != YES and obj.automation_applicable.lower() == YES and obj.automation_completion.lower() == "" and obj.automation_potential != AUTOMATION_CATEGORIES.MANUAL and obj.automation_potential != AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE and obj.is_deprecated.lower() != YES:
			doman_results_dict[obj.domain][_auto_blocked] = doman_results_dict[obj.domain][_auto_blocked] + 1
		if obj.automation_block_category.lower() == _exploration.lower() and obj.is_new_tc.lower() != YES and obj.automation_applicable.lower() == YES and obj.automation_completion.lower() == "" and obj.automation_potential != AUTOMATION_CATEGORIES.MANUAL and obj.automation_potential != AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE and obj.is_deprecated.lower() != YES:
			doman_results_dict[obj.domain][_exploration] = doman_results_dict[obj.domain][_exploration] + 1
		if obj.is_new_tc.lower() == YES and obj.is_deprecated.lower() != YES:
			doman_results_dict[obj.domain][NEW_TCS] = doman_results_dict[obj.domain][NEW_TCS] + 1
		if obj.is_deprecated.lower() == YES:
			doman_results_dict[obj.domain][PARENT_TABLE_CONTENTS.DEPRECATED_TCS] = doman_results_dict[obj.domain][PARENT_TABLE_CONTENTS.DEPRECATED_TCS] + 1
		if obj.automation_category.lower() == _auto_cat_rework and obj.is_deprecated.lower() != YES:
			doman_results_dict[obj.domain][_rework] = doman_results_dict[obj.domain][_rework] + 1


	# print(doman_results_dict.keys())
	for key, value in doman_results_dict.items():
		doman_results_dict[key][_pending] = doman_results_dict[key][_total_automatable] - doman_results_dict[key][_total_automated] - doman_results_dict[key][_exploration] - doman_results_dict[key][_auto_blocked]
		doman_results_dict[key][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY] = doman_results_dict[key][_total_automated] - doman_results_dict[key][_deployed]

	doman_results_dict["Total"] = {_total_tests: 0,_total_automatable: 0,_manual: 0,
													   _total_automated: 0, _deployed: 0,
													   PARENT_TABLE_CONTENTS.YET_TO_DEPLOY: 0, _pending: 0,
													   _auto_blocked: 0, _exploration: 0,
													   _rework: 0, PARENT_TABLE_CONTENTS.DEPRECATED_TCS: 0, NEW_TCS:0}
	for obj in doman_results_dict.keys():
		if obj != "Total":
			doman_results_dict["Total"][_total_tests] = doman_results_dict["Total"][_total_tests] + doman_results_dict[obj][_total_tests]
			doman_results_dict["Total"][_total_automatable] = doman_results_dict["Total"][_total_automatable] + doman_results_dict[obj][_total_automatable]
			doman_results_dict["Total"][_pending] = doman_results_dict["Total"][_pending] + doman_results_dict[obj][_pending]
			doman_results_dict["Total"][_total_automated] = doman_results_dict["Total"][_total_automated] + doman_results_dict[obj][_total_automated]
			doman_results_dict["Total"][_manual] = doman_results_dict["Total"][_manual] + doman_results_dict[obj][_manual]
			doman_results_dict["Total"][_deployed] = doman_results_dict["Total"][_deployed] + doman_results_dict[obj][_deployed]
			doman_results_dict["Total"][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY] = doman_results_dict["Total"][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY] + doman_results_dict[obj][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY]
			doman_results_dict["Total"][_auto_blocked] = doman_results_dict["Total"][_auto_blocked] + doman_results_dict[obj][_auto_blocked]
			doman_results_dict["Total"][_exploration] = doman_results_dict["Total"][_exploration] + doman_results_dict[obj][_exploration]
			doman_results_dict["Total"][NEW_TCS] = doman_results_dict["Total"][NEW_TCS] + doman_results_dict[obj][NEW_TCS]
			doman_results_dict["Total"][PARENT_TABLE_CONTENTS.DEPRECATED_TCS] = doman_results_dict["Total"][PARENT_TABLE_CONTENTS.DEPRECATED_TCS] + doman_results_dict[obj][PARENT_TABLE_CONTENTS.DEPRECATED_TCS]
			doman_results_dict["Total"][_rework] = doman_results_dict["Total"][_rework] + doman_results_dict[obj][_rework]
	return render(request, "automation/platform_statistics.html", context={"results_dict": results_dict,  "bkc": bkc, "username": request.session["username"], "enable_results_dict": enable_results_dict, "platform": platform, "doman_results_dict": doman_results_dict})




def bkc_filters(request, platform):
	if not login(request):
		return render(request, "automation/login.html", context={})
	results = TestCaseExcel.objects.filter(platform=platform, automation_applicable=YES).order_by("id")
	bkc_categories = {}
	domain_wise_filters = {}
	for category in _BKC_CATEGORIES:
		bkc_categories[category] = _FILTERS
	for obj in results:
		if obj.domain not in domain_wise_filters.keys():
			domain_wise_filters[obj.domain] = _FILTERS
	return render(request, "automation/bkc_filters.html", context={"bkc_categories": bkc_categories, "domain_wise_filters": domain_wise_filters, "platform": platform, "username": request.session["username"]})


def filter_query(request, platform, bkc, bkc_candidate, automation_category):
	print("==============\n", request)
	if not login(request):
		return render(request, "automation/login.html", context={})
	test_plan_details = []
	candidate_categories = _BKC_CANDIDATES
	if automation_category.lower() == "new tcs":
		new_tc = YES
	else:
		new_tc = NO
	if bkc == "PV":
		candidate_categories = _PV_CANDIDATES
	egs_blocked = request.GET.get("egs_blocked")
	print("EGS block status : {}".format(egs_blocked))
	db_columns = ['temp_test_case_id', 'phoenix_id', 'test_case_id', 'title','is_new_tc', 'is_deprecated', 'developer_comments', 'database_source', 'feature_group', 'domain', 'operating_system', 'hw_config','milestone', 'bkc_candidate',
				  'automation_potential', 'automation_eta', 'automation_completion','automation_deployment_eta', 'deployed_result',
				  'automation_deployed', 'automation_developer', 'egs_blocked', 'automation_category',
				  'automation_remarks', 'automation_block_category','source_patch_link', 'non_automatable_remarks', 'platform_tc_category']
	if bkc.upper() not in _DB_SOURCES.keys():
		return render(request, "automation/filter_query.html", context={"test_plan_details": test_plan_details, "platform": platform, "hsdes_columns": db_columns, "username": request.session["username"]})
	if bkc_candidate in candidate_categories:
		#if automation_category not in PARENT_TABLE_CONTENTS:
		#	return render(request, "automation/filter_query.html", context={"test_plan_details": test_plan_details, "platform": platform, "hsdes_columns": db_columns})
		if egs_blocked == "False":
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, bkc_candidate=bkc_candidate, automation_applicable=YES).exclude(is_deprecated=YES)
			if automation_category.lower() == PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
											 bkc_candidate=bkc_candidate,egs_blocked=egs_blocked,
											 automation_potential=AUTOMATION_CATEGORIES.FULLY_AUTOMATE, automation_applicable=YES, is_new_tc=new_tc).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,egs_blocked=egs_blocked,
											 bkc_candidate=bkc_candidate, automation_applicable=YES, is_new_tc=new_tc).exclude(automation_completion="", is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.MANUAL.lower():

				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, automation_applicable=YES,
											 bkc_candidate=bkc_candidate, is_new_tc=new_tc, automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE], egs_blocked=egs_blocked).exclude(is_deprecated=YES)
				#print(q1)
				#print(q2)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,egs_blocked=egs_blocked,
											 bkc_candidate=bkc_candidate, is_new_tc=new_tc, automation_potential=AUTOMATION_CATEGORIES.FULLY_AUTOMATE, automation_completion="", automation_applicable=YES, automation_block_category="").exclude(is_deprecated=YES).exclude(automation_block_category=PARENT_TABLE_CONTENTS.EXPLORATION)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.DEPLOYED.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,egs_blocked=egs_blocked,
											 bkc_candidate=bkc_candidate, is_new_tc=new_tc, automation_applicable=YES).exclude(automation_completion="").exclude(automation_deployed="").exclude(is_deprecated=YES).exclude(automation_category=AUTOMATION_DEV_CATEGORIES.REWORK)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.YET_TO_DEPLOY.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,egs_blocked=egs_blocked,
											 bkc_candidate=bkc_candidate, is_new_tc=new_tc, automation_deployed="", automation_applicable=YES).exclude(automation_completion="").exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate,egs_blocked=egs_blocked,
															automation_deployed="", is_new_tc=new_tc, automation_completion="", automation_applicable=YES).exclude(automation_block_category="").exclude(automation_block_category=PARENT_TABLE_CONTENTS.EXPLORATION).exclude(automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE])
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.EXPLORATION.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate, is_new_tc=NO,egs_blocked=egs_blocked, automation_applicable=YES,
															automation_deployed="", automation_completion="", automation_block_category=PARENT_TABLE_CONTENTS.EXPLORATION).exclude(automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE])
			elif automation_category.lower() == NEW_TCS.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate, is_new_tc=YES,egs_blocked=egs_blocked, automation_applicable=YES,
															automation_deployed="", automation_completion="").exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.REWORK.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, egs_blocked=egs_blocked,
															bkc_candidate=bkc_candidate,automation_applicable=YES,
															automation_category=AUTOMATION_DEV_CATEGORIES.REWORK).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.DEPRECATED_TCS.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate,automation_applicable=YES,
															is_deprecated=YES, egs_blocked=NO)
		else:
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
														bkc_candidate=bkc_candidate, is_new_tc=new_tc, automation_applicable=YES).exclude(is_deprecated=YES)
			if automation_category.lower() == PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate, is_new_tc=new_tc,
															automation_potential=AUTOMATION_CATEGORIES.FULLY_AUTOMATE, automation_applicable=YES).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate, is_new_tc=NO, automation_applicable=YES).exclude(
					automation_completion="").exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.MANUAL.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate, is_new_tc=new_tc,
															automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE], automation_applicable=YES).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate, is_new_tc=new_tc,
															automation_potential=AUTOMATION_CATEGORIES.FULLY_AUTOMATE,
															automation_completion="", automation_applicable=YES, automation_block_category="").exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.DEPLOYED.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate, is_new_tc=new_tc, automation_applicable=YES).exclude(
					automation_completion="").exclude(automation_deployed="").exclude(automation_deployed="").exclude(is_deprecated=YES).exclude(automation_category=AUTOMATION_DEV_CATEGORIES.REWORK)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.YET_TO_DEPLOY.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate, is_new_tc=new_tc,
															automation_deployed="", automation_applicable=YES).exclude(automation_completion="").exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate, is_new_tc=new_tc,
															automation_deployed="", automation_completion="", automation_applicable=YES).exclude(automation_block_category="").exclude(automation_block_category=PARENT_TABLE_CONTENTS.EXPLORATION).exclude(automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE]).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.EXPLORATION.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate, is_new_tc=new_tc,
															automation_deployed="", automation_completion="", automation_block_category=PARENT_TABLE_CONTENTS.EXPLORATION, automation_applicable=YES).exclude(automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE]).exclude(is_deprecated=YES)
			elif automation_category.lower() == NEW_TCS.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate, is_new_tc=YES,
															automation_deployed="", automation_completion="", automation_applicable=YES).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.REWORK.lower():
				# import pdb; pdb.set_trace()
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate,
															automation_category="REWORK".lower()).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.DEPRECATED_TCS.lower():
				# import pdb; pdb.set_trace()
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															bkc_candidate=bkc_candidate,
															is_deprecated=YES.lower())
		for item in query_filter:
			# print (item.test_case_id)
			sub_dict = {}
			for column in db_columns:
				sub_dict[column] = eval("item.%s" % column)
			test_plan_details.append(sub_dict)


	elif bkc_candidate.lower() == "total":
		#if automation_category not in PARENT_TABLE_CONTENTS:
		#	return render(request, "automation/filter_query.html", context={"test_plan_details": test_plan_details, "platform": platform, "hsdes_columns": db_columns})
		if egs_blocked == "False":
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, egs_blocked=egs_blocked, automation_applicable=YES).exclude(is_deprecated=YES)
			if automation_category.lower() == PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, is_new_tc=new_tc, platform_tc_category=bkc,egs_blocked=egs_blocked,
											 automation_potential=AUTOMATION_CATEGORIES.FULLY_AUTOMATE, automation_applicable=YES).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, is_new_tc=new_tc,egs_blocked=egs_blocked, automation_applicable=YES).exclude(automation_completion="").exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.MANUAL.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, is_new_tc=new_tc, automation_applicable=YES, automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE], egs_blocked=egs_blocked).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,egs_blocked=egs_blocked,
															automation_potential=AUTOMATION_CATEGORIES.FULLY_AUTOMATE, is_new_tc=new_tc, automation_completion="", automation_applicable=YES, automation_block_category="").exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.DEPLOYED.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, is_new_tc=new_tc,egs_blocked=egs_blocked, automation_applicable=YES).exclude(automation_completion="").exclude(automation_deployed="").exclude(automation_deployed="").exclude(is_deprecated=YES).exclude(automation_category=AUTOMATION_DEV_CATEGORIES.REWORK).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.YET_TO_DEPLOY.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															egs_blocked=egs_blocked, automation_deployed="", is_new_tc=new_tc, automation_applicable=YES).exclude(automation_completion="").exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, is_new_tc=new_tc, egs_blocked=egs_blocked,
															automation_deployed="", automation_completion="", automation_applicable=YES).exclude(automation_block_category="").exclude(automation_block_category=PARENT_TABLE_CONTENTS.EXPLORATION).exclude(automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE]).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.EXPLORATION.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, is_new_tc=new_tc, egs_blocked=egs_blocked,
															automation_deployed="", automation_completion="", automation_block_category=PARENT_TABLE_CONTENTS.EXPLORATION, automation_applicable=YES).exclude(automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE]).exclude(is_deprecated=YES)
			elif automation_category.lower() == NEW_TCS.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,egs_blocked=egs_blocked,
															automation_deployed="", automation_completion="", is_new_tc=new_tc, automation_applicable=YES).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.REWORK.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															automation_category=AUTOMATION_DEV_CATEGORIES.REWORK).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.DEPRECATED_TCS.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															is_deprecated=YES)

		else:
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, is_new_tc=new_tc, automation_applicable=YES).exclude(is_deprecated=YES)
			if automation_category.lower() == PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															automation_potential=AUTOMATION_CATEGORIES.FULLY_AUTOMATE, is_new_tc=new_tc, automation_applicable=YES).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, is_new_tc=new_tc, automation_applicable=YES).exclude(automation_completion="").exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.MANUAL.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, is_new_tc=new_tc,
															automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE], automation_applicable=YES).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															automation_potential=AUTOMATION_CATEGORIES.FULLY_AUTOMATE,
															automation_completion="", is_new_tc=new_tc, automation_applicable=YES, automation_block_category="").exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.DEPLOYED.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, is_new_tc=new_tc, platform_tc_category=bkc, automation_applicable=YES).exclude(
					automation_completion="").exclude(automation_deployed="").exclude(is_deprecated=YES).exclude(automation_category=AUTOMATION_DEV_CATEGORIES.REWORK)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.YET_TO_DEPLOY.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															automation_deployed="", automation_applicable=YES, is_new_tc=new_tc).exclude(automation_completion="").exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															automation_deployed="", automation_completion="", is_new_tc=new_tc, automation_applicable=YES).exclude(automation_block_category="").exclude(automation_block_category=PARENT_TABLE_CONTENTS.EXPLORATION).exclude(automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE]).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.EXPLORATION.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															automation_deployed="", automation_completion="", is_new_tc=new_tc, automation_block_category=PARENT_TABLE_CONTENTS.EXPLORATION, automation_applicable=YES).exclude(automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE]).exclude(is_deprecated=YES)

			elif automation_category.lower() == NEW_TCS.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															automation_deployed="", automation_completion="", is_new_tc=YES, automation_applicable=YES).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.REWORK.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															automation_category=AUTOMATION_DEV_CATEGORIES.REWORK).exclude(is_deprecated=YES)
			elif automation_category.lower() == PARENT_TABLE_CONTENTS.DEPRECATED_TCS.lower():
				query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
															is_deprecated=YES)

		for item in query_filter:
			# print (item.test_case_id)
			sub_dict = {}
			for column in db_columns:
				sub_dict[column] = eval("item.%s" % column)
			test_plan_details.append(sub_dict)




	else:
		query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
													domain=bkc_candidate, automation_applicable=YES).exclude(is_deprecated=YES)
		if automation_category.lower() == PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE.lower():
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
														domain=bkc_candidate, is_new_tc=new_tc,
														automation_potential=AUTOMATION_CATEGORIES.FULLY_AUTOMATE, automation_applicable=YES).exclude(is_deprecated=YES)
		elif automation_category.lower() == PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED.lower():
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, is_new_tc=new_tc,
														domain=bkc_candidate, automation_applicable=YES).exclude(automation_completion="").exclude(is_deprecated=YES)
		elif automation_category.lower() == PARENT_TABLE_CONTENTS.MANUAL.lower():
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, is_new_tc=new_tc,
														domain=bkc_candidate,
														automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE], automation_applicable=YES).exclude(is_deprecated=YES)
		elif automation_category.lower() == PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE.lower():
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
														domain=bkc_candidate, is_new_tc=new_tc,
														automation_potential=AUTOMATION_CATEGORIES.FULLY_AUTOMATE,
														automation_completion="", automation_applicable=YES, automation_block_category="").exclude(is_deprecated=YES)
		elif automation_category.lower() == PARENT_TABLE_CONTENTS.DEPLOYED.lower():
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
														domain=bkc_candidate, is_new_tc=new_tc, automation_applicable=YES).exclude(
				automation_completion="").exclude(automation_deployed="").exclude(is_deprecated=YES).exclude(automation_category=AUTOMATION_DEV_CATEGORIES.REWORK)
		elif automation_category.lower() == PARENT_TABLE_CONTENTS.YET_TO_DEPLOY.lower():
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, is_new_tc=new_tc,
														domain=bkc_candidate, automation_deployed="", automation_applicable=YES).exclude(automation_completion="").exclude(is_deprecated=YES)
		elif automation_category.lower() == PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED.lower():
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
														domain=bkc_candidate, is_new_tc=new_tc,
														automation_deployed="", automation_completion="", automation_applicable=YES).exclude(
				automation_block_category="").exclude(automation_block_category=PARENT_TABLE_CONTENTS.EXPLORATION).exclude(automation_potential__in = [AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE]).exclude(is_deprecated=YES)
		elif automation_category.lower() == PARENT_TABLE_CONTENTS.EXPLORATION.lower():
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,domain=bkc_candidate,
														automation_deployed="", is_new_tc=new_tc, automation_completion="",
														automation_block_category=PARENT_TABLE_CONTENTS.EXPLORATION, automation_applicable=YES).exclude(
				automation_potential__in=[AUTOMATION_CATEGORIES.MANUAL, AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE]).exclude(is_deprecated=YES)
		elif automation_category.lower() == NEW_TCS.lower():
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,domain=bkc_candidate,
														automation_deployed="", is_new_tc=YES, automation_completion="", automation_applicable=YES).exclude(is_deprecated=YES)
		elif automation_category.lower() == PARENT_TABLE_CONTENTS.REWORK.lower():
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
														domain=bkc_candidate,
														automation_category=AUTOMATION_DEV_CATEGORIES.REWORK).exclude(is_deprecated=YES)
		elif automation_category.lower() == PARENT_TABLE_CONTENTS.DEPRECATED_TCS.lower():
			query_filter = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,
														domain=bkc_candidate,
														is_deprecated=YES)

		for item in query_filter:
			# print (item.test_case_id)
			sub_dict = {}
			for column in db_columns:
				sub_dict[column] = eval("item.%s" % column)
			test_plan_details.append(sub_dict)
	# print (test_plan_details)

	#return render(request, "automation/testplan.html",
	#			  context={"test_plan_details": test_plan_details, "platform": platform, "hsdes_columns": db_columns})
	return render(request, "automation/filter_query.html", context={"test_plan_details": test_plan_details, "platform": platform, "hsdes_columns": db_columns, "username": request.session["username"]})




def automation_dev_tracker(request, platform, bkc):
	if not login(request):
		return render(request, "automation/login.html", context={})
	results = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, automation_applicable=YES).exclude(automation_completion="").order_by("id")
	developers = list(set([obj.automation_developer for obj in results if obj.automation_developer.strip() != ""]))
	developed_wws = list(set([obj.automation_completion for obj in results if obj.automation_completion.strip() != ""]))
	platforms_list = []
	platforms = Platform.objects.all()
	for p in platforms:
		platforms_list.append(p.platform_name_short)
	developed_results = OrderedDict()
	total_developed_results = OrderedDict()
	developers.append("Total")
	for developer in developers:
		developed_results[developer] = {}
		for ww in sorted(developed_wws, reverse = True):
			developed_results[developer][ww] = 0


	for obj in results:
		if obj.automation_developer != "" and obj.automation_completion != "":
			developed_results[obj.automation_developer][obj.automation_completion] = developed_results[obj.automation_developer][obj.automation_completion]  + 1
			developed_results["Total"][obj.automation_completion] = developed_results["Total"][obj.automation_completion] + 1
	planned_wws = []
	planned_results = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, automation_applicable=YES).order_by("id")
	for obj in planned_results:
		actual_planned_wws = [ww.strip() for ww in obj.automation_eta.split(",") if ww.strip() != ""]
		for a_ww in sorted(actual_planned_wws, reverse=True):
			if a_ww not in planned_wws:
				planned_wws.append(a_ww)
	planned_wws = (list(set(planned_wws)))
	planned_wws.sort(reverse=True)
	for ww in sorted(planned_wws, reverse=True):
		total_developed_results[ww] = OrderedDict()
		total_developed_results[ww]["Actual"] = 0
		total_developed_results[ww]["Plan"] = 0
		objects = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, automation_eta__contains=ww, automation_applicable=YES).order_by("id") | TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, automation_completion=ww).order_by("id")
		for obj in objects:
			actual_planned_wws = [p_ww.strip() for p_ww in obj.automation_eta.split(",") if p_ww.strip() != ""]
			if ww in actual_planned_wws:
				total_developed_results[ww]["Plan"] = total_developed_results[ww]["Plan"] + 1

			if ww == obj.automation_completion:
				total_developed_results[ww]["Actual"] = total_developed_results[ww]["Actual"] + 1
	u_obj = User.objects.get(user=request.session["idsid"])
	is_auto_admin = False
	if u_obj.role.lower() in _AUTOMATION_ADMINS:
		is_auto_admin = True
	#for key, value in developed_results.items():
		#for ww in developed_wws:
		#	developed_results["Total"][ww] = developed_results["Total"][ww] + developed_results[key][ww]

	return render(request, "automation/automation_dev_tracker.html", context={"results_dict": developed_results, "bkc":bkc, "total_developed_results": total_developed_results,"is_auto_admin": is_auto_admin, "username": request.session["username"], "platform": platform, "platforms": platforms_list, "planned_wws": planned_wws})

def developer_tracker(request, platform, bkc, developer, developed_ww):
	if not login(request):
		return render(request, "automation/login.html", context={})
	db_columns = ['temp_test_case_id', 'phoenix_id', 'test_case_id', 'title','is_new_tc', 'is_deprecated', 'developer_comments', 'database_source', 'feature_group', 'domain', 'operating_system', 'hw_config',  'milestone', 'bkc_candidate',
				  'automation_potential', 'automation_eta', 'automation_completion', 'automation_deployment_eta',
				  'automation_deployed', 'automation_developer', 'egs_blocked', 'automation_category',
				  'automation_remarks', 'automation_block_category','source_patch_link', 'non_automatable_remarks', 'platform_tc_category']
	if developer == "Total":
		tcid_details = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,automation_completion=developed_ww, automation_applicable=YES).exclude(automation_developer = "").order_by('id')
	else:
		tcid_details = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, automation_developer=developer, automation_completion=developed_ww, automation_applicable=YES).order_by('id')
	test_plan_details = []
	for item in tcid_details:
		sub_dict = {}
		for column in db_columns:
			sub_dict[column] = eval("item.%s" % column)
		test_plan_details.append(sub_dict)

	return render(request, "automation/filter_query.html", context={"test_plan_details": test_plan_details, "platform": platform, "hsdes_columns": db_columns, "username": request.session["username"], "platform": platform})

def developer_plan_tracker(request, platform, bkc, developer, plan_ww, automation_category):
	if not login(request):
		return render(request, "automation/login.html", context={})
	db_columns = ['temp_test_case_id', 'phoenix_id', 'test_case_id', 'title','is_new_tc', 'is_deprecated', 'developer_comments', 'database_source', 'feature_group', 'domain', 'operating_system', 'hw_config','milestone', 'bkc_candidate',
				  'automation_potential', 'automation_eta', 'automation_completion','automation_deployment_eta',
				  'automation_deployed', 'automation_developer', 'egs_blocked', 'automation_category',
				  'automation_remarks', 'automation_block_category', 'source_patch_link', 'non_automatable_remarks', 'platform_tc_category']
	if developer == "Total":
		tcid_details = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc,automation_eta__contains=plan_ww, automation_category=automation_category, automation_applicable=YES).exclude(automation_developer = "").order_by('id')
	else:
		tcid_details = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, automation_developer=developer, automation_eta__contains=plan_ww, automation_category=automation_category, automation_applicable=YES).order_by('id')
	test_plan_details = []

	for item in tcid_details:
		automation_etas = [ww.strip() for ww in item.automation_eta.split(",") if ww.strip() != ""]
		if plan_ww in automation_etas:
			sub_dict = {}
			for column in db_columns:
				sub_dict[column] = eval("item.%s" % column)
			test_plan_details.append(sub_dict)
	print (test_plan_details)
	return render(request, "automation/filter_query.html", context={"test_plan_details": test_plan_details, "platform": platform, "hsdes_columns": db_columns, "username": request.session["username"], "platform": platform})


def get_automation_plan(request, platform, bkc, ww):
	#print(request.POST)
	results = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, automation_eta__contains = ww, automation_applicable=YES).order_by('id')
	planned_data_dict = {}
	developers = list(set([obj.automation_developer for obj in results if obj.automation_developer.strip() != ""]))


	developed_results = OrderedDict()
	test_case_list = OrderedDict()
	developers.append("Total")
	for developer in developers:
		developed_results[developer] = {}
		test_case_list[developer] = []
		for category in sorted(_AUTOMATION_DEV_CATEGORIES):
			if category != "":
				developed_results[developer][category] = 0

	for obj in results:
		actual_planned_wws = [p_ww.strip() for p_ww in obj.automation_eta.split(",") if p_ww.strip() != ""]
		if obj.automation_developer != "" and obj.automation_eta != "" and obj.automation_category != "" and ww in actual_planned_wws:
			test_case_list[obj.automation_developer].append([obj.test_case_id, obj.title, obj.automation_developer, obj.automation_category, obj.automation_block_category, obj.developer_comments])
			developed_results[obj.automation_developer][obj.automation_category] = developed_results[obj.automation_developer][obj.automation_category] + 1
			developed_results["Total"][obj.automation_category] = developed_results["Total"][
																		obj.automation_category] + 1
	body = """
		<h2>Auomation Plan: """ + ww + """</h2>
		<table border="1">
			<tr>
				<th>S.No</th>
				<th>test_case_id</th>
				<th>title</th>
				<th>automation_developer</th>
				<th>automation_category</th>
				<th>automation_block_category</th>
				<th>developer_comments</th>
			</tr>
			%s
		</table>
	
	"""

	#print(test_case_list)
	html_data = """<table class="table table-bordered" id="plan">"""
	headings = html_data + """<tr class="info">"""
	for key, value in developed_results.items():
		html_data = html_data + "<th></th>"
		for k, v in value.items():
			html_data = html_data + "<th>%s</th>" % k
		break
	html_data = html_data + "</tr>"
	data = """"""
	for key, value in developed_results.items():
		html_data = html_data + "<tr><td>%s</td>" % key
		for k, v in value.items():
			if v !=0:
				html_data = html_data + '<td style="background-color:green;"><a style="color:white;" target="_blank" href="http://%s/automation/dev_tracker/%s/%s/%s/%s/%s/">%s</a></td>' % (request.get_host(),platform,bkc,key,ww,k, v)
			else:
				html_data = html_data + "<td>%s</td>" % v
		html_data = html_data + "</tr>"
	html_data = html_data + "</table>"
	if str(request.POST.get("send_email")).lower() == "true":
		i_body = """"""
		count = 0
		for developer, value in test_case_list.items():
			#send_mail(subject, head_body + body, to= _CW_AUTOMATION_TEAM + [updated_user_email], cc=_CW_AUTOMATION_TEAM_LEADS + _AUTOMATION_LEADS) email_recipients
			for i_value in value:
				count = count + 1
				i_body = i_body + """<tr><td>%s</td>""" % count
				for item in i_value:
					i_body = i_body + """<td><pre>%s</pre></td>""" % item
				i_body = i_body + "</tr>"
		email_list = [email for email in request.POST.get("email_recipients").split(",") if email.strip() != ""]
		send_mail("%s Automation Planned TCs - Update" % ww, (body % i_body) + html_data, to=email_list, cc=_AUTOMATION_LEADS)
	#print(html_data)
	return HttpResponse(html_data)


def automation_charts(request, platform, bkc):
	if not login(request):
		return render(request, "automation/login.html", context={})
	results = TestCaseExcel.objects.filter(platform=platform, platform_tc_category=bkc, automation_applicable=YES).order_by("id")
	enable_results = TestCaseExcel.objects.filter(platform=platform, egs_blocked="False", platform_tc_category=bkc, automation_applicable=YES).order_by("id")
	results_dict = {}
	for obj in results:
		if obj.bkc_candidate not in results_dict.keys():
			results_dict[obj.bkc_candidate] = {PARENT_TABLE_CONTENTS.TOTAL_TESTS: 0, PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE: 0, PARENT_TABLE_CONTENTS.MANUAL: 0,
											   PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED: 0, PARENT_TABLE_CONTENTS.DEPLOYED: 0,
											   PARENT_TABLE_CONTENTS.YET_TO_DEPLOY: 0, PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE: 0, PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED: 0}
		results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.TOTAL_TESTS] = results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.TOTAL_TESTS] + 1
		if obj.automation_potential.lower() == AUTOMATION_CATEGORIES.FULLY_AUTOMATE.lower():
			results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE] = results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE] + 1
		if obj.automation_potential.lower() == AUTOMATION_CATEGORIES.FULLY_AUTOMATE.lower() and obj.automation_completion.lower().strip() != "":
			results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED] = results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED] + 1
		if obj.automation_potential.lower() == AUTOMATION_CATEGORIES.FULLY_AUTOMATE.lower() and obj.automation_completion.lower().strip() != "" and obj.automation_deployed.lower().strip() != "":
			results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.DEPLOYED] = results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.DEPLOYED] + 1
		if obj.automation_potential.lower() == AUTOMATION_CATEGORIES.MANUAL.lower() or obj.automation_potential.lower() == AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE.lower():
			results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.MANUAL] = results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.MANUAL] + 1
		if obj.automation_block_category.lower() != "" and obj.automation_completion.lower() == "" and obj.automation_potential != AUTOMATION_CATEGORIES.MANUAL and obj.automation_potential != AUTOMATION_CATEGORIES.PARTIAL_AUTOMATE:
			results_dict[obj.bkc_candidate][PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED] = results_dict[obj.bkc_candidate][
																				PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED] + 1

	for key, value in results_dict.items():
		results_dict[key][PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE] = results_dict[key][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE] - results_dict[key][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED]
		results_dict[key][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY] = results_dict[key][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED] - results_dict[key][PARENT_TABLE_CONTENTS.DEPLOYED]

	results_dict["Total"] = {PARENT_TABLE_CONTENTS.TOTAL_TESTS: 0, PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE: 0,
							 PARENT_TABLE_CONTENTS.MANUAL: 0, PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED: 0,PARENT_TABLE_CONTENTS.DEPLOYED: 0,
							 PARENT_TABLE_CONTENTS.YET_TO_DEPLOY: 0, PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE: 0, PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED: 0}
	for obj in results_dict.keys():
		if obj != "Total":
			results_dict["Total"][PARENT_TABLE_CONTENTS.TOTAL_TESTS] = results_dict["Total"][PARENT_TABLE_CONTENTS.TOTAL_TESTS] + results_dict[obj][PARENT_TABLE_CONTENTS.TOTAL_TESTS]
			results_dict["Total"][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE] = results_dict["Total"][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE] + results_dict[obj][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE]
			results_dict["Total"][PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE] = results_dict["Total"][PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE] + results_dict[obj][PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE]
			results_dict["Total"][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED] = results_dict["Total"][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED] + results_dict[obj][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED]
			results_dict["Total"][PARENT_TABLE_CONTENTS.MANUAL] = results_dict["Total"][PARENT_TABLE_CONTENTS.MANUAL] + results_dict[obj][PARENT_TABLE_CONTENTS.MANUAL]
			results_dict["Total"][PARENT_TABLE_CONTENTS.DEPLOYED] = results_dict["Total"][PARENT_TABLE_CONTENTS.DEPLOYED] + results_dict[obj][PARENT_TABLE_CONTENTS.DEPLOYED]
			results_dict["Total"][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY] = results_dict["Total"][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY] + results_dict[obj][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY]
			results_dict["Total"][PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED] = results_dict["Total"][PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED] + results_dict[obj][PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED]

	return render(request, "automation/charts.html", context={"test_plan_details": results_dict,
															  "total_tests" : results_dict["Total"][PARENT_TABLE_CONTENTS.TOTAL_TESTS],
															  "total_automatable": results_dict["Total"][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATABLE],
															  "manual": results_dict["Total"][PARENT_TABLE_CONTENTS.MANUAL],
															  "pending_to_automate_without_blockers": results_dict["Total"][PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE] - results_dict["Total"][PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED],
															  "automated": results_dict["Total"][PARENT_TABLE_CONTENTS.TOTAL_AUTOMATED],
															  "blocked": results_dict["Total"][PARENT_TABLE_CONTENTS.AUTOMATION_BLOCKED],
															  "pending_to_automate": results_dict["Total"][PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE],
															  "yet_to_deploy": results_dict["Total"][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY],
															  "yet_to_deploy_and_pending_to_automate": results_dict["Total"][PARENT_TABLE_CONTENTS.YET_TO_DEPLOY] + results_dict["Total"][PARENT_TABLE_CONTENTS.PENDING_TO_AUTOMATE],
															  "deployed": results_dict["Total"][PARENT_TABLE_CONTENTS.DEPLOYED],
															  "platform": platform, "username": request.session["username"]})


import pandas as pd
import weakref
import re



class EsApi:


    def __init__(self, env):
        self.version = '0.1'
        self.lasterror = ''
        # self.query = None

        if env in ('PREPRODUCTION', 'PRODUCTION'):
            self.env = env
        else:
            err = 'Env must be "PRODUCTION" or "PREPRODUCTION"'
            self.setLastError(err)
            raise TypeError(err)

    def Article(self):

        return Article(self)


    def getLastError(self):

        return self.lasterror


    def send_request(self, method, args, data={},func = ''):

        if self.env == 'PRODUCTION':
            url = 'https://hsdes.intel.com/rest/'
        else:
            url = 'https://hsdes-pre.intel.com/rest/'

        url += args
        app = 'Python Rest API 0.2 ' + func
        headers = {'Content-type': 'application/json', 'APP': app}


        try:

            if method == 'post':
                response = requests.post(url=url, verify=False, auth=HTTPKerberosAuth(), headers=headers, json=data)

            elif method == 'get':
                response = requests.get(url=url, verify=False, auth=HTTPKerberosAuth(), headers=headers, allow_redirects=True)

            elif method == 'put':
                #print(url)
                response = requests.put(url=url, verify=False, auth=HTTPKerberosAuth(), headers=headers, json=data)

            else:
                raise Exception('Invalid/unsupported rest method')

            if response.status_code == 200:
                if 'json' in response.headers['content-type']:
                    return response.json()
                elif 'text' in response.headers['content-type']:
                    return response.text
                else:
                    return response



            else:
                return response.text

        except Exception as exc:

            self.setLastError(exc)
            raise exc


##########################################################################################


##########################################################################################
class Article:
    # reserved_cols = ['updated_fields','esapi','data', 'id','es','hierarchy_id','hierarchy_path','is_current','parent_id','record_type','rev','row_num','subject', 'tenant', 'parent']

    reserved_cols = ['updated_fields', 'esapi', 'data', 'id', 'subject', 'tenant']

    def __init__(self, esapi):

        self.updated_fields = []

        if not isinstance(esapi, EsApi):
            err = '''Article object must be initiated from an EsApi object.
            e.g.
            esapi = EsApi('PREPRODUCTION')
            qry = Article(esapi)'''

            raise TypeError(err)

        self.esapi = weakref.ref(esapi)

        self.id = None
        self.tenant = None
        self.subject = None

    # --------------------------------------------------------------------------------------
    '''def __setattr__(self,field_name,field_value):
        #print(name, value)
        self.__dict__[field_name] = field_value
        if field_name not in self.reserved_cols:
            self.updated_fields.append({field_name: field_value})
        else:
            pass'''

    # --------------------------------------------------------------------------------------
    def set(self, field_name, field_value):

        self.updated_fields.append({field_name: field_value})

    # --------------------------------------------------------------------------------------
    def get(self, field_name):

        return self.data[field_name]

    # --------------------------------------------------------------------------------------
    '''def __getattr__(self, field_name ):

        return self.data[field_name]'''

    # --------------------------------------------------------------------------------------
    def load(self, id):

        # self.id = id

        arg = 'article/' + str(id)

        try:
            # request = self.esapi().parse_request(command, command_args, var_args,'Article.load')

            responseText = self.esapi().send_request('get', arg, 'Article->load')

            r = pd.Series(responseText['data'][0])
            # print(r)
            self.data = r
            self.id = id
            self.tenant = r.tenant
            self.subject = r.subject
            return True

        except Exception as exc:

            self.esapi().setLastError(exc)
            raise exc


    def update(self):

        method = 'put'
        args = 'article/' + str(self.id)
        # str({'id': self.id, 'subject': self.subject, 'tenant': self.tenant})
        data = { "subject": self.subject , "tenant": self.tenant, "fieldValues": self.updated_fields}

        #print(data)

        try:
            # request = self.esapi().parse_request(command, command_args, var_args,'Article.update')

            # print(request)
            responseText = self.esapi().send_request(method, args, data, 'Article->update')

            if responseText == {}:
                return 'Record updated: ' + self.id
            else:
                return responseText  # ['result_params']  # True #'Successfully updated id: {}'.format(self.id)



        except Exception as exc:

            self.esapi().setLastError(exc)
            raise exc

##########################################################################################






def run_connect():

    api = EsApi('PRODUCTION')
    #api = hsdes_web.EsApi('PREPRODUCTION')
    return api

def run_get():

    try:
        api = EsApi('PRODUCTION')

        artcl = api.Article()
        artcl.load('18016910426')
        print(artcl.data)
        print('id: ', artcl.data.id, ' , ', 'title: ', artcl.data.title)

        print('id: ', artcl.get('id'))


        print(artcl.get('test_case_definition.test_steps'))


    except Exception:
        print(str(api.getLastError()))



def run_update(phoenix_id,automation_potential):

    try:
        api = EsApi('PRODUCTION')

        artcl = api.Article()
        artcl.load(phoenix_id)

        artcl.set('send_mail','false')

        artcl.set('server_platf.test_case_definition.automation_potential', automation_potential)

        result = artcl.update()
        print(result)


    except Exception:
        print(str(api.getLastError()))
