#!/usr/bin/env python
#################################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################
# ###############################################################################
# Install six, scp and requests python packages on the python interpreter environment
#################################################################################
import sys
import time

from dtaf_core.lib.dtaf_constants import ProductFamilies
from src.lib import content_exceptions

class Telemetry():
    """
    This class implements functions to collect the Telemetry
    """

    def __init__(self, cpu, log):
        sys.path.append("c:\\pythonsv")
        self._log = log
        try:
            if cpu == ProductFamilies.SPR:
                from sapphirerapids.telemetry.release.gjallarhorn.collector import telemetry_collector as tc
                self.tc = tc
            else:
                self._log.error("Configured CPU family is not supported by telemetry %s", cpu)
                raise content_exceptions
        except ImportError as err:
            self._log.info("{} Telemetry collector module is not imported, Telemetry data won't be captured\n{}".format(cpu, err))
        except content_exceptions:
            raise content_exceptions.TestFail("Configured CPU family is not supported by Telemetry URAM collector")
        except Exception as err:
            self._log.info(" {} Telemetry data won't be captured due to \n{}".format(cpu, err))

    def start_telemetry(self, name="DTAF_Automation", owner="DTAF", tag="21WW28"):
        """
        This method is used to start the telemetry collection
        :param name: Test contenet name
        :param owner: owner of the test content
        :param tag: TC execution WW
        :return None
        """
        try:
            self.tc.main(test_name=name, test_owner=owner, test_tag=tag)
            time.sleep(0.5)
        except Exception as err:
            self._log.info("Telemetry URAM collector is not started\n{}".format(err))

    def stop_telemetry(self):
        """
        This Method is to stop the telemetry collection
        :return: None
        """
        try:
            self.tc.stop_all_collectors()
        except Exception as err:
            self._log.info("Telemetry URAM collector is not stopped\n{}".format(err))
