#!/bin/sh
chmod 600 Appendix/Rsync/USER.password

update_result=$(rsync -avzP --password-file=Appendix/Rsync/USER.password USER@172.20.102.250::USER . 2>&1 | head -n 1 | grep 'failed')

if [ "${update_result}" == "" ];then
	echo "\033[5;32mYou have been successfully updated the QA's performance tool!!!\033[0m"
        echo "\n"
	echo "\033[5;33m[The Lastest Version Info]--------comes from Verison.txt\033[0m"
	head -30 Version.txt
else
	echo "cannot connect to QA's rsync service, call fengxiaomeng01@baidu.com"
	exit

fi
