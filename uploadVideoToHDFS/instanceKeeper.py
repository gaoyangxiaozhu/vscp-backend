# coding=utf-8
'''
Created on 2016.10.7

@author: Gyy
'''

import logging
import videoInfo
import multiprocessing
import json
import importlib
import traceback
import threading
import socket
import thread
import subprocess
import time
import os


logger = logging.getLogger('monitor')

#需要添加的soket的通信监听进程
class watchProcess(multiprocessing.Process):
    ITEMS_SIZE = 20
    SLEEP_TIME = 60
    MAX_TIME_DIFFER = 1

    __dataKeeper = None
    __dirInfo = None
    __stop_monitor_proc = None
    __ratroQueue = None #Feedback message queue
    __lockQue = None #Queue lock mechanism for __domainData data security
    __domainData = None #Data storage slot, used to store the the video file related data for the current dir
    __slotCache = None #Buffer storage area for a single sampled data
    __port = None
    __udpServer = None #UDP server for data transmission
    __dataQue = None
    __selfInitTime = None #The start time of the initialization

    def __init__(self, dirInfo, retroQue, sleepTime, dataQue): #dirInfo { 'dirname': 'xxx', 'dirpath': 'xxx'}
        multiprocessing.Process.__init__(self)
        self.__stop_monitor_proc = False
        self.__sleepTime = sleepTime
        self.__ratroQueue = retroQue
        self.__dirInfo = dirInfo
        self.__dataQue = dataQue


    def __init(self):
        #The initialization for the basic properties of  process
        self.__slotCache = []
        self.__dirname = self.__dirInfo["dirname"]
        self.__dirpath = self.__dirInfo['dirpath']
        self.__lockQue = multiprocessing.Queue()
        self.__lockQue.put("1")
        self.__dataKeeper = {"dirname":self.__dirInfo["dirname"], "dirpath": self.__dirpath}

        if self.__sleepTime:
            self.SLEEP_TIME=self.__sleepTime

    def __doMonitor(self):

        self.__slotCache = []
        videoInfo.start(self.__slotCache, self.__dataKeeper, self.__videofiles)

        if self.__slotCache and len(self.__slotCache):
            for item in self.__slotCache:
                #put using tuple form , it is need  for  storage to db
                _dataQueItem = (item['tableName'], item['f_name'], item['size'], item['format'], item['start_time'], item['total_time'], item['channel'])
                self.__dataQue.put(_dataQueItem)

        self.__slotCache = None

    def __checkNewInstances(self): #whether has new video file in current dir
        dirpath = self.__dirpath
        self.__videofiles = os.listdir(dirpath)
        if self.__videofiles and len(self.__videofiles):
            return True
        return False

    #this method is mainly responsible for provide Feedback to main process
    def __doRatroActionToMonitor(self):
        pass
        #self.__ratroQueue.put({})

    '''
    The method is responsible for calculating the time error,
    due to the long time of the query work, may cause the error within the interval time,
    the error is specific to one second
    '''

    def __checkAndDoretra(self,curSampleTime):
        if not self.__selfInitTime:
            self.__selfInitTime=curSampleTime
        else:
            timeDiffer=(curSampleTime-self.__selfInitTime)%self.SLEEP_TIME
            return timeDiffer>self.SLEEP_TIME and self.SLEEP_TIME-timeDiffer>self.SLEEP_TIME
        return False

    def getName(self):
        return self._name

    def stop(self):
        self.__stop_monitor_proc = True

    def run(self):
        self.__init()
        logger.info("start instance %s ..."%(self.getName()))
        time.sleep(0.5)
        start = time.time()
        try:
            while not self.__stop_monitor_proc:
                try:
                    if self.__checkNewInstances():
                        self.__doMonitor()

                    end=time.time()
                    time.sleep(self.SLEEP_TIME-(end-start))
                    start=time.time()
                except Exception ,e:
                    print e
                    print traceback.format_exc()
        except (KeyboardInterrupt, SystemExit):
            pass
        if self.__stop_monitor_proc:
            logger.info("%s will be shutdown ..."%(self._name))

'''
if __name__=="__main__":
    mm=["readDataModule.cpu","readDataModule.mem","readDataModule.block","readDataModule.interface"]
    name="instance-00000051"
    machinInfo={"port":23346,"name":"instance-00000032","UUID":"a483a6e0-bf48-4183-a413-7e3d3aaa1254"}
    que=multiprocessing.Queue()
    dataque=multiprocessing.Queue()
    watch=watchProcess(machinInfo,mm,que,10,dataque)
    watch.start()
'''
