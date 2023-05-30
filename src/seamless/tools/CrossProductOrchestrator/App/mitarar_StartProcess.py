import datetime
import multiprocessing

class StartProcess():
    def __init__(self,step_object):
        self.step_object = step_object
        self.run_until = RunUntil(step_object.get("run_until"))

    def start_process(self):
        start_time  = datetime.datetime.now()
        multiprocessing.process(keep_running_process, params= run_until, step_object)









dictionary_ = {
    "json_id_1":{
        "process_id": None,
        "object": None,
        "param": step_object,
        "Start_time": datetime.now(),
        "force_terminate": False,
        "loop_counter": 0
    }


}