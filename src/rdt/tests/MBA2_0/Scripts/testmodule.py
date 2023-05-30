# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 10:03:18 2020

@author: leirong
"""

import os
import subprocess
import re
import time
import threading
import svtools.common.baseaccess as ba
import namednodes
from mba2_functions import MBM_UPPER_LIMITATION
from mba2_functions import RDT_MBA2_SCRIPT_VERSION
sv = namednodes.sv
TERMINATE_ERROR = ['MBL_overflow','MBL_readzeroerror']
MBM_LOWER_LIMITATION = 1

class PySVStartTool:
    def __init__(self, APP_LOG):
        self.reconnect_master_frame()
        self.socketlist=None
        self.APP_LOG = APP_LOG
        self.itp = None
    
    def change_timewindow(self, request_socket, cos, tw):
        self.APP_LOG.info('Change timewindow to:{}'.format(tw))
        delayvalue_x = int(cos/2)
        tw_y = int(cos%2)
        sv_command = 'sv.{}.uncore.cha.chas.cms.mbe_delayvalue_{}.timewindow{}.write({})'.format(self.socketlist[0],
                                                                                                 str(delayvalue_x),
                                                                                                 str(tw_y),
                                                                                                 tw)
        eval(sv_command)
        
    def change_mbadelay(self, request_socket, cos, delay):
        self.APP_LOG.info('Change MBAdelay to:{}'.format(delay))
        delayvalue_x = int(cos/2)
        delay_y = int(cos%2)
        sv_command = 'sv.{}.uncore.cha.chas.cms.mbe_delayvalue_{}.delay{}.write({})'.format(self.socketlist[0],
                                                                                            str(delayvalue_x),
                                                                                            str(delay_y),
                                                                                            delay)
        eval(sv_command)
    
    def change_mbavalid(self, request_socket, mbavalid):
        self.APP_LOG.info('Change MBA valid to:{}'.format(mbavalid))
        sv_command = 'sv.{}.uncore.cha.chas.cms.mbe_config.rbe_valid.write({})'.format(self.socketlist[0],mbavalid)
        eval(sv_command)
        
    def change_fastvalid(self, request_socket, fastvalid):
        self.APP_LOG.info('Change FaST valid to:{}'.format(fastvalid))
        sv_command = 'sv.{}.uncore.cha.chas.cms.agt_fast_ctl_0.irq_throttle_en.write({})'.format(self.socketlist[0],fastvalid)
        eval(sv_command)
        
    def change_mode(self, request_socket, mode):
        if mode:
            self.APP_LOG.info('Change to Max Mode')
        else:
            self.APP_LOG.info('Change to Cascade Mode') 
        sv_command = 'sv.{}.uncore.cha.chas.cms.mbe_settings.disable_cascade_delay.write({})'.format(self.socketlist[0],mode)
        eval(sv_command)
    
    def get_uncorefreq(self,core):
        msr_cmd = "rdmsr -p {} 0x621".format(core)
        res = int(os.popen(msr_cmd).read().strip(),16) & 0x3f
        #base freq 100MHz
        res = 100*res/1000.0
        return res
    # def change_uncorefreq(self, request_socket, uncorefreq):
    #     self.APP_LOG.info('Change uncore frequency to:{}'.format(uncorefreq))
    #     pega.uncoreRatioSingleShot(request_socket,uncorefreq)
    
    def change_unthrottleddelay(self, request_socket, undelay):
        self.APP_LOG.info('Change unthrottle delay to:{}'.format(undelay))
        sv_command = 'sv.{}.uncore.cha.chas.cms.mbe_settings.unthrottled_delay.write({})'.format(self.socketlist[0],
                                                                                                 undelay)
        eval(sv_command)
    
    def get_unthrottleddelay(self,request_socket):
        sv_command = 'sv.{}.uncore.cha.chas.cms.mbe_settings.unthrottled_delay.get_value()'.format(self.socketlist[0])
        return int(eval(sv_command)[0])
    
    def change_leakybucketsize(self, request_socket, lbsize):
        self.APP_LOG.info('Change LeakyBucketSize to:{}'.format(lbsize))
        sv_command = 'sv.{}.uncore.ms2idis.mbe_leakybucketsize.write({})'.format(self.socketlist[0],lbsize)
        eval(sv_command)
    
    def get_timewindow_ubox(self,request_socket,throttlepercent):
        tw_x = int(throttlepercent-20 <= 0)
        tw_y = int((100-throttlepercent)/10)
        sv_command = 'sv.{}.uncore.ubox.ncevents.ncevents_cfg_mbe_timewindow_{}_cfg.mbe_timewindow_{}.get_value()'.format(self.socketlist[0],
                                                                                                                         str(tw_x),
                                                                                                                         str(tw_y),
                                                                                                                         )
        return int(eval(sv_command))
    
    def change_timewindow_ubox(self,request_socket,throttlepercent,tw):
        self.APP_LOG.info('Change MBA Throttle Percent {} Timewindow in ubox to:{}'.format(throttlepercent,tw))
        tw_x = int(throttlepercent-20 <= 0)
        tw_y = int((100-throttlepercent)/10)
        if request_socket == None:
            sv_command = 'sv.{}.uncore.ubox.ncevents.ncevents_cfg_mbe_timewindow_{}_cfg.mbe_timewindow_{}.write({})'.format(self.socketlist[0],
                                                                                                                             str(tw_x),
                                                                                                                             str(tw_y),
                                                                                                                             tw,
                                                                                                                             )
            eval(sv_command)
            sv_command = 'sv.{}.uncore.ubox.ncevents.ncevents_cfg_mbe_timewindow_{}_cfg.mbe_timewindow_{}.write({})'.format(self.socketlist[1],
                                                                                                                             str(tw_x),
                                                                                                                             str(tw_y),
                                                                                                                             tw,
                                                                                                                             )
            eval(sv_command)
        else:
            sv_command = 'sv.{}.uncore.ubox.ncevents.ncevents_cfg_mbe_timewindow_{}_cfg.mbe_timewindow_{}.write({})'.format(self.socketlist[0],
                                                                                                                             str(tw_x),
                                                                                                                             str(tw_y),
                                                                                                                             tw,
                                                                                                                             )
            eval(sv_command)
    
    def get_mbadelay_ubox(self,request_socket,throttlepercent):
        d_x = int(throttlepercent-20 <= 0)
        d_y = int((100-throttlepercent)/10)
        sv_command = 'sv.{}.uncore.ubox.ncevents.ncevents_cfg_mbe_delay_{}_cfg.mbe_delay_{}.get_value()'.format(self.socketlist[0],
                                                                                                               str(d_x),
                                                                                                               str(d_y),
                                                                                                               )
        return int(eval(sv_command))
    
    def change_mbadelay_ubox(self,request_socket,throttlepercent,delay):
        self.APP_LOG.info('Change MBA Throttle Percent {} Delay in ubox to:{}'.format(throttlepercent,delay))
        d_x = int(throttlepercent-20 <= 0)
        d_y = int((100-throttlepercent)/10)
        if request_socket == None:
            sv_command = 'sv.{}.uncore.ubox.ncevents.ncevents_cfg_mbe_delay_{}_cfg.mbe_delay_{}.write({})'.format(self.socketlist[0],
                                                                                                                   str(d_x),
                                                                                                                   str(d_y),
                                                                                                                   delay,
                                                                                                                   )
            eval(sv_command)
            sv_command = 'sv.{}.uncore.ubox.ncevents.ncevents_cfg_mbe_delay_{}_cfg.mbe_delay_{}.write({})'.format(self.socketlist[1],
                                                                                                                   str(d_x),
                                                                                                                   str(d_y),
                                                                                                                   delay,
                                                                                                                   )
            eval(sv_command)
        else:
            sv_command = 'sv.{}.uncore.ubox.ncevents.ncevents_cfg_mbe_delay_{}_cfg.mbe_delay_{}.write({})'.format(self.socketlist[0],
                                                                                                                   str(d_x),
                                                                                                                   str(d_y),
                                                                                                                   delay,
                                                                                                                   )
            eval(sv_command)
    
    def get_timewindow(self, request_socket, cos):
        delayvalue_x = int(cos/2)
        tw_y = int(cos%2)
        sv_command = 'sv.{}.uncore.cha.chas.cms.mbe_delayvalue_{}.timewindow{}.get_value()'.format(self.socketlist[0],
                                                                                                   str(delayvalue_x),
                                                                                                   str(tw_y),
                                                                                                   )
        return int(eval(sv_command)[0])
    
    def get_mbadelay(self,request_socket,cos):
        delayvalue_x = int(cos/2)
        delay_y = int(cos%2)
        sv_command = sv_command = 'sv.{}.uncore.cha.chas.cms.mbe_delayvalue_{}.delay{}.get_value()'.format(self.socketlist[0],
                                                                                                           str(delayvalue_x),
                                                                                                           str(delay_y),
                                                                                                           )
        return int(eval(sv_command)[0])
    
    def get_base_access(self):
        access_env = str(ba.getaccess())
        if access_env == 'ipc':
            import ipccli
            return ipccli.baseaccess(), access_env
        elif access_env == 'itpii':
            import itpii
            return itpii.baseaccess(), access_env
        else:
            return ba.getglobalbase(), access_env
    
    def build_socket_list(self, request_socket=None, force_search=False):
        # None means default: all sockets
        if request_socket == None:
            socket_list = sv.socket.getSocketGroup(forceSearch=force_search)
            # we use name instead of object for building SV commands
            self.socketlist = socket_list.name
        # Get socket by group
        else:
            socket_list = namednodes.comp.ComponentGroup()
            socket = sv.socket.getSocketGroup(int(request_socket), forceSearch=force_search)
            # Skip invalid and duplicated socket_ids
            if len(socket) != 0 and socket not in socket_list:
                socket_list.append(socket)
            # end for
            # we use name instead of object for building SV commands
            self.socketlist = socket_list.name

    def reconnect_master_frame(self):
        self.itp, access_var = self.get_base_access()
        if access_var == 'ipc':
            self.itp.reconnect()
            self.itp.forcereconfig()
            if not self.itp.isunlocked:
                self.itp.unlock()
        elif access_var == 'itpii':
            self.itp.reconnectmasterframe()
            self.itp.forcereconfig()
            if not self.itp.isunlocked:
                self.itp.unlock()
        else:
            pass

def findtoolpath(toolpath, toolname, dirname):
        if os.path.isfile(toolpath) and toolname == toolpath.split('/')[-1]:
            return toolpath
        for file_name in os.listdir(toolpath):
            if toolname == file_name and os.path.isfile(os.path.join(toolpath,file_name)):
                return os.path.join(toolpath, file_name)
            if os.path.isdir(os.path.join(toolpath, file_name)) and file_name == dirname:
                if os.path.exists(os.path.join(toolpath,file_name,toolname)):
                    return os.path.join(toolpath,file_name,toolname)
                else:
                    for file in os.listdir(os.path.join(toolpath,file_name)):
                        if os.path.exists(os.path.join(toolpath,file_name,file,toolname)):
                            return os.path.join(toolpath,file_name,file,toolname)

def cmd_stresstool(toolpath='/home', toolname = None, core = None, cachesize = None, request_socket = None):
    if toolname == 'stream':
        streampath = findtoolpath(toolpath,'stream', 'STREAM-master')
        cmd = 'taskset -c {} {} &'.format(core, streampath)
    elif toolname == 'memtester':
        memtesterpath = findtoolpath(toolpath,'memtester', 'memtester-4.3.0')
        cmd = 'taskset -c {} {} {}M > /dev/tmp &'.format(core, memtesterpath, cachesize)
    elif toolname == 'mlc':
        mlcpath = findtoolpath(toolpath,'mlc_internal', 'mlc_v3.7')
        cmd = '{} --loaded_latency --max_bandwidth -d0 -W6 -k{} -t1000000 -j{} -T &'.format(mlcpath,core,request_socket)
    elif toolname == 'membw':
        membwpath = findtoolpath(toolpath, 'membw', 'membw')
        cmd = '{} -c {} -b 20000 --nt-write &'.format(membwpath,core)
    os.popen(cmd)



class StressTools(threading.Thread):
    def __init__(self, toolpath='/home', toolname = None, core = None, cachesize = None, request_socket = None, traffic = 'W6'):
        threading.Thread.__init__(self)
        self.toolpath = toolpath
        self.toolname = toolname
        self.core = core
        self.cachesize = cachesize
        self.running_flag = True
        self.output = None
        self.request_socket = request_socket
        self.traffic = traffic
    
    def run(self):
        self.running_flag = True
        if self.toolname == 'stream':
            streampath = self.findtoolpath(self.toolpath,'stream', 'STREAM-master')
            cmd = 'taskset -c {} {}'.format(self.core, streampath)
        elif self.toolname == 'memtester':
            memtesterpath = self.findtoolpath(self.toolpath,'memtester', 'memtester-4.3.0')
            cmd = 'taskset -c {} {} {}M > /dev/tmp'.format(self.core, memtesterpath, self.cachesize)
        elif self.toolname == 'mlc':
            mlcpath = self.findtoolpath(self.toolpath,'mlc_internal', 'mlc_v3.7')
            cmd = '{} --loaded_latency -d0 -{} -k{} -t1000000 -T -b300m'.format(mlcpath,self.traffic,self.core)
        elif self.toolname == 'membw':
            membwpath = self.findtoolpath(self.toolpath, 'membw', 'membw')
            cmd = '{} -c {} -b 30000 --{}'.format(membwpath,self.core,self.traffic)
        shell = os.popen(cmd)
        self.output = shell.readlines()
        self.running_flag = False
        shell.close()        
            
    def stop(self):
        cmd = 'pkill {}'.format(self.toolname)
        os.popen(cmd)        
    
    def findtoolpath(self, toolpath, toolname, dirname):
        if os.path.isfile(toolpath) and toolname == toolpath.split('/')[-1]:
            return toolpath
        for file_name in os.listdir(toolpath):
            if toolname == file_name and os.path.isfile(os.path.join(toolpath,file_name)):
                return os.path.join(toolpath, file_name)
            if os.path.isdir(os.path.join(toolpath, file_name)) and file_name == dirname:
                if os.path.exists(os.path.join(toolpath,file_name,toolname)):
                    return os.path.join(toolpath,file_name,toolname)
                else:
                    for file in os.listdir(os.path.join(toolpath,file_name)):
                        if os.path.exists(os.path.join(toolpath,file_name,file,toolname)):
                            return os.path.join(toolpath,file_name,file,toolname)
        raise Exception('Can not find the {} path! '.format(toolname))
        
class PqosChecker():
    def __init__(self, APP_LOG):
        self.output = None
        self.mbl_position = 4
        self.cpuinfo = None
        self.max_socket = None
        self.max_core = None
        self.max_thread = None
        self.max_cos = None
        self.max_rmid = None
        self.core_persocket = None
        self.l3cache = None
        self.script_version = RDT_MBA2_SCRIPT_VERSION
        self.model = None
        self.stepping = None
        self.Numa = ''
        self.bios= None
        self.ucode = None
        self.os = None
        self.kernel = None
        self.memory = None
        self.msr = None
        self.APP_LOG = APP_LOG
        
    def monitor(self, mon_time=4, core=None):
        if not core:
            cmd = 'pqos --mon-core="all:" --mon-time={}'.format(mon_time)
        else:
            cmd = 'pqos --mon-core="all:{}" --mon-time={}'.format(core,mon_time)
        shell = os.popen(cmd)
        self.output = shell.readlines()
        cmd = 'pqos -r --mon-time=1'
        os.popen(cmd)
        shell.close()
        
    def get_mbl_position(self):
        for line in self.output:
            if 'MBL' in line:
                for index,col in enumerate(line.split()):
                    if 'MBL' in col:
                        self.mbl_position = index
                        break
                break
        
    def getmbm(self, core):
        self.monitor()
        self.get_mbl_position()
        flag = 0
        mbl = 1
        mbr = 1 
        errorflag = None
        for index,line in enumerate(self.output):
            if 'TIME' in line:
                flag += 1
            if flag == 4:
                if line.split()[0] == str(core):
                    mbl = float(line.split()[self.mbl_position])
                    mbr = float(line.split()[self.mbl_position+1])
        if mbl <= MBM_LOWER_LIMITATION:
            print(self.output)
            self.APP_LOG.info('[warning]:MBL value<={}, check fail! wait 20s for remonitor...'.format(MBM_LOWER_LIMITATION))
            time.sleep(20)
            self.monitor()
            flag = 0
            mbl = 0
            mbr = 0 
            errorflag = None
            for index,line in enumerate(self.output):
                if 'TIME' in line:
                    flag += 1
                if flag == 4:
                    if line.split()[0] == str(core):
                        mbl = float(line.split()[self.mbl_position])
                        mbr = float(line.split()[self.mbl_position+1])
            if mbl <= MBM_LOWER_LIMITATION:
                errorflag = 'MBL_readzeroerror'
        if mbl > MBM_UPPER_LIMITATION:
            self.APP_LOG.info('[error]:Get abnormal MBL {}!'.format(mbl))
            errorflag = 'MBL_overflow'
        return mbl,mbr,errorflag
    
    def getmbms(self, core):
        self.monitor(5)
        self.get_mbl_position()
        flag = 0
        mbl = 1
        mbr = 1 
        errorflag = None
        for index,line in enumerate(self.output):
            if 'TIME' in line:
                flag += 1
            if flag == 3:
                if line.split()[0] in [str(x) for x in core]:
                    mbl += float(line.split()[self.mbl_position])
                    mbr += float(line.split()[self.mbl_position+1])
        if mbl <= MBM_LOWER_LIMITATION:
            self.APP_LOG.info('[warning]:MBL value<={}, check fail! wait 20s for remonitor...'.format(MBM_LOWER_LIMITATION))
            time.sleep(20)
            self.monitor(5)
            flag = 0
            mbl = 0
            mbr = 0 
            errorflag = None
            for index,line in enumerate(self.output):
                if 'TIME' in line:
                    flag += 1
                if flag == 3:
                    if line.split()[0] in [str(x) for x in core]:
                        mbl += float(line.split()[self.mbl_position])
                        mbr += float(line.split()[self.mbl_position+1])
            if mbl <= MBM_LOWER_LIMITATION:
                errorflag = 'MBL_readzeroerror'
        if mbl > MBM_UPPER_LIMITATION*len(core):
            self.APP_LOG.info('[error]:Get abnormal MBLs {}!'.format(mbl))
            errorflag = 'MBL_overflow'
        return mbl,mbr,errorflag
    
    def displayverbose(self):
        cmd = 'pqos -D'
        shell = os.popen(cmd)
        self.output = shell.readlines()
    
    def readsysinfo(self):
        self.displayverbose()
        for line in self.output:
            if 'max rmid' in line:
                self.max_rmid = int(re.findall("(\d+\.\d+|\d+)",line)[0])
            elif 'Num COS' in line:
                self.max_cos = int(re.findall("(\d+\.\d+|\d+)",line)[0])
        self.max_socket = int(os.popen('lscpu |grep Socket |tr -cd "[0-9]"').read())
        self.core_persocket = int(os.popen('lscpu |grep "Core(s) per socket" |tr -cd "[0-9]"').read())
        self.max_core = int(os.popen('lscpu |grep "Core(s) per socket" |tr -cd "[0-9]"').read())*self.max_socket
        self.max_thread = int(os.popen('lscpu |grep "Thread(s) per core" |tr -cd "[0-9]"').read())*self.max_core
        self.cpuinfo = os.popen('lscpu |grep "Model name:" ').read().split(':')[1].strip()
        self.l3cache = os.popen('lscpu |grep "L3 cache:" ').read().split(':')[-1].strip()
        self.model = os.popen('lscpu |grep "Model:"').read().split(':')[-1].strip()
        self.stepping = os.popen('lscpu |grep "Stepping:"').read().split(':')[-1].strip()
        Numa_info = os.popen('lscpu |grep "NUMA"').readlines()
        for index,line in enumerate(Numa_info):
            if index == len(Numa_info)-1:
                self.Numa += '#'*3+line.strip()
            else:self.Numa += '#'*3+line
        self.bios = os.popen('dmidecode -s bios-version').read().strip()
        self.ucode = os.popen('grep microcode /proc/cpuinfo | uniq').read().split(':')[-1].strip()
        self.os = os.popen('cat /etc/redhat-release').read().strip()
        self.kernel = os.popen('uname -r').read().strip()
        self.memory = os.popen('cat /proc/meminfo |grep "MemTotal"').read().split(':')[-1].strip()
        msr_info = subprocess.Popen('wrmsr --version',stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        self.msr = msr_info.stderr.read().decode('utf-8').split(' ')[-1].strip()
        
    def printsysinfo(self):
        self.APP_LOG.info('#'*18+'  SYSTEM INFO  '+'#'*18)
        self.APP_LOG.info('#'*3+'RDT_MBA2.0 Script Version:{}'.format(self.script_version))
        self.APP_LOG.info('#'*3+'Model:{}'.format(self.model))
        self.APP_LOG.info('#'*3+'Model name:{}'.format(self.cpuinfo))
        self.APP_LOG.info('#'*3+'Stepping:{}'.format(self.stepping))
        self.APP_LOG.info('#'*3+'BIOS:{}'.format(self.bios))
        self.APP_LOG.info('#'*3+'Ucode:{}'.format(self.ucode))
        self.APP_LOG.info('#'*3+'OS:{}'.format(self.os))
        self.APP_LOG.info('#'*3+'kernel:{}'.format(self.kernel))
        self.APP_LOG.info('#'*3+'Core Number:{}'.format(self.max_core))
        self.APP_LOG.info('#'*3+'Thread Number:{}'.format(self.max_thread))
        self.APP_LOG.info('#'*3+'Socket Number:{}'.format(self.max_socket))
        self.APP_LOG.info(self.Numa)
        self.APP_LOG.info('#'*3+'Memory Size:{}'.format(self.memory))
        self.APP_LOG.info('#'*3+'Max COSID:{}'.format(self.max_cos))
        self.APP_LOG.info('#'*3+'Max RMID:{}'.format(self.max_rmid))
        self.APP_LOG.info('#'*3+'L3 cache size:{}'.format(self.l3cache))
        self.APP_LOG.info('#'*3+'Msr-tool version:{}'.format(self.msr))
        self.APP_LOG.info('#'*50)  
        
    def refresh(self):
        cmd = 'pqos -r --mon-time=1'
        shell = os.popen(cmd)
        self.output = shell.readlines()
    
    def reset(self):
        cmd = 'pqos -R'
        shell = os.popen(cmd)
        self.output = shell.readlines()
        
    def getmbm_count(self, core, number):
        totalmbl = 0
        totalmbr = 0
        for i in range(number):
            mbl_, mbr_ = self.getmbm(core)
            totalmbl += mbl_
            totalmbr += mbr_
        totalmbl = totalmbl/number
        totalmbr = totalmbr/number
        return totalmbl, totalmbr        
        
    def bindllc(self, cos, core):
        cmd = 'pqos -a "llc:{}={}"'.format(cos,core)
        shell = os.popen(cmd)
        self.output = shell.readlines()
        self.APP_LOG.info('Bind llc command:{}'.format(cmd))
    
    def bindllcs(self, cos, core):
        cmd = 'pqos -a "llc:{}={}-{}"'.format(cos,core[0],core[-1])
        shell = os.popen(cmd)
        self.output = shell.readlines()
        self.APP_LOG.info('Bind llc command:{}'.format(cmd))
        
    def bindmba(self, cos, request_socket, throttlepercent):
        cmd = 'pqos -e "mba@{}:{}={}"'.format(request_socket,cos,throttlepercent)
        shell = os.popen(cmd)
        self.output = shell.readlines()
        self.APP_LOG.info('Bind MBA command:{}'.format(cmd))

    