# coding=utf-8
'''
Created on 2016.10.6
@Author Gyy
'''
from mylogger import logger
import instanceKeeper
import os
import re
import copy
import multiprocessing
import random
import traceback
import threading
import socket
import json
import sys
import time
import subprocess
import snydata


BaseVideoPath='../data' # the top directory path  for storage video file, default is 'data' directory

#TODO Need to add the child process socket can not communicate the parent process restart function
class monitor(multiprocessing.Process):
    __path = None;  #the base directory for video storage
    __proc_stop=False             #Process open or stop signal
    __procSleepTime=None          #Sampling interval time
    __dirInstanceNameList=None
    __dirInstanceProcInfoDict=None
    __ratroQueue=None             #Message queue for process communication
    __subSleepTime=None
    __dataQue=None #Used to collect data from each thread/Process
    __snycDataServer=None
    __instanceDirNum=None #The number of directories currently monitored ,each thread/process for each directory

    def __init__(self, procName, path, sleeptime, subProcSleepTime): #procName为当前进程名称，sleeptime主进程休眠时间，subProcSleepTime监控进程间隔时间
        multiprocessing.Process.__init__(self)
        self.__path = path or '../data'
        self.__proc_stop = False
        self.__procSleepTime = sleeptime
        self._name = procName
        self.__subSleepTime = subProcSleepTime
        self.__ratroQueue = multiprocessing.Queue()
        self.__dataQue = multiprocessing.Queue()
        self.__dirInstanceNameList = [] #dirname list eg: ['ch101', 'ch201' ...]
        self.__dirInstanceProcInfoDict = {} #{ "ch101" :{'dirname': "xx", 'dirpath':'xxx', 'startTime':'xxx', ''monitorProc':'xxx'}, 'ch201':{...} }
        self.__instanceDirNum = {"num":0}


    def __init(self):
        #Scan and add a new and not yet monitored video-storage directory to the corresponding __instanceThreadInfoDict dictionary
        #This step will also open the monitoring process for the current content of the video content monitoring
        self.__scanNewDirInstance()
        #Sync storage monitored data to database
        logger.info('init __snycDataServer class for sync data to db...')
        self.__snycDataServer = snyDataServer(self.__dataQue)

        #self.__backupserver=snydata.backupServer(self.__instanceListenPortDict,self.__mysqlHost,self.__subSleepTime)

    # close all watcher subprocess
    def __closeAllWatcherProcess(self):
        for dirname in self.__dirInstanceNameList:
            self.__closeProc(dirname)

    # close watcher subprocess according to dirname
    def __closeProc(self, dirname):

        currentDirDict = self.__dirInstanceProcInfoDict
        if currentDirDict.has_key(dirname):
            self.__instanceDirNum["num"] -= 1
            currentInstanceProc = currentDict[dirname]["'monitorProc"]
            if currentInstanceProc.is_alive():
                currentInstanceProc.terminate()
                currentDict[dirname]["'monitorProc"].join()
            del currentDirDict[dirname]
            logger.info("terminal the process %s for dir %s"%(currentInstanceProc.name, dirname))
        if self.__snycDataServer.is_alive:
            self.__snycDataServer.terminate()
            self.snyDataServer.join()
            logger.info('ternimal the proccess %s for dir %s'%(self.__snycDataServer))



    def __scanNewDirInstance(self):

        currentDirInstanceProcInfoDict = self.__dirInstanceProcInfoDict
        newDirInstanceInfoDict = self.__getNewDirInstanceInfoDict()
        toInstanceList = []
        for dirInstaceName in newDirInstanceInfoDict.keys():
            toInstanceList.append(dirInstaceName)

        #update cureent dir name list
        self.__dirInstanceNameList += toInstanceList
        #Begin to instantiate monitor process
        for toinstance in toInstanceList:
            self.__instanceDirNum["num"] += 1
            newDirInstanceInfoDict[toinstance]['startMonitorTime'] = time.time()  #Used to record the start time for current monitor process,  distinguish the age of the thread
            instanceProc = instanceKeeper.watchProcess(dataQue   = self.__dataQue,
                                                     dirInfo   = copy.deepcopy(newDirInstanceInfoDict[toinstance]),
                                                     retroQue  = self.__ratroQueue,
                                                     sleepTime = self.__subSleepTime)
            newDirInstanceInfoDict[toinstance]['monitorProc'] = instanceProc #Add a new process (monitor process for current video dir) to the maintenance queue
            currentDirInstanceProcInfoDict[toinstance] = copy.copy(newDirInstanceInfoDict[toinstance]) #Add new monitoring instance information to the list.
            try:
                instanceProc.start()

            except Exception,e:
                logger.info("can't create new instance proccess")
                print e
                print traceback.format_exc()
                instanceProc.terminate()

        del newDirInstanceInfoDict #release resources


    def __getNewDirInstanceInfoDict(self):
        currenDirInstanceNameList = self.__dirInstanceNameList
        path = self.__path
        newDirInstanceInfoDict = {}

        filenames = os.listdir(path)

        for filename in filenames:
            #if filename is already in current dir list, by other word, is already monitored , pass it
            if filename in currenDirInstanceNameList:
                continue

            full_filename = os.path.join(path, filename)
            if os.path.isdir(full_filename) and re.match('^ch', filename):
                newDirInstanceInfoDict[filename]={"dirname":filename, 'dirpath':full_filename, 'startMonitorTime': None, 'monitorProc':None }
        return newDirInstanceInfoDict

    def reInit(self):
        pass

    def run(self):
        print 'monitor process pid:', os.getpid()
        self.__init()#init

        time.sleep(2)

        self.__snycDataServer.start()

        logger.info('monitor service start...')
        try:
            while not self.__proc_stop:
                self.__scanNewDirInstance()
                que = self.__ratroQueue
                try:
                    ratroAction = que.get(True, self.__procSleepTime)
                    self.ratroDataHandler(ratroAction)
                except:
                    continue
            if self.__proc_stop:
                logger.info('begin shut down monitor ...')
                #close all sub watch process before main process exit
                self.__closeAllWatcherProcess()
        except (KeyboardInterrupt, SystemExit):
            logger.info('begin shut down monitor...')
            # close all sub watch process before main process exit
            self.__proc_stop = True
            self.__closeAllWatcherProcess()

    def getName(self):
        return self.getName()

    def setSleep(self,time):
        self.__procSleepTime = time

    def getSleep(self):
        return self.__procSleepTime

    def stop(self):
        self.__proc_stop = True

    #The method is mainly used to process the feedback from the other sub process.
    def ratroDataHandler(self, data={}):
        pass

#sync data to db
class snyDataServer(multiprocessing.Process):

    __dataQue = None #queue for submit data
    __host = None #Database host to synchronize
    __instanceNum = None
    __tableName = None

    def __init__(self, dataQueue):
        multiprocessing.Process.__init__(self)
        self.__dataQue = dataQueue
        self.__is_stop = False
        self.__tableKeeper = snydata.tableKeeper();

    def __handler(self):
        num = self.__dataQue.qsize()
        dataTmp = []
        num = 6 if num > 6 else num # only execute 6 times insert statement each cycle, avoid long time connect to  mysql  
        for i in range(num):
            data = self.__dataQue.get()
            dataTmp.append(data)
        conn = self.__tableKeeper.getconnect() #get db  connect

        #start one snycThread for storage data
        snycThread = snydata.backupServer(dataTmp, self.__tableKeeper)
        snycThread.start()

    def run(self):
        logger.info('start sync data to db sub process ...')
        try:
            while not self.__is_stop:
                try:
                    self.__handler()

                except Exception,e:
                    print e
        except (KeyboardInterrupt, SystemExit):
            pass

    def stop(self):
        self.__is_stop = True

if __name__=="__main__":
    print 'main process pid: ', os.getpid()
    mo = None
    try:
        #set the monitor process auto restart
        while True:
            if mo and mo.is_alive:
                mo.terminate()
                mo.join()
                logger.info('monitor process already exit... restart it after 4 seconds...')
                time.sleep(4)
            name = "monitor"
            main_process_time = 5
            subthread_time = 60
            mo = monitor(name, BaseVideoPath, main_process_time, subthread_time)
            logger.info('monitor process start/restart...')
            mo.start()
            mo.join()
    except (KeyboardInterrupt, SystemExit):
        if mo.is_alive:
            mo.terminate()
        time.sleep(2)
        print 'exit main process..'

    # if current monitor process exit , then clear watcher sub proecss before it exit
