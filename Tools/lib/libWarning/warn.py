#!/python
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

import sys
import smtplib
import json
from email.mime.text import MIMEText

if sys.version[0] == "3":
    import http.client as http
else:
    import httplib as http
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s #: %(message)s',
                    )

# 发送邮箱服务器
smtpserver = 'smtp.163.com'

# 发送邮箱用户/密码
user = '18811795722'
password = 'dumi2019'

# 发送邮箱
sender = '18811795722@163.com'

# 接收邮箱
receiver = "duer-qa-show@baidu.com"

# 发hi地址
hi_url = "qy.im.baidu.com"


#  发送邮件告警
def sendEmail(level, tester, deviceSn, dest, date, rom, content, receiverRd=None):
    """
    :param level: 日志级别,分为: warning, error
    :param tester: 本次测试者
    :param deviceSn: 设备的sn
    :param dest: 设备的测试目的
    :param date: 测试时间
    :param rom: 设备rom信息
    :param content: 告警内容,
    :param receiverRd: 要告知的rd邮箱, 此处可以选填
    :return:
    """
    # 发送邮件主题
    subject = "[压测告警][Show团队][告警等级:%s][测试目的:%s][测试者:%s][%s设备出现:%s]" % (level, dest, tester, deviceSn, content)

    # 网址链接
    link = "http://172.20.102.249:8080/WebTestDemo_war_exploded/DuerQA-Client?dateSelected=%s&deviceSelected=%s_%s" % (
    date, deviceSn, rom)

    # 编写plain类型的邮件正文
    msg = MIMEText('Show团队压测告警：\n 压测信息和日志地址:%s' % link, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['FROM'] = sender
    mreceiver = receiver + "," + receiverRd if receiverRd is not None else receiver
    msg["TO"] = mreceiver

    logging.info("向%s发送邮件告警, 告警内容为:%s" % (mreceiver, subject))

    # 连接发送邮件
    smtp = smtplib.SMTP()
    smtp.set_debuglevel(0)  # 用set_debuglevel(1)就可以打印出和SMTP服务器交互的所有信息
    smtp.connect(smtpserver)
    smtp.login(user, password)
    smtp.sendmail(sender, msg["TO"].split(","), msg.as_string())
    smtp.quit()
    logging.info("邮件发送结束")


# 发送hi告警信息
def sendHi(level, tester, deviceSn, dest, date, rom, content):
    """
        :param level: 日志级别,分为: warning, error
        :param tester: 本次测试者
        :param deviceSn: 设备的sn
        :param dest: 设备的测试目的
        :param date: 测试时间
        :param rom: 设备rom信息
        :param content: 告警内容,
        :return:
    """
    link = "http://172.20.102.249:8080/WebTestDemo_war_exploded/DuerQA-Client?dateSelected=%s&deviceSelected=%s_%s" % (
    date, deviceSn, rom)
    content = "[压测告警][show团队][告警等级:%s][测试目的:%s][测试者: %s][%s设备出现: %s]\n [地址: %s ]" % (
    level, dest, tester, deviceSn, content, link)

    hi_body = {
        "to": 1961316,
        "access_token": "de00428530d2ec16534c83f9818787f3",
        "msg_type": "text",
        "content": content
    }

    data = json.dumps(hi_body)
    header = {"Content-Type": "application/json"}
    connection = http.HTTPConnection(hi_url)
    logging.info("向show压测监控群发送hi告警, 告警内容为:%s" % content)
    connection.request("POST", "/msgt/api/sendMsgToGroup?access_token=a6932511b882efc48c920fb5bdf8f03", data, header)
    logging.info("hi告警发送结束")


if __name__ == "__main__":
    # sendEmail("wanring", "fengxiaomeng", "2123123123","test","2019-08-31", "dddddddd", "如果出现了问题","v_xiaoyi@baidu.com")
    # sendEmail("wanring", "fengxiaomeng", "2123123123","test","2019-08-31", "dddddddd", "如果出现了问题12312")
    sendHi("warning", "fengxiaomeng01", "3F182012F3271E18", "程序调试", "2019-08-31",
           "octopus_f1-eng_6.0.1_MMB29M_20190826_release-keys", "launcher pid 出现变化")
