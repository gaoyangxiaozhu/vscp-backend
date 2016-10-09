# coding=utf-8
'''
Created on 2016.10.7

@author: Gyy
'''

import logging
import os
import json
import string
import thread
import time
import math
import subprocess
from hdfs3 import HDFileSystem
import re

###############HDFS Controler Node #########
HOST="10.103.242.128"
PORT=9000
############################################

logger = logging.getLogger('monitor')

class videoInfo():

    __hdfsInstance = None

    def __init__(self, dataSlot, dataKeeper, videofiles):
        self.__dataSlot = dataSlot
        self.__dirpath = dataKeeper["dirpath"]
        self.__dirname = dataKeeper['dirname']
        self.__videofiles = videofiles
        self.__domainCache = []
        try:
            self.__hdfsInstance = HDFileSystem(host=HOST, port=PORT)
        except BaseException, e:
            logger.error(e)
            self.__hdfsInstance = None

    def uploadHDFS(self, localVideoPath, remotePath, filename):
        hdfs = self.__hdfsInstance
        if hdfs:
            if os.path.isfile(localVideoPath):
                #if not exists current dir path, create it
                if not hdfs.exists(remotePath):
                    logger.info('%s not exists in hdfs, create it...'%(remotePath))
                    hdfs.mkdir(remotePath)
                if not re.match('^ch', filename):
                    # if filename in localVideoPath has no 'chXXX-' prefix , then rename it when storage it in hdfs
                    filename = "-".join([self.__dirname, filename])

                hdfs.put(localVideoPath, "/".join([remotePath, filename]))
                # delete local video file
                self.removeFile(localVideoPath)

    def removeFile(self, signlefilepath):
        os.remove(signlefilepath)

    def getInfo(self):

        if not self.__hdfsInstance:#if current is not connect hdfs , try to connect
            try:
                self.__hdfsInstance = HDFileSystem(host=HOST, port=PORT)
            except BaseException, e:
                logger.error(e)
                self.__hdfsInstance = None
        if self.__hdfsInstance: # if connect success
            for filename in self.__videofiles:
                videopath=os.path.join(self.__dirpath, filename)
                child = subprocess.Popen("ffprobe -v quiet -print_format json -show_format %s"%(videopath), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                videoAttr = child.communicate()[0] #returns a tuple (stdoutdata, stderrdata) : Gets the relevant information about the current video file
                videoAttr = json.loads(videoAttr)
                dbRowData = {}

                #　the 'chxxx-' prefix in flv name can be omitted
                #　so dataTmp.group(1) dataTmp.group(2) can be None
                dataTmp = re.match('^((ch\d+)-)?(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})\.(\w+)', filename)


                if videoAttr.has_key('format') and dataTmp:
                    formatData = videoAttr['format']

                    dbRowData['tableName'] = "".join([dataTmp.group(2) or self.__dirname, "_", dataTmp.group(3),  dataTmp.group(4), dataTmp.group(5)]) #tableName eg: ch101_20161007
                    dbRowData['channel'] = dataTmp.group(2) or self.__dirname

                    dbRowData['year'] = dataTmp.group(3)
                    dbRowData['month'] = dataTmp.group(4)
                    dbRowData['day'] = dataTmp.group(5)
                    # it is important to note that the 'f_name'field in db table is the video name in hdfs , not the local video name
                    dbRowData['f_name'] = filename if re.match('^ch', filename) else "-".join([self.__dirname, filename])
                    dbRowData['format'] = formatData['format_name'] or dataTmp[9]
                    dbRowData['f_name'] = dbRowData['f_name'].replace('.' + dbRowData['format'],'') # remove filename suffix eg: 'ch101-xxx.flv' to 'ch101-xxx'
                    dbRowData['size'] = math.ceil(float(formatData['size'])/1024)

                    dbRowData['start_time'] = "%s-%s-%s %s:%s:%s"%(dataTmp.group(3), dataTmp.group(4),  dataTmp.group(5), dataTmp.group(7), dataTmp.group(7), dataTmp.group(8))
                    dbRowData['total_time'] = formatData['duration']

                    remotePath = "/".join(["/data", dbRowData['channel'], dbRowData['year'], dbRowData['month'], dbRowData['day']])

                    if dbRowData['size'] <  1.0:
                        self.removeFile(localVideoPath) #if video file size < 1M delete it from local and continue
                        continue
                    try:
                        self.uploadHDFS(videopath, remotePath, filename) #upload current video to hdfs
                        self.__dataSlot.append(dbRowData) #append video info to dataQue
                    except BaseException, e:
                        logger.error('upload err: %s'%(e))


def start(dataSlot, dataKeeper, videofiles):
    videoinfo=videoInfo(dataSlot, dataKeeper, videofiles)
    videoinfo.getInfo()

'''
if __name__=="__main__":
    dataslot=[]
    dataKeeper={"dirname":"ch101", "dirpath":"/home/gyy/Python/data/ch101/"}
    videofiles=("ch101-2016-07-08-12-32-48.flv", "ch101-2016-07-09-12-32-48.flv")

    thread.start_new_thread(start, (dataslot,dataKeeper, videofiles))
    time.sleep(5)
    print dataslot
'''
