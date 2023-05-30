from multiprocessing import Process

class SeamLessProcess:
    """
        implementation of the process class can be using concurrent future or Multiprocessing

    """
    def __init__(self):
        self.process_data_file = "SeamlessDatabase.json"
        self.process_data = {}
        
    def set_process_data(self, process_obj):
        print("process obj", process_obj)
        #quit()
        p_id = str(process_obj).split(" ")[2].split("=")[1]
        p_name = str(process_obj).split(" ")[1].split("=")[1]

        self.process_data[str(p_id) + "_" + p_name] = process_obj
        print("process data ", self.process_data)
        return p_id, p_name

    def start_process(self, pid):
        """
        :return:
        """
        
        process_found = False
        
        for process_obj in self.process_data.values():
            if pid == process_obj.pid:
                process_obj.start()
                process_found = True
                break

        if process_found:
            return {
                "process_id" : f"the process {process_obj.pid} started",
                "status": str(process_obj).split(" ")[-1].replace(">","")
            }
            
        return {
                "process_id" : f"the process {pid} not started",
                "status": "Couldn't run"
            }


    def kill_process_by_id(self, process_id):
        print("Entered the function to kill th eproccess")
        process_id.terminate()

        # for process_obj in self.process_data.values():
        #     if process_id == process_obj.pid:
        #         print("process id inside the kill function", process_id)
        #         print("process id inside the kill function", process_obj.pid)
        #         process_obj.kill()
        #         process_found = True
        #         return True
        #         break
            
        return {
            "status":"True/False",
            "message":" Give a message wether able to stop the process or not"
        }

    def check_process_status_by_id(self, process_id:str):
        return {
            "status":"True/False",
            "message":"any additional message you want to return on the process status"
        }


def sample_fun():
    print("simple")

if __name__ == '__main__': 
    obj = SeamLessProcess()
    
    p = Process(target=sample_fun)
    obj.set_process_data(p)
    print(obj.process_data)
    print(obj.start_process(p.pid))
    
    