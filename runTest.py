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

from __future__ import division
import re
import sys
import os
import time
import traceback
import subprocess
import logging
import json
import shutil
import signal
import argparse
import getpass
import json
from threading import Timer

if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding('utf-8')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s #: %(message)s',
                    )


##########################################################################
# 方法定义区
########################################################################
def replace(deviceName):
    """
    整理deviceslist,去掉设备名称后面紧跟的'    devices'
    """
    deviceName = deviceName.replace("	device", "")
    return deviceName


def adbLog(deviceName):
    """
    采用多进程的形式，为每一个设备分配一个进程记录日志
    """
    folderName = dictDeviceToFolderName[deviceName]

    if "/" in deviceName:
        fileName = os.path.join(folderName, deviceName.split("/")[1] + "_" + dictDevicesToName[
            deviceName] + "@#@_" + "log" + timeStampStart + ".txt")  # 生成带有目录的日志文件，目录由设备决定
        fileBaiduName = os.path.join(folderName, deviceName.split("/")[1] + "_" + dictDevicesToName[
            deviceName] + "@#@_" + "record_BaiduConcerned" + timeStampStart + ".txt")  # 生成带有目录的日志文件，目录由设备决定

    else:
        fileName = os.path.join(folderName, deviceName + "_" + dictDevicesToName[
            deviceName] + "@#@_" + "log" + timeStampStart + ".txt")  # 生成带有目录的日志文件，目录由设备决定
        fileBaiduName = os.path.join(folderName, deviceName + "_" + dictDevicesToName[
            deviceName] + "@#@_" + "record_BaiduConcerned" + timeStampStart + ".txt")  # 生成带有目录的日志文件，目录由设备决定

    os.system("adb -s " + deviceName + " logcat -c")  # 记录日志之前，清理掉之前的日志
    logging.info("设备" + deviceName + "的日志保存到" + fileName)

    # 记录全日志和信息检索相关的日志
    tagLists = mInfo.getTags(deviceName)  # 过滤到初步
    dcsEventTag = "notifydcshandleevent: event=send_event"  # DuerShow系统过滤日志的关键字
    tagLists.append(dcsEventTag)

    try:
        cmd = "adb -s " + deviceName + " logcat -v threadtime | tee -a " + fileName + "| grep -i -a -E '%s' >> " % (
            '|'.join(tagLists)) + fileBaiduName
        std = subprocess.Popen(cmd, shell=True)
        logging.info("device " + deviceName + " started adb logact success! ")
    except:
        logging.warning(traceback.format_exc())  # 可能有意外情况，暂时未知

    toBeKilled.append(std)
    return std


def makeFolder(deviceName):
    """
    根据设备名称，创建对应的文件夹，tesplan文件夹，数据库存储文件夹
    """
    timeStamp = time.strftime("%Y_%m_%d_%H_%M")  # 时间戳 年_月_日
    timeStampPlan = time.strftime("%Y_%m_%d")

    if "/" in deviceName:
        deviceName = deviceName.split("/")[1]
    else:
        pass

    folderName = os.path.join(deviceName, timeStamp)  # eg: A12121231/2018-11-20

    try:
        os.system("mkdir -p " + folderName)
    except:
        pass

    try:
        os.system("mkdir -p " + os.path.join("History", timeStampPlan))
    except:
        pass

    try:
        os.system("mkdir -p Data")
    except:
        pass

    return folderName


def cpuAndMemory(deviceName):
    """
    采用多进程，为每个设备执行 cpuandmemory.sh文件
    """

    folderPath = dictDeviceToFolderName[deviceName]
    band = dictDevicesToBand[deviceName]
    dest = dictDevicesToDestination[deviceName]
    version = dictDevicesToName[deviceName]

    fileNamePre = folderPath + "/" + folderPath.split("/")[0] + "_" + version + "@#@" + "_" \
                  + band + "_" + dest + "_"

    timeStamp = time.strftime("_%Y_%m_%d_%H_%M")

    global processList, proMemorySwitch

    processListTotal = processList + privateProcess[deviceName]
    try:
        processListTotal = list(set(processListTotal.remove("")))
    except:
        pass

    processAB = " ".join(processListTotal)

    std = subprocess.Popen("sh Tools/cpuandmemory.sh " + proMemorySwitch[
        deviceName] + " " + deviceName + " " + fileNamePre + " " + timeStamp + " " + processAB, shell=True)

    toBeKilled.append(std)
    return std


def space(deviceName):
    """
    采用多进程，为每个设备执行 cpuandmemory.sh文件
    """

    folderPath = dictDeviceToFolderName[deviceName]
    band = dictDevicesToBand[deviceName]
    dest = dictDevicesToDestination[deviceName]
    version = dictDevicesToName[deviceName]

    fileNamePre = folderPath + "/" + folderPath.split("/")[0] + "_" + version + "@#@" + "_" \
                  + band + "_" + dest + "_"

    timeStamp = time.strftime("_%Y_%m_%d_%H_%M")

    global processList, proMemorySwitch

    processListTotal = processList + privateProcess[deviceName]
    try:
        processListTotal = processListTotal.remove("")
    except:
        pass

    processAB = " ".join(processListTotal)

    isUser = "y" if isUserVersion[deviceName] == True else "n"

    std = subprocess.Popen(
        "sh Tools/disk.sh " + isUser + " " + deviceName + " " + fileNamePre + " " + timeStamp + " " + processAB,
        shell=True)

    toBeKilled.append(std)
    return std


def temperature(deviceName):
    """
    用于记录设备的使用温度
    """
    timeStamp = time.strftime("%Y%m%d%H%M%S")
    folderPath = dictDeviceToFolderName[deviceName]
    band = dictDevicesToBand[deviceName]
    destination = dictDevicesToDestination[deviceName]
    band = band + "_" + destination

    if "/" in deviceName:

        tempFileName = os.path.join(folderPath, deviceName.split("/")[1] + "_" + dictDevicesToName[
            deviceName] + "@#@" + "_" + band + "_" + timeStampStart + "_tempInfo" + ".txt")
    else:
        tempFileName = os.path.join(folderPath, deviceName + "_" + dictDevicesToName[
            deviceName] + "@#@" + "_" + band + "_" + timeStampStart + "_tempInfo" + ".txt")

    try:
        Zone0 = os.popen("adb -s %s shell cat /sys/class/thermal/thermal_zone0/temp" % deviceName).read().rstrip(
            "\n").rstrip("\r")
        Zone1 = os.popen("adb -s %s shell cat /sys/class/thermal/thermal_zone1/temp" % deviceName).read().rstrip(
            "\n").rstrip("\r")
        if 4 < len(Zone0):
            Zone0 = Zone0[0:2]
            Zone1 = Zone1[0:2]
        os.system("echo {time}~~{zone1}~~{zone0} >> {filepath}".format(time=timeStamp, zone1=Zone1, zone0=Zone0,
                                                                       filepath=tempFileName))
    except:
        logging.warning(traceback.format_exc())

    Timer(60, temperature, [deviceName]).start()


def totalCpu5(deviceName, currentActivity):
    """
    通过dumpsys cpuinfo方式获得当前前5的cpu
       参数：
       currentActivity: 前台activity
    """

    timeStamp = time.strftime("%Y%m%d%H%M%S")
    folderPath = dictDeviceToFolderName[deviceName]
    band = dictDevicesToBand[deviceName]
    destination = dictDevicesToDestination[deviceName]
    band = band + "_" + destination
    global cpuNum

    if "/" in deviceName:
        tempFileName = os.path.join(folderPath, deviceName.split("/")[1] + "_" + dictDevicesToName[
            deviceName] + "@#@" + "_" + band + timeStampStart + "_totalCpuDetail" + ".txt")
        tempInfoFileName = os.path.join(folderPath, deviceName.split("/")[1] + "_" + dictDevicesToName[
            deviceName] + "@#@" + "_" + band + timeStampStart + "_totalCpuInfo" + ".txt")

    else:
        tempFileName = os.path.join(folderPath, deviceName + "_" + dictDevicesToName[
            deviceName] + "@#@" + "_" + band + timeStampStart + "_totalCpuDetail" + ".txt")
        tempInfoFileName = os.path.join(folderPath, deviceName + "_" + dictDevicesToName[
            deviceName] + "@#@" + "_" + band + timeStampStart + "_totalCpuInfo" + ".txt")

    try:
        os.system("echo ==============={time}==================== >> {filepath}".format(time=timeStamp,
                                                                                        filepath=tempFileName))
        cpuInfo = os.popen(
            "adb -s %s shell dumpsys cpuinfo | tee -a %s | grep -a -A5 'CPU usage'\
             | sed -e 's_[0-9]*/__' -e 's/%%//' -e 's/: / /' -e 's/:/-/'\
             | awk 'BEGIN{OFS=\":\";ORS=\"~~\"}NR!=1{print $2,$1/%s}'" % (
            deviceName, tempFileName, cpuNum[deviceName])).read().rstrip("\r").rstrip("\n").rstrip("~~")

        os.system("echo {time}:{activity}~~{info}>>{fileName}" \
                  .format(time=timeStamp, activity=currentActivity, info=cpuInfo, fileName=tempInfoFileName))

    except:
        logging.warning(traceback.format_exc())


def adbBugreport(deviceName, androidVersion):
    """
    抓取设备adb bugreport信息，前提是整机Free Ram 小于200M
    """

    timeStamp = time.strftime("%Y_%m_%d_%H_%M")
    folderPath = dictDeviceToFolderName[deviceName]

    # 开始抓取adb bugreport信息
    if androidVersion is not None and androidVersion <= 6:
        band = dictDevicesToBand[deviceName]
        destination = dictDevicesToDestination[deviceName]
        band = band + "_" + destination

        if "/" in deviceName:
            tempFileName = os.path.join(folderPath, deviceName.split("/")[1] + "_" + dictDevicesToName[
                deviceName] + "@#@" + "_" + band + timeStamp + "_bugreport" + ".txt")

        else:
            tempFileName = os.path.join(folderPath, deviceName + "_" + dictDevicesToName[
                deviceName] + "@#@" + "_" + band + timeStamp + "_bugreport" + ".txt")

        logging.info("%s设备抓取bugreport信息" % deviceName)
        os.system("adb -s %s bugreport &> %s" % (deviceName, tempFileName))

    elif androidVersion is not None and androidVersion > 6:  # 如果是android 7 8 9 的设备
        # 首先创建bugreport文件夹
        bugReportFolderName = folderPath + os.path.sep + "bugreport"

        if not os.path.exists(bugReportFolderName):
            os.system("mkdir -p " + bugReportFolderName)
            logging.info("创建bugreport文件夹：" + bugReportFolderName)
        else:
            pass

        logging.info("%s设备抓取bugreport信息" % deviceName)
        os.system("adb -s %s bugreport %s/." % (deviceName, bugReportFolderName))

        # 将抓取的bugreport压缩包重命名
        file_names = os.listdir(bugReportFolderName)

        if "/" in deviceName:
            temp = deviceName.split("/")[1] + "_" + dictDevicesToName[deviceName]

        else:
            temp = deviceName + "_" + dictDevicesToName[deviceName]

        for name in file_names:
            if temp not in name:
                newName = temp + "@#@_" + name
                newname = os.path.join(bugReportFolderName, newName)
                oldname = os.path.join(bugReportFolderName, name)
                logging.info("将%s文件改名为%s" % (oldname, newname))
                os.rename(oldname, newname)
            else:
                continue
    else:
        logging.warning("此时获取不到设备中的安卓版本")


def totalMemory5(deviceName):
    """
    通过dumpsys meminfo获取整机前5的memory占用率
    """

    global bugreportFlag

    # 获取安卓版本
    try:
        androidVersion = int(
            os.popen("adb -s %s shell getprop ro.build.version.release" % deviceName).read().rstrip("\n").rstrip("\r")[
                0])
    except IndexError:
        androidVersion = None

    if androidVersion is not None and androidVersion > 6:
        memoryRaw = os.popen(
            "adb -s %s shell dumpsys meminfo\
            | grep -a -A5 'by process'|sed -e 's/K://g' -e 's/,//g' | awk 'BEGIN{OFS=\"*\";ORS=\"~~\"}NR!=1{print $2,$1}'"\
            % deviceName).read().replace(
            ":", "_").replace("*", ":").rstrip("~~")
        freeRaw = os.popen(
            "adb -s %s shell dumpsys meminfo| grep -a 'Free RAM'\
            |sed -e 's/K//g' -e 's/,//g'|awk '{print $1,$2 $3}'" % deviceName).read().rstrip(
            "\n").rstrip("\r")

    elif androidVersion is not None and androidVersion <= 6:
        memoryRaw = os.popen(
            "adb -s %s shell dumpsys meminfo| grep -a -A5 'by process'\
            | awk 'BEGIN{OFS=\"*\";ORS=\"~~\"}NR!=1{print $3,$1}'" % deviceName).read().replace(
            ":", "_").replace("*", ":").rstrip("~~")
        freeRaw = os.popen(
            "adb -s %s shell dumpsys meminfo\
            | grep -a 'Free RAM'|awk '{print $1,$2 $3}'" % deviceName).read().rstrip(
            "\n").rstrip("\r")

    else:
        memoryRaw = ""
        freeRaw = ""

    memoryRaw = memoryRaw + "~~" + freeRaw

    # 如果free Ram 小于 200M，则抓取adb bugreport

    try:
        freeRawValue = int(freeRaw.split(":")[-1])
    except ValueError:  # 如果此时系统提供的数值为空字符串
        freeRawValue = None

    if isinstance(freeRawValue, int) and freeRawValue >= 200000:
        logging.info("%s设备的free Ram > 200M" % deviceName)
        bugreportFlag[deviceName] = True  # 可以执行adbBugreport函数

    elif isinstance(freeRawValue, int) and freeRawValue < 200000 and bugreportFlag[deviceName] == True:
        logging.info("%s设备 free Ram < 200M，将调用adbBugreport" % deviceName)
        adbBugreport(deviceName, androidVersion)
        bugreportFlag[deviceName] = False

    activity = os.popen(
        "adb -s %s shell dumpsys activity activities\
         | sed -En -e '/Running activities/,/Run #0/p' | awk 'NR==3{print $5}'" % deviceName).read().rstrip(
        "\n").rstrip("\r")
    timeStamp = time.strftime("%Y%m%d%H%M%S")
    timeStamp = timeStamp + ":" + activity
    folderPath = dictDeviceToFolderName[deviceName]
    band = dictDevicesToBand[deviceName]
    destination = dictDevicesToDestination[deviceName]
    band = band + "_" + destination

    if "/" in deviceName:

        tempFileName = os.path.join(folderPath, deviceName.split("/")[1] + "_" + dictDevicesToName[
            deviceName] + "@#@" + "_" + band + timeStampStart + "_totalMemoryInfo" + ".txt")
    else:
        tempFileName = os.path.join(folderPath, deviceName + "_" + dictDevicesToName[
            deviceName] + "@#@" + "_" + band + timeStampStart + "_totalMemoryInfo" + ".txt")

    try:
        os.system("echo {time}~~{result} >> {filepath}"\
                  .format(time=timeStamp, result=memoryRaw, filepath=tempFileName))
    except:
        logging.warning(traceback.format_exc())

    logging.info("%s设备抓取cpu前5的进程" % deviceName)
    totalCpu5(deviceName, activity)

    Timer(140, totalMemory5, [deviceName]).start()


def getFdInfo(deviceName, pidNum, processName):
    """
    为解决fd溢出问题, 抓取fd信息
    """
    folderPath = dictDeviceToFolderName[deviceName]
    band = dictDevicesToBand[deviceName]
    destination = dictDevicesToDestination[deviceName]
    band = band + "_" + destination

    if "/" in deviceName:

        tempFileName = os.path.join(folderPath, deviceName.split("/")[1] + "_" + dictDevicesToName[
            deviceName] + "@#@" + "_" + band + "_" + processName + "_" + timeStampStart + "_deviceFd" + ".txt")
    else:
        tempFileName = os.path.join(folderPath, deviceName + "_" + dictDevicesToName[
            deviceName] + "@#@" + "_" + band + "_" + processName + "_" + timeStampStart + "_deviceFd" + ".txt")

    timeStamp = time.strftime("%Y%m%d%H%M%S")
    try:
        os.system("echo ===================={time}==================== >> {filepath}".format(time=timeStamp,
                                                                                             filepath=tempFileName))
        os.system("adb -s {sn} shell ls -la /proc/{pid}/fd/ >> {filepath}".format(sn=deviceName, pid=pidNum,
                                                                                  filepath=tempFileName))
    except:
        logging.warning(traceback.format_exc())


def pullSystemFiles(deviceName):
    """
    以一定时间间隔，将系统内的trace文件,dumphpro， smaps文件提取出来
    """

    traceFolderName = dictDeviceToFolderName[deviceName] + os.path.sep + "traces"
    dumpFolderName = dictDeviceToFolderName[deviceName] + os.path.sep + "dump"
    smapsFolderName = dictDeviceToFolderName[deviceName] + os.path.sep + "smaps"

    dest = dictDevicesToDestination[deviceName]  # 获取该设备测试目的

    if "/" in deviceName:
        temp = deviceName.split("/")[1] + "_" + dictDevicesToName[deviceName]
    else:
        temp = deviceName + "_" + dictDevicesToName[deviceName]

    if not os.path.exists(traceFolderName):
        os.system("mkdir -p " + traceFolderName)
        logging.info("创建trace文件夹：" + traceFolderName)
    else:
        pass

    if not os.path.exists(dumpFolderName):
        os.system("mkdir -p " + dumpFolderName)
        logging.info("创建dump文件夹：" + dumpFolderName)
    else:
        pass

    if not os.path.exists(smapsFolderName):
        os.system("mkdir -p " + smapsFolderName)
        logging.info("创建smaps文件夹：" + smapsFolderName)
    else:
        pass

    try:
        os.system("adb -s %s shell mkdir -p /data/local/tmp" % deviceName)
    except:
        pass

    # 进行trace文件相关操作
    try:
        os.popen("adb -s " + deviceName + " pull /data/anr/. " + traceFolderName + os.path.sep + ".")  # 需要增加判断条件
    except:
        pass

    file_names = os.listdir(traceFolderName)

    for name in file_names:
        if temp not in name:
            newName = temp + "@#@_" + name
            newname = os.path.join(traceFolderName, newName)
            oldname = os.path.join(traceFolderName, name)
            os.rename(oldname, newname)
        else:
            continue
    time.sleep(30)  # 等待30s，在进行其余操作

    processListTotal = processList + privateProcess[deviceName]
    for i in processListTotal:

        if "com." in i:  # 只有应用层应用才回去进行gc dumpheap文件
            # 首先进行gc操作,首先获得进程pid
            pid = os.popen("adb -s %s shell ps|grep -a %s$|awk '{print $2}'" % (deviceName, i)).read().rstrip(
                "\n").rstrip("\r")
            if pid == "":
                pid = os.popen("adb -s %s shell ps|grep -a %s[^:.]|awk '{print $2}'" % (deviceName, i)).read().rstrip(
                    "\n").rstrip("\r")
            if pid == "":
                pid = os.popen(
                    "adb -s %s shell ps -ef|grep -a %s[^:.]|awk '{print $2}'" % (deviceName, i)).read().rstrip(
                    "\n").rstrip("\r")
            if pid == "":
                pid = os.popen("adb -s %s shell ps -ef|grep -a %s$|awk '{print $2}'" % (deviceName, i)).read().rstrip(
                    "\n").rstrip("\r")

            # 抓取fd信息
            if isUserVersion[deviceName] == False and pid != "" and "com.baidu.launcher" == i:
                logging.info("%s设备的%s进程获取Fd信息" % (deviceName, i))
                getFdInfo(deviceName, pid, i)
                time.sleep(30)

            # 进行gc操作
            if gcSwitch[deviceName] == "y":
                logging.info("%s设备的%s进程进行gc" % (deviceName, i))
                os.system("adb -s %s shell kill -10 %s" % (deviceName, pid))
                time.sleep(2)
                logging.info("%s设备的%s进程进行生成hprof文件" % (deviceName, i))

            timeStamp = time.strftime("%Y_%m_%d_%H_%M")

            # 抓取smaps文件
            if smapsSwitch[deviceName] == "y":
                logging.info("%s设备的%s进程抓取smaps文件" % (deviceName, i))
                os.popen("adb -s {} pull /proc/{}/smaps {}/{}"\
                         .format(deviceName, pid, smapsFolderName,\
                                 temp + "@#@" + "_" + i + "_smaps_" + timeStamp + ".txt"))
                time.sleep(2)

            if dumpSwitch[deviceName] == "y" and args.dumpoperate == "y" and isUserVersion[deviceName] == False:
                # 抓取进程hprof文件，该操作会使设备卡顿
                os.popen("adb -s " + deviceName + " shell am dumpheap %s /data/local/tmp/%s_%s.hprof" % (
                i, temp + "@#@_" + dest + "_" + i, timeStamp))
                time.sleep(60)

    if dumpSwitch[deviceName] == "y" and args.dumpoperate == "y" and isUserVersion[deviceName] == False:
        logging.info("%s设备的进程hprof文件pull到测试机端" % deviceName)
        cmd = "adb -s " + deviceName + " pull /data/local/tmp/. " + dumpFolderName + os.path.sep + "."
        p = subprocess.Popen(args=cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
        p.communicate()

        os.system("adb -s %s shell rm -rf /data/local/tmp/*" % deviceName)

    Timer(7200, pullSystemFiles, [deviceName]).start()


def postFiles(deviceName):
    """
    上传cpu, memeory，pid, hprof, memoryDetail, trace文件信息到web展示平台 
    """
    folderName = dictDeviceToFolderName[deviceName]
    logging.info("folderName: " + folderName)
    for folderName, subfolders, filenames in os.walk(folderName):
        for filename in filenames:
            if "_log_" not in filename and "Baidu" not in filename:

                if ".swp" in filename:
                    continue

                if filename.split("/")[-1] in curledFiles:
                    continue

                filename = os.path.join(folderName, filename)

                logging.info("上传%s" % filename)
                cmd = 'curl -F "file=@%s"\
                 http://172.20.102.249:8080/WebTestDemo_war_exploded/FileProcessingServlet' % filename
                p = subprocess.Popen(args=cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     close_fds=True)
                stdout, stderr = p.communicate()

                if "hprof" in filename or "bugreport" in filename or "smaps" in filename:
                    if "上传成功" in stdout.decode("utf-8"):
                        curledFiles.append(filename.split("/")[-1])
                        logging.info("%s文件已经上传成功，之后不在上传" % filename)

                if "上传成功" not in stdout.decode("utf-8"):
                    logging.info("%s文件上传失败" % filename)
                    logging.info("原因如下:" + stdout.decode("utf-8"))

    Timer(120, postFiles, [deviceName]).start()


def reconnect(deviceName):
    """
    为防止ip断开重新连接ip,以及检测是否记录日志的进程断掉
    """
    devices = os.popen("adb devices").read()
    logging.info("即将校验的设备：" + deviceName)
    if re.search(r"1(9|7)\d.\d{1,3}.\d{1,3}.\d{1,3}", deviceName) is not None and deviceName not in devices:
        logging.info("即将重连设备：" + deviceName)
        cmd = "adb connect " + deviceName
        os.system(cmd)

    devices = os.popen("adb devices").read()
    if deviceName in devices:
        if "logcat" not in os.popen("ps aux|grep -a %s" % deviceName).read():
            time.sleep(2)  # 等待2s再次确认
            if "logcat" not in os.popen("ps -ef|grep -a %s" % deviceName).read():
                logging.info("设备%s日志重新记录" % deviceName)
                adbLog(deviceName)

    Timer(90, reconnect, [deviceName]).start()


def getKernelLog(deviceName):
    """
    获得设备的kernel 日志
    """
    folderName = dictDeviceToFolderName[deviceName]
    band = dictDevicesToBand[deviceName]
    destination = dictDevicesToDestination[deviceName]
    band = band + "_" + destination
    timeStamp = time.strftime("%Y_%m_%d_%H_%M_%S")

    tempFolderName = os.path.join(folderName, deviceName + "_" + dictDevicesToName[
        deviceName] + "@#@" + "_" + band + "_kernel_log" + "_" + timeStamp)
    tempZipName = os.path.join(folderName, deviceName + "_" + dictDevicesToName[
        deviceName] + "@#@" + "_" + band + "_kernel_log" + "_" + timeStamp + ".zip")

    os.system("adb -s %s pull /data/log/kernel %s" % (deviceName, tempFolderName))
    os.system("zip -r %s %s" % (tempZipName, tempFolderName))
    os.system("rm -rf %s" % tempFolderName)


def postLog(deviceName):
    """
    上传日志
    """
    folderName = dictDeviceToFolderName[deviceName]

    # 将设备的kernel log提取出来
    getKernelLog(deviceName)

    for foldername, subfolders, filenames in os.walk(folderName):
        for filename in filenames:
            if "_log_" in filename:
                if ".swp" in filename:
                    continue
                if "kernel_" not in filename:
                    cmd = "zip -r " + folderName + os.path.sep + filename.split(".txt")[
                        0] + ".zip" + " " + folderName + os.path.sep + filename
                    p = subprocess.Popen(args=cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         close_fds=True)
                    p.communicate()
                filename = os.path.join(folderName, filename.split(".txt")[
                    0] + ".zip") if "kernel_" not in filename else os.path.join(folderName, filename)
                logging.info("filename:" + filename)
                os.system(
                    'curl -F "file=@%s"\
                     http://172.20.102.249:8080/WebTestDemo_war_exploded/FileProcessingServlet' % filename)
                logging.info("log传输结束")

    os.system("rm -rf %s/*.zip" % folderName)

    Timer(9600, postLog, [deviceName]).start()


def handler(signalnlu, frame):
    """
    负责杀死所有测试设备用来统计数据的进程(与设备本身无关), 结束测试
    """
    for i in toBeKilled:
        logging.info("杀死进程")
        try:
            i.terminate()
        except OSError:
            pass

    for i in devicesList:
        os.system("ps aux | grep -a %s | grep -a -v \"grep\" | awk '{print $2}' | xargs -I {} kill {}" % i)
        postLog(i)

    time.sleep(5)

    # 测试即将结束, 将告警信息发出去
    logging.info("测试即将结束, 将存储的告警信息,发送到[showh测试组]群里")
    mBoss.lastWarning()

    # 关闭数据库连接
    try:
        counter.closeDataBase()
        mInfo.exit()
    except NameError:
        pass

    logging.info("本次测试结束，程序退出")
    os._exit(0)


def countEvent():
    """
    监测日志中的dcs，事件上报
    """
    counter.filterEvent()  # 首先进行日志过滤
    counter.countEvent()  # 对日志中的事件进行统计
    counter.getEventResult()  # 把结果展示出来

    Timer(3600, countEvent).start()


def logInfo():
    """
    监测日志中的信息检索,生成文件上报数据平台
    """
    mLogParser.getInfo()

    Timer(1800, logInfo).start()


def writeIntoProfileAndMap(jsonList, startTime, deviceSerial=None, common=True):
    """
    向profile表, Map表中写入数据
    默认参数: 
            common 用于表示处理公共配置文件
            jsonList: 传入的配置文件列表
    """
    for jsonfile in jsonList:  # 针对每个配置文件, 将其信息写入到

        jsonfile = jsonfile.encode("utf-8")
        logging.info("解析%s配置文件" % json)
        with open(jsonfile, "r") as temp:  # 打开json文件
            fp = json.load(temp)

            jsonfile = jsonfile.decode("utf-8")
            file_name = jsonfile.rpartition(".")[0].rpartition("/")[2]  # 对应profile数据表中的 fileName属性
            tag = fp["Tag"]  # 对应profile数据表中的 tag属性
            way = fp["Way"]  # 对应profile数据表中的 way属性

            content = fp["Content"]  # 对应map数据表中的 keyword和note
            if True == common:
                mInfo.writeIntoProfile(file_name, tag, way, 'default', startTime)  # 向profile表中写入数据, device_no 为0,
            else:
                mInfo.writeIntoProfile(file_name, tag, way, deviceSerial, startTime)  # 向profile表中写入数据

            for k, v in content.items():  # 向map表中写入数据
                mInfo.writeIntoMap(k, v, file_name)


def patrolData():
    """
    巡视测试数据, 一小时巡视一次
    """
    mBoss.patrol()

    Timer(3600, patrolData).start()


def getFileToCheck():
    """
    获得要check的数据文件
    """
    mBoss.getFileToCheck()


if __name__ == "__main__":
    ###############################################################
    # 添加本次测试所需的开关参数，用于控制测试中的操作                 
    ###############################################################
    parser = argparse.ArgumentParser(description='''
        1:添加dumoheap总开关,如果不想配置config.json中的相关项非y
        可以使用参数方法关闭每个测试设备的dumpheap操作,即使config.json中仍然为y, -d 参数默认为y.
        执行时使用python runTest.py -d n 的方式来关闭测试过程的dumpheap操作,

        2.支持命令方式设置测试时间,-t 参数（单位小时） 默认参数12小时 

        3.指定配置文件, -c config_**.json 用户每次升级可以保留之前的配置文件复用,如果有抱错,可能是config.json有了新的功能,请对其config.json
        ''')
    parser.add_argument("-d", "--dumpoperate", default="y",
                        help="此参数若设置为非“y”，则config.json文件中的分开关将失效: python runTest.py -d n")
    parser.add_argument("-t", "--time", default=12, type=float,
                        help="测试时间参数，执行脚本的命令后追加-t+整数时间则可以控制测时长. python runTest.py -t 24")
    parser.add_argument("-c", "--config", default="config.json",
                        help="测试配置文件，执行脚本的命令后追加-c [测试配置文件]. python runTest.py -c config_**.json")

    args = parser.parse_args()

    ###############################################################
    # 向系统加载测试平台路径,                
    ###############################################################
    abpath = os.popen("pwd").read().rstrip("\n").rstrip("\r")
    sys.path.append(abpath)

    ########################################################################
    # 删除5天之前的测试日志，dump文件，smaps, bugreport, BaiduConcerned文件等                                                
    #######################################################################
    for file in ["_log_", "logDot", "dcsEvent20", "hprof", "smaps", "bugreport", "BaiduConcerned"]:
        os.system("find %s -mtime +5 -name '*%s*' -exec rm -rf {} \\;" % (abpath, file))

    #################################################################
    #  定义测试使用的列表，字典                                     
    #################################################################
    processListTemp = None
    processList = []  # 公共关注进程
    destinationList = []  # 设备测试目的列表
    privateProcess = {}  # 设备私自关注进程
    privateInfo = {}  # 设备私有的info类配置文件列表
    curledFiles = []  # 已经上传的文件
    toBeKilled = []  # 程序结束时要杀死的进程列表防止出现僵尸进程
    devicesBand = []  # 设备名
    devicesVersion = []  # 设备rom版本
    bugreportFlag = {}  # 是否抓取adb bugreport的标志位
    dumpSwitch = {}  # 记录是否dumpheap
    cpuNum = {}  # 每个设备的cpu逻辑核数
    userName = None  # 测试执行者
    rdReceiver = None  # 告警接收方的rd邮箱
    totalSwitch = {}  # 记录是否抓取totalCpuInfo totalMemoryInfo
    gcSwitch = {}  # 记录是否对应用层的程序进行gc操作
    smapsSwitch = {}  # 记录是否对应用层进程进行smaps文件抓取
    proMemorySwitch = {}  # 单进程是否取内存数据
    isUserVersion = {}  # 是否是user版本， 如果是，则不能进行dumpheap，和抓取fd操作
    commonInfoJson = []  # 所有设备共同要从日志检索的配置文件

    ###############################################################
    # 开始执行测试                                                
    ###############################################################
    logging.info("开始测试")
    logging.info("本次测试将执行%s个小时" % args.time)
    devicesList = os.popen("adb devices").read().split("\n")[1:-2]
    logging.info("初步获得设备列表: adb devices方式")
    devicesList = list(map(replace, devicesList))

    #################################################################  
    #  读取config文件中的测试设备，和关注进程, 各种开关,                      
    #################################################################
    logging.info("读取%s文件" % args.config)
    with open(args.config, "r") as fp:
        temp = json.load(fp)

        try:
            processListTemp = temp["process"]
            userName = temp["tester"]
            commonInfoJson = temp["info"]
            rdReceiver = temp["rdReceiver"]

            # 检查配置文件中是否有重复的配置文件名
            if len(commonInfoJson) != len(set(commonInfoJson)):
                logging.error("信息提取配置文件中,有重名文件,不可执行测试, 请检查'info'字段")
                os._exit(0)
        except:
            logging.warning("%s文件与最新的config.json文件结构不同,请对齐config.json" % args.config)
            os._exit(0)

        if len(userName) < 5 or userName == "baidu":
            logging.warning("'tester'字段请填写你的测试设备用户名,如果是baidu的话请, 填写你的真实姓名")
            os._exit(0)

        elif getpass.getuser() != "baidu" and getpass.getuser() != userName:
            logging.warning("'tester'字段请填写你的测试本的用户名, 如果是baidu的话,请填写你的真实姓名")
            os._exit(0)

        noUseDevices = []
        for i in devicesList:
            try:
                destinationList.append(temp[i]["dest"] + "_" + userName)
            except:  # 如果报错，说明此连接的设备不在测试计划中
                noUseDevices.append(i)  # 将该不在测试计划中的设备，加入noUseDevices列表

        for i in noUseDevices:
            devicesList.remove(i)  # 将该设备从devicesList中删除

        for i in devicesList:

            destCheck = temp[i]["dest"]
            if len(destCheck) < 8:
                logging.warning("设备%s的'dest'字段少于8个字符，请重新填写！" % i)
                os._exit(0)

            if " " in destCheck or "&" in destCheck:
                logging.warning("设备%s的'dest'字段具有空格，或者&字符, 不要带有空格和&,请重新填写!" % i)
                os._exit(0)

            try:
                privateProcessTemp = temp[i]["process"]  # 获取设备的私有关注进程
                privateProcess[i] = privateProcessTemp

                privateDumpSwitchTemp = temp[i]["dumpheap"]  # 获取设备的dumpheap开关
                dumpSwitch[i] = privateDumpSwitchTemp

                privateTotalSwitchTemp = temp[i]["total"]  # 获取设备的totalCPu,Memory开关
                totalSwitch[i] = privateTotalSwitchTemp

                privateProMemorySwitchTemp = temp[i]["proMemory"]  # 获取设备的单进程memory开关
                proMemorySwitch[i] = privateProMemorySwitchTemp

                privateGcSwitchTemp = temp[i]["gc"]  # 获取设备的gc操作开关状态
                gcSwitch[i] = privateGcSwitchTemp

                privateSmapsSwitchTemp = temp[i]["smaps"]  # 获取设备的smaps操作开关状态
                smapsSwitch[i] = privateSmapsSwitchTemp

                privateInfoTemp = temp[i]["info"]  # 获取设备的私有info 配置文件
                privateInfo[i] = privateInfoTemp

            except:
                logging.warning("%s文件与最新的config.json文件结构不同,请对齐config.json" % args.config)
                os._exit(0)

    #####################################################################  
    #  确定下要测试的设备，如果设备为0，则退出程序; 已经初始化bugreportFlag为true                  
    #####################################################################
    logging.info("完成设备过滤")
    logging.info("总共有" + str(len(devicesList)) + "个设备，分别为")
    logging.info(devicesList)
    if len(devicesList) == 0:  # 如果测试设备列表，则退出测试
        logging.warning("没有设备进入测试计划，请确认%s文件中的测试设备填写正确" % args.config)
        os._exit(0)

    bugreportFlag = dict(zip(devicesList, [True] * len(devicesList)))

    #################################################################  
    #  将测试设备与要关注的进程进行绑定, 和其cpu核数绑定                             
    #################################################################
    dictDevicesToDestination = dict(zip(devicesList, destinationList))
    for i in processListTemp:
        processList.append(i)

    cpuNum = dict(zip(devicesList, list(
        map(lambda deviceName: os.popen("adb -s %s shell cat /proc/cpuinfo | grep -a 'processor'|wc -l" % deviceName) \
            .read().rstrip("\r").rstrip("\n"), devicesList))))

    #################################################################
    #  将测试设备生成的数据，确定好rom版本和设备型号比如NV6001                
    #################################################################
    for i in devicesList:
        os.system("adb -s " + i + " shell setprop log.tag.dcslog VERBOSE")
        os.system("adb -s " + i + " root")
        if "Not" in os.popen("adb -s " + i + " remount").read():
            isUserVersion[i] = True
        else:
            isUserVersion[i] = False

        if re.search(r"1(9|7)\d.\d{1,3}.\d{1,3}.\d{1,3}", i) is not None:
            os.system("adb connect " + i)
        tempBand = os.popen("adb -s " + i + " shell getprop ro.product.model").read().rstrip("\n").rstrip("\r")
        tempVersion = os.popen(
            "adb -s " + i + \
            " shell getprop | grep -a 'description'\
             | awk -F \"]\" 'NR==1{print $2}'|awk -F \"[\" 'NR==1{print $2}' | sed -e 's/ /_/g'")\
            .read().rstrip(
            "\n").rstrip("\r").replace("(", "_").replace(")", "_")
        if " " in tempBand:
            tempBand = tempBand.split(" ")[0]
        devicesBand.append(tempBand)
        devicesVersion.append(tempVersion)

        # 将设别信息写入到
    dictDevicesToBand = dict(zip(devicesList, devicesBand))
    dictDevicesToName = dict(zip(devicesList, devicesVersion))

    #################################################################  
    #  创建本次测试的保存文件夹 保存此次测试计划到History          
    #################################################################
    folderNameList = list(map(makeFolder, devicesList))
    dictDeviceToFolderName = dict(zip(devicesList, folderNameList))
    logging.info("本次测试的设备目录文件为：")
    logging.info(dictDeviceToFolderName)

    timeStampStart = time.strftime("_%Y_%m_%d_%H_%M")
    timeStampPlan = time.strftime("%Y_%m_%d")
    timeStampHM = time.strftime("_%H_%M")

    # 将测试的config*.json文件，设备测试结果目录合并为同一个文件，写入到History文件中，
    configName = os.path.join("History", timeStampPlan, timeStampHM.lstrip("_") + "_config.json")
    shutil.copy(args.config, configName)
    with open(configName, "a") as fp:
        json.dump(dictDeviceToFolderName, fp, indent=4)

    ###################################################################
    # import Counter类, InfoWriter  Creater类
    ##################################################################
    from Tools.lib.libEvent.eventCounter import Counter  # 导入Counter类
    from Tools.lib.libFilter.writeAndSearch import Info  # 导入InfoWriter类
    from Tools.lib.libFilter.createTable import Creater  # 导入Creater类
    from Tools.lib.libFilter.logParse import LogParser  # 导入LogParser类
    from Tools.lib.libWarning.command import Boss  # 导入Boss类

    logging.info("确保生成数据库")
    mCreater = Creater()  # 初始化Creater类
    mCreater.createTable()  # 创建数据表
    del mCreater  # 创建完后删除该对象
    logging.info("删除mCreater对象")

    logging.info("创建写和读数据库对象")
    mInfo = Info()  # 初始化Info实例

    mBoss = Boss(devicesList, dictDevicesToDestination, dictDeviceToFolderName, dictDevicesToName, isUserVersion,
                 dumpSwitch, gcSwitch, userName, rdReceiver)  # 初始化Boss实例

    ####################################################################
    # 将设备信息写入logDot数据库
    ####################################################################

    writeIntoProfileAndMap(commonInfoJson, timeStampStart)  # 将公共信息检索配置文件写入profile, map数据表中

    for i in devicesList:
        mInfo.writeIntoDevice(i, dictDevicesToName[i], dictDevicesToBand[i])  # 写入device表数据
        mInfo.writeIntoTest(dictDevicesToDestination[i], userName, args.time, timeStampStart, dictDeviceToFolderName[i],
                            i)  # 写入test表数据
        writeIntoProfileAndMap(privateInfo[i], timeStampStart, i, False)  # 写入profile表, 和map表

    #################################################################
    #  利用信号机制，避免测试结束时，产生的野进程                   
    #################################################################
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGALRM, handler)
    signal.signal(signal.SIGINT, handler)

    #################################################################
    #  开始执行测试 获取cpu, memory, pid, disk space等信息                        
    #################################################################
    logging.info("start record the devices cpu and memory")
    cpuAndMemoryProcess = list(map(cpuAndMemory, devicesList))
    diskSpace = list(map(space, devicesList))

    for i in devicesList:
        Timer(1500, pullSystemFiles, [i]).start()
        Timer(72, temperature, [i]).start()

        if totalSwitch[i] == 'y':
            Timer(87, totalMemory5, [i]).start()

        Timer(100, reconnect, [i]).start()
        time.sleep(1)

    #################################################################  
    # 10s后开始记录日志，上传数据，日志，以及统计dcs事件上报        
    #################################################################
    time.sleep(10)
    logging.info("start record the devices log")
    adbLogProcess = list(map(adbLog, devicesList))
    for i in devicesList:
        Timer(10, postFiles, [i]).start()
        Timer(9600, postLog, [i]).start()

    #################################################################  
    # 创建事件分析器对象，巡视告警器,log分析器隔一定时间统计事件, 和信息上报        
    #################################################################
    counter = Counter(devicesList, dictDeviceToFolderName, dictDevicesToDestination, dictDevicesToName)
    mLogParser = LogParser(devicesList, mInfo)

    Timer(900, logInfo).start()
    Timer(1800, countEvent).start()
    Timer(10780, getFileToCheck).start()
    Timer(10800, patrolData).start()

    #################################################################  
    # 获取指定的测试时间，默认为12小时                              
    #################################################################
    dura = args.time
    signal.alarm(int(3600.0 * dura))

    while True:
        logging.info("测试中")
        time.sleep(30)
