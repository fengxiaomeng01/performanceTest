#!/usr/bin/python
# coding=utf-8

"""
该模块实现巡视告警功能
"""

import copy
import datetime
import logging
import os
import time

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s #: %(message)s',
                    )

from Tools.lib.libWarning.warn import sendHi, sendEmail
from Tools.lib.libWarning.check import (tempCheck, pidCheck, totalCpuCheck,
                                        freeRamCheck, memoryCheck, dcsEventCheck, threadCheck, sdcardCheck)


class Boss(object):
    """
    负责进行巡视
    """

    def __init__(self, devicesList, dictDeviceToDestination, dictDeviceToFolderName, \
                 dictDevicesToName, isUserVersion, dumpSwitch, gcSwitch, tester, rdReciever=None):
        self.devicesList = devicesList
        self.dictDeviceToDestination = dictDeviceToDestination
        self.dictDeviceToFolderName = dictDeviceToFolderName
        self.dictDeviceToName = dictDevicesToName
        self.dumpSwitch = dumpSwitch
        self.isUserVersion = isUserVersion
        self.gcSwitch = gcSwitch
        self.tester = tester
        self.rdReciever = rdReciever

        self.lastWarningObjectList = []

    def getFileToCheck(self):
        """
        获得要验证的数据文件
        """
        logging.info("获取%s测试设备的要check的数据文件" % self.devicesList)
        self.dictDeviceToFile = self.__fileToCheck()
        logging.info("获取的数据巡视文件为 : %s" % self.dictDeviceToFile)

    def __fileToCheck(self):
        """
        将要进行检查的文件挑选出来, cpu, memory, pid, free Ram
        """
        temp = []

        for sn in self.devicesList:
            snFiles = os.popen("ls -l " + self.dictDeviceToFolderName[sn] + \
                               "| grep -E '^-'|grep -E \
                               '_cpuInfo|_memoryInfo|_totalMemoryInfo|_sdcardInfo\
                               |_threadInfo|_pidInfo|_tempInfo|_tableInfo' | awk '{print "
                               "$NF}'").read().rstrip("\n").split("\n")

            # 只保留一个cpuInfo
            cpuNum = 0
            toBeRemove = []
            for f in snFiles:
                if f.find("_cpuInfo") != -1:
                    cpuNum += 1
                    toBeRemove.append(f)

            for fi in toBeRemove:
                if cpuNum == 1:
                    break
                snFiles.remove(fi)
                cpuNum -= 1

            temp.append(snFiles)

        return dict(zip(self.devicesList, temp))

    def patrol(self):
        """
        开始对关键性数据进行巡视
        """
        date = time.strftime("%Y-%m-%d")
        nowDateTime = datetime.datetime.now()  # 当时时刻
        allowWarningTime1 = datetime.datetime(int(time.strftime("%Y")), int(time.strftime("%m")),
                                              int(time.strftime("%d")), 8, 0, 0)
        allowWarningTime2 = datetime.datetime(int(time.strftime("%Y")), int(time.strftime("%m")),
                                              int(time.strftime("%d")), 23, 0, 0)

        for sn in self.devicesList:
            logging.info("对%s设备进行数据巡视" % sn)
            checkFiles = copy.deepcopy(self.dictDeviceToFile[sn])
            path = self.dictDeviceToFolderName[sn]
            for txt in checkFiles:
                # 检查cpuInfo数据
                logging.info("%s文件的数据将被校验" % txt)

                if txt.find("_cpuInfo") != -1:
                    result = totalCpuCheck(path + "/" + txt)
                    if "ok" != result:
                        sendEmail("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                  self.dictDeviceToName[sn], result,
                                  self.rdReciever if self.rdReciever is not None else None)
                        if nowDateTime >= allowWarningTime1 and nowDateTime <= allowWarningTime2:
                            sendHi("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                   self.dictDeviceToName[sn], result)
                        else:
                            self.lastWarningObjectList.append(
                                WarningObject(self.tester, sn, self.dictDeviceToDestination[sn],
                                              self.dictDeviceToName[sn], result, "Error"))
                        self.dictDeviceToFile[sn].remove(txt)

                # 检查memoryInfo数据
                if txt.find("memoryInfo") != -1:
                    result = memoryCheck(path + "/" + txt)
                    if "ok" != result:
                        sendEmail("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                  self.dictDeviceToName[sn], result,
                                  self.rdReciever if self.rdReciever is not None else None)
                        if nowDateTime >= allowWarningTime1 and nowDateTime <= allowWarningTime2:
                            sendHi("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                   self.dictDeviceToName[sn], result)
                        else:
                            self.lastWarningObjectList.append(
                                WarningObject(self.tester, sn, self.dictDeviceToDestination[sn],
                                              self.dictDeviceToName[sn], result, "Error"))
                        self.dictDeviceToFile[sn].remove(txt)
                        # if self.isUserVersion[sn] == False: # 出现内存泄露, 且为userDebug版本
                        #    self.gcSwitch[sn] = "y";self.dumpSwitch[sn] = "y" #进行dumpheap文件抓取

                if txt.find("totalMemoryInfo") != -1:
                    result = freeRamCheck(path + "/" + txt)
                    if "ok" != result:
                        sendEmail("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                  self.dictDeviceToName[sn], result,
                                  self.rdReciever if self.rdReciever is not None else None)
                        if nowDateTime >= allowWarningTime1 and nowDateTime <= allowWarningTime2:
                            sendHi("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                   self.dictDeviceToName[sn], result)
                        else:
                            self.lastWarningObjectList.append(
                                WarningObject(self.tester, sn, self.dictDeviceToDestination[sn],
                                              self.dictDeviceToName[sn], result, "Error"))
                        self.dictDeviceToFile[sn].remove(txt)

                if txt.find("pidInfo") != -1:
                    result = pidCheck(path + "/" + txt)
                    if "ok" != result:
                        sendEmail("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                  self.dictDeviceToName[sn], result,
                                  self.rdReciever if self.rdReciever is not None else None)
                        if nowDateTime >= allowWarningTime1 and nowDateTime <= allowWarningTime2:
                            sendHi("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                   self.dictDeviceToName[sn], result)
                        else:
                            self.lastWarningObjectList.append(WarningObject \
                                                                  (self.tester, sn, self.dictDeviceToDestination[sn],
                                                                   self.dictDeviceToName[sn], result, "Error"))
                        self.dictDeviceToFile[sn].remove(txt)

                if txt.find("_tempInfo") != -1:
                    result = tempCheck(path + "/" + txt)
                    if "ok" != result:
                        sendEmail("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                  self.dictDeviceToName[sn], result,
                                  self.rdReciever if self.rdReciever is not None else None)
                        if nowDateTime >= allowWarningTime1 and nowDateTime <= allowWarningTime2:
                            sendHi("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                   self.dictDeviceToName[sn], result)
                        else:
                            self.lastWarningObjectList.append(WarningObject \
                                                                  (self.tester, sn, self.dictDeviceToDestination[sn],
                                                                   self.dictDeviceToName[sn], result, "Error"))
                        self.dictDeviceToFile[sn].remove(txt)

                if txt.find("_dcsEvent_") != -1:
                    result = dcsEventCheck(path + "/" + txt)
                    if "ok" != result:
                        sendEmail("Warning", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                  self.dictDeviceToName[sn], result,
                                  self.rdReciever if self.rdReciever is not None else None)
                        if nowDateTime >= allowWarningTime1 and nowDateTime <= allowWarningTime2:
                            sendHi("Warning", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                   self.dictDeviceToName[sn], result)
                        else:
                            self.lastWarningObjectList.append(WarningObject \
                                                                  (self.tester, sn, self.dictDeviceToDestination[sn],
                                                                   self.dictDeviceToName[sn], result, "Warning"))
                        self.dictDeviceToFile[sn].remove(txt)

                if txt.find("_threadInfo") != -1:
                    result = threadCheck(path + "/" + txt)
                    if "ok" != result:
                        sendEmail("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                  self.dictDeviceToName[sn], result,
                                  self.rdReciever if self.rdReciever is not None else None)
                        if nowDateTime >= allowWarningTime1 and nowDateTime <= allowWarningTime2:
                            sendHi("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                   self.dictDeviceToName[sn], result)
                        else:
                            self.lastWarningObjectList.append(WarningObject \
                                                                  (self.tester, sn, self.dictDeviceToDestination[sn],
                                                                   self.dictDeviceToName[sn], result, "Error"))
                        self.dictDeviceToFile[sn].remove(txt)

                if txt.find("_sdcardInfo") != -1:
                    result = sdcardCheck(path + "/" + txt)
                    if "ok" != result:
                        sendEmail("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                  self.dictDeviceToName[sn], result,
                                  self.rdReciever if self.rdReciever is not None else None)
                        if nowDateTime >= allowWarningTime1 and nowDateTime <= allowWarningTime2:
                            sendHi("Error", self.tester, sn, self.dictDeviceToDestination[sn], date,
                                   self.dictDeviceToName[sn], result)
                        else:
                            self.lastWarningObjectList.append(WarningObject \
                                                                  (self.tester, sn, self.dictDeviceToDestination[sn],
                                                                   self.dictDeviceToName[sn], result, "Error"))
                        self.dictDeviceToFile[sn].remove(txt)

    def lastWarning(self):
        """
        测试即将结束, 将保存起来的告警信息,发到hi里去
        """
        date = time.strftime("%Y-%m-%d")
        for ob in self.lastWarningObjectList:
            sendHi(ob.level, ob.tester, ob.sn, ob.dest, date, ob.rom, ob.result)


class WarningObject(object):
    """
    暂时用于保存告警信息, 如果不在允许时间,先保存起来.最后测试结束一定要发出去
    """

    def __init__(self, tester, sn, dest, rom, result, level):
        self.tester = tester
        self.sn = sn
        self.dest = dest
        self.rom = rom
        self.result = result
        self.level = level


if __name__ == '__main__':
    # mBoss = Boss(["3F182012F3271E18"],{"3F182012F3271E18":"告警机制调试"}, {"3F182012F3271E18":"/Users/fengxiaomeng01/Downloads/duerTest1s/3F182012F3271E18/2019_09_10_20_54"},  {"3F182012F3271E18":"octopus_f1-eng_6.0.1_MMB29M_20190902_release-key"}, {"3F182012F3271E18":"y"},{"3F182012F3271E18":"y"},{"3F182012F3271E18":"y"},"fengxiaomeng01")
    # mBoss.patrol()
    # time.sleep(10)
    # mBoss.lastWarning()
    pass
