#!/usr/bin/env python

import os
import logging
from multiprocessing import Process

logging.basicConfig(level=logging.INFO)


class ProcessCreate:
    """
        implementation of the process class can be using concurrent future or Multiprocessing

    """

    def __init__(self):
        self.ProcessData = {}

    def print(self):
        print("ID of process running print: {}".format(os.getpid()))
        print("Creating the process for this function")

    def fun1(self):
        print("ID of process running fun1: {}".format(os.getpid()))
        print("function 1 name")

    def set_process_data(self, process):
        p_id = process.pid
        print(process)

    def start_process(self):
        """
        TODO: Implement the logic of starting a process and returning the process status
        :return:
        """
        p = Process(target=self.print, args=())
        print(Process(target=))
        p.start()
        print(p)
        self.set_process_data(p)
        quit()
        self.ProcessData[p.pid] = p
        DICT = { "OBJ": p }
        print("dictionay obj",DICT["OBJ"])
        DICT["OBJ"].start()
        print("id alive of obj", DICT["OBJ"].is_alive())
        print("process id for p1 ", p.pid)
        p.join()
        print("p joinin111obj", p)
        p.start()

        # p1 = Process(target=self.fun1, args=())
        # DICT1 = {"OBJ": p1}
        # print("dictionay obj fun1", DICT1["OBJ"])
        # DICT["OBJ"].start()
        # print("id alive of obj fun1", DICT1["OBJ"].is_alive())
        # print("process id for fun1 ", p1.pid)
        # # quit()
        # # print("print the p object", p)
        # # p.start()
        # # print("p. start ",p)
        # DICT["OBJ"].join()
        # print("p joinin", p1)


        return
        {
            "process_id":"the process id started",
            "status":"Running/Couldnt run"
        }

    def kill_process_by_id(self, process_id: str):


        return {
            "status": "True/False",
            "message": " Give a message wether able to stop the process or not"
        }

    def check_process_status_by_id(self, process_id: str):




        return {
            "status": "True/False",
            "message": "any additional message you want to return on the process status"
        }


obj = ProcessCreate()
obj.start_process()
