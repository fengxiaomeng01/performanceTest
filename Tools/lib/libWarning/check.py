#!/usr/bin/python
# coding=utf-8
################################################################################
#
# Copyright (c) 2018 Baidu.com, Inc. All Rights Reserved
#
################################################################################
"""
Authors: fengxiaomeng01(fengxiaomeng01@baidu.com)
Date:    2018/11/06 12:35:06
"""

import functools
import math
import os
import re


def pidCheck(pid_path):
    """
    传递pid文件的绝对路径，判断pid信息是否发生变化
    """
    # 获取进程名
    pidFileName = pid_path.split("/")[-1]
    progressName = re.search(r"^.*_(.+?)_20\d{2}_\d{2}", pidFileName).group(1)

    # 定义检查结果
    pid_normal = "ok"
    pid_error = progressName + "的Pid发生变化"

    # 初步获得pid原始数据
    pid = os.popen("cat " + pid_path + " | awk -F \"~~\" '{print $2}'").read().rstrip("\n").split("\n")

    # 开始判断 
    pid_Info = list(set(pid))
    if "" in pid_Info:
        pid_Info.remove("")

    pid_change = len(pid_Info)
    if pid_change == 1:
        return pid_normal
    elif pid_change > 1:
        for i in pid_Info[1:]:
            j = pid.index(i)
            if pid[j - 1] == pid[j + 1]:
                continue
            elif pid[j - 1] != pid[j + 2]:
                return pid_error
        return pid_normal


def totalCpuCheck(cpu_path):
    """
    根据获取的cpu文件路径，判断整机cpu是否超过80%
    """
    cpuFileName = cpu_path.split("/")[-1]
    cpunormal = "ok"
    cpuerror = "整机cpu超过80%"
    cpu = os.popen("cat " + cpu_path + " | awk -F \"~~\" '{print $3}'").read().rstrip("\n").split("\n")
    cpu_float = []
    cpu_float = list(map(float, list(filter(isNotNullString, cpu))))
    cpu_average = average(cpu_float)

    if cpu_average > 80:
        return cpuerror
    else:
        return cpunormal


def isNotNullString(value):
    """
    判断是否是空字符串
    """
    return value != "" and value != "nan" and value != "Null"


def average(List):
    """
    计算平均值
    :param List:数据列表
    :return: List中元素的平均值
    """
    k = functools.reduce(add, List)
    return k / len(List)


def add(x, y):
    """
    求和
    :param x:
    :param y:
    :return:返回x+y
    """
    return x + y


def freeRamCheck(freeRAM_path):
    """
    根据获取的memory文件路径，判断free RAM是否低于200M
    """
    free_RAM = []
    memoryError = "almost 25% of running time, device free RAM is less than 200M"
    free_ = os.popen("cat " + freeRAM_path + " |awk -F \":\" '{print $8}'").read().rstrip("\n").split("\n")
    free_RAM = list(map(int, list(filter(isNotNullString, free_))))

    num = 0
    for i in free_RAM:
        if i < 200000:
            num += 1

    if (num * 1.0) / len(free_RAM) >= 0.25:
        return memoryError

    return "ok"


def cleanMemoryData(List):
    """
    将memory的数据中的异常大,小值,进行清理
    """
    num = len(List)  # 获取memory数据列表的总大小
    abnormal = []  # 记录的异常值
    for i in range(0, num, 3):
        if (i + 2) <= (num - 1):
            temp1 = abs((List[i + 2] - List[i]) * 1.0 / List[i])
            if temp1 <= 0.08:  # 说明两头的值基本基本持平
                averageValue = (List[i + 2] + List[i]) * 1.0 / 2
                temp2 = abs(1.0 * (List[i + 1] - averageValue) / averageValue)
                if temp2 >= 0.3:  # 说明存在异常值
                    abnormal.append(List[i + 1])

    for j in abnormal:
        List.remove(j)

    return List


def piece(List):
    """
    该函数负责将拐点找到
    """
    dot = []
    for k, j in enumerate(List):
        if (k + 3) <= len(List) and k >= 1:
            temp = abs(1.0 * (j - List[k + 1]) / j)
            if temp >= 0.3:
                temp1 = abs(1.0 * (j - List[k - 1]) / j)
                temp2 = abs(1.0 * (List[k + 1] - List[k + 2]) / List[k + 1])
                if temp1 <= 0.20 and temp1 > 0 and temp2 <= 0.20:
                    dot.append(k)
    return dot


def linefit(x, y):
    """
    对memory数据进行线性拟合,以支持是否存在内存泄露
    """
    N = float(len(x))
    sx, sy, sxx, syy, sxy = 0, 0, 0, 0, 0
    for i in range(0, int(N)):
        sx += x[i]
        sy += y[i]
        sxx += x[i] * x[i]
        syy += y[i] * y[i]
        sxy += x[i] * y[i]

    a = (sy * sx / N - sxy) / (sx * sx / N - sxx)

    return a


def memoryCheck(memory_path):
    """
    根据给的单进程memory文件，判断单进程是否存在内存泄漏
    """
    path = memory_path.split("/")[-1]
    progressName = re.search(r"^.*_(.+?)_20\d{2}_\d{2}", path).group(1)
    memoryError = progressName + "的memory 存在内存泄露"
    memory = os.popen("cat " + memory_path + " | awk -F \"~~\" '{print $4}'").read().rstrip("\n").split("\n")
    new_memory = list(map(int, list(filter(isNotNullString, memory))))

    # 首先进行数据清晰,去除异常值包括异常大值, 异常小值
    cleanData = cleanMemoryData(new_memory)

    # 开始判断, 
    breakPoint = piece(cleanData)  # 保存的是拐点的位置索引

    if len(breakPoint) == 0:
        X = list(range(len(cleanData)))
        slope = linefit(X, cleanData)
        num = len(str(min(cleanData)))
        slope = 1.0 * slope / (float(str(cleanData[0])[0]) * math.pow(10, num - 1))
        if slope >= 0.0008:
            return memoryError
    else:

        for k, j in enumerate(breakPoint):
            if k == 0:
                X = list(range((j + 1)))
                Y = cleanData[:(j + 1)]
                slope = linefit(X, Y)
                num = len(str(min(Y)))
                slope = 1.0 * slope / (float(str(Y[0])[0]) * math.pow(10, num - 1))
                if slope >= 0.0008:
                    return memoryError
            else:
                X = list(range(breakPoint[k - 1] + 1, j + 1))
                Y = cleanData[breakPoint[k - 1] + 1:j + 1]
                slope = linefit(X, Y)
                num = len(str(min(Y)))
                slope = 1.0 * slope / (float(str(Y[0])[0]) * math.pow(10, num - 1))
                if slope >= 0.0008:
                    return memoryError

    return "ok"


def dcsEventCheck(dcsEvent_path):
    """
    根据统计的协议事件上报的比率，若上报比率超过50%，则报警
    """
    event_rate = os.popen("cat " + dcsEvent_path + " | awk -F \"~~\" 'NR==2{print $4}'").read().rstrip("\n")

    if event_rate != "" and float(event_rate) > 50:
        protocal = os.popen("cat " + dcsEvent_path + " |awk -F \"~~\" 'NR==2{print $2}'").read().rstrip("\n")
        event = os.popen("cat " + dcsEvent_path + " | awk -F \"~~\" 'NR==2{print $1}'").read().rstrip("\n")

        return (protocal + "协议的" + event + "事件上报比率超过50%")

    return "ok"


def tempCheck(temp_path):
    """
    检查设备温度，若最大温度超过80度，则报警
    """
    temp1 = os.popen("cat " + temp_path + " | awk -F \"~~\" '{print $2}'").read().rstrip("\n").split("\n")
    temp2 = os.popen("cat " + temp_path + " | awk -F \"~~\" '{print $3}'").read().rstrip("\n").split("\n")

    temp = temp1 + temp2
    temp = list(map(float, list(filter(isNotNullString, temp))))

    i = max(temp)  # 获得最大值

    if i > 80:
        return "设备cpu温度超过80度"

    return "ok"


def threadCheck(threadInfo_path):
    """
    对线程数进行检查，若线程数一直处于增长趋势明则报警
    """
    fileName = threadInfo_path.split("/")[-1]
    progressName = re.search(r"^.*_(.+?)_20\d{2}_\d{2}", fileName).group(1)
    threadError = progressName + "进程的线程数一直在增长"
    threadInfo = os.popen("cat " + threadInfo_path + " | awk -F \"~~\" '{print $2}'").read().replace("\r", "").rstrip(
        "\n").split("\n")
    threadInfo = list(map(int, list(threadInfo)))
    cleanData = cleanMemoryData(threadInfo)
    breakPoint = piece(cleanData)
    if len(breakPoint) == 0:
        X = list(range(len(cleanData)))
        slope = linefit(X, cleanData)
        num = len(str(min(cleanData)))
        slope = 1.0 * slope / (float(str(cleanData[0])[0]) * math.pow(10, num - 1))
        if slope >= 0.008:
            return threadError

    return "ok"


def sdcardCheck(sdcard_path):
    """
    抓去sdcard/Android/data文件夹大小信息，若一直处于增长趋势，则报警Error
    """
    fileName = sdcard_path.split("/")[-1]
    progressName = re.search(r"^.*_(.+?)_20\d{2}_\d{2}", fileName).group(1)
    sdcardError = progressName + "进程sdcard/Android/data文件夹大小一直在增长"
    sdcardInfo = os.popen("cat " + sdcard_path + " | awk -F \"~~\" '{print $2}'").read().rstrip("\n").split("\n")
    sdcardInfo = list(map(int, list(sdcardInfo)))
    cleanData = cleanMemoryData(sdcardInfo)
    breakPoint = piece(cleanData)
    if len(breakPoint) == 0:
        X = list(range(len(cleanData)))
        slope = linefit(X, cleanData)
        num = len(str(min(cleanData)))
        slope = 1.0 * slope / (float(str(cleanData[0])[0]) * math.pow(10, num - 1))
        if slope >= 0.008:
            return sdcardError

    return "ok"


if __name__ == '__main__':
    print(memoryCheck("_com.qiyi.video.speaker_2019_09_04_01_03_m.txt"))
    print(memoryCheck("_com.baidu.launcher_2019_09_04_01_03_memoryInfo.txt"))
    print(memoryCheck("_com.baidu.launcher_20122_47_memoryInfo.txt"))
    # print(pidCheck("_com.baidu.duershow.statistic_2019_47_pidInfo.txt"))
    # print(pidCheck("_com.baidu.duer.ota_2019_06_13_21_31_pidInfo.txt"))
    # print(totalCpuCheck("_com.baidu.launcher.dcs2019_06_11_21_37_cpuInfo.txt"))
    # print(freeRamCheck("_totalMemoryInfo.txt"))
