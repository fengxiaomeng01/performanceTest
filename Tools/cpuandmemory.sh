#!/bin/sh

proMemorySwitch=$1     # 是否进行dumpsys meminfo
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

while true
do

# 获得每个进程的pid信息，组成数组
pidnum=0
currentActivity=`adb -s $deviceSerial shell dumpsys activity activities | sed -En -e '/Running activities/,/Run #0/p' | awk 'NR==3{print $5}'`
for processName in ${processList[@]}
do

echo ==================================================================================
echo $processName"'s pid:"
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

# 经过一轮进程号扫描后，如果确实不存在该进程，则该进程的进程号使用null代替
if [ ! -n "$pidName" ];then
    pidName="Null"
fi

pidList[$pidnum]=$pidName
((pidnum=pidnum+1))
echo `date +%Y%m%d%H%M%S`':'$currentActivity'~~'$pidName |tee -a $fileNamePre$processName$timeStampFile'_pidInfo.txt'
done

# 获得第一次整机cpu信息的快照
cpuRawList=(`adb -s $deviceSerial shell cat /proc/stat | awk 'NR==1{print $2,$3,$4,$5,$6,$7,$8}'`)

# 获得第一次app的cpu信息快照
appnum=0
for pidName in ${pidList[@]}
do
processCpu14and15=(`adb -s $deviceSerial shell cat /proc/$pidName/stat | awk '{print $14+$15}'`)
AppCpuList[$appnum]=$processCpu14and15
((appnum=appnum+1))
done


sleep 2 # 间隔定为2s,与top同步


# 第二次获得整机cpu信息的快照
cpuRawList2=(`adb -s $deviceSerial shell cat /proc/stat | awk 'NR==1{print $2,$3,$4,$5,$6,$7,$8}'`)

# 第二次获得app的cpu信息
appnum=0
for pidName in ${pidList[@]}
do
processCpu142and152=(`adb -s $deviceSerial shell cat /proc/$pidName/stat | awk '{print $14+$15}'`)
AppCpu2List[$appnum]=$processCpu142and152
((appnum=appnum+1))
done

# 计算快照的结果，整机cpu 和 app cpu
totalCpu=0
for i in "${cpuRawList[@]}"
do
    let "totalCpu = $i + $totalCpu"
done
nonIdleCpu=`expr $totalCpu - ${cpuRawList[3]}`

totalCpu2=0
for j in "${cpuRawList2[@]}"
do
    let "totalCpu2 = $j + $totalCpu2"
done
nonIdleCpu2=`expr $totalCpu2 - ${cpuRawList2[3]}`


nonIdleTime=`awk -v x=$nonIdleCpu2 -v y=$nonIdleCpu 'BEGIN{printf "%.4f\n",x-y}'`
totalCpuTime=`awk -v x=$totalCpu2 -v y=$totalCpu 'BEGIN{printf "%.4f\n",x-y}'`

# cpu ratio
totalCpuRatio=`awk -v x=$nonIdleTime -v y=$totalCpuTime 'BEGIN{printf "%.4f\n",x/y}'`
totalCpuRatio2=`awk -v x=$totalCpuRatio -v y=100 'BEGIN{printf "%.2f\n",x*y}'`

for i in `seq 0 $temp`
do
AppCpu2=${AppCpu2List[$i]}
AppCpu=${AppCpuList[$i]}
processCpuTime=`awk -v x=$AppCpu2 -v y=$AppCpu 'BEGIN{printf "%.4f\n",x-y}'`
appCpuRatio=`awk -v x=$processCpuTime -v y=$totalCpuTime 'BEGIN{printf "%.4f\n",x/y}'`
appCpuRatio2=`awk -v x=$appCpuRatio -v y=100 'BEGIN{printf "%.2f\n",x*y}'`

echo ===================================================================================
echo ${processList[$i]}"'s process_cpu and total_cpu:"
echo `date +%Y%m%d%H%M%S`':'$currentActivity'~~'$appCpuRatio2'~~'$totalCpuRatio2 |tee -a $fileNamePre${processList[$i]}$timeStampFile'_cpuInfo.txt'
done

sleep 5 # 在计算cpu和memory之间间隔5s

if [ "$proMemorySwitch" = "y" ] 
then
# 处理内存数据
for processName in ${processList[@]}
do

if [[ $processName =~ "com." || $processName =~ "cn." || $processName =~ "vulture.app.home" ]];then
echo =====================================================================
echo $processName"'s process_memory:"
echo '==========================='`date +%Y%m%d%H%M%S`'==================================' >> $fileNamePre$processName$timeStampFile'_memoryDetail.txt'

currentActivity=`adb -s $deviceSerial shell dumpsys activity activities | sed -En -e '/Running activities/,/Run #0/p' | awk 'NR==3{print $5}'`

memRawList=(`adb -s $deviceSerial shell dumpsys meminfo $processName|tee -a $fileNamePre$processName$timeStampFile'_memoryDetail.txt' | grep -E "TOTAL|Dalvik Heap|Native Heap" |grep -v "TOTAL:"|sed 's/Heap//g'|awk 'NR!=4{print $2}'`)

NativeMemo=${memRawList[0]}
echo NativeMemo:$NativeMemo
DalvikMemo=${memRawList[1]}
echo DalvikMemo:$DalvikMemo
TotalMemo=${memRawList[2]}
echo TotalMemo:$TotalMemo


echo `date +%Y%m%d%H%M%S`':'$currentActivity'~~'$NativeMemo'~~'$DalvikMemo'~~'$TotalMemo |tee -a $fileNamePre$processName$timeStampFile'_memoryInfo.txt'

sleep 10

fi
done

fi

done
