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
import traceback

from Tools.lib.libFilter.db import DataBase

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s #: %(message)s',
                    )


class Creater(DataBase):
    """
    创建logDot数据库中的相应的数据表
    """
    def createTable(self):
        """
        用于创建日志信息相关的表
        :return:
        """
        logging.info("创建device表: device_no, deviceSerial, deviceRom, deviceBand")
        try:  # 创建device表
            self.cursor.execute('''create table device 
            (device_no integer primary key autoincrement,
            deviceSerial varchar(20) not null,
            deviceRom varchar(80) not null,
            deviceBand varchar(20) not null)''')
        except Exception:
            logging.warning("数据表device已经存在")

        logging.info("创建device表的唯一性索引, deviceSerial")
        try:  # 创建device表的唯一性索引,为更新数据
            self.cursor.execute('create unique index sn on device (deviceSerial)')
        except Exception:
            logging.warning("索引sn已经存在")

        logging.info("创建test表: test_no, destination, tester, duration, startTime, resultFilePath, device_no")
        try:  # 创建test表
            self.cursor.execute('''create table test
            (test_no integer primary key autoincrement,
            destination varchar(20) not null,
            tester varchar(20) not null,
            duration varchar(5) not null,
            startTime varchar(20) not null,
            resultFilePath varchar(40) not null,
            device_no integer not null)''')
        except Exception:
            logging.warning("数据表test已经存在")

        logging.info("创建profile表: profile_no, fileName, tag, device_no, startTime")
        try:  # 创建profile表
            self.cursor.execute('''create table profile
            (profile_no integer primary key autoincrement,
            fileName varchar(40) not null,
            tag varchar(80) not null,
            way varchar(10) not null,
            device_no integer Default 0,
            startTime varchar(20) not null)''')  # devide_no的自增是从1开始的, 这里0 代表该配置文件为多个测试设备共有
        except Exception:
            logging.warning("数据表profile已经存在")

        logging.info("创建profile表的唯一性索引, fileName")
        try:  # 创建profile表的唯一性组合索引,为更新数据
            self.cursor.execute('create unique index f on profile (fileName)')
        except Exception:
            logging.warning("索引f已经存在")

        logging.info("创建map表: map_no, keyword, note, profile_no")
        try:  # 创建map表
            self.cursor.execute('''create table map
            (map_no integer primary key autoincrement,
            keyword varchar(30) not null,
            note varchar(20) default 'uncertain',
            profile_no integer not null
            )''')
        except Exception:
            logging.warning("数据表map已经存在")

        logging.info("创建map表的唯一性索引, key")
        try:  # 创建map表的唯一索引,为更新数据
            self.cursor.execute('create unique index key on map (keyword)')
        except Exception:
            logging.warning("索引key已经存在")

        logging.info("创建result表: result_no, time, keyword, result, pointer, startTime, test_no, profile_no")
        try:  # 创建result表
            self.cursor.execute('''create table result
            (result_no integer primary key autoincrement,
            time varchar(30) not null,
            keyword varchar(30) not null,
            result varchar(100) not null,
            pointer integer not null,
            startTime varchar(20) not null,
            test_no integer not null,
            profile_no integer not null
            )''')
        except Exception:
            logging.warning("数据表result已经存在")

        logging.info("创建result表的组合索引, (startTime, test_no, profile_no)")
        try:  # 创建result表的复合索引,加速数据查询
            self.cursor.execute('create index test_map_profileNO on result (startTime, test_no, profile_no)')
        except Exception:
            logging.warning("索引test_map_profileNO已经存在")

        logging.info("关闭与logDot数据库的连接")
        self.exit()  # 创建完数据数据库和列表后, 关闭数据库连接
