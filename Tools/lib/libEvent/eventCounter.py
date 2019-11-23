#!/bin/python
# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2018 Baidu.com, Inc. All Rights Reserved
#
################################################################################
"""
Authors: fengxiaomeng01(fengxiaomeng01@baidu.com)
Date:    2018/11/06 12:35:06
"""

import os
import time
import logging
import re
from Tools.lib.libEvent.sqlExecute import Sql

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s #: %(message)s',
                    )


class Counter(object):
    """
    功能:用于统计测试过程中的事件
    """

    def __init__(self, devices, deviceToFolder, deviceToDest, deviceToRom):
        self.deviceToFolder = deviceToFolder  # deviceToFolder的形式。eg {"HAOWST":"HAOWST/2019_03_14_57", "6SEDWEWES":"6SEDWEWES/2019_03_14_57"}, 可以在这里获得许多重要信息，比如测试设备，开始时间（可以作为一个标签）
        self.deviceToDestination = deviceToDest  # 测试设备对应的测试目的.eg {"HAOWST":"swan_query", "6SEDWEWES":"shortvideo"}
        self.devices = devices  # 设备的测试列表

        logging.info("初始化event-dcs.txt文件指针为0")
        self.deviceToPointer = self.__initFilePointer()  # 记录event-count.txt文件的所读到的指针位置

        logging.info("建立dcsEvent列表")

        ts = time.strftime("%Y-%m-%d_%H:%M:%S")
        self.dataBase = Sql("Data/dcsEvent" + ts + ".db")

        logging.info("从FolderName中获得该设备的测试开始时间")
        self.startTimeDict = self.__getStartTime()

        self.deviceToRom = deviceToRom  # 设备的Rom信息

    def __initFilePointer(self):
        """
        本类的实例创建后，同时初始化下event文件的指针位置均为0
        """
        dictPointer = {}

        for deviceSerial in self.devices:
            dictPointer[deviceSerial] = 0

        return dictPointer

    def __getStartTime(self):
        """
        获得每个设备本次开始测试的时间
        """
        dictTime = {}

        for deviceSerial in self.devices:
            dictTime[deviceSerial] = self.deviceToFolder[deviceSerial].split("/")[-1]

        logging.info("获得的设备测试开始时间为：")
        logging.info(dictTime)

        return dictTime

    def __str__(self):
        return "统计事件的Counter类的实例对象"

    def filterEvent(self):
        """
        过滤对应设备的日志文件中的dcs协议事件部分
        """
        for deviceSerial in self.devices:
            logging.info("%s 设备开始过滤日志型成event-count.txt文件" % deviceSerial)
            self.__filterEvent(deviceSerial)
            time.sleep(1)

    def __filterEvent(self, deviceSerial):
        """
        过滤日志的功能，私有方法
        """
        FolderName = self.deviceToFolder[deviceSerial]  # 获得该设备日志所在的文件夹

        logName = self.__getLogName(FolderName)  # 获得日志名称

        if logName != "Null":
            os.system("cat {}/{} | grep -i -E 'notifydcshandleevent: event=send_event| - postEvent :' > {}/{} ".format(
                FolderName, logName, FolderName,
                deviceSerial + "_" + self.deviceToRom[deviceSerial] + "@#@_" + "event-count.txt"))
            logging.info("生成%s设备的event-count文件" % deviceSerial)

        else:
            logging.warning("%s设备目前没有日志文件" % deviceSerial)

    def __getLogName(self, FolderName):
        """
        获得指定FolderName文件夹下的log文件
        """
        logName = os.popen("ls -l %s | grep -i record_BaiduConcerned | awk '{print $NF}'" % FolderName).read().rstrip(
            "\n").rstrip("\r")

        return logName if logName != "" else "Null"

    def countEvent(self):
        """
        针对生成的event-count.txt文件，进行分析，并将结果写入到数据库中去
        """
        for deviceSerial in self.devices:
            event_count = self.deviceToFolder[deviceSerial] + "/" + deviceSerial + "_" + self.deviceToRom[
                deviceSerial] + "@#@_" + "event-count.txt"

            if os.path.exists(event_count):  # 如果过滤的事件文件存在，则进行处理
                logging.info("开始读取%s设备的event-count.txt文件" % deviceSerial)

                with open(event_count, "r") as fp:  # 打开事件文件

                    logging.info("文件指针跳转至%s位置开始读取" % self.deviceToPointer[deviceSerial])
                    fp.seek(self.deviceToPointer[deviceSerial])  # 将文件指针跳转到上次读取的位置

                    for event in fp.readlines():

                        (name, namespace, messageId) = self.__reg(event)  # 返回匹配的内容
                        if name is not None and namespace is not None and messageId is not None:  # 如果匹配到了内容
                            logging.info(
                                "将过滤到的一行数据 name:%s，namespace:%s，messageId:%s 写入数据表" % (name, namespace, messageId))
                            self.dataBase.insertData(deviceSerial, self.deviceToDestination[deviceSerial], \
                                                     self.startTimeDict[deviceSerial], name, namespace, messageId)

                    logging.info("更新%s设备的event-count文件的指针" % deviceSerial)
                    self.deviceToPointer[deviceSerial] = fp.tell()  # 更新读到的文件位置

    def getEventResult(self):
        """
        获得统计结果，并写到相应测试目录里
        """

        for deviceSerial in self.devices:

            result = self.dataBase.getResult(deviceSerial, self.deviceToDestination[deviceSerial],
                                             self.startTimeDict[deviceSerial])

            logging.info("从DcsEvent数据库获得的数据为：")
            logging.info(result)

            fileName = self.deviceToFolder[deviceSerial] + "/" \
                       + deviceSerial + "_" + self.deviceToRom[deviceSerial] + "@#@_dcsEvent_" + \
                       self.deviceToDestination[deviceSerial] \
                       + "_" + self.startTimeDict[deviceSerial] + "_tableInfo.txt"

            logging.info("将数据写入到文件%s中" % fileName)

            fp = open(fileName, "w")
            fp.write("name~~namespace~~pv~~percent(%)\n")  # 文件第一行为列表标题
            fp.close()

            fp = open(fileName, "a")
            for row in result:
                fp.write(row[0] + "~~" + row[1] + "~~" + str(row[2]) + "~~" + str(
                    row[3]) + "\n")  # 形如 playbacked~~ai.dueros.baidu.video_palyer~~74~~20.34
            fp.close()

    def __reg(self, content):
        """
        使用正则表达式过滤name namespace messageId
        """

        nameWord = re.compile('''
                        ^.*?                                # 匹配开头内容
                        "name":"(.*?)"                     # 匹配name的内容
                        ''', re.VERBOSE)

        nameSpaceWord = re.compile('''
                        ^.*?                                # 匹配开头内容
                        "namespace":"(.*?)"                # 匹配namespace的内容
                        ''', re.VERBOSE)

        messageIdWord = re.compile('''
                        ^.*?                                # 匹配开头内容
                        "messageId":"(.*?)"                # 匹配messageId的内容
                        ''', re.VERBOSE)

        name = nameWord.search(content)
        nameSpace = nameSpaceWord.search(content)
        messageId = messageIdWord.search(content)

        try:
            return (name.group(1), nameSpace.group(1), messageId.group(1))

        except AttributeError:
            return (None, None, None)

    def closeDataBase(self):
        """
        关闭数据库
        """

        logging.info("关闭%s连接" % str(self.dataBase))
        self.dataBase.exit()


if __name__ == "__main__":
    pass
