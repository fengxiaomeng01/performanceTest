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
import sqlite3
import logging

from Tools.lib.libFilter.db import DataBase

logging.basicConfig(level=logging.INFO,
        format='%(asctime)s %(levelname)s #: %(message)s',
                )


class Info(DataBase):
    """本类的实例负责向logDot中的device表, test表, profile表, map表,写入数据"""
    def writeIntoDevice(self, deviceSerial, deviceRom, deviceBand):
        """
        向device表中写入数据
        deviceSerial: 设备序列号
        deviceRom: 设备rom信息
        deviceBand: 设备型号
	"""
        logging.info("向device表中写入数据 - deviceSerial : %s, deviceRom : %s, deviceBand : %s"\
%(deviceSerial, deviceRom, deviceBand))
        self.cursor.execute('replace into device ( deviceSerial, deviceRom, deviceBand) \
			values ("{Serial}", "{Rom}", "{Band}");'.format(Serial = deviceSerial, Rom = deviceRom, Band = deviceBand))

        self.conn.commit() # 提交修改

    def writeIntoTest(self, destination, tester, duration, startTime, resultFilePath, deviceSerial):
        """
        向test表中写入数据
        destination: 测试目的
        tester: 测试人员
        duration: 确认人员
        startTime: 测试开始时间
        resultFilePath: 测试数据文件存放地址
        deviceSerial: 设备序列号
        """
        logging.info("向test表中写入数据 - destination : %s, tester : %s,duration\
 : %s, startTime : %s, resultFilePath : %s, device_no : %s"\
%(destination, tester, duration, startTime, resultFilePath, deviceSerial))
        self.cursor.execute('insert into test (destination, tester, duration, startTime, resultFilePath, device_no) \
			values ("{dest}", "{te}", "{dura}", "{start}", "{result}",\
 (select device_no from device where deviceSerial = "{Serial}"))'\
			.format(dest = destination, te = tester, dura = duration, start = startTime,\
 result = resultFilePath, Serial = deviceSerial))

        self.conn.commit() # 提交修改

    def writeIntoProfile(self, fileName, tag, way, deviceSerial, startTime):
        """
        向profile表中写入数据
        fileName: 信息检索配置文件名称
        tag: log的tag, 从配置文件中获取
        way: 统计方式, 分三种, uv, pv, all(包含uv, pv)
        startTime: 测试开始时间
	"""
        logging.info("向profile表中写入数据 - fileName : %s, tag : %s, way : %s, device_no : %s, startTime : %s"\
%(fileName, tag, way, deviceSerial, startTime))

        if "default" != deviceSerial: 
            self.cursor.execute('replace into profile (fileName, tag, way, device_no, startTime) values \
			("{file}", "{t}", "{w}", (select device_no from device where deviceSerial = "{Serial}"), "{start}")'\
			.format(file = fileName, t = tag, w = way, Serial = deviceSerial, start = startTime))
        else:
            self.cursor.execute('replace into profile (fileName, tag, way, startTime) values \
			("{file}", "{t}", "{w}", "{start}")'\
			.format(file = fileName, t = tag, w = way, start = startTime))

        self.conn.commit() # 提交修改

    def writeIntoMap(self, keyword, note, profileName):
        """
        向map表中写入数据
        keyword: 捕捉关键字
        note: value值
        profileName: keyword 所属的信息检索配置文件
	"""
        logging.info("向map表中写入数据 - keyword : %s, note : %s, profileName : %s " % (keyword, note, profileName))
        self.cursor.execute('replace into map (keyword, note, profile_no) values \
			("{key}", "{no}", (select profile_no from profile where fileName = "{name}"))'.format\
(key = keyword, no = note, name = profileName))
		
        self.conn.commit() # 提交修改

    def writeIntoResult(self, time, keyword, result, pointer, startTime, deviceSerial, profile_no):
        """
        向result表中写入数据
        time:日志中的时间戳
        keyword:关键字
        result: 关键字对应的结果
        deviceSerial: 设备序列号
        startTime: 测试开始时间
        profile_no:keyword的来源信息检索配置文件id
        startTime: 测试开始时间
        """
        logging.info("向result表中写入数据:time:%s, keyword:%s, result:%s, deviceSerial:%s, profile_no:%s, startTime:%s"\
                %(time, keyword, result, deviceSerial, profile_no, startTime))

        self.cursor.execute('select test_no from test where device_no = \
(select device_no from device where deviceSerial = "{}")'.format(deviceSerial))
        test_no = self.cursor.fetchone()[0]

        self.cursor.execute('insert into result (time, keyword, result, \
pointer, startTime, test_no, profile_no) values ("{tm}", "{key}", \
"{res}", "{p}", "{start}", "{test}", "{profile}")'\
.format(tm = time, key = keyword, res = result, p = pointer, start = startTime, test = test_no, profile = profile_no))

        self.conn.commit() # 提交修改

    def getTags(self, deviceSerial):
        """
        从profile表中获得设备本次测试使用的所有tags
        """
        logging.info("从device表获取 %s 设备关注的tag" % deviceSerial)
        
        # 首先从数据表test中获得开始的测试时间
        self.cursor.execute('select startTime from test where device_no =\
 (select device_no from device where deviceSerial = "{Serial}")'.format(Serial = deviceSerial))

        startTime = self.cursor.fetchone()[0]

        # 获取设备本次测试对应的tags
        self.cursor.execute('select tag from profile where startTime = "{start}"\
 and device_no = 0 or (select device_no from device where deviceSerial = "{Serial}")'\
    		.format(start = startTime, Serial = deviceSerial))
        
        origin_result = self.cursor.fetchall() # 获取初步结果

        return [x[0] for x in origin_result]

    def getTags_FileName_Way_ProfileNo(self, deviceSerial):
        """
        从profile表中获得设备本次测试使用的所有tags, 对应的fileName, way, profile_no
        """
        logging.info("从device表获取 %s 设备关注的tag, fileName, way" % deviceSerial)
        
        # 首先从数据表test中获得开始的测试时间
        self.cursor.execute('select startTime from test where device_no\
 = (select device_no from device where deviceSerial = "{Serial}")'.format(Serial = deviceSerial))

        startTime = self.cursor.fetchone()[0]

        # 获取设备本次测试对应的tags
        self.cursor.execute('select tag, fileName, way, profile_no from profile where startTime\
 = "{start}" and device_no = 0 or (select device_no from device where deviceSerial = "{Serial}")'\
    		.format(start = startTime, Serial = deviceSerial))
        
        origin_result = self.cursor.fetchall() # 获取初步结果

        return origin_result

    def getDeviceInfo(self, deviceSerial):
        """
        从device表中获得设备序列号对应的rom信息和型号信息
        """
        logging.info("从device表获取 %s 设备关注到rom, band" % deviceSerial)
        self.cursor.execute('select deviceRom, deviceBand from\
 device where deviceSerial = "{sn}"'.format(sn = deviceSerial))

        origin_result = self.cursor.fetchone() # 获得初步结果

        return [origin_result[0], origin_result[1]]

    def getDestinationAndStartTimeAndResultFilePath(self, deviceSerial):
        """
        从test表中, 获得设备序列号对应的测试目的和测试开始时间和结果存放目录
        """
        logging.info("从test表中获取设备本次测试获得的destination, startTime, resultFilePath")
        self.cursor.execute('select destination, startTime, resultFilePath from test\
 where device_no = (select device_no from device where deviceSerial = "{sn}")'.format(sn = deviceSerial))

        origin_result = self.cursor.fetchone() #获取初步结果

        return [origin_result[0], origin_result[1], origin_result[2]] # destination, startTime, resultFilePath

    def getKeyword_Note(self, tag, fileName):
        """
        获取map表达信息keyword, note
        """
        logging.info("从map表中获取设备profile_no本次测试对应的keyword, note信息")

        # 首先获取tag对应的profile_no
        self.cursor.execute('select profile_no from profile where fileName\
 = "{name}" and tag = "{t}"'.format(name = fileName, t = tag))
        profile_no = self.cursor.fetchone()[0] # 获取到profile_no

        # 再次根据profile_no获取, keyword, note
        self.cursor.execute('select keyword, note from map where profile_no = "{no}"'.format(no = profile_no))

        return self.cursor.fetchall()

    def getPointer(self, serial, profile_no):
        """
        从result表中获取上次读到的tagTxt文件的位置
        """
        logging.info("从result表中获取pointer的数值")

        # 获取test_no
        self.cursor.execute('select test_no from test where device_no\
 = (select device_no from device where deviceSerial = "{}")'.format(serial))
        test_no = self.cursor.fetchone()[0]

        self.cursor.execute('select pointer from result where test_no\
 = "{test}" and profile_no = "{no}" order by result_no desc'.format(test = test_no, no = profile_no))
        return self.cursor.fetchone()

    def getUvResult(self, serial, profile_no, startTime):
        """
        以uv方式,返回Result结果
        """
        logging.info("从result表中,获得time, keyword, result")
       
        # 获取test_no
        self.cursor.execute('select test_no from test where device_no\
 = (select device_no from device where deviceSerial = "{}")'.format(serial))
        test_no = self.cursor.fetchone()[0]

        self.cursor.execute('select time, keyword, result from result where startTime\
 = "{start}" and test_no = "{no}" and profile_no\
 = "{profile}"'.format(start = startTime, no = test_no, profile = profile_no))
        return self.cursor.fetchall()

    def getPvResult(self, serial, profile_no, startTime):
        """
        以pv方式, 返回Result结果
        """
        logging.info("从result中, 获得keyword, result,并以pv方式呈现")

        # 获取test_no        
        self.cursor.execute('select test_no from test where device_no\
 = (select device_no from device where deviceSerial = "{}")'.format(serial))
        test_no = self.cursor.fetchone()[0]

        # 获得总数
        self.cursor.execute('select count(*) from result where startTime = "{start}" and test_no\
 = "{no}" and profile_no = "{profile}"'.format(start = startTime, no = test_no, profile = profile_no))
        totalNum = float(self.cursor.fetchone()[0])

        self.cursor.execute('select distinct keyword, result, count(result_no) as pv,\
 (count(result_no)/"{total}")*100 from result where startTime = "{start}" and test_no\
 = "{no}" and profile_no = "{profile}" group by keyword, result order by pv desc'\
.format(start = startTime, no = test_no, profile = profile_no, total = totalNum))
        return self.cursor.fetchall()
