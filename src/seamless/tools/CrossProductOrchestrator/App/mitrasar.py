import json


class CSP:
    def __init__(self, JSON_FILE_NAME):
        self.input_file = JSON_FILE_NAME
        pass


    def execute(self):
        csp_definition:dict = self.get_csp_definition()
        for step_object in csp_definition:
            if self.__verify_execute_bg(step_object):
                #logic to start the  step process in parallel
                start_process = StartProcess(step_object)
                start_process.start()
            else:
                #logic to start process in sequesce


    def __verify_execute_bg(self, step_object:dict):
        if step_object.get("execute_in_bg"):
            return True
        return False



    def get_csp_definition(self)->dict:
        with open(self.input_file, "r") as fp:
            return json.loads(fp.read())
