"""
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
"""

import unittest
import urllib3
import highspeeddatabaseinfra as hsd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# class MyTestCase(unittest.TestCase):
#     def test_something(self):
#         resp = hsd.hsdesRecordGetApi("16016532543", "id,title")
#         self.assertEqual(200, resp.status_code)  # add assertion here
#         self.assertEqual(
#             resp.json()["data"][0]["title"], "Testrecord1"
#         )  # add assertion here
#         self.assertNotEqual(resp.json()["data"][0]["id"], None)  # add assertion here

def test_answer():
    resp = hsd.hsdesRecordGetApi("16016532543", "id,title")
    assert 200 == resp.status_code  # add assertion here
    assert resp.json()["data"][0]["title"] == "Testrecord1"
    assert resp.json()["data"][0]["id"] == "16016532543"  # add assertion here
    assert len(resp.json()["data"][0]) == 2


# if __name__ == "__main__":
#     unittest.main()
