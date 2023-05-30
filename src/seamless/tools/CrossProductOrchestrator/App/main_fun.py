#!/usr/bin/env python

import os
import platform
import time
from multiprocessing import Process
import logging
from importlib import import_module

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib import log_utils
from dtaf_core.lib.dtaf_constants import Framework
from src.seamless.tools.JsonParserValidator.json_parser import JsonParser
from src.seamless.tools.CrossProductOrchestrator.App.RunCrosses import RunCrosess
from src.seamless.lib.seamless_common import SeamlessBaseTest
from src.seamless.tools.CrossProductOrchestrator.App.Utils.Process import SeamLessProcess

def preprocessing(class_name, method_name, path):
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

    import_module(path)
    mod = import_module(path, class_name)
    class_name = getattr(mod, class_name)

    ob = class_name(test_log, arguments, config_parameters)
    ob.prepare()
    eval(f"ob.{method_name}()")



def current_executable(json_data):

    for step_object in json_data:
        print("===============================================")
        if step_object.get("execute_in_background"):
            print("step obj", step_object)
            current_block_data = obj.get_current_block(step_object, step_object['step_id'])
            block_values = obj.execute_current_block(current_block_data)
            path = block_values[0]
            class_name = block_values[1]
            fun1_name = block_values[2]
            pro_run_obj = Process(target=preprocessing, args=(class_name, fun1_name, path))
            # pro_run_obj.start()
            pid, p_name = pro_run_obj.set_process_data(pro_run_obj)
            process_start_time = time.time()
            print("process start time  ", process_start_time)
            print("pid== and pname===", pid, p_name)
            return pro_run_obj, step_object['step_id']


if __name__ == "__main__":

    JsonFile = os.path.join(os.getcwd(), "Seamless_new.json")
    obj = RunCrosess(JsonFile)
    SchemaObj = JsonParser(JsonFile)
    # ret = SchemaObj.SchemaValidator()
    # if not ret:
    #     exit()
    print("new code snippet-------------------------")
    json_data = SchemaObj.loadJson()
    #preprocessing()
    loop_count = 1
    while loop_count != 0: #get the value from the json file    while loop_count != 0:
        #pre_executable()
        #start_time_count = current_time()   # global_val
        pro_obj, step_id = current_executable(json_data)
        print("========================================")
        print("pro_obj-----------------", pro_obj)
        print("step id---------------------", step_id)
        # while True:
        #     BooleanVal, StepId = run_until()     #under run_until check for the current_time and compare with start_time_count            if not BooleanVal:
        #     if not BooleanVal:
        #         break
        #     if BooleanVal:
        #         custome_run_function(step_id[])   # this is similar to current_executable
        # post_executable()
        loop_count =- 1