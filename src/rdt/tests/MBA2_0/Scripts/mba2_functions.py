import subprocess
import time
import re
import logging
import sys

RDT_MBA2_SCRIPT_VERSION="V7.4"
MBM_UPPER_LIMITATION = 100000
class sys_info:
    def max_thread(self):
        command = "lscpu"
        threadnum = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        (stdout, stderr) = threadnum.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\n")
        for line in lines:
            if "CPU(s)" in line and "NUMA" not in line and "list" not in line:
                match = re.search(r"(\d+)", line)
                thread = match.group(0)
                maxthread = int(thread)
        return maxthread
    
    def thread_per_core(self):
        command = "lscpu"
        tpcnum = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        (stdout, stderr) = tpcnum.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\n")
        for line in lines:
            if "Thread(s) per core:" in line :
                match = re.search(r"(\d+)", line)
                tpc = match.group(0)
                ht = int(tpc)
        return ht

    def max_socket(self):
        command = "lscpu"
        socketnum = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        (stdout, stderr) = socketnum.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\n")
        for line in lines:
            if "Socket(s):" in line :
                match = re.search(r"(\d+)", line)
                socket = match.group(0)
                maxsocket = int(socket)
        return maxsocket

    def max_core(self):
        socket = 0
        corespersocket = 0
        command = "lscpu"
        corenum = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        (stdout, stderr) = corenum.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\n")
        for line in lines:
            if "Core(s) per socket:" in line:
                match = re.search(r"(\d+)", line)
                corespersocket = match.group(0)
            if "Socket(s):" in line:
                match = re.search(r"(\d+)", line)
                socket = match.group(0)
            maxcore = int(socket)*int(corespersocket)
        return maxcore


    def max_cos(self):
        command = "pqos -d"
        cosnum = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        (stdout, stderr) = cosnum.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\n")
        for line in lines:
            if "Num COS:" in line:
                match = re.search(r"(\d+)", line)
                cos = match.group(0)
                maxcos = int(cos)
        return maxcos

    def max_rmid(self):
        command = "pqos -D"
        rmidnum = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        (stdout, stderr) = rmidnum.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\n")
        for line in lines:
            if "rmid" in line:
                rmid = line.split()[-1]
        return rmid
    
    def msr_version(self):
        command = "wrmsr -V"
        check_msr_command = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,shell=True)
        (stdout, stderr) = check_msr_command.communicate()
        stroutput = str(stderr, encoding="utf-8")
        #lines = stroutput.split("\n")
        match = re.search(r"[0-9.]+", stroutput)
        strversion=match.group(0)
        version = float(strversion)
        return strversion
    
    def L3_cache_size(self):
        command = "lscpu"
        check_l3_command = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,shell=True)
        (stdout, stderr) = check_l3_command.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\n")
        for line in lines:
            if "L3 cache:" in line:
                match = re.findall(r"(\d+)", line)[1]
                l3_size_M = int(int(match)/1000)
                l3_size_K = match
        return l3_size_M,l3_size_K
    
    def compare(self,a: str, b: str):
        lena = len(a.split('.'))
        lenb = len(b.split('.'))
        a2 = a + '.0' * (lenb-lena)
        b2 = b + '.0' * (lena-lenb)
        for i in range(max(lena, lenb)):
            if int(a2.split('.')[i]) > int(b2.split('.')[i]):
                return a
            elif int(a2.split('.')[i]) < int(b2.split('.')[i]):
                return b
            else:
                if i == max(lena, lenb)-1:
                    return a
    
    def script_version(self):
        version = RDT_MBA2_SCRIPT_VERSION
        return version
    
    def cpu_model(self):
        command = "lscpu"
        check_model_command = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,shell=True)
        (stdout, stderr) = check_model_command.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\n")
        for line in lines:
            if "Model" in line:
                print(line)
            if "Stepping" in line:
                print(line)
        pass
    
    def bios_version(self):
        command = "dmidecode -s bios-version"
        check_bios_command = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,shell=True)
        (stdout, stderr) = check_bios_command.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\n")
        return lines[0]
    
    def ucode_version(self):
        command = "grep microcode /proc/cpuinfo | uniq"
        check_ucode_command = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,shell=True)
        (stdout, stderr) = check_ucode_command.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\t")[1].split()[1]
        return lines
    
    def os_version(self):
        command = "cat /etc/redhat-release"
        check_os_command = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,shell=True)
        (stdout, stderr) = check_os_command.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\n")
        return lines[0]
        
    def kernel_version(self):
        command = "uname -r"
        check_kernel_command = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,shell=True)
        (stdout, stderr) = check_kernel_command.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\n")
        return lines[0]

    def numa_info(self):
        command = "lscpu"
        check_numa_command = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,shell=True)
        (stdout, stderr) = check_numa_command.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\n")
        for line in lines:
            if "NUMA" in line:
                print(line)
        pass

    def memory_size(self):
        command = "cat /proc/meminfo"
        check_numa_command = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,shell=True)
        (stdout, stderr) = check_numa_command.communicate()
        stroutput = str(stdout, encoding="utf-8")
        lines = stroutput.split("\n")
        for line in lines:
            if "MemTotal" in line:
                sp = line.split()
                mem = sp[1]+sp[2]
        return mem


    def show_sys_info(self):
        print("System Info: ")
        script = str(sys_info().script_version())
        print("RDT_MBA2.0 Script Version:%4s"%script)
        sys_info().cpu_model()
        bios = str(sys_info().bios_version())
        print("BIOS version:        %30s"%bios)
        ucode = str(sys_info().ucode_version())
        print("ucode version:%17s"%ucode)
        os = str(sys_info().os_version())
        print("OS version:          %20s"%os)
        kernel = str(sys_info().kernel_version())
        print("Kernel version:      %20s"%kernel)
        core = str(sys_info().max_core())
        print("Max core:%14s"%core)
        thread = str(sys_info().max_thread())
        print("Max thread:%12s"%thread)
        socket = str(sys_info().max_socket())
        print("Max socket:%11s"%socket)
        sys_info().numa_info()
        memory = str(sys_info().memory_size())
        print("Total Memory Size:%14s"%memory)
        cos = str(sys_info().max_cos())
        print("Max COS:%15s"%cos)
        l3 = str(sys_info().L3_cache_size()[1])
        print("L3 cache size:%12s"%l3+"K")
        msr = str(sys_info().msr_version())
        print("msrtools version:%7s"%msr)
        msr_v = sys_info().msr_version()
        if msr_v == "1.3":
            pass
        else:
            later_version = sys_info().compare("1.3",msr_v)
            if later_version == "1.3":
                print("MSR tool version too low, please update to 1.3 or above")
                sys.exit(1)
        rmid = str(sys_info().max_rmid())
        print("Max RMID:%15s"%rmid)
        ht = str(sys_info().thread_per_core())
        #print("Thread(s) per core:%10s"%ht)
        time.sleep(2)


class stress_tools:
    def run_stress(self, core):
        command = "taskset -c "+str(core)+" stress -m 100"
        stress = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        return command


    def run_stream(self, core):
        command = "taskset -c "+str(core)+" /home/STREAM-master/stream"
        stream = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        return command

    def memtester(self, core, size):
        command = "taskset -c "+str(core)+" memtester "+size
        memtester = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        return command

    def mlc(self, core, traffic, method):
        command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -d0 -T -t10"
        mlc = memtester = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        return command

    def kill_tool(self):
        kill = "killall -9 stream && killall -9 stream.AVX512.NTW && killall -9 stream.AVX512.RFO && killall -9 membw && killall -9 pqos && killall -9 mlc_internal"
        stream = subprocess.Popen(kill.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
    def run_membw(self, core):
        command = "/home/intel-cmt-cat-master/tools/membw/membw -c "+str(core)+" -b 20000 --nt-write"
        stream = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        return command

class TESTMBA2():
    # log = logging.getLogger('MBA2.0-test')

    def __init__(self):
        self.pqos = "pqos"
        self.stress = "stress"
        self.stream = "stream"

    def run(self, command, quiet=False):
        child = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        (stdout, stderr) = child.communicate()

        if stdout is not None:
            stdout = stdout.decode("utf-8")
        if stderr is not None:
            stderr = stderr.decode("utf-8")

        # if not quiet:
        #     self.log.debug(command)
        # if not quiet and stdout:
        #     self.log.debug("===> stdout")
        #     self.log.debug(stdout)
        # if not quiet and stderr:
        #     self.log.debug("===> stderr")
        #     self.log.debug(stderr)

        return stdout, stderr

    def reset(self):
        command = "pqos -R"
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        pass

    def refresh(self):
        command = "pqos -r -t 1"
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        pass
        
    def case01_MBR(self, command, corenum, cos,mba):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 01: MBL=MBT"
        print(start)
        time.sleep(1)
        #stream = stress_tools().run_stream(corenum)
        #print("Step1: "+stream)
        stressCommand = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("Step1: "+command)
        time.sleep(1)
        clos = "pqos -a llc:" + str(cos) + "=" + str(corenum)
        print("Step2: " + clos)
        closCommand = subprocess.Popen(clos.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        mba_pct = 'pqos -e "mba:'+str(cos)+'='+str(mba)+'"'
        print("Step3: "+mba_pct)
        mbaCommand = subprocess.Popen(mba_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(5)
        mbm1 = "pqos -m all:"+str(corenum)+" -t 5"
        print("Step4: "+ mbm1)
        (stdout1,stderr1) = TESTMBA2().run(mbm1)
        lines1 = stdout1.split("\n")
        flag1 = 0
        for index1,line1 in enumerate(lines1):
                if 'TIME' in line1:
                    flag1 += 1
                if flag1 == 6:
                    if len(line1.split())!=0:
                        if line1.split()[0] == str(corenum):
                            mbl=float(line1.split()[-2])
                            mbr=float(line1.split()[-1])
        stress_tools().kill_tool()
        if int(mbl)>= MBM_UPPER_LIMITATION:
            print("MBM: ",mbl)
            print("Error: MBM exceed limit")
            sys.exit(1)
        print("Step5: Reset pqos")
        TESTMBA2().reset()
        TESTMBA2().refresh()
        time.sleep(3)
        reset = "pqos -R"
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("----------------------------------------------------------")
        return mbl, mbr


    def case02_MBA(self, command, corenum, cos, mba):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 02: MBA Throttling"
        print(start)
        time.sleep(1)
        #membw = stress_tools().run_membw(corenum)
        #print("Step1: "+membw)
        #stressCommand = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        #                               stderr=subprocess.PIPE,shell=True)
        print("Step1: "+command)
        time.sleep(1)
        clos = "pqos -a llc:" + str(cos) + "=" + str(corenum)
        print("Step2: " + clos)
        closCommand = subprocess.Popen(clos.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        time.sleep(1)
        mba_pct = 'pqos -e "mba:'+str(cos)+'='+str(mba)+'"' 
        print("Step3: "+mba_pct)
        mbaCommand = subprocess.Popen(mba_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(1)
        stressCommand = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(5)
        mbm1 = "pqos -m all:"+str(corenum)+" -t 10"
        print("Step4: "+ mbm1)
        (stdout1,stderr1) = TESTMBA2().run(mbm1)
        lines1 = stdout1.split("\n")
        flag1 = 0
        print(stdout1)
        for index1,line1 in enumerate(lines1):
                if 'TIME' in line1:
                    flag1 += 1
                if flag1 == 10:
                    if len(line1.split())!=0:
                        if line1.split()[0] == str(corenum):
                            mbm=float(line1.split()[-2])
                            print(mbm)
        time.sleep(1)
        stress_tools().kill_tool()
        killmlc = "killall -9 mlc_internal"
        killcommand = subprocess.Popen(killmlc, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)        
        if int(mbm)>= MBM_UPPER_LIMITATION:
            print("MBM: ",mbm)
            print("Error: MBM exceed limit")
            sys.exit(1)
        print("Step5: Reset pqos")
        time.sleep(3)
        reset = "pqos -R"
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("----------------------------------------------------------")
        return mbm
    
    def case03_mlcvsmbm(self, corenum, cos, traffic, pattern, socket):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 03: Check Mlc vs MBM accuracy"
        print(start)
        time.sleep(1)
        config = str(corenum)+" "+traffic+" "+pattern+" 1000000 dram "+str(socket)
        configCommand =  "echo "+ "\""+config+"\""+ " > config.txt"
        configFile = subprocess.Popen(configCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
        mlcCommand =" /home/mlc_v3.7/Linux/mlc_internal -oconfig.txt --loaded_latency -d0 -T -t20"
        mlc = subprocess.Popen(mlcCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
        print("Step1: "+mlcCommand)
        time.sleep(7)
        mbm1 = "pqos -m all:"+str(corenum)+" -t 5"
        print("Step2: "+ mbm1)
        (stdout1,stderr1) = TESTMBA2().run(mbm1)
        lines1 = stdout1.split("\n")
        flag1 = 0
        for index1,line1 in enumerate(lines1):
                if 'TIME' in line1:
                    flag1 += 1
                if flag1 == 6:
                    if len(line1.split())!=0:
                        if line1.split()[0] == str(corenum):
                            mbl=float(line1.split()[-2])
                            mbr=float(line1.split()[-1])
        thread = sys_info().max_thread()
        hyperthreading = sys_info().thread_per_core()
        global numa
        if hyperthreading == 2: 
            if corenum >= 0 and corenum <= (thread/4)-1:
                numa = 0
            elif corenum >= thread/2 and corenum <= (thread*0.75)-1:
                numa = 0
            else:
                numa = 1
        elif hyperthreading ==1:
            if corenum >= 0 and corenum <= (thread/2)-1:
                numa = 0
            else:
                numa = 1
        else:
            numa = 0
        if numa == socket:
            mbm = mbl
        else:
            mbm = mbr
        if int(mbm)>= MBM_UPPER_LIMITATION:
            print("MBM: ",mbm)
            print("Error: MBM exceed limit")
            sys.exit(1)
        stress_tools().kill_tool()
        time.sleep(6)
        print("Step3: Get mlc result")
        mlcCommand1 = " /home/mlc_v3.7/Linux/mlc_internal -oconfig.txt --loaded_latency -d0 -T -t10"
        (stdoutmlc,stderrmlc) = TESTMBA2().run(mlcCommand1)
        mlclines = stdoutmlc.split("\n")
        m = 0
        for mlcline in mlclines:
            m = m+1
            if "Delay" in mlcline:
                resulta = mlclines[m+1]
        mlcresult = resulta.split()[-1]
        time.sleep(1)
        stress_tools().kill_tool()
        print("Step4: Reset pqos")
        TESTMBA2().reset()
        TESTMBA2().refresh()
        time.sleep(3)
        reset = "pqos -R"
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("----------------------------------------------------------")
        return mlcresult, mbm



        

    def case04_unusedCOS(self, command1,command2,corenum1, corenum2, cos1, cos2, mba1, mba2):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 04: Throttling on unused COS"
        print(start)
        time.sleep(1)
        #stream1 = stress_tools().run_membw(corenum1)
        #stream2 = stress_tools().run_membw(corenum2)
        #print("Step1: "+stream1)
        #print("       "+stream2)
        stressCommand1 = subprocess.Popen(command1, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        stressCommand2 = subprocess.Popen(command2, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("Step1: "+command1)
        print("       "+command2)
        time.sleep(1)
        clos = "pqos -a llc:" + str(cos1) + "=" + str(corenum1)+";llc:"+str(cos2) + "=" + str(corenum2)
        print("Step2: " + clos)
        closCommand = subprocess.Popen(clos.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        time.sleep(1)
        mba1_pct = 'pqos -e "mba:'+str(cos1)+'='+str(mba1)+'"'
        mba2_pct = 'pqos -e "mba:'+str(cos2)+'='+str(mba2)+'"'
        print("Step3: "+mba1_pct)
        print("       "+mba2_pct)
        mba1Command = subprocess.Popen(mba1_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        mba2Command = subprocess.Popen(mba2_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(5)
        
        mbm1 = "pqos -m all:"+str(corenum1)+" -t 1"
        mbm2 = "pqos -m all:"+str(corenum2)+" -t 1"
        print("Step4: "+ mbm1)
        print("       "+ mbm2)
        (stdout1,stderr1) = TESTMBA2().run(mbm1)
        (stdout2,stderr2) = TESTMBA2().run(mbm2)
        lines1 = stdout1.split("\n")
        lines2 = stdout2.split("\n")
        flag1 = 0
        flag2 = 0
        for index1,line1 in enumerate(lines1):
                if 'TIME' in line1:
                    flag1 += 1
                if flag1 == 2:
                    if len(line1.split())!=0:
                        if line1.split()[0] == str(corenum1):
                            mbl1=float(line1.split()[-2])
                            print(mbl1)
                            #if line1.split()[0]==str(core2):
                                #mbl = float(line1.split()[4])
                                #print(mbl)
                                #mbr=float(line.split()[5])
        for index2,line2 in enumerate(lines2):
                    if 'TIME' in line2:
                        flag2 += 1
                    if flag2 == 2:
                        if len(line2.split())!=0:
                            if line2.split()[0] == str(corenum2):
                                mbl2=float(line2.split()[-2])
                                print(mbl2)
        time.sleep(1)
        stress_tools().kill_tool()
        if int(mbl1)>= MBM_UPPER_LIMITATION:
            print("MBM: ",mbl1)
            print("Error: MBM exceed limit")
            sys.exit(1)
        print("Step5: Reset pqos")
        TESTMBA2().reset()
        TESTMBA2().refresh()
        time.sleep(3)
        reset = "pqos -R"
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("----------------------------------------------------------")
        return mbl1,mbl2



    def case05_unusedCOS(self, command1, command2, corenum1, corenum2, cos1, cos2, mba1, mba2):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 05: Throttling on unused COS"
        print(start)
        time.sleep(1)
        #stream1 = stress_tools().run_membw(corenum1)
        #stream2 = stress_tools().run_membw(corenum2)
        #print("Step1: "+stream1)
        #print("       "+stream2)
        stressCommand1 = subprocess.Popen(command1, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        stressCommand2 = subprocess.Popen(command2, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("Step1: "+command1)
        print("       "+command2)
        time.sleep(1)
        clos = "pqos -a llc:" + str(cos1) + "=" + str(corenum1)+";llc:"+str(cos2) + "=" + str(corenum2)
        print("Step2: " + clos)
        closCommand = subprocess.Popen(clos.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        time.sleep(1)
        mba1_pct = 'pqos -e "mba:'+str(cos1)+'='+str(mba1)+'"'
        mba2_pct = 'pqos -e "mba:'+str(cos2)+'='+str(mba2)+'"'
        print("Step3: "+mba1_pct)
        print("       "+mba2_pct)
        mba1Command = subprocess.Popen(mba1_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        mba2Command = subprocess.Popen(mba2_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(5)
        mbm1 = "pqos -m all:"+str(corenum1)+" -t 1"
        mbm2 = "pqos -m all:"+str(corenum2)+" -t 1"
        print("Step4: "+ mbm1)
        print("       "+ mbm2)
        (stdout1,stderr1) = TESTMBA2().run(mbm1)
        (stdout2,stderr2) = TESTMBA2().run(mbm2)
        lines1 = stdout1.split("\n")
        lines2 = stdout2.split("\n")
        flag1 = 0
        flag2 = 0
        for index1,line1 in enumerate(lines1):
                if 'TIME' in line1:
                    flag1 += 1
                if flag1 == 2:
                    if len(line1.split())!=0:
                        if line1.split()[0] == str(corenum1):
                            mbl1=float(line1.split()[-2])
                            print(mbl1)
                            #if line1.split()[0]==str(core2):
                                #mbl = float(line1.split()[4])
                                #print(mbl)
                                #mbr=float(line.split()[5])
        for index2,line2 in enumerate(lines2):
                    if 'TIME' in line2:
                        flag2 += 1
                    if flag2 == 2:
                        if len(line2.split())!=0:
                            if line2.split()[0] == str(corenum2):
                                mbl2=float(line2.split()[-2])
                                print(mbl2)

        time.sleep(1)
        stress_tools().kill_tool()
        if int(mbl1)>= MBM_UPPER_LIMITATION:
            print("MBM: ",mbl1)
            print("Error: MBM exceed limit")
            sys.exit(1)
        print("Step5: Reset pqos")
        TESTMBA2().reset()
        TESTMBA2().refresh()
        time.sleep(3)
        reset = "pqos -R"
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("----------------------------------------------------------")
        return mbl1,mbl2
   

    def case06_RMID(self, command, corenum, cos, mba, rmid):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 06: Vary which RMID is used"
        print(start)
        time.sleep(1)
        stressCommand = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("Step1: "+command)
        time.sleep(1)
        clos = "pqos -a llc:" + str(cos) + "=" + str(corenum)
        closCommand = subprocess.Popen(clos.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        print("Step2: " + clos)
        time.sleep(1)
        mba_pct = 'pqos -e "mba:'+str(cos)+'='+str(mba)+'"'
        print("Step3: "+mba_pct)
        mbaCommand = subprocess.Popen(mba_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(5)
        mbmCommand = 'pqos --rmid='+str(rmid)+'='+str(corenum)+' -m all:'+str(corenum)+' -t 5'
        print("Step4: "+mbmCommand)
        (stdout,stderr) = TESTMBA2().run(mbmCommand)
        mbm = stdout    
        lines = mbm.split("\n")
        flag1 = 0
        for index1,line1 in enumerate(lines):
                    if 'TIME' in line1:
                        flag1 += 1
                    if flag1 == 6:
                        if len(line1.split())!=0:
                            if line1.split()[0] == str(corenum):
                                mbl1=float(line1.split()[-2])
        if mbl1>= MBM_UPPER_LIMITATION:
            print("MBM: ",mbl1)
            print("Error: MBM exceed limit")
            sys.exit(1)
        time.sleep(1)
        stress_tools().kill_tool()
        print("Step5: Reset pqos")
        TESTMBA2().reset()
        TESTMBA2().refresh()
        time.sleep(2)
        reset = "pqos -R"
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        refresh = "pqos -r -t 1"
        refreshCommand = subprocess.Popen(refresh, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("----------------------------------------------------------")
        return mbl1
        

    def case07_varyCOS(self, command,corenum, cos, mba):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 07: Vary which COS is used"
        print(start)
        time.sleep(1)
        #membw1 = stress_tools().run_membw(corenum)
        #print("Step1: "+membw1)
        stressCommand = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("Step1: "+command)
        time.sleep(1)
        clos = "pqos -a llc:" + str(cos) + "=" + str(corenum)
        print("Step2: " + clos)
        closCommand = subprocess.Popen(clos.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        time.sleep(1)
        mba_pct = 'pqos -e "mba:'+str(cos)+'='+str(mba)+'"'
        print("Step3: "+mba_pct)
        mbaCommand = subprocess.Popen(mba_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(5)
        mbm1 = "pqos -m all:"+str(corenum)+" -t 5"
        print("Step4: "+ mbm1)
        (stdout1,stderr1) = TESTMBA2().run(mbm1)
        lines1 = stdout1.split("\n")
        flag1 = 0
        for index1,line1 in enumerate(lines1):
                if 'TIME' in line1:
                    flag1 += 1
                if flag1 == 6:
                    if len(line1.split())!=0:
                        if line1.split()[0] == str(corenum):
                            mbm=float(line1.split()[-2])
                            print(mbm)
        time.sleep(1)
        stress_tools().kill_tool()
        if int(mbm)>= MBM_UPPER_LIMITATION:
            print("MBM: ",mbm)
            print("Error: MBM exceed limit")
            sys.exit(1)
        print("Step5: Reset pqos")
        TESTMBA2().reset()
        TESTMBA2().refresh()
        time.sleep(3)
        reset = "pqos -R"
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("----------------------------------------------------------")
        return mbm


    def case08_CDP(self, core, cos, cache):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 08: CAT"
        print(start)
        time.sleep(1)
        #stressCommand = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        #                               stderr=subprocess.PIPE,shell=True)
        #print("Step1: "+command)
        cacheways = "pqos -s -v"
        print("Step1: "+cacheways)
        (stdout1,stderr1) = TESTMBA2().run(cacheways)
        time.sleep(1)
        lines1 = stdout1.split("\n")
        num = 0
        size = []
        #global statuscdp
        for line1 in lines1:
            if "#ways=" in line1:
                ways=line1.split()[9]
                way = int(ways[-3:-1])
        #        for i in range(0,way):
        #            num = num+2**i
        #            hexway = hex(num)
        #            size.append(hexway)
                print("INFO: Cache ways =", way)
        #    if "L3 CDP" in line1:
        #        print(line1)
        time.sleep(10)
        clos = "pqos -a llc:" + str(cos) + "=" + str(core)
        print("Step2: " + clos)
        closCommand = subprocess.Popen(clos.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        time.sleep(1)
        #mba_pct = 'pqos -e "mba:'+str(cos)+'='+str(mba)+'"'
        #print("Step3: "+mba_pct)
        #mbaCommand = subprocess.Popen(mba_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        #                               stderr=subprocess.PIPE,shell=True)
        #time.sleep(5)
        #mbmCommand = 'pqos -m all:'+str(core)+' -t 5'
        #print("Step4: "+mbmCommand)
        #(stdout1,stderr1) = TESTMBA2().run(mbmCommand)
        #print(stdout1)
        #mbm1 = stdout1
        #lines1 = mbm1.split("\n")
        #flag1 = 0
        #for index1,line1 in enumerate(lines1):
        #            if 'TIME' in line1:
        #                flag1 += 1
        #            if flag1 == 6:
        #                if len(line1.split())!=0:
        #                    if line1.split()[0] == str(core):
        #                        mbl1=float(line1.split()[-2])
        #                        print(mbl1)
        cat = 'pqos -e "llc:'+str(cos)+'='+str(cache)+'"'
        print("Step3: "+cat)
        catCommand = subprocess.Popen(cat, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(5)
        #print("Step4: Get mlc result")
        l3cache = int(int(sys_info().L3_cache_size()[1])/2000)
        print(l3cache)
        mlcCommand1 = " /home/mlc_v3.7/Linux/mlc_internal --loaded_latency -T -d0 -t10 -u -k"+str(core)+" -b"+str(l3cache)+"m"
        print("Step4: "+mlcCommand1)
        (stdoutmlc,stderrmlc) = TESTMBA2().run(mlcCommand1)
        mlclines = stdoutmlc.split("\n")
        m = 0
        for mlcline in mlclines:
            m = m+1
            if "Delay" in mlcline:
                resulta = mlclines[m+1]
        mlcresult = resulta.split()[-1]
        print(mlcresult)
        #print("Step6: "+mbmCommand)d
        #(stdout2,stderr2) = TESTMBA2().run(mbmCommand)
        #print(stdout2)
        #mbm2 = stdout2
        #lines2 = mbm2.split("\n")
        #flag2 = 0
        #for index2,line2 in enumerate(lines2):
        #            if 'TIME' in line2:
        #                flag2 += 1
        #            if flag2 == 6:
        #                if len(line2.split())!=0:
        #                    if line2.split()[0] == str(core):
        #                        mbl2=float(line2.split()[-2])
        #                        print(mbl2)
        time.sleep(1)
        reset = "pqos -R"
        print("Step5: "+reset)
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("----------------------------------------------------------")
        return float(mlcresult)




    def case09_MinMax(self, command1, command2, core1, cos1, core2, cos2, mba1, mba2):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 09: Min/Max Delay"
        print(start)
        time.sleep(1)
        #membw1 = stress_tools().run_membw(core1)
        #membw2 = stress_tools().run_membw(core2)
        #print("Step1: "+membw1)
        #print("       "+membw2)
        stressCommand1 = subprocess.Popen(command1, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        stressCommand2 = subprocess.Popen(command2, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("Step1: "+command1)
        print("       "+command2)
        time.sleep(1)
        clos1 = "pqos -a llc:" + str(cos1) + "=" + str(core1)
        clos2 = "pqos -a llc:"+str(cos2) + "=" + str(core2)
        print("Step2: " + clos1)
        print("       "+clos2)
        clos1Command = subprocess.Popen(clos1.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        clos2Command = subprocess.Popen(clos2.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        time.sleep(1)
        mba1_pct = 'pqos -e "mba:'+str(cos1)+'='+str(mba1)+'"'
        mba2_pct = 'pqos -e "mba:'+str(cos2)+'='+str(mba2)+'"'
        print("Step3: "+mba1_pct)
        print("       "+mba2_pct)
        mba1Command = subprocess.Popen(mba1_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        mba2Command = subprocess.Popen(mba2_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(2)
        mbm1 = "pqos -m all:"+str(core1)+" -t 5"
        mbm2 = "pqos -m all:"+str(core2)+" -t 5"
        print("Step4: "+ mbm1)
        print("       "+ mbm2)
        (stdout1,stderr1) = TESTMBA2().run(mbm1)
        (stdout2,stderr2) = TESTMBA2().run(mbm2)
        lines1 = stdout1.split("\n")
        lines2 = stdout2.split("\n")
        flag1 = 0
        flag2 = 0
        for index1,line1 in enumerate(lines1):
                    if 'TIME' in line1:
                        flag1 += 1
                    if flag1 == 6:
                        if len(line1.split())!=0:
                            if line1.split()[0] == str(core1):
                                mbl1=float(line1.split()[-2])
                                print(mbl1)
                                #mbr=float(line.split()[5])
        for index2,line2 in enumerate(lines2):
                    if 'TIME' in line2:
                        flag2 += 1
                    if flag2 == 6:
                        if len(line2.split())!=0:
                            if line2.split()[0] == str(core2):
                                mbl2=float(line2.split()[-2])
                                print(mbl2)
                                #mbr=float(line.split()[5])
        if mbl1>= MBM_UPPER_LIMITATION:
            print("MBM: ",mbl1)
            print("Error: MBM exceed limit")
            sys.exit(1)
        #mbmmax = (float(mbl1)+float(mbl2))/2
        #mbmmax1 = format(mbmmax,".2f")
        mbmmax1 = float(mbl1)
        mbmmax2 = float(mbl2)
        time.sleep(1)
        max2minCommand = "wrmsr -a 0xC84 2"
        max2min = subprocess.Popen(max2minCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("Step5: "+max2minCommand)
        time.sleep(2)
        mbm3 = "pqos -m all:"+str(core1)+" -t 5"
        mbm4 = "pqos -m all:"+str(core2)+" -t 5"
        print("Step6: "+ mbm3)
        print("       "+ mbm4)
        (stdout3,stderr3) = TESTMBA2().run(mbm3)
        (stdout4,stderr4) = TESTMBA2().run(mbm4)
        lines3 = stdout3.split("\n")
        lines4 = stdout4.split("\n")
        flag3 = 0
        flag4 = 0
        for index3,line3 in enumerate(lines3):
                    if 'TIME' in line3:
                        flag3 += 1
                    if flag3 == 6:
                        if len(line3.split())!=0:
                            if line3.split()[0] == str(core1):
                                mbl3=float(line3.split()[-2])
                                #mbr=float(line.split()[5])
        for index4,line4 in enumerate(lines4):
                    if 'TIME' in line4:
                        flag4 += 1
                    if flag4 == 6:
                        if len(line4.split())!=0:
                            if line4.split()[0] == str(core2):
                                mbl4=float(line4.split()[-2])
                                #mbr=float(line.split()[5])
        #mbmmin = (float(mbl3)+float(mbl4))/2
        #mbmmin1 = format(mbmmin,".2f")
        mbmmin1 = float(mbl3)
        mbmmin2 = float(mbl4)
        time.sleep(1)
        print("Step7: Reset")
        TESTMBA2().reset()
        TESTMBA2().refresh()
        stress_tools().kill_tool()
        resetmsrCommand = "wrmsr -a 0xC84 2"
        resetmsr = subprocess.Popen(resetmsrCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(3)
        reset = "pqos -R"
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("----------------------------------------------------------")
        return mbmmax1,mbmmin1,mbmmax2,mbmmin2
    
    
    def case10_MinMax_SameCOS(self, command1, command2, core1, cos1, core2, cos2, mba1):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 10: Min/Max Delay Same COS"
        print(start)
        time.sleep(1)
        #membw1 = stress_tools().run_membw(core1)
        #membw2 = stress_tools().run_membw(core2)
        #print("Step1: "+membw1)
        #print("       "+membw2)
        stressCommand1 = subprocess.Popen(command1, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        stressCommand2 = subprocess.Popen(command2, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("Step1: "+command1)
        print("       "+command2)
        time.sleep(1)
        clos1 = "pqos -a llc:" + str(cos1) + "=" + str(core1)
        clos2 = "pqos -a llc:" + str(cos2) + "=" + str(core2)
        print("Step2: " + clos1)
        print("       " + clos2)
        clos1Command = subprocess.Popen(clos1.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        clos2Command = subprocess.Popen(clos2.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        time.sleep(1)
        mba1_pct = 'pqos -e "mba:'+str(cos1)+'='+str(mba1)+'"'
        print("Step3: "+mba1_pct)
        mba1Command = subprocess.Popen(mba1_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(3)
        mbm1 = "pqos -m all:"+str(core1)+" -t 5"
        mbm2 = "pqos -m all:"+str(core2)+" -t 5"
        print("Step4: "+ mbm1)
        print("       "+ mbm2)
        (stdout1,stderr1) = TESTMBA2().run(mbm1)
        (stdout2,stderr2) = TESTMBA2().run(mbm2)
        lines1 = stdout1.split("\n")
        lines2 = stdout2.split("\n")
        flag1 = 0
        flag2 = 0
        for index1,line1 in enumerate(lines1):
                    if 'TIME' in line1:
                        flag1 += 1
                    if flag1 == 6:
                        if len(line1.split())!=0:
                            if line1.split()[0] == str(core1):
                                mbl1=float(line1.split()[-2])
                                #mbr=float(line.split()[5])
        for index2,line2 in enumerate(lines2):
                    if 'TIME' in line2:
                        flag2 += 1
                    if flag2 == 6:
                        if len(line2.split())!=0:
                            if line2.split()[0] == str(core2):
                                mbl2=float(line2.split()[-2])
                                #mbr=float(line.split()[5])
        if mbl1>= MBM_UPPER_LIMITATION:
            print("MBM: ",mbl1)
            print("Error: MBM exceed limit")
            sys.exit(1)
        #mbmmax = (float(mbl1)+float(mbl2))/2
        #mbmmax1 = format(mbmmax,".2f")
        mbmmax1 = float(mbl1)
        mbmmax2 = float(mbl2)
        time.sleep(1)
        max2minCommand = "wrmsr -a 0xC84 2"
        max2min = subprocess.Popen(max2minCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("Step5: "+max2minCommand)
        time.sleep(5)
        mbm3 = "pqos -m all:"+str(core1)+" -t 5"
        mbm4 = "pqos -m all:"+str(core2)+" -t 5"
        print("Step6: "+ mbm3)
        print("       "+ mbm4)
        (stdout3,stderr3) = TESTMBA2().run(mbm3)
        (stdout4,stderr4) = TESTMBA2().run(mbm4)
        lines3 = stdout3.split("\n")
        lines4 = stdout4.split("\n")
        flag3 = 0
        flag4 = 0
        for index3,line3 in enumerate(lines3):
                    if 'TIME' in line3:
                        flag3 += 1
                    if flag3 == 6:
                        if len(line3.split())!=0:
                            if line3.split()[0] == str(core1):
                                mbl3=float(line3.split()[-2])
                                #mbr=float(line.split()[5])
        for index4,line4 in enumerate(lines4):
                    if 'TIME' in line4:
                        flag4 += 1
                    if flag4 == 6:
                        if len(line4.split())!=0:
                            if line4.split()[0] == str(core2):
                                mbl4=float(line4.split()[-2])
                                #mbr=float(line.split()[5])
        #mbmmin = (float(mbl3)+float(mbl4))/2
        #mbmmin1 = format(mbmmin,".2f")
        mbmmin1 = float(mbl3)
        mbmmin2 = float(mbl4)
        time.sleep(1)
        print("Step7: Reset")
        TESTMBA2().reset()
        TESTMBA2().refresh()
        stress_tools().kill_tool()
        resetmsrCommand = "wrmsr -a 0xC84 2"
        resetmsr = subprocess.Popen(resetmsrCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(3)
        reset = "pqos -R"
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("----------------------------------------------------------")
        return mbmmax1,mbmmin1,mbmmax2,mbmmin2

    def case11_MinMax_DiffCore_SameCOS(self, command1, command2, core1, cos1, core2, cos2, mba1):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        msrcore = sys_info().max_thread()
        max2minCommand1 = "wrmsr -a 0xC84 2"
        max2min1 = subprocess.Popen(max2minCommand1, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 11: Min/Max Delay Different Core Same COS"
        print(start)
        time.sleep(1)
        #membw1 = stress_tools().run_membw(core1)
        #membw2 = stress_tools().run_membw(core2)
        #print("Step1: "+membw1)
        #print("       "+membw2)
        stressCommand1 = subprocess.Popen(command1, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        stressCommand2 = subprocess.Popen(command2, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("Step1: "+command1)
        print("       "+command2)
        time.sleep(2)
        clos1 = "pqos -a llc:" + str(cos1) + "=" + str(core1)
        clos2 = "pqos -a llc:" + str(cos2) + "=" + str(core2)
        print("Step2: " + clos1)
        clos1Command = subprocess.Popen(clos1.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        clos2Command = subprocess.Popen(clos2.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        time.sleep(1)
        mba1_pct = 'pqos -e "mba:'+str(cos1)+'='+str(mba1)+'"'
        print("Step3: "+mba1_pct)
        mba1Command = subprocess.Popen(mba1_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(3)
        mbm1 = "pqos -m all:"+str(core1)+" -t 5"
        mbm2 = "pqos -m all:"+str(core2)+" -t 5"
        print("Step4: "+ mbm1)
        print("       "+ mbm2)
        (stdout1,stderr1) = TESTMBA2().run(mbm1)
        (stdout2,stderr2) = TESTMBA2().run(mbm2)
        lines1 = stdout1.split("\n")
        lines2 = stdout2.split("\n")
        flag1 = 0
        flag2 = 0
        for index1,line1 in enumerate(lines1):
                    if 'TIME' in line1:
                        flag1 += 1
                    if flag1 == 6:
                        if len(line1.split())!=0:
                            if line1.split()[0] == str(core1):
                                mbl1=float(line1.split()[-2])
                                #mbr=float(line.split()[5])
        for index2,line2 in enumerate(lines2):
                    if 'TIME' in line2:
                        flag2 += 1
                    if flag2 == 6:
                        if len(line2.split())!=0:
                            if line2.split()[0] == str(core2):
                                mbl2=float(line2.split()[-2])
                               #mbr=float(line.split()[5])
        if mbl1>= MBM_UPPER_LIMITATION:
            print("MBM: ",mbl1)
            print("Error: MBM exceed limit")
            sys.exit(1)
        #mbmmax = (float(mbl1)+float(mbl2))/2
        #mbmmax1 = format(mbmmax,".2f")
        mbmmax1 = float(mbl1)
        mbmmax2 = float(mbl2)
        time.sleep(1)
        max2minCommand2 = "wrmsr -a 0xC84 2"
        max2min2 = subprocess.Popen(max2minCommand2, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("Step5: "+max2minCommand2)
        time.sleep(5)
        mbm3 = "pqos -m all:"+str(core1)+" -t 5"
        mbm4 = "pqos -m all:"+str(core2)+" -t 5"
        print("Step6: "+ mbm3)
        print("       "+ mbm4)
        (stdout3,stderr3) = TESTMBA2().run(mbm3)
        (stdout4,stderr4) = TESTMBA2().run(mbm4)
        lines3 = stdout3.split("\n")
        lines4 = stdout4.split("\n")
        flag3 = 0
        flag4 = 0
        for index3,line3 in enumerate(lines3):
                    if 'TIME' in line3:
                        flag3 += 1
                    if flag3 == 6:
                        if len(line3.split())!=0:
                            if line3.split()[0] == str(core1):
                                mbl3=float(line3.split()[-2])
                                #mbr=float(line.split()[5])
        for index4,line4 in enumerate(lines4):
                    if 'TIME' in line4:
                        flag4 += 1
                    if flag4 == 6:
                        if len(line4.split())!=0:
                            if line4.split()[0] == str(core2):
                                mbl4=float(line4.split()[-2])
                                #mbr=float(line.split()[5])
        #mbmmin = (float(mbl3)+float(mbl4))/2
        #mbmmin1 = format(mbmmin,".2f")
        mbmmin1 = float(mbl3)
        mbmmin2 = float(mbl4)
        time.sleep(1)
        print("Step7: Reset")
        TESTMBA2().reset()
        TESTMBA2().refresh()
        stress_tools().kill_tool()
        resetmsrCommand = "wrmsr -a 0xC84 2"
        resetmsr = subprocess.Popen(resetmsrCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(3)
        reset = "pqos -R"
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("----------------------------------------------------------")
        return mbmmax1,mbmmin1,mbmmax2,mbmmin2

        
    def case12_MBR(self, command,corenum, cos, mba):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 12: MBR=MBT"
        print(start)
        time.sleep(1)
        #thread = sys_info().max_thread()
        #if corenum >= 0 and corenum <= (thread/4)-1:
        #    numa = 1
        #elif corenum >= thread/2 and corenum <= (thread*0.75)-1:
        #    numa = 1
        #else:
        #    numa = 0
        #stream = "taskset -c "+str(corenum)+" numactl --membind="+str(numa)+" /home/STREAM-master/stream"
        #streamCommand = subprocess.Popen(stream.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        #                               stderr=subprocess.PIPE)
        #print("Step1: "+stream)
        stressCommand = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("Step1: "+command)
        time.sleep(1)
        clos = "pqos -a llc:" + str(cos) + "=" + str(corenum)
        print("Step2: " + clos)
        closCommand = subprocess.Popen(clos.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        mba_pct = 'pqos -e "mba:'+str(cos)+'='+str(mba)+'"'
        print("Step3: "+mba_pct)
        mbaCommand = subprocess.Popen(mba_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(5)
        mbm1 = "pqos -m all:"+str(corenum)+" -t 5"
        print("Step4: "+ mbm1)
        (stdout1,stderr1) = TESTMBA2().run(mbm1)
        lines1 = stdout1.split("\n")
        flag1 = 0
        for index1,line1 in enumerate(lines1):
                if 'TIME' in line1:
                    flag1 += 1
                if flag1 == 6:
                    if len(line1.split())!=0:
                        if line1.split()[0] == str(corenum):
                            mbl=float(line1.split()[-2])
                            mbr=float(line1.split()[-1])
        stress_tools().kill_tool()
        if int(mbr)>= MBM_UPPER_LIMITATION:
            print("MBM: ",mbr)
            print("Error: MBM exceed limit")
            sys.exit(1)
        print("Step5: Reset pqos")
        TESTMBA2().reset()
        TESTMBA2().refresh()
        time.sleep(3)
        reset = "pqos -R"
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("----------------------------------------------------------")
        return mbl, mbr

    def case17_CacheSize(self, corenum, cos, mba, buffersize):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 17: MBA within cache size"
        print(start)
        time.sleep(1)
        clos1 = "pqos -a llc:" + str(cos) + "=" + str(corenum)
        print("Step1: " + clos1)
        closCommand1 = subprocess.Popen(clos1, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(1)
        mba_pct = "pqos -e mba:"+str(cos)+"="+str(mba)
        print("Step2: "+mba_pct)
        mbaCommand = subprocess.Popen(mba_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        cleancache = "echo 3 > /proc/sys/vm/drop_caches"
        cleanCommand = subprocess.Popen(cleancache, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
        mlcCommand = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -R -d0 -T -t15 -b"+str(buffersize)+"M -k"+str(corenum)
        print("Step3: "+mlcCommand)
        (stdout1,stderr1) = TESTMBA2().run(mlcCommand)
        mlclines1 = stdout1.split("\n")
        n = 0
        for mlcline1 in mlclines1:
            n = n+1
            if "Delay" in mlcline1:
                result1 = mlclines1[n+1]
        mlcresult1 = result1.split()[-1]
        mlc1 = subprocess.Popen(mlcCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(10)
        mbm1 = "pqos -m all:"+str(corenum)+" -t 5"
        print("Step4: "+ mbm1)
        (stdout1,stderr1) = TESTMBA2().run(mbm1)
        lines1 = stdout1.split("\n")
        flag1 = 0
        for index1,line1 in enumerate(lines1):
                if 'TIME' in line1:
                    flag1 += 1
                if flag1 == 6:
                    if len(line1.split())!=0:
                        if line1.split()[0] == str(corenum):
                            mbm=float(line1.split()[-2])
                            print(mbm)
        time.sleep(6)
        if float(mlcresult1)>= MBM_UPPER_LIMITATION:
            print("MBM: ",mlcresult1)
            print("Error: MBM exceed limit")
            sys.exit(1)
        time.sleep(1)
        TESTMBA2().reset()
        TESTMBA2().refresh()
        time.sleep(3)
        reset = "pqos -R"
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("----------------------------------------------------------")
        return float(mlcresult1),float(mbm)





    def case18_StopThrottle(self, command, corenum, cos1, cos2, mba):
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 18: Stop Throttle"
        print(start)
        time.sleep(1)
        #membw = stress_tools().run_membw(corenum)
        #print("Step1: "+membw)
        stressCommand = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("Step1: "+command)
        time.sleep(1)
        clos1 = "pqos -a llc:" + str(cos1) + "=" + str(corenum)
        print("Step2: " + clos1)
        closCommand1 = subprocess.Popen(clos1.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        time.sleep(1)
        mba_pct = "pqos -e mba:"+str(cos1)+"="+str(mba)
        print("Step3: "+mba_pct)
        mbaCommand = subprocess.Popen(mba_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        time.sleep(3)
        mbm = "pqos -m all:"+str(corenum)+" -t 5"
        print("Step4: "+ mbm)
        (stdout1,stderr1) = TESTMBA2().run(mbm)
        lines1 = stdout1.split("\n")
        flag1 = 0
        for index1,line1 in enumerate(lines1):
                if 'TIME' in line1:
                    flag1 += 1
                if flag1 == 6:
                    if len(line1.split())!=0:
                        if line1.split()[0] == str(corenum):
                            mbm1=float(line1.split()[-2])
                            print(mbm1)
        if float(mbm1)>= MBM_UPPER_LIMITATION:
            print("MBM: ",mbm1)
            print("Error: MBM exceed limit")
            sys.exit(1)
        time.sleep(1)
        clos2 = "pqos -a llc:" + str(cos2) + "=" + str(corenum)
        print("Step5: " + clos2)
        closCommand2 = subprocess.Popen(clos2.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        time.sleep(3)
        print("Step6: "+ mbm)
        (stdout2,stderr2) = TESTMBA2().run(mbm)
        lines2 = stdout2.split("\n")
        flag2 = 0
        for index2,line2 in enumerate(lines2):
                if 'TIME' in line2:
                    flag2 += 1
                if flag2 == 6:
                    if len(line2.split())!=0:
                        if line2.split()[0] == str(corenum):
                            mbm2=float(line2.split()[-2])
                            print(mbm2)
        time.sleep(1)
        stress_tools().kill_tool()
        print("Step5: Reset pqos")
        TESTMBA2().reset()
        TESTMBA2().refresh()
        reset = "pqos -R"
        resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        print("----------------------------------------------------------")
        return mbm1,mbm2




    def case19_MBAonCOS0(self, core1, core2, cos2, mba1, c1, c2, multitools):
        #libpath = "source /opt/intel/bin/compilervars.sh intel64"
        #libCommand = subprocess.Popen(libpath, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        #                               stderr=subprocess.PIPE,shell=True)
        time.sleep(10)
        resetcommand = "pqos -r -t 1"
        resetchild = subprocess.Popen(resetcommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        print("\n")
        print("----------------------------------------------------------")
        start = "Start testing MBA2.0 Case 19: MBA on COS0"
        print(start)
        time.sleep(1)
        if multitools == 1:
            command1 = subprocess.Popen(c1, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,shell=True)
            time.sleep(1)
            command2 = subprocess.Popen(c2, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,shell=True)
            print("Step1: "+c1)
            print("       "+c2)
            time.sleep(1)
            clos1 = 'pqos -a "llc:0=' + str(core1)+'"'
            clos2 = 'pqos -a "llc:'+str(cos2) + '=' + str(core2)+'"'
            print("Step2: " + clos1)
            print("       " + clos2)
            clos1Command = subprocess.Popen(clos1, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
            clos2Command = subprocess.Popen(clos2, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
            time.sleep(1)
            mba2_pct = 'pqos -e "mba:'+str(cos2)+'=50;mba:0='+str(mba1)+'"'
            print("Step3: "+mba2_pct)
            mba2Command = subprocess.Popen(mba2_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
            mba1_pct = 'pqos -e "mba:0='+str(mba1)+'"'
            time.sleep(1)
            print("Step4: "+mba1_pct)
            #mba1Command = subprocess.Popen(mba1_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            #                           stderr=subprocess.PIPE,shell=True)
            time.sleep(5)
            mbm1 = "pqos -m all:"+str(core1)+" -t 5"
            mbm2 = "pqos -m all:"+str(core2)+" -t 5"
            print("Step5: "+ mbm1)
            print("       "+ mbm2)
            (stdout1,stderr1) = TESTMBA2().run(mbm1)
            #print(stdout1)
            time.sleep(1)
            (stdout2,stderr2) = TESTMBA2().run(mbm2)
            #print(stdout2)
            lines1 = stdout1.split("\n")
            lines2 = stdout2.split("\n")
            flag1 = 0
            flag2 = 0
            for index1,line1 in enumerate(lines1):
                    if 'TIME' in line1:
                        flag1 += 1
                    if flag1 == 6:
                        if len(line1.split())!=0:
                            if line1.split()[0] == str(core1):
                                mbl1=float(line1.split()[-2])
                                print(mbl1)
                                #mbr=float(line.split()[5])
            for index2,line2 in enumerate(lines2):
                    if 'TIME' in line2:
                        flag2 += 1
                    if flag2 == 6:
                        if len(line2.split())!=0:
                            if line2.split()[0] == str(core2):
                                mbl2=float(line2.split()[-2])
                                print(mbl2)
                                #mbr=float(line.split()[5])
            if float(mbl1)>= MBM_UPPER_LIMITATION:
                print("MBM: ",mbl1)
                print("Error: MBM exceed limit")
                sys.exit(1)
            stress_tools().kill_tool()
            time.sleep(10)
            return mbl1, mbl2
        elif multitools == 0:
            #TESTMBA2().reset()
            time.sleep(1)
            command2 = subprocess.Popen(c2,stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,shell=True)
            print("Step1: "+c2)
            time.sleep(1)
            clos = 'pqos -a "llc:0=' + str(core1)+';llc:'+str(cos2) + '=' + str(core2)+'"'
            print("Step2: " + clos)
            closCommand = subprocess.Popen(clos, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,shell=True)
            time.sleep(1)
            mba2_pct = 'pqos -e "mba:'+str(cos2)+'=50;mba:0=50"'
            print("Step3: "+mba2_pct)
            mba2Command = subprocess.Popen(mba2_pct,stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,shell=True)
            time.sleep(1)
            mba1_pct = 'pqos -e "mba:0='+str(mba1)+'"'
            print("Step4: "+mba1_pct)
            mba1Command = subprocess.Popen(mba1_pct, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,shell=True)
            time.sleep(5)
            #pqos = "pqos -s"
            #(stdout,stderr) = TESTMBA2().run(pqos)
            #print(stdout)
            mbm1 = "pqos -m all:"+str(core1)+" -t 5"
            mbm2 = "pqos -m all:"+str(core2)+" -t 5"
            print("Step5: "+ mbm1)
            print("       "+ mbm2)
            (stdout1,stderr1) = TESTMBA2().run(mbm1)
            time.sleep(1)
            (stdout2,stderr2) = TESTMBA2().run(mbm2)
            lines1 = stdout1.split("\n")
            lines2 = stdout2.split("\n")
            flag1 = 0
            flag2 = 0
            for index1,line1 in enumerate(lines1):
                    if 'TIME' in line1:
                        flag1 += 1
                    if flag1 == 6:
                        if len(line1.split())!=0:
                            if line1.split()[0] == str(core1):
                                mbl1=float(line1.split()[-2])
                                print(mbl1)
                            #if line1.split()[0]==str(core2):
                                #mbl = float(line1.split()[4])
                                #print(mbl)
                                #mbr=float(line.split()[5])
            for index2,line2 in enumerate(lines2):
                    if 'TIME' in line2:
                        flag2 += 1
                    if flag2 == 6:
                        if len(line2.split())!=0:
                            if line2.split()[0] == str(core2):
                                mbl2=float(line2.split()[-2])
                                print(mbl2)
                                #mbr=float(line.split()[5])
            if float(mbl1)>= MBM_UPPER_LIMITATION:
                print("MBM: ",mbl1)
                print("Error: MBM exceed limit")
                sys.exit(1)
            stress_tools().kill_tool()
            time.sleep(1)
            reset = "pqos -R"
            resetCommand = subprocess.Popen(reset, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
            print("----------------------------------------------------------")
            return mbl1, mbl2
        else:
            errormessage = "Wrong Input"
            print("Wrong input")
            return errormessage 






        





