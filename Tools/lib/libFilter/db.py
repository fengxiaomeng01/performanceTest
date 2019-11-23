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


class DataBase(object):
    """
    该类连接数据库的实例
    """

    def __init__(self):
        ts = time.strftime("%Y-%m-%d_%H:%M")
        self.name = "Data/logDot" + ts + ".db"
        self.conn = self.__connectToData()
        self.cursor = self.conn.cursor()

    def __connectToData(self):
        """
        连接数据库，如果不存在则创建数据库
        """
        return sqlite3.connect(self.name, timeout=10, check_same_thread=False)

    @property
    def getSqlCursor(self):
        """
        提供给外界连接数据库的指针
        """
        return self.cursor

    def exit(self):
        """
        断开与数据库的连接
        """
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
