#!/bin/bash

LOG_DIR=/opt/mfg/ui/log
SCRIPTS_DIR=/opt/mfg/ui/scripts
UTILS_DIR=/opt/mfg/ui/utils

# 1, get sn
# 2, create upload file name .ok
# 3, set args of SF server
# 4, ncftpput file to SF
# 5, ncftpget file from SF
# 6, check "ERR=OK"

creat_handshake()
{

	SN=$(vpd -l |grep "serial_number" |cut -d"=" -f2|sed 's/"//g')
	((len=${#SN}-3))

	MBRST=$( echo $SN | head -c $len ).$( echo $SN | tail -c 4).OK
        BIOS=$(crossystem |grep -w "fwid"|cut -d"=" -f2|cut -d"#" -f1 |sed 's/ //g')
        echo -ne "\n MBRST is $MBRST \n" >> $LOG_DIR/fft.log

        imei=$(modem status | grep "imei" | sed 's/ //g' | cut -d ":" -f2)
        fwv=$(sudo $UTILS_DIR/com /dev/ttyUSB1 at\$qcbootver | head -n 3| tail -n 1|cut -d "-" -f 3) 
        version=$(sudo $UTILS_DIR/com /dev/ttyUSB1 at\$qcbootver | head -n 3| tail -n 1|cut -d "-" -f 3) 
        sudo $UTILS_DIR/com /dev/ttyUSB1 at+cfun=1
        main=$(sudo cat $LOG_DIR/fft.log|grep main|cut -d ":" -f 3|tail -n 1) 
        aux=$(sudo cat $LOG_DIR/fft.log|grep aux|cut -d ":" -f 3 |tail -n 1) 
        #gobimode=$(sudo $UTILS_DIR/com /dev/ttyUSB1 at+cfun? | grep CFUN)
	tmp=$(ifconfig wlan0|grep HWaddr)
	MAC=${tmp#*HWaddr}
	MAC=$(echo $MAC | sed 's/://g')
        echo $MAC
	echo "SN=$SN" > $LOG_DIR/$MBRST
	echo "Serial_Number=$SN" >> $LOG_DIR/$MBRST
	echo "motherbrd_sn=NA" >> $LOG_DIR/$MBRST
	echo "MAC=NOMAC" >> $LOG_DIR/$MBRST
	echo "GUID=NA" >> $LOG_DIR/$MBRST	
	echo "UUID=" >> $LOG_DIR/$MBRST
	echo "WLANID=$MAC" >> $LOG_DIR/$MBRST
	echo "WMAXID=" >> $LOG_DIR/$MBRST
        echo "IMEI=$imei" >> $LOG_DIR/$MBRST
        echo "3GFWVersion=$version" >>$LOG_DIR/$MBRST                     
        echo "3GHWVersion=10-VP090-3" >>$LOG_DIR/$MBRST   
        echo "3GMainRSSI=$main" >>$LOG_DIR/$MBRST  
        echo "3GAuxRSSI=$aux" >>$LOG_DIR/$MBRST  
	echo "ATT_FW=$fwv" >> $LOG_DIR/$MBRST
	echo "3Gmode=+CFUN: 1" >> $LOG_DIR/$MBRST	
        echo "BIOS=$BIOS" >> $LOG_DIR/$MBRST
    	echo "Station=FFT" >> $LOG_DIR/$MBRST
	echo "ERRCODE=PASS" >> $LOG_DIR/$MBRST
                                                                 
        $UTILS_DIR/unix2dos $LOG_DIR/$MBRST
}


uploadfft_hs()
{

#---------------------------------------------------------------------------
	monitor_server_ip=`grep 'sp_ip_fft' /opt/mfg/ui/config/factory_conf.py | cut -d"=" -f2 | sed 's/ //g' |sed "s/'//g"`                                     
	monitor_server_user="google"                
	monitor_server_passwd="google"   
    
        monitor_root_hsr="ACER_M/Handshak/"
        monitor_root_hsf="ACER_M/Finish/"


echo "start handshake"



#----------------------------------------------------------------------------
        cp $LOG_DIR/$MBRST $LOG_DIR/45Hsk.bak

	$UTILS_DIR/ncftpput -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $monitor_root_hsr/ $LOG_DIR/$MBRST
        
	if [ $? -ne 0 ]; then
		echo -ne "Put $LOG_DIR/$MBRST to $monitor_root_hsr fail!!!\n"  >> $LOG_DIR/fft.log
		exit 1
	fi
        sync
	rm $LOG_DIR/$MBRST
	if [ $? -ne 0 ]; then
		echo -ne "\nRemove $LOG_DIR/$MBRST fail !!!\n" >> $LOG_DIR/fft.log
		exit 1
	fi
        sync
#----------------------------------------------------------------------------
	sleep 2
	count=1
	$UTILS_DIR/ncftpget -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $LOG_DIR/ $monitor_root_hsf/$MBRST 
	while [	! -e $LOG_DIR/$MBRST ] && [ $count -ne 20 ]
	do
		sleep 1
		count=$(($count+1))
		echo -ne ".......Waiting for response from shop floor......\n" >> $LOG_DIR/fft.log
		$UTILS_DIR/ncftpget -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $LOG_DIR/ $monitor_root_hsf/$MBRST  
	done

	if [ $count -eq 20 ]; then
		echo -ne "\nWait for response from shop floor timeout.....\n" >> $LOG_DIR/fft.log
		exit 1
	fi

	
	sleep 1
	sync

	if [ ! -e $LOG_DIR/$MBRST ]; then
		echo -ne "\nReceive (response) error !! \n" >> $LOG_DIR/fft.log
		exit 1
	fi

#-------------------------------------------------------------------------------
	grep 'ERR_MSG=OK' $LOG_DIR/$MBRST
 	if [ $? -ne 0 ]; then
		echo -ne "Shop floor reply error !!!\n" >> $LOG_DIR/fft.log
		exit 1
	fi

	echo "rm $monitor_root_hsf/$MBRST">rmcmd.txt
	$UTILS_DIR/ncftp -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip <rmcmd.txt 
	rm -rf rmcmd.txt
	sleep 2

}

mount -o remount,rw /
sleep 2

creat_handshake

uploadfft_hs

echo -ne "45 Station is ok !!!\n" >> $LOG_DIR/fft.log
exit 0
