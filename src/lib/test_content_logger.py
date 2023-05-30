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


class TestContentLogger(object):
    """
        Utility class to add step separators in the Test logs.
    """

    def __init__(self, log_obj, tc_id, step_data_dict):
        """
        :param log_obj: log object
        :param tc_id: test case id
        :param step_data_dict: test content data dictionary
        """
        self._log = log_obj
        self._tc_id = tc_id
        self._step_data_dict = step_data_dict

    def start_step_logger(self, step_no):
        """
        This function is used to start the Step separators in the Test Logs and will log the Step No and Step details
        along with the Test Case no
        :param step_no: Step no of the respective Test Case
        :return: None
        :raise: RuntimeError
        """
        try:
            self._log.info("Start of TC:{}-Step{}".format(self._tc_id, step_no))
            self._log.info("TC:{}-Step{}: Details: {}".format(self._tc_id, step_no,
                                                              self._step_data_dict[step_no]['step_details']))
        except Exception as ex:
            ex_msg = "Exception occurred while running 'start_step_logger' function"
            self._log.error(ex_msg)
            raise RuntimeError(ex)

    def end_step_logger(self, step_no, return_val):
        """
        This function is used to start the Step separators in the Test Logs and will log the Step No and Step details
        along with the Test Case no
        :param step_no: Step no of the respective Test Case
        :param return_val: return status of the step method
        :return: None
        :raise: RuntimeError
        """
        try:
            self._log.info("TC:{}-Step{}: Expected Results: {}".format(self._tc_id, step_no,
                                                                       self._step_data_dict[step_no]
                                                                       ['expected_results']))
            if not return_val:
                self._log.error("TC:{}-Step{}: FAILED".format(self._tc_id, step_no))
            else:
                self._log.info("TC:{}-Step{}: SUCCEEDED".format(self._tc_id, step_no))
            self._log.info("End of TC:{}-Step{}".format(self._tc_id, step_no))
        except Exception as ex:
            ex_msg = "Exception occurred while running 'end_step_logger' function"
            self._log.error(ex_msg)
            raise RuntimeError(ex)
