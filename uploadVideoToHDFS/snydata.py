# coding=utf-8
'''
Created on 2016.10.3

@author: gyy
'''
import logging
import MySQLdb
import threading
import string
import time
########mysql的配置信息####################
mysql_user="root"
mysql_passwd="1q2w3e4r"
mysql_database="vscp"
mysql_port=3306
mysql_host="10.103.242.97"

########################################
logger = logging.getLogger('monitor')

class backupServer(threading.Thread):

    def __init__(self, data, tableKeeper):
        threading.Thread.__init__(self)
        self.__data = data

        self.__tableKeeper = tableKeeper

    #格式化为tuple格式数据(f_name, size, format, start_time, total_time, channel)
    def __formatData(self,data):
        # tableName, f_name, size, format, start_time, total_time, channel
        return (data[0], data[1], data[2], data[3], data[4], data[5], data[6])

    def run(self):
        dataTmp = self.__data

        #local function for insert data to db
        def __insertDataToDB():
            conn = self.__tableKeeper.getconnect()
            if conn:
                cur = conn.cursor()
                if type(dataTmp) is list:
                    for item in self.__data:
                        formatData = self.__formatData(item)
                        print formatData
                        if self.__tableKeeper.getTableName(conn, item[0]):
                            cur.execute('''insert into %s(f_name, size, format, start_time, total_time, channel) values('%s','%s', '%s', '%s', '%s', '%s')'''%formatData)
                            conn.commit()#Submit to database for execute
                            logger.info('insert current videofiles info to table %s ...'%item[0])
                elif type(dataTmp) is tuple:
                    formatData = self.__formatData(dataTmp)
                    print formatData
                    if self.__tableKeeper.getTableName(conn, dataTmp[0]):
                        cur = conn.cursor()
                        cur.execute('''insert into %s(f_name, size, format, start_time, total_time, channel) values('%s','%s', '%s', '%s', '%s', '%s')'''%formatData)
                        conn.commit()
                        logger.info('insert current videofiles info to table %s ...'%item[0])
                else:
                    pass

                cur.close()#close cursor
                if len(dataTmp):
                    logger.info('insert videofiels info in dataQue to db successfully.')
            try:
                __insertDataToDB()
            except (AttributeError, MySQLdb.OperationalError): # Lost connection to MySQL server during query
                self.__tableKeeper.close()
                __insertDataToDB()

        #close current db connect
        self.__tableKeeper.close()

class tableKeeper():
    def __init__(self):
        self.__connect=None

    def  getconnect(self):
        if self.__connect and self.__connect.open==True:
            return self.__connect

        connTime = 0
        conn = None
        while not conn and connTime < 6:
            connTime += 1
            try:
                conn=MySQLdb.Connect(host = mysql_host,
                                     user = mysql_user,
                                   passwd = mysql_passwd,
                                       db = mysql_database,
                                     port = mysql_port)
            except MySQLdb.Error, e:
                print "Error %d:%s" % (e.args[0], e.args[1]), "try again to get connect %d" % connTime
            time.sleep(3)
        return conn

    def close(self):
        if self.__connect and self.__connect.open==True:
            self.__connect.close()

    def __check(self, conn, tableName):

        #Testing whether table is existed , andcreate it if not existed
        if conn:
            cur=conn.cursor()
            res=cur.execute("show tables like '%s'"%tableName)
            logger.info("table %s not exists, create it.."%(tableName))
            if not res:
                cur.execute(''' CREATE TABLE `%s` (
                              `f_name` varchar(100) NOT NULL,
                              `size` varchar(50) NOT NULL,
                              `format` varchar(50) NULL,
                              `start_time` varchar(50) NULL,
                              `total_time` varchar(50) NULL,
                              `channel` varchar(50) NOT NULL,
                              PRIMARY KEY (`f_name`)
                            ) ENGINE=InnoDB '''%tableName)
            conn.commit()
            cur.close()
            return tableName
        return None

    def getTableName(self, conn, tableName):
        return self.__check(conn, tableName)

'''
if __name__ =="__main__":


    data=[("ch101_20161007", "201413-13-13.flv", "1201.00", "flv", "12011201 120:1201", "232.00", "ch101")]
    tableKeeper = tableKeeper()
    con = tableKeeper.getconnect()
    threads=backupServer(data, tableKeeper)
    threads.start();


    # con=MySQLdb.Connect(host="10.103.242.128",user="root",passwd="1q2w3e4r",port=3306,db="vscp")
    # cur=con.cursor()
    # cur.execute("show databases")
    # print cur.fetchall()
    # cur.close()
    # con.close()
'''
