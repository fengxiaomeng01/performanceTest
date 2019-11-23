#!/bin/sh

isUser=$1              # 设备是否是userdebug版本
deviceSerial=$2        # 设备序列号
fileNamePre=$3         # 文件名前缀
timeStampFile=$4       # 文件末尾时间内戳

# 四次移动位置参数，生成进程列表
shift
shift
shift
shift

processList=("$@") # 获取进程列表
temp=${#processList[*]} #获得进程个数
((temp=temp-1))

sleep 3

while true
do
# 获得当前的前台activity
currentActivity=`adb -s $deviceSerial shell dumpsys activity activities | sed -En -e '/Running activities/,/Run #0/p' | awk 'NR==3{print $5}'`

# 获得/sdcard/Android/data/包名文件夹下的大小
for processName in ${processList[@]}
do
  if [[ $processName =~ "com." || $processName =~ "cn." || $processName =~ "vulture.app.home" ]];then

        #####################################################################################################################
        #                                           获取进程的线程数目                                                      #
        #####################################################################################################################
	pidName=`adb -s $deviceSerial shell ps -ef | grep -i $processName[^:.] | awk 'NR==1{print $2}'`
	if [ ! -n "$pidName" ];then
	    pidName=`adb -s $deviceSerial shell ps | grep -i $processName[^:.] | awk 'NR==1{print $2}'`
	fi
	if [ ! -n "$pidName" ];then
	    pidName=`adb -s $deviceSerial shell ps | grep -i $processName$ | awk 'NR==1{print $2}'`
	fi
	if [ ! -n "$pidName" ];then
	    pidName=`adb -s $deviceSerial shell ps -ef| grep -i $processName$ | awk 'NR==1{print $2}'`
	fi
        
        if [ -n "$pidName" ];then
           echo '==========================='`date +%Y%m%d%H%M%S`'==================================' >> $fileNamePre$processName$timeStampFile'_statusDetail.txt'
           processThreadCount=(`adb -s $deviceSerial shell cat /proc/$pidName/status|tee -a $fileNamePre$processName$timeStampFile'_statusDetail.txt'|grep -i thread | awk '{print $2}'`)
           
           echo =======================================================================
           echo $processName"'s threadCount:"
           echo `date +%Y%m%d%H%M%S`':'$currentActivity'~~'$processThreadCount|tee -a $fileNamePre$processName$timeStampFile'_threadInfo.txt'

           echo '==========================='`date "+%Y-%m-%d_%H:%M:%S"`'===========================' >> $fileNamePre$processName$timeStampFile'_threadDetail.txt'
           echo `adb -s $deviceSerial shell ps -t $pidName` >> $fileNamePre$processName$timeStampFile'_threadDetail.txt'

        fi
 

          ######################################################################################################################
          #                                   下为程序为获取进程的磁盘空间占用                                                 #
          ######################################################################################################################
	  sdcardSpace=`adb -s $deviceSerial shell du -sk /sdcard/Android/data/$processName 2>/dev/null | awk 'NR==1{print $1}'` 

	  if [[ $sdcardSpace =~ "du" || -z $sdcardSpace ]];then
              echo =======================================================================
	      echo $processName' has no /sdcard/Android/data/package directory'
	      echo `date +%Y%m%d%H%M%S`':'$currentActivity'~~'0 | tee -a $fileNamePre$processName$timeStampFile'_sdcardInfo.txt'
	  else
	      echo ========================================================================
	      echo $processName"'s sdcard_Space:"     
	      echo `date +%Y%m%d%H%M%S`':'$currentActivity'~~'$sdcardSpace | tee -a $fileNamePre$processName$timeStampFile'_sdcardInfo.txt'
	  fi

	  if [ "$isUser" != "y" ];then
	     totalData=`adb -s $deviceSerial shell du -sk /data | awk 'NR==1{print $1}'`    
	     dataProcess=`adb -s $deviceSerial shell du -sk /data/data/$processName | awk 'NR==1{print $1}'`
             
             if [[ $dataProcess =~ "du" || -z $dataProcess ]];then 
	         echo ========================================================================
	         echo $processName' has no /data/data/package directory'
	         echo `date +%Y%m%d%H%M%S`':'$currentActivity'~~'0'~~'$totalData | tee -a $fileNamePre$processName$timeStampFile'_DataInfo.txt'
             else
	         echo ========================================================================
	         echo $processName"'s dataProcess and totalData:"
	         echo `date +%Y%m%d%H%M%S`':'$currentActivity'~~'$dataProcess'~~'$totalData | tee -a $fileNamePre$processName$timeStampFile'_DataInfo.txt'
             fi
	  fi
  fi
done

###########################################################
#      获取详细的/sdcard和/data各子文件夹的大小       #####        
###########################################################
if [ "$isUser" != "y" ];then
   echo '=========================='`date "+%Y-%m-%d_%H:%M:%S"`'========================' >> $fileNamePre$timeStampFile'_DataDetail.txt'
   echo `adb -s $deviceSerial shell du -h /data/` >> $fileNamePre$timeStampFile'_DataDetail.txt'
fi

echo '=========================='`date "+%Y-%m-%d_%H:%M:%S"`'========================' >> $fileNamePre$timeStampFile'_sdcardDetail.txt'
echo `adb -s $deviceSerial shell du -h /sdcard/` >> $fileNamePre$timeStampFile'_sdcardDetail.txt'

sleep 300


done
