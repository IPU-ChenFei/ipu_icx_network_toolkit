"""
Copyright (c) 2022, Intel Corporation. All rights reserved.
Intention is to use HSDES query and platform config to generate, trigger and
update results back to HSDES using CommandCenter and HSDES rest APIs

Title          : highspeeddatabaseinfra.py
Author(s)      : Mandar Chandrakant Thorat; Santosh Deshpande

Documentation:
HSDES-API Link         : https://hsdes.intel.com/rest/doc/

"""

import traceback
import requests
from requests_kerberos import HTTPKerberosAuth

headers = {"Content-type": "application/json"}
proxy = {"http": "", "https": ""}


def hsdesRecordGetApi(recordId, fields=None):
    """
    Execute get request using HSDES API

    :param url: url for post request
    """
    url = "https://hsdes-api.intel.com/rest/article/%s" % recordId
    url = url + "?fields={0}".format(fields)
    try:
        response = requests.get(
            url, verify=False, auth=HTTPKerberosAuth(), headers=headers
        )
    except requests.ConnectionError as e:
        print(
            "OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n"
        )
        print(str(e))
    except requests.Timeout as e:
        print("OOPS!! Timeout Error")
        print(str(e))
    except requests.RequestException as e:
        print("OOPS!! General Error")
        print(str(e))
    except KeyboardInterrupt:
        print("Someone closed the program")
    except Exception as ex:
        print("Failed to execute get request : {}".format(ex))
        print(traceback.format_exc())
        raise Exception()

    return response
