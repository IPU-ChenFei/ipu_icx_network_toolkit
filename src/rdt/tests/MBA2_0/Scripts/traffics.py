from mba2_functions import *
import random


class TrafficType:
    def get_traffic(self,randcore):
        core = sys_info().max_thread()
        commandlist = []
        streamCommand = "taskset -c "+str(randcore)+" /home/STREAM-master/stream"
        membw_NTW_Command = "/home/intel-cmt-cat-master/tools/membw/membw -c "+str(randcore)+" -b 100000 --nt-write"
        membw_R_Command = "/home/intel-cmt-cat-master/tools/membw/membw -c "+str(randcore)+" -b 100000 --read"
        mlc_R_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -R -d0 -T -b300m -t20 -k"+str(randcore)
        mlc_W2_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W2 -d0 -T -b300m -t20 -k"+str(randcore)
        mlc_W3_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W3 -d0 -T -b300m -t20 -k"+str(randcore)
        mlc_W5_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W5 -d0 -T -b300m -t20 -k"+str(randcore)
        mlc_W6_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W6 -d0 -T -b300m -t20 -k"+str(randcore)
        mlc_W7_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W7 -d0 -T -b300m -t20 -k"+str(randcore)
        mlc_W8_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W8 -d0 -T -b300m -t20 -k"+str(randcore)
        mlc_W9_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W9 -d0 -T -b300m -t20 -k"+str(randcore)
        mlc_W10_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W10 -d0 -T -b300m -t20 -k"+str(randcore)
        mlc_W11_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W11 -d0 -T -b300m -t20 -k"+str(randcore)
        mlc_W12_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W12 -d0 -T -b300m -t20 -k"+str(randcore)
        commandlist.extend((streamCommand,membw_NTW_Command,membw_R_Command,mlc_R_Command,mlc_W2_Command,mlc_W3_Command,mlc_W5_Command,mlc_W6_Command,mlc_W7_Command,mlc_W8_Command,mlc_W9_Command,mlc_W10_Command,mlc_W11_Command,mlc_W12_Command))
        #commandlist.extend((streamCommand,membw_NTW_Command,membw_R_Command,mlc_R_Command,mlc_W2_Command,mlc_W3_Command,mlc_W6_Command,mlc_W7_Command,mlc_W8_Command,mlc_W9_Command,mlc_W10_Command,mlc_W11_Command,mlc_W12_Command))
        trafficlist=["stream","membw_NTW","membw_R","mlc_R","mlc_W2","mlc_W3","mlc_W5","mlc_W6","mlc_W7","mlc_W8","mlc_W9","mlc_W10","mlc_W11","mlc_W12"]
        #trafficlist=["stream","membw_NTW","membw_R","mlc_R","mlc_W2","mlc_W3","mlc_W6","mlc_W7","mlc_W8","mlc_W9","mlc_W10","mlc_W11","mlc_W12"]
        dic = dict(map(lambda x,y:[x,y],trafficlist,commandlist))
        pair = random.sample(dic.items(),1)
        randtraffic= pair[0][0]
        randcommand= pair[0][1]
        return randtraffic,randcommand,randcore

    def get_same_traffics(self,randcore1,randcore2):
        commandlist1 = []
        commandlist2 = []
        streamCommand = "taskset -c " + str(randcore1) + " /home/STREAM-master/stream"
        membw_NTW_Command = "/home/intel-cmt-cat-master/tools/membw/membw -c " + str(randcore1) + " -b 100000 --nt-write"
        membw_R_Command = "/home/intel-cmt-cat-master/tools/membw/membw -c " + str(randcore1) + " -b 100000 --read"
        mlc_R_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -R -d0 -T -b300m -t20 -k" + str(randcore1)
        mlc_W2_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W2 -d0 -T -b300m -t20 -k" + str(randcore1)
        mlc_W3_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W3 -d0 -T -b300m -t20 -k" + str(randcore1)
        mlc_W5_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W5 -d0 -T -b300m -t20 -k" + str(randcore1)
        mlc_W6_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W6 -d0 -T -b300m -t20 -k" + str(randcore1)
        mlc_W7_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W7 -d0 -T -b300m -t20 -k" + str(randcore1)
        mlc_W8_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W8 -d0 -T -b300m -t20 -k" + str(randcore1)
        mlc_W9_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W9 -d0 -T -b300m -t20 -k" + str(randcore1)
        mlc_W10_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W10 -d0 -T -b300m -t20 -k" + str(randcore1)
        mlc_W11_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W11 -d0 -T -b300m -t20 -k" + str(randcore1)
        mlc_W12_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W12 -d0 -T -b300m -t20 -k" + str(randcore1)
        commandlist1.extend((streamCommand, membw_NTW_Command, membw_R_Command, mlc_R_Command, mlc_W2_Command,
                            mlc_W3_Command, mlc_W5_Command, mlc_W6_Command, mlc_W7_Command, mlc_W8_Command,
                            mlc_W9_Command, mlc_W10_Command, mlc_W11_Command, mlc_W12_Command))
        #commandlist1.extend((streamCommand, membw_NTW_Command, membw_R_Command, mlc_R_Command, mlc_W2_Command,
        #                    mlc_W3_Command, mlc_W6_Command, mlc_W7_Command, mlc_W8_Command,
        #                    mlc_W9_Command, mlc_W10_Command, mlc_W11_Command, mlc_W12_Command))
        streamCommand2 = "taskset -c " + str(randcore2) + " /home/STREAM-master/stream"
        membw_NTW_Command2 = "/home/intel-cmt-cat-master/tools/membw/membw -c " + str(
            randcore2) + " -b 100000 --nt-write"
        membw_R_Command2 = "/home/intel-cmt-cat-master/tools/membw/membw -c " + str(randcore2) + " -b 100000 --read"
        mlc_R_Command2 = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -R -d0 -T -b300m -t20 -k" + str(randcore2)
        mlc_W2_Command2 = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W2 -d0 -T -b300m -t20 -k" + str(randcore2)
        mlc_W3_Command2 = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W3 -d0 -T -b300m -t20 -k" + str(randcore2)
        mlc_W5_Command2 = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W5 -d0 -T -b300m -t20 -k" + str(randcore2)
        mlc_W6_Command2 = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W6 -d0 -T -b300m -t20 -k" + str(randcore2)
        mlc_W7_Command2 = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W7 -d0 -T -b300m -t20 -k" + str(randcore2)
        mlc_W8_Command2 = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W8 -d0 -T -b300m -t20 -k" + str(randcore2)
        mlc_W9_Command2 = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W9 -d0 -T -b300m -t20 -k" + str(randcore2)
        mlc_W10_Command2 = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W10 -d0 -T -b300m -t20 -k" + str(randcore2)
        mlc_W11_Command2 = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W11 -d0 -T -b300m -t20 -k" + str(randcore2)
        mlc_W12_Command2 = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W12 -d0 -T -b300m -t20 -k" + str(randcore2)
        #commandlist2.extend((streamCommand2, membw_NTW_Command2, membw_R_Command2, mlc_R_Command2, mlc_W2_Command2,
        #                     mlc_W3_Command2, mlc_W6_Command2, mlc_W7_Command2, mlc_W8_Command2,
        #                     mlc_W9_Command2, mlc_W10_Command2, mlc_W11_Command2, mlc_W12_Command2))
        commandlist2.extend((streamCommand2, membw_NTW_Command2, membw_R_Command2, mlc_R_Command2, mlc_W2_Command2,
                             mlc_W3_Command2, mlc_W5_Command2, mlc_W6_Command2, mlc_W7_Command2, mlc_W8_Command2,
                             mlc_W9_Command2, mlc_W10_Command2, mlc_W11_Command2, mlc_W12_Command2))
        trafficlist = ["stream", "membw_NTW", "membw_R", "mlc_R", "mlc_W2", "mlc_W3", "mlc_W5", "mlc_W6", "mlc_W7",
                       "mlc_W8", "mlc_W9", "mlc_W10", "mlc_W11", "mlc_W12"]
        #trafficlist = ["stream", "membw_NTW", "membw_R", "mlc_R", "mlc_W2", "mlc_W3", "mlc_W6", "mlc_W7",
        #               "mlc_W8", "mlc_W9", "mlc_W10", "mlc_W11", "mlc_W12"]
        #dic = dict(map(lambda x, y: [x, y], trafficlist, commandlist))
        #air = random.sample(dic.items(),1)
        #randtraffic= pair[0][0]
        #randcommand= pair[0][1]
        randtraffic = random.choice(trafficlist)
        index = trafficlist.index(randtraffic)
        randcommand1 = commandlist1[index]
        randcommand2 = commandlist2[index]

        return randtraffic,randcommand1,randcommand2

    def remote_traffic(self,randcore):
        trafficlist = ["stream", "membw_NTW", "membw_R", "mlc_R", "mlc_W2", "mlc_W3", "mlc_W5", "mlc_W6", "mlc_W7",
                       "mlc_W8", "mlc_W9", "mlc_W10", "mlc_W11", "mlc_W12"]
        #trafficlist = ["stream", "membw_NTW", "membw_R", "mlc_R", "mlc_W2", "mlc_W3", "mlc_W6", "mlc_W7",
        #               "mlc_W8", "mlc_W9", "mlc_W10", "mlc_W11", "mlc_W12"]
        commandlist = []
        thread = sys_info().max_thread()
        hyperthreading = sys_info().thread_per_core()
        if hyperthreading == 2:
            if randcore >= 0 and randcore <= (thread/4)-1:
                numa = 1
            elif randcore >= thread/2 and randcore <= (thread*0.75)-1:
                numa = 1
            else:
                numa = 0
        elif hyperthreading == 1:
            if randcore >= 0 and randcore <= (thread/2)-1:
                numa = 1
            else:
                numa = 0
        streamCommand = "taskset -c "+str(randcore)+" numactl --membind="+str(numa)+" /home/STREAM-master/stream"
        membw_NTW_Command = "numactl --membind="+str(numa)+" /home/intel-cmt-cat-master/tools/membw/membw -c "+str(randcore)+" -b 100000 --nt-write"
        membw_R_Command = "numactl --membind="+str(numa)+" /home/intel-cmt-cat-master/tools/membw/membw -c "+str(randcore)+" -b 100000 --read"
        mlc_R_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -R -d0 -T -j"+str(numa)+" -b300m -t20 -k" + str(randcore)
        mlc_W2_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W2 -d0 -T -j"+str(numa)+" -b300m -t20 -k" + str(randcore)
        mlc_W3_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W3 -d0 -T -j"+str(numa)+" -b300m -t20 -k" + str(randcore)
        mlc_W5_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W5 -d0 -T -j"+str(numa)+" -b300m -t20 -k" + str(randcore)
        mlc_W6_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W6 -d0 -T -j"+str(numa)+" -b300m -t20 -k" + str(randcore)
        mlc_W7_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W7 -d0 -T -j"+str(numa)+" -b300m -t20 -k" + str(randcore)
        mlc_W8_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W8 -d0 -T -j"+str(numa)+" -b300m -t20 -k" + str(randcore)
        mlc_W9_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W9 -d0 -T -j"+str(numa)+" -b300m -t20 -k" + str(randcore)
        mlc_W10_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W10 -d0 -T -j"+str(numa)+" -b300m -t20 -k" + str(randcore)
        mlc_W11_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W11 -d0 -T -j"+str(numa)+" -b300m -t20 -k" + str(randcore)
        mlc_W12_Command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -W12 -d0 -T -j"+str(numa)+" -b300m -t20 -k" + str(randcore)
        #commandlist.extend((streamCommand,membw_NTW_Command,membw_R_Command,mlc_R_Command,mlc_W2_Command,mlc_W3_Command,mlc_W6_Command,mlc_W7_Command,mlc_W8_Command,mlc_W9_Command,mlc_W10_Command,mlc_W11_Command,mlc_W12_Command))
        commandlist.extend((streamCommand,membw_NTW_Command,membw_R_Command,mlc_R_Command,mlc_W2_Command,mlc_W3_Command,mlc_W5_Command,mlc_W6_Command,mlc_W7_Command,mlc_W8_Command,mlc_W9_Command,mlc_W10_Command,mlc_W11_Command,mlc_W12_Command))
        randtraffic = random.choice(trafficlist)
        index = trafficlist.index(randtraffic)
        randcommand = commandlist[index]
        return randtraffic,randcommand



