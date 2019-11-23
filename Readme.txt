################################################################################
#
# Copyright (c) 2018 Baidu.com, Inc. All Rights Reserved
#
################################################################################
"""
Authors: fengxiaomeng01(fengxiaomeng01@baidu.com)
Date:    2019/04/15 
"""

duerTest是show端用于压力测试的自动化工具，具有便捷易用，可扩展性强，数据即时性，不会产生僵尸进程等优点

『使用手册』
# 在执行测试前，请先修改好config.json文件,第一个process字段本次测试关注的设备公共进程
# 后面"6S184730058C1ECF"修改为你自己设备的sn号，『dest』为你本次测试的目的，不少于8个字符
# tester字段填的是测试机的用户名,比如fengxiaomeng01
# dest字段后的process为该设备本次测试所关注的独有进程，若无则不填
# dumpheap为测试过程中dumpheap操作的开关，若想避免测试过程中dumpheap操作对设备性能产生影响，则将"y"改为"n"
# 默认测试时间为12h，若想修改测试时间，比如24h：请执行python runTest.py -t 24
# 本地测试数据会实时上传web服务器并保存，其中hprof、smaps等大体积数据会保存40天，并生成图表数据
# 压测数据地址：http://172.20.102.249:8080/WebTestDemo_war_exploded/DuerQA-Client


『注意事项』
# 若执行过程报错，请先检查config.json文件是否填写正确
