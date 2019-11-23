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

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s #: %(message)s',
                    )


class Sql(object):
    """
    向数据库中写入name,namespace, messageId,dest,time等信息,以及统计信息使用
    """

    def __init__(self, name):
        self.name = name
        self.conn = self.__connectToData()  # 创建数据库 位于Data/dcsEvent.db
        self.cursor = self.conn.cursor()

        try:
            self.cursor.execute('''create table DcsEvent 
            (id integer primary key autoincrement, 
             deviceSerial varchar(20) not null,
             destination varchar(30) not null,
             startTime varchar(18) not null, 
             name varchar(40) not null,
             namespace varchar(50) not null,
             messageId varchar(80),
             createdTime TimeStamp NOT NULL DEFAULT CURRENT_TIMESTAMP);''')  # 创建数据表
        except Exception:
            logging.warning("DcsEvent表已经存在")

        try:
            self.cursor.execute(
                'create index serial_dest_time on DcsEvent (deviceSerial, destination, startTime)')  # 创建索引, 加快查询速度
        except Exception:
            logging.warning("索引 serial_dest_time 已经存在")

    def exit(self):
        """
        断开与数据库的连接
        """
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def __connectToData(self):
        """
        连接数据库
        """
        return sqlite3.connect(self.name, check_same_thread=False)

    def __str__(self):
        return "{}数据库中的{}数据表".format(self.name, "DcsEvent")

    def insertData(self, deviceSerial, destination, startTime, name, namespace, messageId):
        """
        向数据表中写入数据
        """
        try:
            self.cursor.execute('insert into DcsEvent (deviceSerial, destination, startTime, name, namespace, messageId) \
                values ("{Serial}", "{dest}", "{start}", "{nameEvent}", "{namespaceEvent}", "{messageIdEvent}")' \
                                .format(Serial=deviceSerial, dest=destination, start=startTime, nameEvent=name,
                                        namespaceEvent=namespace, messageIdEvent=messageId))

        except Exception:
            logging.warning("连接dcsEvent的cursor已经断掉, 进行重连")
            self.cursor = self.conn.cursor()

        self.conn.commit()  # 提交修改

    def getResult(self, deviceSerial, destination, startTime):
        """
        返回统计结果,name namespace pv 百分百
        """
        try:
            self.cursor.execute(
                "select count(*) from DcsEvent where deviceSerial = '{}' and destination = '{}' and startTime = '{}'"\
                    .format(deviceSerial, destination, startTime))
            totalNum = float(self.cursor.fetchone()[0])

            self.cursor.execute('select distinct name, namespace, count(id) as pv\
            , (count(id)/"{}")*100 as percent from DcsEvent \
                where deviceSerial = "{}" and destination = "{}"\
                 and startTime = "{}" group by name, namespace order by pv desc' \
                                .format(totalNum, deviceSerial, destination, startTime))
            finalResult = self.cursor.fetchall()  # 结果形如 [('1', 'Michael'), ('2', 'jordan')]

        except Exception:
            logging.warning("连接dcsEvent的cursor已经断掉, 进行重连")
            self.cursor = self.conn.cursor()

            self.cursor.execute(
                "select count(*) from DcsEvent where deviceSerial\
                 = '{}' and destination = '{}' and startTime = '{}'".format(
                    deviceSerial, destination, startTime))
            totalNum = float(self.cursor.fetchone()[0])

            self.cursor.execute('select distinct name, namespace, count(id) as pv,\
             (count(id)/"{}")*100 as percent from DcsEvent \
                where deviceSerial = "{}" and destination = "{}"\
                 and startTime = "{}" group by name, namespace order by pv desc' \
                                .format(totalNum, deviceSerial, destination, startTime))
            finalResult = self.cursor.fetchall()  # 结果形如 [('1', 'Michael'), ('2', 'jordan')]

        return finalResult
