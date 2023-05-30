#!/usr/bin/env python

import os
import platform
import time
from multiprocessing import Process
import logging

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib import log_utils
from dtaf_core.lib.dtaf_constants import Framework
from src.seamless.tools.JsonParserValidator.json_parser import JsonParser
from src.seamless.lib.seamless_common import SeamlessBaseTest
from src.seamless.lib.pm_common import SocwatchCommon
from src.seamless.tools.CrossProductOrchestrator.App.Utils.Process import SeamLessProcess


class RunCrosess:

    def __init__(self, json_file):

        self.json_obj = JsonParser(json_file)
        # super().__init__(json_file)

    def parse_input(self):
        """
        Start parsing the input json which is having the schema defined

        :param input_path:
        :return:
        """
        json_data = self.json_obj.loadJson()
        return json_data

    def execute_current_block(self, current_block: list):
        block_values = []
        for each_block in current_block:
            for key, val in each_block.items():
                if key == "executable_path":
                    block_values.append(val)
                if key == "class_name":
                    block_values.append(val)
                if key == "entry_method_name":
                    block_values.append(val)
        print("----------------", block_values)
        return block_values


    def execute_pre_block(self, json_block: list):
        pass

    def execute_post_block(self, json_block: list):
        pass


    def get_current_block(self, json_data, step_id=None):
        """
        parse the block id json data based on the step_id only
        if the step_id is not given, program doesn't know which bock to pick.
        """
        check_current_executable = None
        """
        once the step_id is given match the step_id and get the index and use it.
        if the step id is not given then raise an exception
        """
        if not step_id:
            raise RuntimeError("Step id is not available")
        #if item in json_data:
            # print("item", item["step_id"])
            # if step_id == item["step_id"]:
        check_current_executable = json_data["executable"]["current_executable"]
        print("=========", check_current_executable)
        return check_current_executable


    def get_step_id(self, json_data):
        """

        """
        step_id_list = []
        print("Getting the step id")
        for item in json_data:
            step_id_list.append(item["step_id"])
        #print("block step id ", step_id_list)
        return step_id_list



class seamless_abstract(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(seamless_abstract, self).__init__(test_log, arguments, cfg_opts)
        self.warm_reset = False

    def check_capsule_pre_conditions(self):
        pass

    def get_current_version(self, echo_version=True):
        fw_inv = self._bmc_redfish.get_firmwareinventory()
        for each in fw_inv:
            if each['Id'] == 'bmc_active':
                version = each['Version']
                print(each)
        return version

    def examine_post_update_conditions(self):
        pass

    def evaluate_workload_output(self, output):
        pass

    def block_until_complete(self, pre_version):
        pass


def create_object(class_name, method_name, package):
    print("Class name --> ", class_name, "Method name -->", method_name)
    exec_os = platform.system()

    try:
        cfg_file_default = Framework.CFG_FILE_PATH[exec_os]
    except KeyError:
        print("Error - execution OS " + str(exec_os) + " not supported!")
        raise RuntimeError("Error - execution OS " + str(exec_os) + " not supported!")
    arguments = BaseTestCase.parse_arguments(None, cfg_file_default)

    # Add user-specified arguments
    # BaseTestCase.add_arguments()

    print(arguments.cfg_file)
    config_parameters = BaseTestCase.parse_config_file(arguments)

    test_log = log_utils.create_logger(class_name, False, config_parameters)

    sut_os_cfg = config_parameters.find(SutOsProvider.DEFAULT_CONFIG_PATH)
    os_obj = ProviderFactory.create(sut_os_cfg, test_log)

    run_function(class_name, method_name, test_log, arguments, os_obj, config_parameters, package)


def run_function(class_name1, method_name, test_log, arguments, os_obj, config_parameters, path):
    """

    """
    from importlib import import_module
    print("path ", path)
    import_module(path)
    mod = import_module(path, class_name1)
    class_name = getattr(mod, class_name1)
    ob = class_name(test_log, arguments, config_parameters)
    ob.prepare()
    eval(f"ob.{method_name}()")
    quit()


if __name__ == "__main__":
    logging.basicConfig(filename='C:\example.log', encoding='utf-8', level=logging.DEBUG)

    #process class object
    process_obj = SeamLessProcess()

    JsonFile = os.path.join(os.getcwd(), "Seamless_new.json")
    obj = RunCrosess(JsonFile)
    json_data = obj.parse_input()

    process_info = {
        "step_id": "",
        "process_object": "" }
    process_list = []

    def run_in_sequence(step_object):
        pass

    def run_until(run_until_obj, pid, p_name, process_start_time):
        if run_until_obj.get("step_ids"):
            print("The step id", run_until_obj.get("step_ids"))
            status = process_obj.check_process_status_by_id(p_name)
            if status:
                return True
            else:
                return True
        # elif run_until_obj.get("min_time_out"):
        #     time.sleep(run_until_obj.get("min_time_out"))
        #     spawn_process(step_object)
        #     return False
        elif run_until_obj.get("time_out"):
            print("Run until max timeout block", run_until_obj.get("time_out"))
            time.sleep(10)
            current_process_time = time.time()
            current_run_time = current_process_time - process_start_time
            if current_run_time > 20:
                if process_obj.kill_process_by_id(pid):
                    return True
                else:
                    print("Not able to kill the process")

        # elif run_until_obj.get("end_of_life"):
        #
        #     process_obj.kill_process_by_id()
        #     return False


    def get_runtil_block(json_data, step_id):
        check_current_rununtil = None
        for item in json_data:
            if step_id == item["step_id"]:
                check_current_rununtil = item["run_until"]
        return check_current_rununtil

    def spawn_process(step_object):
        # create process
        current_block_data = obj.get_current_block(step_object, step_object['step_id'])
        block_values = obj.execute_current_block(current_block_data)
        path = block_values[0]
        classname = block_values[1]
        fun1_name = block_values[2]
        #runtil_block = get_runtil_block(json_data, step_object['step_id'])

        pro_run_obj = Process(target=create_object, args=(classname, fun1_name, path))
        pro_run_obj.start()
        pid, p_name = process_obj.set_process_data(pro_run_obj)
        process_start_time = time.time()
        logging.info("process start time  %s ", process_start_time)
        logging.info("pid==%s and pname===%s", pid, p_name)
        return pro_run_obj, step_object['step_id']

        # while (1):
        #     if run_until(runtil_block, pro_run_obj, p_name, process_start_time):
        #         print("continue")
        #     else:
        #         print("timing is not reached")
        #     return True

    for step_object in json_data:
        print("===============================================")
        if step_object.get("execute_in_background"):
            print("step obj", step_object)
            pro_obj, id = spawn_process(step_object)
            process_info["step_id"] = id
            process_info["process_object"] = pro_obj
            print("process info", process_info)
            process_list.append(process_info)
        else:
            run_in_sequence(step_object)
            print("entered else")
    print("THe proceess list", process_list)
    # if not run until:
    #     start the process:
    #
    # else:
    #     continue

