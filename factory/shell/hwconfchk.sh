#!/bin/bash


LOG_DIR=/opt/mfg/ui/log
SCRIPTS_DIR=/opt/mfg/ui/shdirs
UTILS_DIR=/opt/mfg/ui/utils

prepare_request()
{ 

        SN=$(vpd -l |grep "serial_number" |cut -d"=" -f2|sed 's/"//g')
        echo $SN

	((len=${#SN}-3))
	MBRST=$( echo $SN | head -c $len ).$( echo $SN | tail -c 4).OK
	MAC=`$SCRIPTS_DIR/getmac.sh`
	MAC=$(echo $MAC | sed 's/://g')

        BIOS=$(crossystem |grep -w "fwid"|cut -d"=" -f2|cut -d"#" -f1 |sed 's/ //g')
	echo "SERIAL_NUMBER=$SN" > $LOG_DIR/$MBRST
	echo "motherbrd_sn=NA" >> $LOG_DIR/$MBRST
	echo "MAC=NOMAC" >> $LOG_DIR/$MBRST
	echo "GUID=NA" >> $LOG_DIR/$MBRST
	echo "BIOS=$BIOS" >> $LOG_DIR/$MBRST
	echo "UUID=NA" >> $LOG_DIR/$MBRST
	echo "WLANID=$MAC" >> $LOG_DIR/$MBRST
	echo "WMAXID=" >> $LOG_DIR/$MBRST
	echo "ATT_FW=" >> $LOG_DIR/$MBRST
	echo "Qual3Gmode=" >> $LOG_DIR/$MBRST
        $UTILS_DIR/unix2dos $LOG_DIR/$MBRST
        sleep 3
}



checkbios_ec()
{

	DEVSW_CUR=$(crossystem |grep -w "devsw_cur"|cut -d"=" -f2|sed 's/ //g')
	if [ $DEVSW_CUR -eq 0 ];then
		echo -ne "\nPlease Enable the Dev-mode switch"\n
		exit 1
	fi
	BIOS_LOC=$(crossystem |grep -w "fwid"|cut -d"=" -f2|cut -d"#" -f1 |sed 's/ //g')
	if [ "$BIOS_LOC" != "$BIOS_SF" ];then 
		if [ ! -e $FW_DIR/bios-zgb.bin ]; then	
			echo -ne "\nBIOS fireware need upgrade,but there's no update file,Please check it!!!"\n
			exit 1
		fi
		flashrom -p internal:bus=spi -w $FW_DIR/bios-zgb.bin
		BIOS_LOC=$(crossystem |grep -w "fwid"|cut -d"=" -f2|cut -d"#" -f1 |sed 's/ //g')
		if [ "$BIOS_LOC" != "$BIOS_SF" ];then 
			echo -ne "\nUpgrade BIOS FW failed,Please check it!!!"\n
			exit 1
		fi
	fi	    

	EC_LOC=$(mosys smbios info bios|cut -d"|" -f5|sed 's/ //g')
	if [ "$EC_LOC" != "$EC_SF" ];then 
		if [ ! -e $FW_DIR/ec-zgb.bin ]; then	
			echo -ne "\nEC fireware need upgrade,but there's no update file,Please check it!!!"\n
			exit 1
		fi
		flashrom -p internal:bus=lpc -w $FW_DIR/ec-zgb.bin
		EC_LOC=$(mosys smbios info bios|cut -d"|" -f5|sed 's/ //g')
		if [ "$EC_LOC" != "$EC_SF" ];then 
			echo -ne "\nUpgrade EC FW failed,Please check it!!!"\n
			exit 1
		fi
	fi		
	

}


get_local_hwinfo()
{
	# MBSN : get from setsn()

	#CPUTYPE_LOC
	CPUTYPE_LOC=$(grep "model name" /proc/cpuinfo | head -n 1 |cut -d ":" -f2 | cut -d"@" -f1| tr   a-z   A-Z | sed 's/ //g' )
	if [ "" = "$CPUTYPE_LOC" ]; then
		echo -ne "\nReceive Error: Get local CPU type failure!!!\n"
		exit 1
	else	
		echo "CPUTYPE_LOC=" $CPUTYPE_LOC 
	fi

	#CACHESIZE_LOC
	CACHESIZE_LOC=$(grep "cache size" /proc/cpuinfo | head -n 1 |cut -d ":" -f2|cut -d " " -f2| sed 's/ //g' )
	if [ "" = "$CACHESIZE_LOC" ]; then
		echo -ne "\nReceive Error: Get local CPU cache failure!!!\n"
		exit 1
	else	
		echo "CACHESIZE_LOC=" $CACHESIZE_LOC 
	fi

	#CPUSPEED_LOC
	CPUSPEED_LOC=$(grep "model name" /proc/cpuinfo | head -1 | sed 's/ //g' |cut -d "@" -f2 | cut -d "G" -f1 )
        #((CPUSPEED_LOC=CPUSPEED_LOC * 1000))
	if [ "" = "$CPUSPEED_LOC" ]; then
		echo -ne "\nReceive Error: Get local CPU speed failure!!!\n"
		exit 1
	else	
		echo "CPUSPEED_LOC=" $CPUSPEED_LOC 
	fi

	#MEMSIZE_LOC
         
	mem=$(grep "MemTotal" /proc/meminfo |sed 's/ //g' |cut -d ":" -f2 | cut -d "k" -f1 )
        if [ $mem -ge 1017586 ] && [ $mem -le 1079296 ];then
                 MEMSIZE_LOC=1024 
        fi
	if [ "" = "$MEMSIZE_LOC" ]; then
		echo -ne "\nReceive Error: Get local Mem size failure!!!\n"
		exit 1
	else	
		echo "MEMSIZE_LOC=" $MEMSIZE_LOC 
	fi


	# SSD_LOC 
	SSD_LOC=$(hdparm -I /dev/sda |grep "Model Number" | cut -d":" -f2 | tr   a-z   A-Z | sed 's/ //g' )
	if [ "" = "$SSD_LOC" ]; then
		echo -ne "\nReceive Error: Get local SSD_Model failure!!!\n"
		exit 1
	else	
		echo "SSD_LOC=" $SSD_LOC 
	fi

	# CCD_LOC 
        CCD_LOC=$(lsusb |grep "Chicony" | cut -d " " -f6 | cut -b 1-9 | tr   a-z   A-Z )
	if [ "" = "$CCD_LOC" ]; then
		echo -ne "\nReceive Error: Get local Webcam_VID/PID failure!!!\n"
		exit 1
	else
		echo "Webcam_VID:PID=" $CCD_LOC 
	fi


	# CDC_LOC 
	CDC_LOC=$(lsusb |grep  -E "(Ericsson|Qualcomm)" | cut -d " " -f6 | cut -b 1-9 |tr   a-z   A-Z )
	if [ "" = "$CDC_LOC" ]; then
		#CDC_LOC=$(lsusb |grep  "Qualcom" | cut -d " " -f6 | cut -b 1-9|tr   a-z   A-Z)
		#if [ "" = "$CDC_LOC" ]; then
		echo -ne "\nReceive Error: Get local CDC_VID/PID failure!!!\n"
		exit 1
	else
		echo "CDC_LOC_VID:PID=" $CDC_LOC 
		#fi
		
	fi


	# BT_LOC 
	BT_LOC=$(lsusb |grep  "0489:e024" | cut -d " " -f6 | cut -b 1-9 | tr   a-z   A-Z )
	if [ "" = "$BT_LOC" ]; then
		echo -ne "\nReceive Error: Get local BT_VID/PID failure!!!\n"
		exit 1
	else
		echo "BT_LOC_VID:PID=" $BT_LOC 
	fi

	# LCD_LOC 
	

	edidfile=$(find /sys/devices/ -name edid | grep LVDS)
	if [ $? -eq 0 ]; then
		LCD_VendorName=$( parse-edid $edidfile |grep "VendorName" |cut -d "\"" -f2 |tr   a-z   A-Z)
			if [  "" = "$LCD_VendorName" ]; then
				echo -ne "\nReceive Error: Get local LCD Vendor Name failure!!!\n"
				exit 1
			else
				LCD_LOC=$LCD_VendorName
			fi
		 LCD_ModelName=$( parse-edid $edidfile |grep "ModelName" |cut -d "\"" -f2|tr   a-z   A-Z )
			if [ "" = "$LCD_ModelName" ]; then
				echo -ne "\nReceive Error: Get local LCD_ModelName failure!!!\n"
				exit 1
			else
				LCD_LOC=$LCD_LOC:$LCD_ModelName
				echo "LCD VendorName:ModelName=" $LCD_LOC
			fi
	else
		echo -ne "\nReceive Error: Get local-edid failure!\n"
		exit 1
	fi

	
	# WLAN_LOC 
	WLAN_LOC=$(lspci -nn |grep "Network controller" | cut -d "[" -f3 | cut -b 1-9|tr   a-z   A-Z)
	if [ "" = "$WLAN_LOC" ]; then
		echo -ne "\nReceive Error: Get local 3G WLAN_VID/PD failure!!!\n"
		exit 1
	else
		echo "WLAN_LOC=" $WLAN_LOC
	fi

	# BAT_LOC 
	Battery_OEM=$(cat "/proc/acpi/battery/BAT1/info" |grep "OEM info:" | cut -d ":" -f2 |tr   a-z   A-Z| sed 's/ //g')
	if [ "" = "$Battery_OEM" ]; then
		echo -ne "\nReceive Error: Get local Battery_OEM failure!!!\n"
		exit 1
	else
		echo "Battery_OEM=" $Battery_OEM 
		BAT_LOC=$Battery_OEM
	fi

	Battery_Model=$(cat "/proc/acpi/battery/BAT1/info" |grep "model number:" | cut -d ":" -f2|tr   a-z   A-Z | sed 's/ //g')
	if [ "" = "$Battery_Model" ]; then
		echo -ne "\nReceive Error: Get local Battery_Model failure!!!\n"
		exit 1
	else
		echo "Battery_Model=" $Battery_Model 
		BAT_LOC=$BAT_LOC":"$Battery_Model
	fi

	

}

checkit()
{
	
	# MBSN v.s MBSN_SF

	# SN v.s SN_SF
	if [ "$SN" != "$SN_SF" ]; then
		echo -ne "\nSN in local is: $SN not matched SN from shop floor: $SN_SF\n"
		
		exit 1
	else
		echo -ne "SN in local is: $SN  matched SN from shop floor: $SN_SF \n"
	fi

	# CPUTYPE_LOC v.s CPUTYPE_SF
	if [ "$CPUTYPE_LOC" != "$CPUTYPE_SF" ]; then
		echo -ne "\nCPU type in local is: $CPUTYPE_LOC not matched CPU type from shop floor: $CPUTYPE_SF\n"
		
		exit 1
	else
		echo -ne "CPU type in local is: $CPUTYPE_LOC  matched CPU type from shop floor: $CPUTYPE_SF \n"
	fi

	# CACHESIZE_LOC v.s CACHESIZE_SF
	if [ "$CACHESIZE_LOC" != "$CACHESIZE_SF" ]; then
		echo -ne "\nCache size in local is: $CACHESIZE_LOC not matched Cache size from shop floor: $CACHESIZE_SF\n"
		
		exit 1
	else
		echo -ne "Cache size in local is: $CACHESIZE_LOC  matched Cache size from shop floor: $CACHESIZE_SF \n"
	fi

	# CPUSPEED_LOC v.s CPUSPEED_SF
	if [ "$CPUSPEED_LOC" != "$CPUSPEED_SF" ]; then
		echo -ne "\nCPU speed in local is: $CPUSPEED_LOC not matched CPU speed from shop floor: $CPUSPEED_SF\n"
		
		exit 1
	else
		echo -ne "CPU speed in local is: $CPUSPEED_LOC  matched CPU speed from shop floor: $CPUSPEED_SF \n"
	fi
	# MEMSIZE_LOC v.s MEMSIZE_SF
	if [ "$MEMSIZE_LOC" != "$MEMSIZE_SF" ]; then
		echo -ne "\nMemory size type in local is: $MEMSIZE_LOC not matched Memory size from shop floor: $MEMSIZE_SF\n"
		
		exit 1
	else
		echo -ne "Memory size in local is: $MEMSIZE_LOC  matched Memory size from shop floor: $MEMSIZE_SF \n"
	fi

	# SSD_LOC v.s SSD_SF
	if [ "$SSD_LOC" != "$SSD_SF" ]; then
		echo -ne "\nSSD in local is: $SSD_LOC not matched SSD from shop floor: $SSD_SF \n"
		
		exit 1
	else
		echo -ne "SSD in local is: $SSD_LOC  matched SSD from shop floor: $SSD_SF \n"
	fi

	# CCD_LOC v.s CCD_SF
	if [ "$CCD_LOC" != "$CCD_SF" ]; then
		echo -ne "\nCCD in local is: $CCD_LOC not matched CCD from shop floor: $CCD_SF \n"
		
		exit 1
	else	
		echo -ne "CCD in local is: $CCD_LOC  matched CCD from shop floor: $CCD_SF \n"
	fi

	# CDC_LOC v.s CDC_SF
	if [ "$CDC_LOC" != "$CDC_SF" ]; then
		echo -ne "\n3G in local is: $CDC_LOC not matched 3G from shop floor: $CDC_SF \n"
		
		exit 1
	else
		echo -ne "3G in local is: $CDC_LOC   matched 3G from shop floor: $CDC_SF \n"
	fi	

	# BT_LOC v.s BT_SF
	if [ "$BT_LOC" != "$BT_SF" ]; then
		echo -ne "\nBT in local is: $BT_LOC not matched BT from shop floor: $BT_SF \n"
		
		exit 1
	else
		echo -ne "BT in local is: $BT_LOC  matched BT from shop floor: $BT_SF \n"
	fi	

	# LCD_LOC v.s LCD_SF
	if [ "$LCD_LOC" != "$LCD_SF" ]; then
		echo -ne "\nLCD in local is: $LCD_LOC not matched LCD from shop floor: $LCD_SF \n"
		
		exit 1
	else
		echo -ne "LCD in local is: $LCD_LOC   matched LCD from shop floor: $LCD_SF \n"
	fi		

	# WLAN_LOC v.s WLAN_SF
	if [ "$WLAN_LOC" != "$WLAN_SF" ]; then
		echo -ne "\nWLAN in local is: $WLAN_LOC not matched WLAN from shop floor: $WLAN_SF\n"
		
		exit 1
	else
		echo -ne "WLAN in local is: $WLAN_LOC matched WLAN from shop floor: $WLAN_SF \n"
	fi			

	# BAT_LOC v.s BAT_SF
	if [ "$BAT_LOC" != "$BAT_SF" ]; then
		echo -ne "\nBAT in local is: $BAT_LOC not matched BAT from shop floor: $BAT_SF \n"
		
		exit 1
	else	
		echo -ne "BAT in local is: $BAT_LOC matched BAT from shop floor: $BAT_SF \n"
	fi		

}

creat_request()
{
	
	#---------------------------------------------------------------------------
    	SN=$(vpd -l |grep "serial_number" |cut -d"=" -f2|sed 's/"//g')
	((len=${#SN}-3))
	MBRST=$( echo $SN | head -c $len ).$( echo $SN | tail -c 4).OK 
        echo -ne "\n MBRST is $MBRST \n" >> $LOG_DIR/fft.log

#---------------------------------------------------------------------------
        BIOS=$(crossystem |grep -w "fwid"|cut -d"=" -f2|cut -d"#" -f1 |sed 's/ //g')

        #sudo $UTILS_DIR/com /dev/ttyUSB1 at+cfun=5
	#modem_set_carrier "Generic UMTS"
	#sleep 15
	HWID=$(corssystem hwid|sed 's/ /_/g')
grep "id_3g': \[''\]" /opt/mfg/ui/grt/chromeos-hwid/components_$HWID
if [ $? -eq 0 ];then
	ThreeG=0
	echo "No Gobi"
else        
        imei=$(modem status | grep "imei" | sed 's/ //g' | cut -d ":" -f2)
        imei_times=0
        while [ -z "$imei" ] 
        do
        imei=$(modem status | grep "imei" | sed 's/ //g' | cut -d ":" -f2)
        ((imei_times=imei_times+1))
        sleep 3
        if [ $imei_times -eq 5 ];then
	echo "cannot get imei" >>$LOG_DIR/fft.log
	exit 1
        fi
        done 
	
        meid=$(modem status | grep "meid" | sed 's/ //g' | cut -d ":" -f2)
        meid_times=0
        while [ -z "$meid" ] 
        do
        meid=$(modem status | grep "meid" | sed 's/ //g' | cut -d ":" -f2)
        ((meid_times=meid_times+1))
        sleep 3
        if [ $meid_times -eq 5 ];then
	echo "cannot get meid" >>$LOG_DIR/fft.log
	exit 1
        fi
        done 
	
	fwr=$(modem status | grep "firmware_revision" | sed 's/ //g' | cut -d ":" -f2)

	pv=$(modem status | grep "prl_version" | sed 's/ //g' | cut -d ":" -f2)

              
        fwv=$(sudo $UTILS_DIR/com /dev/ttyUSB1 at\$qcbootver | head -n 3| tail -n 1|cut -d "-" -f 3) 
        version=$(sudo $UTILS_DIR/com /dev/ttyUSB1 at\$qcbootver | head -n 3| tail -n 1|cut -d "-" -f 3) 

        main=$(sudo cat $LOG_DIR/fft.log |grep main|cut -d ":" -f 3|tail -n 1) 
        aux=$(sudo cat $LOG_DIR/fft.log |grep aux |cut -d ":" -f 3 |tail -n 1) 
fi

	#gobimode=$(sudo $UTILS_DIR/com /dev/ttyUSB1 at+cfun? | grep CFUN)
        #$UTILS_DIR/com /dev/ttyUSB1 at+cfun=1
        #carrer=$(vpd -l 2>/dev/null |grep CARRIER |cut -d"=" -f2|sed 's/"//g')
        #modem_set_carrier "$carrer" 
        #sleep 5
        

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
 	echo "MEID=$meid" >> $LOG_DIR/$MBRST
        echo "3GFWVersion=$version" >>$LOG_DIR/$MBRST                     
        echo "3GHWVersion=10-VP090-3" >>$LOG_DIR/$MBRST   
        echo "3GMainRSSI=$main" >>$LOG_DIR/$MBRST  
        echo "3GAuxRSSI=$aux" >>$LOG_DIR/$MBRST  
	echo "ATT_FW=$fwv" >> $LOG_DIR/$MBRST
	echo "3Gmode=+CFUN: 1" >> $LOG_DIR/$MBRST	
        echo "BIOS=$BIOS" >> $LOG_DIR/$MBRST
	echo "FW_Revision=$fwr" >>$LOG_DIR/$MBRST
	echo "Prl_version=$pv" >>$LOG_DIR/$MBRST
    	echo "Station=FFT" >> $LOG_DIR/$MBRST
	echo "ERRCODE=PASS" >> $LOG_DIR/$MBRST
                                                                 
        $UTILS_DIR/unix2dos $LOG_DIR/$MBRST
}
get_sf_response()
{

	monitor_server_ip=`grep 'sp_ip_fft' /opt/mfg/ui/config/factory_conf.py | cut -d"=" -f2 | sed 's/ //g' |sed "s/'//g"`                                     
	monitor_server_user="google"                
	monitor_server_passwd="google"   
    
	monitor_request="ACER_M/Request/"
	monitor_response="ACER_M/Response/"


#----------------------------------------------------------------------------
	$UTILS_DIR/ncftpput -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $monitor_request/ $LOG_DIR/$MBRST
        
	if [ $? -ne 0 ]; then
		echo -ne "Put $LOG_DIR/$MBRST to $monitor_request fail!!!\n"  >> $LOG_DIR/fft.log
		exit 1
	fi
        sync
	mv $LOG_DIR/$MBRST $LOG_DIR/D2Rqs.bak
	if [ $? -ne 0 ]; then
		echo -ne "\nRename $LOG_DIR/$MBRST fail !!!\n" >> $LOG_DIR/fft.log
		exit 1
	fi
        sync
#----------------------------------------------------------------------------
	sleep 2
	count=1
	$UTILS_DIR/ncftpget -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $LOG_DIR/ $monitor_response/$MBRST 
	while [	! -e $LOG_DIR/$MBRST ] && [ $count -ne 20 ]
	do
		sleep 1
		count=$(($count+1))
		echo -ne ".......Waiting for response from shop floor......\n" >> $LOG_DIR/fft.log
		$UTILS_DIR/ncftpget -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $LOG_DIR/ $monitor_response/$MBRST 
	done

	if [ $count -eq 20 ]; then
		echo -ne "\nWait for response(request) from shop floor timeout.....\n" >> $LOG_DIR/fft.log
		exit 1
	fi

	echo -ne "\n\n"
	
	sleep 1
	sync

	if [ ! -e $LOG_DIR/$MBRST ]; then
		echo -ne "\nReceive (response) error !! \n" >> $LOG_DIR/fft.log
		exit 1
	fi

        grep 'ERR_MSG' $LOG_DIR/$MBRST
        if [ $? -eq 0 ]; then
		echo -ne "Shop-floor reply error !! \n" >> $LOG_DIR/fft.log
		exit 1
        fi      
	echo "rm $monitor_response/$MBRST">rmcmd.txt
	$UTILS_DIR/ncftp -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip <rmcmd.txt 
        	
        rm -rf rmcmd.txt
	sleep 2

	mv $LOG_DIR/$MBRST $LOG_DIR/D2Rsp.bak
	#echo -ne "D2 Station is ok !!!\n" >> $LOG_DIR/fft.log
}



#prepare_request



#checkbios_ec

#get_local_hwinfo

#check_it

creat_request

get_sf_response

exit 0
