#!/usr/bin/env python
import json
import os
import platform
import time
from datetime import datetime
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

RunUntilTracker = []
RUnUntilMapping = []
GlobalRunDepex = []
RunUntilTimer = []
RunUntilEOL = []
MaxTimeOut = []
os_obj = None

def TempFun(executable_path, class_name, method_name):
    obj = CrossProduct()
    object = obj.preprocessing(executable_path, class_name)
    object.prepare()
    eval(f"object.{method_name}()")
    # print("RasScript")
    # time.sleep(3)

def GetTimMinutes(data):
    temp = ""

    for each in data:
        if each.isdigit():
            temp += each

    if temp == "":
        print("Something Went Wrong, No Digit Found")
        return 0

    return int(temp)


class CrossProduct():

    def __init__(self):
        self.exec_os = platform.system()
        self.userjsonfile = os.path.join(os.getcwd(), "Seamless_new.json")
        self.userjsondata = None
        self.cfg_file_default = None
        self.arguments = None
        self.config_parameters = None
        self.sut_os_cfg = None
        self.loop_count = 0
        self.temp_array = []
        self.process_obj = {}

    def validator(self):
        return True

    def preprocessing(self, executable_path, class_name):
        print("#" * 15 + "PreProcessing" + "#" * 15)
        try:
            self.cfg_file_default = Framework.CFG_FILE_PATH[self.exec_os]
        except KeyError:
            print("Error - execution OS " + str(self.exec_os) + " not supported!")
            raise RuntimeError("Error - execution OS " + str(self.exec_os) + " not supported!")

        self.arguments = BaseTestCase.parse_arguments(None, self.cfg_file_default)
        self.config_parameters = BaseTestCase.parse_config_file(self.arguments)
        self.sut_os_cfg = self.config_parameters.find(SutOsProvider.DEFAULT_CONFIG_PATH)

        # file = open(self.userjsonfile, 'r')
        # self.userjsondata = json.load(file)

        test_log = log_utils.create_logger(class_name, False, self.config_parameters)

        import_module(executable_path)
        mod = import_module(executable_path, class_name)
        current_class_name = getattr(mod, class_name)
        os_obj = ProviderFactory.create(self.sut_os_cfg, test_log)

        ob = current_class_name(test_log, os_obj, self.config_parameters)
        return ob

    def preexecution(self):
        print("Pre Executable Called")

    def executorhelper(self, test_log, arguments, config_parameters, current_class_name, entry_method_name):
        print("******************************")
        ob = current_class_name(test_log, arguments, config_parameters)
        ob.prepare()
        eval(f"ob.{entry_method_name}()")

    def executorhelper1(self, executable_path, class_name, method_name):

        N = 2
        #pro_obj = SeamLessProcess()
        print(f"\nexecutorhelper1 Called\n")
        global RUnUntilMapping, RunUntilTracker
        print("CLASS_NAME : ", class_name)

        # to verification only Start
        """if class_name == "SEAM_BMC_0004_send_bios_update_capsule":
            for i in range(20):
                print("SEAM_BMC_0004_send_bios_update_capsule")
                time.sleep(1)
        else:
            for i in range(2):
                print("RasScript")
                time.sleep(1)"""

        # to verification only End
        object = self.preprocessing(executable_path, class_name)
        object.prepare()
        #object.check_sut_alive(os_obj)
        eval(f"object.{method_name}()")

    def currentexeuctable(self, userjsondata):
        global RunUntilTracker, RUnUntilMapping, GlobalRunDepex, RunUntilTimer, RunUntilEOL, MaxTimeOut
        run_until = None
        print("Current Executable Called")
        for step_object in userjsondata:
            print("1111111111111111111111111111111111111111111")
            if step_object.get("execute_in_background"):
                self.loop_count = int(step_object.get("run_until").get("loop"))
                print("222222222222222222222222222222222222222222222222222")
                while self.loop_count != 0:
                    print("33333333333333333333333333333333333333333333333")
                    current_executable = step_object.get("executable").get("current_executable")
                    current_executable_count = len(current_executable)
                    for each in range(current_executable_count):
                        executable_path = current_executable[each].get("executable_path")
                        print("-------------------executeable path ", executable_path)
                        class_name = current_executable[each].get("class_name")
                        entry_method_name = current_executable[each].get("entry_method_name")

                        if len(step_object.get("run_until").get("step_id")) > 0:
                            print(step_object.get("run_until").get("step_id"))
                            GlobalRunDepex = [executable_path, class_name, entry_method_name]

                        pro_run_obj = Process(target=self.executorhelper1,
                                              args=(executable_path, class_name, entry_method_name))
                        TempData = {step_object.get("step_id"): {
                            current_executable[each].get("current_executable_id"): pro_run_obj}}
                        RunUntilTracker.append(TempData)
                        RUnUntilMapping.append(
                            {step_object.get("step_id"): step_object.get("run_until").get("step_id")})
                        #print("max timeout 00000000000000000000", step_object.get("max_time_out"))
                        MaxTimeOut.append({step_object.get("step_id") : step_object.get("max_time_out")})
                        if step_object.get("run_until").get("end_of_life"):
                            TempData = {step_object.get("step_id"): {
                                current_executable[each].get("current_executable_id"): pro_run_obj}}
                            RunUntilEOL.append(TempData)

                        time.sleep(2)
                        print("------------------------------")
                        #if len(step_object.get("run_until").get("step_id")) > 0:
                        current_time = datetime.now()
                        min_time = step_object.get("run_until").get("min_time_out")
                        time_out = step_object.get("max_time_out")
                        loop = step_object.get("run_until").get("loop")
                        end_of_life = step_object.get("run_until").get("end_of_life")
                        val = [current_time, min_time, loop, time_out, end_of_life]
                        print("val", val)
                        temp_timer = {step_object.get("run_until").get("step_id"): val}
                        RunUntilTimer.append(temp_timer)
                        print("888888888888", RunUntilTimer)
                        run_until = True
                        # else:
                        #     current_time = datetime.now()
                        #     min_time = step_object.get("run_until").get("min_time_out")
                        #     time_out = step_object.get("max_time_out")
                        #     end_of_life = step_object.get("run_until").get("end_of_life")
                        #     val = [current_time, min_time, time_out, end_of_life]
                        #     temp_timer = {step_object.get("run_until").get("step_id")[0]: val}
                        #     RunUntilTimer.append(temp_timer)
                        #     print("888888888888", RunUntilTimer)

                        pro_run_obj.start()

                    self.loop_count -= 1
            # else:
            #     # Run one by one
            #     #if step_object.get("max_time_out") != "None":
            #
            #     print("the max time out ", step_object.get("max_time_out"))
            #     current_executable = step_object.get("executable").get("current_executable")
            #     current_executable_count = len(current_executable)
            #     for each in range(current_executable_count):
            #         executable_path = current_executable[each].get("executable_path")
            #         print("executeable path ", executable_path)
            #         class_name = current_executable[each].get("class_name")
            #         print("classh name step id", class_name)
            #         entry_method_name = current_executable[each].get("entry_method_name")
            #         print("entery ethon noanme", entry_method_name)
            #         self.executorhelper1(executable_path, class_name, entry_method_name)



        #self.max_timeout()
        #if run_until:
        self.rununtil()

    # def max_timeout(self):
    #     if MaxTimeOut != None:
    #         for item in MaxTimeOut:
    #             for step_id, timeout in item.items():
    #                 for row in RunUntilTracker:
    #                     if step_id in row and timeout != "None":
    #                         max_min_timout = GetTimMinutes(timeout)
    #                         for k, v in row.items():
    #                             print("k, v", k, v)
    #                             for k1, v1 in v.items():
    #                                 process_max = v1
    #                                 if process_max.is_alive():
    #                                     time.sleep(max_min_timout)
    #                                     process_max.terminate()
    #                                 else:
    #                                     print("process is not alive")

    def postexecutable(self):
        pass

    def rununtil(self):
        print("rununtil called\n")
        global RunUntilTracker, RUnUntilMapping, GlobalRunDepex, RunUntilTimer, RunUntilEOL
        Status = True

        id_rununtil = None
        process_rununtil = None
        rerun_step_id = None
        rerun_process = None
        rununtil_timer_start_time = None

        print("mapping", RUnUntilMapping)
        for each in RUnUntilMapping:
            for k, v in each.items():
                if len(v) > 0:
                    id_rununtil = v[0]
                    print("id rununtil", id_rununtil)
                    rerun_step_id = k
                    print("rerun stpe id ", rerun_step_id)

        print("RunUntilTracker L ", RunUntilTracker)
        for each in RunUntilTracker:
            for k, v in each.items():
                for k1, v1 in v.items():
                    print("Key : ", k1)
                    if k1 == id_rununtil:
                        process_rununtil = v1

                if k == rerun_step_id:
                    for k2, v2 in v.items():
                        rerun_process = v2

        print("+++++++++++++", RunUntilTimer)

        for timerkey, timer_val in RunUntilTimer[0].items():
            rununtil_timer_start_time = timer_val[0]
            rununtil_min_timout = GetTimMinutes(timer_val[1])
            rununtil_timout = GetTimMinutes(timer_val[2])
            end_of_life = timer_val[3]

        if process_rununtil != None:
            counter = 0
            while Status:
                current_time = datetime.now()
                diff = ((current_time - rununtil_timer_start_time).total_seconds()) / 60
                Status = process_rununtil.is_alive()

                # Min Timeout condition, at-least it should run for min time
                if not Status:
                    if diff <= rununtil_min_timout:
                        Status = True

                if Status:
                    if rerun_process != None:
                        if not rerun_process.is_alive():

                            # if it reaches to max timeout return
                            if rununtil_timout <= diff:
                                print("MAX TIMEOUT REACHED")
                                return

                            # if end_of_life:
                            #     print("EOF*************")

                            if end_of_life: #or diff < rununtil_min_timout or diff <= rununtil_timout:
                                print("counter = ", counter, "rerun_process : ", rerun_process)
                                print(f"diff = {diff} min = {rununtil_min_timout} max = {rununtil_timout}")
                                pro_run_obj = Process(target=TempFun,
                                                      args=(GlobalRunDepex[0], GlobalRunDepex[1], GlobalRunDepex[2]))
                                pro_run_obj.start()
                                rerun_process = pro_run_obj
                                time.sleep(1)
                                counter += 1



if __name__ == "__main__":
    obj = CrossProduct()

    if not obj.validator():
        print("Schema Validator Failed")
        quit()
    userjsonfile = os.path.join(os.getcwd(), "Seamless_new.json")
    print ("user jason ", userjsonfile)
    file = open(userjsonfile, 'r')
    userjsondata = json.load(file)

    # obj.preprocessing()
    # obj.preexecution()
    obj.currentexeuctable(userjsondata)

