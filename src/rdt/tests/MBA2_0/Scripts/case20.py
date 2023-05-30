# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 10:14:05 2020

@author: leirong
"""
import argparse
import time
import os
import sys
import random
import logging
from common import toolbox
from testmodule import PqosChecker
from testmodule import PySVStartTool
from testmodule import StressTools
from testmodule import TERMINATE_ERROR
curPath = os.path.abspath(os.path.dirname(__file__))
sys.path.append(curPath)
sys.path.append("./")
if not os.path.exists(os.path.join(curPath,"log")):
    os.makedirs(os.path.join(curPath,"log"))
APP_NAME = 'case20'
log_doc = os.path.join(curPath,'log')
log_path=os.path.join(curPath,'log',APP_NAME + "_" + time.strftime("%Y-%m-%d_%H-%M-%S",time.localtime()) + '.log')
# Init logging for itself to track execution status
console = logging.StreamHandler()
console.setLevel(logging.INFO)
APP_LOG = toolbox.getLogger(APP_NAME)
APP_LOG.setFile(log_path)
APP_LOG.addHandler(console)
    
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--stress_tool_path', 
                            help='Path of stress tool, default is /home/',
                            dest='stress_tool_path',
                            default='/home')
    arg_parser.add_argument('-t','--toolname', 
                            help='specify stress tool',
                            dest='toolname',
                            default='membw')
    arg_parser.add_argument('-f','--traffic', 
                            help='traffic type of stress tool',
                            dest='traffic',
                            default='nt-write')
    args = arg_parser.parse_args()
    #start pysvtool
    svstart = PySVStartTool(APP_LOG)
    #start pqos checker
    pqos = PqosChecker(APP_LOG)
    pqos.reset()
    pqos.refresh()
    #Read System info
    pqos.readsysinfo()
    pqos.printsysinfo()
    #case13 initial
    APP_LOG.info('='*50)
    APP_LOG.info('='*19+'  '+APP_NAME+'  '+'='*19)
    APP_LOG.info('='*50)
    successcount = 0
    failcount = 0
    restartnumber = 0
    maxcos = pqos.max_cos
    maxdelay = None
    cos = random.sample(range(1,pqos.max_cos), 2)
    request_socket = random.randint(0, pqos.max_socket-1)
    core1 = [x for x in range(request_socket*pqos.core_persocket+2,request_socket*pqos.core_persocket+int(pqos.core_persocket/2)+1)]
    core2 = [x for x in range(request_socket*pqos.core_persocket+int(pqos.core_persocket/2)+1,request_socket*pqos.core_persocket+pqos.core_persocket)]
    uncorefreq = 14
    mbmcount = 3
    mbl0 = []
    mbl1 = []
    deviation_max = []
    deviation_cascade = []
    throttlepercentlist=[100,90,80,70,60,50,40,30,20,10]
    # throttlepercentlist=[100,90]
    svstart.build_socket_list(request_socket)
    k=0
    #setup stress tool
    if args.toolname:
        toolname = args.toolname
    else:
        toollist = ['mlc','membw']
        toolname = random.sample(toollist, 1)[0]
    cachesize = 100
    if args.traffic :
        traffic = args.traffic
    else:
        trafficlist = ['W6']
        if toolname == 'mlc':
            traffic = random.sample(trafficlist, 1)[0]
        else:
            traffic = random.sample(['nt-write'],1)[0]
    #set uncore frequency
    # svstart.change_uncorefreq(0, uncorefreq)
    # svstart.change_uncorefreq(1, uncorefreq)
    ####start####
    mbavalid = 1
    fastvalid = 1
    mode = 1#maxmode:1, cascademode:0
    if mode:
        modename = 'maxmode'
    else: modename = 'cascademode'
    svstart.change_mbavalid(request_socket, mbavalid)
    svstart.change_fastvalid(request_socket, fastvalid)
    svstart.change_mode(request_socket, mode)
    with open(os.path.join(log_doc,'{}_resultmax.log'.format(APP_NAME)),'w') as file:
        file.write('stresstool:{}, traffic:{}\n'.format(toolname,traffic))
        file.write('COSA Percent\\COSB Percent\t')
        for throttlepercent in throttlepercentlist:
            file.write(str(throttlepercent)+'\t'+str(throttlepercent)+'\t'+'Ratio_A/B\texpect_A/B\ttotal\tA/total\texpect_A/total\tA_deviation\tB/total\texpect_B/total\tB_deviation\t')
        file.write('\n')
        for throttlepercent1 in throttlepercentlist:
            file.write(str(throttlepercent1)+'\t')
            for throttlepercent2 in throttlepercentlist:
                time.sleep(20)
                APP_LOG.info('-'*50)
                APP_LOG.info('[test info]>>Start cycle:{}/{}, parameter mode:regular, MBA Mode:{}, test tool:{} {}'.format(k+1, len(throttlepercentlist)*len(throttlepercentlist)*2,modename,toolname,traffic))
                APP_LOG.info('[pqos info]>>Socket:{} logic CoreA:{}-{} COSA:{} Throttle Percent:{}% || logic CoreB:{}-{} COSB:{} Throttle Percent:{}% '.format(request_socket,core1[0],core1[-1],cos[0],throttlepercent1,core2[0],core2[-1],cos[1],throttlepercent2))
                    
                #run stresstool
                stresstool = []
                for core in core1:
                    stresstool.append(StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic))
                    stresstool[-1].setDaemon(True)
                    stresstool[-1].start()
                for core in core2:
                    stresstool.append(StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic))
                    stresstool[-1].setDaemon(True)
                    stresstool[-1].start()
                #Reset to default MBA setting 
                pqos.reset()
                pqos.bindllcs(cos[0], core1)
                pqos.bindmba(cos[0], request_socket, throttlepercent1)
                pqos.bindllcs(cos[1], core2)
                pqos.bindmba(cos[1], request_socket, throttlepercent2)
                pqos.refresh()
                time.sleep(2)
                mbl_core1,mbr_core1,errorflag1 = pqos.getmbms(core1)
                time.sleep(5)
                pqos.refresh()
                mbl_core2,mbr_core2,errorflag2 = pqos.getmbms(core2)
                APP_LOG.info('Stress A MBL value:{}'.format(mbl_core1))
                APP_LOG.info('Stress B MBL value:{}'.format(mbl_core2))
                total_mbl = mbl_core1+mbl_core2
                total_percent = throttlepercent1+throttlepercent2
                
                if throttlepercent1 <= throttlepercent2:
                    APP_LOG.info('[test result]>>Throttle Ratio target:{}  result:{}'.format(round(throttlepercent1/throttlepercent2,2),round(mbl_core1/mbl_core2,2)))
                    deviation_max.append(round(100*(mbl_core1/total_mbl-throttlepercent1/total_percent),2))
                    file.write(str(mbl_core1)+'\t'+
                               str(mbl_core2)+'\t'+
                               str(round(100*mbl_core1/mbl_core2,2))+'%\t'+
                               str(round(100*throttlepercent1/throttlepercent2,2))+'%\t'+
                               str(total_mbl)+'\t'+
                               str(round(100*mbl_core1/total_mbl,2))+'%\t'+
                               str(round(100*throttlepercent1/total_percent,2))+'%\t'+
                               str(deviation_max[-1])+'%\t'+
                               str(round(100*mbl_core2/total_mbl,2))+'%\t'+
                               str(round(100*throttlepercent2/total_percent))+'%\t'+
                               str(round(100*(mbl_core2/total_mbl-throttlepercent2/total_percent),2))+'%\t')
                else:
                    APP_LOG.info('[test result]>>Throttle Ratio target:{}  result:{}'.format(round(throttlepercent2/throttlepercent1,2),round(mbl_core2/mbl_core1,2)))
                    deviation_max.append(round(100*(mbl_core1/total_mbl-throttlepercent1/total_percent),2))
                    file.write(str(mbl_core1)+'\t'+
                               str(mbl_core2)+'\t'+
                               str(round(100*mbl_core2/mbl_core1,2))+'%\t'+
                               str(round(100*throttlepercent2/throttlepercent1,2))+'%\t'+
                               str(total_mbl)+'\t'+str(round(100*mbl_core1/total_mbl,2))+'%\t'+
                               str(round(100*throttlepercent1/total_percent,2))+'%\t'+
                               str(deviation_max[-1])+'%\t'+
                               str(round(100*mbl_core2/total_mbl,2))+'%\t'+
                               str(round(100*throttlepercent2/total_percent))+'%\t'+
                               str(round(100*(mbl_core2/total_mbl-throttlepercent2/total_percent),2))+'%\t')
                k+=1
                for tool in stresstool:
                    tool.stop()
                if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                    APP_LOG.info('Find error in test, early terminate!')
                    APP_LOG.info('[warning]Please reboot system, then retest this case!')
                    sys.exit(1)
            file.write('\n')
    mbavalid = 1
    fastvalid = 1
    mode = 0#maxmode:1, cascademode:0
    if mode:
        modename = 'maxmode'
    else: modename = 'cascademode'
    svstart.change_mbavalid(request_socket, mbavalid)
    svstart.change_fastvalid(request_socket, fastvalid)
    svstart.change_mode(request_socket, mode)
    with open(os.path.join(log_doc,'{}_resultcascade.log'.format(APP_NAME)),'w') as file:
        file.write('stresstool:{}, traffic:{}\n'.format(toolname,traffic))
        file.write('COSA Percent\\COSB Percent\t')
        for throttlepercent in throttlepercentlist:
            file.write(str(throttlepercent)+'\t'+str(throttlepercent)+'\t'+'Ratio_A/B\texpect_A/B\ttotal\tA/total\texpect_A/total\tA_deviation\tB/total\texpect_B/total\tB_deviation\t')
        file.write('\n')
        for throttlepercent1 in throttlepercentlist:
            file.write(str(throttlepercent1)+'\t')
            for throttlepercent2 in throttlepercentlist:
                time.sleep(20)
                APP_LOG.info('-'*50)
                APP_LOG.info('[test info]>>Start cycle:{}/{}, parameter mode:regular, MBA Mode:{}, test tool:{} {}'.format(k+1, len(throttlepercentlist)*len(throttlepercentlist)*2,modename,toolname,traffic))
                APP_LOG.info('[pqos info]>>Socket:{} logic CoreA:{}-{} COSA:{} Throttle Percent:{}% || logic CoreB:{}-{} COSB:{} Throttle Percent:{}% '.format(request_socket,core1[0],core1[-1],cos[0],throttlepercent1,core2[0],core2[-1],cos[1],throttlepercent2))
                    
                #run stresstool
                stresstool = []
                for core in core1:
                    stresstool.append(StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic))
                    stresstool[-1].setDaemon(True)
                    stresstool[-1].start()
                for core in core2:
                    stresstool.append(StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic))
                    stresstool[-1].setDaemon(True)
                    stresstool[-1].start()
                #Reset to default MBA setting 
                pqos.reset()
                pqos.bindllcs(cos[0], core1)
                pqos.bindmba(cos[0], request_socket, throttlepercent1)
                pqos.bindllcs(cos[1], core2)
                pqos.bindmba(cos[1], request_socket, throttlepercent2)
                pqos.refresh()
                time.sleep(2)
                mbl_core1,mbr_core1,errorflag1 = pqos.getmbms(core1)
                time.sleep(5)
                pqos.refresh()
                mbl_core2,mbr_core2,errorflag2 = pqos.getmbms(core2)
                APP_LOG.info('Stress A MBL value:{}'.format(mbl_core1))
                APP_LOG.info('Stress B MBL value:{}'.format(mbl_core2))
                total_mbl = mbl_core1+mbl_core2
                total_percent = throttlepercent1+throttlepercent2
                
                if throttlepercent1 <= throttlepercent2:
                    APP_LOG.info('[test result]>>Throttle Ratio target:{}  result:{}'.format(round(throttlepercent1/throttlepercent2,2),round(mbl_core1/mbl_core2,2)))
                    deviation_cascade.append(round(100*(mbl_core1/total_mbl-throttlepercent1/total_percent),2))
                    file.write(str(mbl_core1)+'\t'+
                               str(mbl_core2)+'\t'+
                               str(round(100*mbl_core1/mbl_core2,2))+'%\t'+
                               str(round(100*throttlepercent1/throttlepercent2,2))+'%\t'+
                               str(total_mbl)+'\t'+
                               str(round(100*mbl_core1/total_mbl,2))+'%\t'+
                               str(round(100*throttlepercent1/total_percent,2))+'%\t'+
                               str(deviation_cascade[-1])+'%\t'+
                               str(round(100*mbl_core2/total_mbl,2))+'%\t'+
                               str(round(100*throttlepercent2/total_percent))+'%\t'+
                               str(round(100*(mbl_core2/total_mbl-throttlepercent2/total_percent),2))+'%\t')
                else:
                    APP_LOG.info('[test result]>>Throttle Ratio target:{}  result:{}'.format(round(throttlepercent2/throttlepercent1,2),round(mbl_core2/mbl_core1,2)))
                    deviation_cascade.append(round(100*(mbl_core1/total_mbl-throttlepercent1/total_percent),2))
                    file.write(str(mbl_core1)+'\t'+
                               str(mbl_core2)+'\t'+
                               str(round(100*mbl_core2/mbl_core1,2))+'%\t'+
                               str(round(100*throttlepercent2/throttlepercent1,2))+'%\t'+
                               str(total_mbl)+'\t'+str(round(100*mbl_core1/total_mbl,2))+'%\t'+
                               str(round(100*throttlepercent1/total_percent,2))+'%\t'+
                               str(deviation_cascade[-1])+'%\t'+
                               str(round(100*mbl_core2/total_mbl,2))+'%\t'+
                               str(round(100*throttlepercent2/total_percent))+'%\t'+
                               str(round(100*(mbl_core2/total_mbl-throttlepercent2/total_percent),2))+'%\t')
                k+=1
                for tool in stresstool:
                    tool.stop()
                if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                    APP_LOG.info('Find error in test, early terminate!')
                    APP_LOG.info('[warning]Please reboot system, then retest this case!')
                    sys.exit(1)
            file.write('\n')
    dev_max_total=0
    dev_cascade_total=0
    countflag=0
    percentrange = 10
    countnum = 0 
    all_total_max = 0
    all_total_cascade = 0
    for index,val in enumerate(deviation_max):
        all_total_max +=abs(deviation_max[index])
        all_total_cascade += abs(deviation_cascade[index])
        if countflag<percentrange:
            dev_max_total+=abs(deviation_max[index])
            dev_cascade_total+=abs(deviation_cascade[index])
            countnum+=1
        if countflag==9:
            countflag=-1
            percentrange-=1
        countflag+=1
    average_max_deviation = round(dev_max_total/countnum,3)
    average_cascade_deviation = round(dev_cascade_total/countnum,3)
    APP_LOG.info('#'*18+'  Test End  '+'#'*18)
    APP_LOG.info('Total test count:{}'.format(k))
    APP_LOG.info('Max mode total deviation:{}, sub total deviation:{} for percent range: COSA percent + COSB percent > 100%'.format(round(all_total_max,3), round(dev_max_total,3)))
    APP_LOG.info('Cascade mode total deviation:{}, sub total deviation:{} for percent range: COSA percent + COSB percent > 100%'.format(round(all_total_cascade,3), round(dev_cascade_total,3)))
    if average_cascade_deviation*0.1 < average_max_deviation - average_cascade_deviation:
        APP_LOG.info('Test pass! Average Max mode deviation is larger than Cascade mode')
    else:
        APP_LOG.info('Test fail! Average Max mode deviation is lower than Cascade mode')