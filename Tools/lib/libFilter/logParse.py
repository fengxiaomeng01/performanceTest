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
import datetime
import traceback

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s #: %(message)s',
                    )


class LogParser(object):
    """
    创建日志解析的主体对象
    """

    def __init__(self, devices, mInfo):
        """
        devices: 设备序列号列表
        mInfo: 写入和读数据表对象
        """
        self.devices = devices
        self.mInfo = mInfo

    def __str__(self):
        return "日志分析器的LogPara类实例"

    def __generateTagFile(self, serial, tag, fileName):
        """
        针对deviceSerial和tag生成唯一性tag文件
        serial: 产品的序列号
        tag:过滤日志的tag
        fileName:该tag来源自这个文件名
        """
        rom, band = self.mInfo.getDeviceInfo(serial)  # 获得这个设备的rom信息和型号
        dest, start, path = self.mInfo.getDestinationAndStartTimeAndResultFilePath(
            serial)  # 获得本次测试的目的, 测试结果路径, 开始时间
        # 获得baiduConcern日志文件
        baiduConcern = self.__getBaiduConcern(path)  # baiduConcern文件
        tagTxt = path + "/" + serial + "_" + rom + "@#@_" + band + "_" + dest + "_" + fileName + start + ".txt"
        if baiduConcern != "Null":
            os.system("cat {}/{} | grep -a -i -E '{}' > {}".format(path, baiduConcern, tag, tagTxt))
            logging.info("生成%s设备的%s文件" % (serial, tagTxt))

        else:
            logging.warning("%s设备目前没有日志文件" % serial)
        return [tagTxt, start]  # 返回这个生成的tag文件,为后面进行检索作准备

    def __getBaiduConcern(self, FolderName):
        """
        获得指定FolderName文件夹下的log文件
        """
        logName = os.popen("ls -l %s | grep -i record_BaiduConcerned | awk '{print $NF}'" % FolderName).read().rstrip(
            "\n").rstrip("\r")

        return logName if logName != "" else "Null"

    def getInfo(self):
        """
        过滤对应设备的日志文件中的,所有的配置文件
        """
        for serial in self.devices:
            # 首先过滤出每个设备对应的sn号的tag和其对应的filename文件
            tagsAndFileNameAndWayAndProfileNoToDevice = self.mInfo.getTags_FileName_Way_ProfileNo(serial)

            # 根据获取到的tags
            for tags_FileName_Way_profileNo in tagsAndFileNameAndWayAndProfileNoToDevice:
                tag = tags_FileName_Way_profileNo[0]
                fileName = tags_FileName_Way_profileNo[1]
                way = tags_FileName_Way_profileNo[2]
                profile_no = tags_FileName_Way_profileNo[3]

                # 首先生成针对这个tag的唯一性文件
                tagTxt, startTime = self.__generateTagFile(serial, tag, fileName)

                # 针对tagTxt文件进行检索并写入数据库
                self.__countTagTxt(tagTxt, tag, fileName, profile_no, serial, startTime)

                # 生成统计tagTxt信息的tableInfo文件
                self.__createTableInfo(tagTxt, way, serial, profile_no, startTime)

    def __createTableInfo(self, tagTxt, way, serial, profile_no, startTime):
        """
        生成相应的tabInfo文件
        """
        tableInfoComm = tagTxt.replace(".txt", "_tableInfo.txt")
        if way == "uv":
            tableInfoUv = tableInfoComm.replace("_tableInfo", "_UV_tableInfo")
            origin_result = self.mInfo.getUvResult(serial, profile_no, startTime)
            # 首先判断是否过滤到结果
            if origin_result == []:
                return  # 被你过滤没有对应数据,跳过

            else:
                fp = open(tableInfoUv, "w")
                fp.write("timeStamp~~keyword~~result\n")
                fp.close()

                fp = open(tableInfoUv, "a")
                for row in origin_result:
                    fp.write(row[0] + "~~" + row[1] + "~~" + row[2] + "\n")
                fp.close()

        elif way == "pv":
            tableInfoPv = tableInfoComm.replace("_tableInfo", "_PV_tableInfo")
            origin_result = self.mInfo.getPvResult(serial, profile_no, startTime)
            # 首先判断是否过滤到结果
            if origin_result == []:
                return  # 被你过滤没有对应数据,跳过

            else:
                fp = open(tableInfoPv, "w")
                fp.write("keyword~~result~~pv~~percent(%)\n")
                fp.close()

                fp = open(tableInfoPv, "a")
                for row in origin_result:
                    fp.write(row[0] + "~~" + row[1] + "~~" + str(row[2]) + "~~" + str(row[3]) + "\n")
                fp.close()

    def __countTagTxt(self, tagTxt, tag, fileName, profile_no, serial, startTime):
        """
        针对tagTxt进行信息检索并写入数据库
        tagTxt: 生成的tagTxt文件
        tag:该文件的tag信息
        fileName:tag所属的文件名
        """
        # 获取map表对应的map_no, keyword, note
        key_note_List = self.mInfo.getKeyword_Note(tag, fileName)
        # 获取上次读取tagTxt处的指针位置
        temp = self.mInfo.getPointer(serial, profile_no)

        fp_pointer = 0 if temp is None else temp[0]

        # 开始处理tag文件     
        with open(tagTxt, "r") as fp:
            fp.seek(fp_pointer)  # 将文件指针跳转到上次读取的位置

            # 依次读取每一行的信息
            for line in fp.readlines():

                for key_note in key_note_List:  # 将key, note在这一行中遍历一遍

                    try:
                        if key_note[0] in line[33:]:  # 确保这一行中有其关键字key

                            if key_note[1] == "uncertain":  # 如果note显示为'uncertain', 则调用正则表达式 去获取这个非固定信息
                                timeStamp, real_note = self.__reg(line, key_note)

                                if "No Match Content" != real_note:
                                    self.mInfo.writeIntoResult(timeStamp, key_note[0], real_note, fp.tell(), startTime,
                                                               serial, profile_no)
                                    break
                                else:
                                    logging.warning("%s设备日志中的%s内容没有匹配到%s的内容" % (serial, line, key_note[1]))

                            else:  # 如果note不是'uncertain'
                                timeStamp = self.__reg(line)  # 获取时间戳
                                self.mInfo.writeIntoResult(timeStamp, key_note[0], key_note[1], fp.tell(), startTime,
                                                           serial, profile_no)
                                break

                    except UnicodeDecodeError:
                        logging.warning(traceback.format_exc())

    def __reg(self, line, key_note=None):
        """
        通过正则表达式获取, 时间戳, 有时候要获取非固定信息的内容.
        """
        timeStampPattern = re.compile("""
        ^(\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})               # 匹配开头的时间戳
        """, re.VERBOSE)

        try:
            timeStamp = timeStampPattern.search(line).group(1)
        except:  # 如果没有获取到时间戳
            timeStamp = "No Match Time:" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

        if key_note is not None:  # 如果要匹配非固定信息
            contentPattern = re.compile('^.*?%s[":\s]*(.*?)[",;:\r\n$]' % key_note[0])

            try:
                content = contentPattern.search(line).group(1)
            except:  # 如果没有匹配到响应结果
                content = "No Match Content"

            return [timeStamp, content]

        else:
            return timeStamp
