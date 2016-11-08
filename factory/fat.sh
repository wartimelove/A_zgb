#!/bin/bash
echo "OPTIND starts at $OPTIND"
while getopts ":pq:" optname
do
    case "$optname" in
    "p")
        echo "Option $optname is specified"
        ;;
    "q")
        echo "Option $optname has value $OPTARG"
        ;;
    "?")
        echo "Unknown option $OPTARG"
        ;;
    ":")
        echo "No argument value for option $OPTARG"
        ;;
    *)
        # Should not occur
        echo "Unknown error while processing options"
        ;;
    esac
    echo "OPTIND is now $OPTIND"
done#!/bin/bash

# EEPROM Mapping
# 0x4A - 0x4F WiMax MAC ID
# 0x60 - 0x75 Serial Number
# 0xA0 - 0xAF Product Name
# 0xB0 - 0xBE Manufacture Name
# 0xBF        Manufacture Mode (0x46)
# 0xC0 - 0xCF UUID
# 0xD0 - 0xD9 3G module IMEI
# 0xDA - 0xDF Local Country Coe
# 0xE0 - 0xEF MB serial number
# 0xF0 - 0xF5 WLAN MAC ID

# Hardware configure check
# 1. M/B SN
# 2. SSD vid/pid/cap
# 3. Webcam vid/pid
# 4. 3G vid/pid
# 5. BT vid/pid
# 6. LCD vid/pid
# 7. WLAN vid/pid
# 8. Battery vid/pid
# 9. CPU type
#10. CPU speed
#11. CPU cache
#12. Memory size
#13. BIOS Version
#14. EC Version

source config/path.sh
echo "Start FAT"
sleep 2
mount -o remount rw, /
python /opt/mfg/ui/pydirs/zgb_ec_bt_factory.py

initializeANSI()
{
	esc=" "
	blackf="\033[30m"
	redf="\033[31m"
	greenf="\033[32m"
	yellowf="\033[33m"
	bluef="\033[34m"
	purplef="\033[35m"
	cyanf="\033[36m"
	whiftf="\033[37m"

	blackb="\033[40m"
	redb="\033[41m"
	greenb="\033[42m"
	yellowb="\033[43m"
	blueb="\033[44m"
	purpleb="\033[45m"
	
	boldon="\033[1m"
	boldoff="\033[22m"
	italicson="\033[3m"
	italicsoff="\033[23m"
	ulon="\033[4m"
	uloff="\033[24m"
	invon="\033[7m"
	invoff="\033[27m"

	reset="\033[0m"

}

showfail()
{
echo 
	echo -ne "                    $redb$blackf ########## Please contact engineers to check defect failure symptoms ########## $reset\n\n"
	echo -ne "                    $redb$blackf ############################################################################### $reset\n\n"
	echo -ne "                    $redb$blackf ******************************************************************************* $reset\n\n"
	echo -ne "                    $redb$blackf ******************************************************************************* $reset\n\n"
	echo -ne "                    $redb$blackf ********************  Failed !!!! Failed !!!! Failed !!! ********************** $reset\n\n"
	echo -ne "                    $redb$blackf ********************  Failed !!!! Failed !!!! Failed !!! ********************** $reset\n\n"
	echo -ne "                    $redb$blackf ********************  Failed !!!! Failed !!!! Failed !!! ********************** $reset\n\n"
	echo -ne "                    $redb$blackf ********************  Failed !!!! Failed !!!! Failed !!! ********************** $reset\n\n"
	echo -ne "                    $redb$blackf ********************  Failed !!!! Failed !!!! Failed !!! ********************** $reset\n\n"
	echo -ne "                    $redb$blackf ********************  Failed !!!! Failed !!!! Failed !!! ********************** $reset\n\n"
	echo -ne "                    $redb$blackf ********************  Failed !!!! Failed !!!! Failed !!! ********************** $reset\n\n"
	echo -ne "                    $redb$blackf ******************************************************************************* $reset\n\n"
	echo -ne "                    $redb$blackf ******************************************************************************* $reset\n\n"
	echo -ne "                    $redb$blackf ############################################################################### $reset\n\n"	
	echo -ne "                    $redb$blackf ########## Please contact engineers to check defect failure symptoms ########## $reset\n\n"
}


setsn()
{ 
	SN=$(vpd -l |grep "serial_number" |cut -d"=" -f2|sed 's/"//g')
	if [ "$SN" == "" ] || [ ${#SN} -ne 22 ];then
            while [ "$SN" == "" ] || [ ${#SN} -ne 22 ]
            do 
              read -n 22 -p "input serial number: " SN
              sleep 1
            done	

            #vpd -s sn="$SN"
            #check_vpd sn $SN
	 fi



	((len=${#SN}-3))
	MBRST=$( echo $SN | head -c $len ).$( echo $SN | tail -c 4).OK


	echo -e "SN=$SN" > $LOG_DIR/$MBRST
	echo -e "MACID=NOMAC" >> $LOG_DIR/$MBRST
	echo -e "MBSN=NA" >> $LOG_DIR/$MBRST
	$UTILS_DIR/unix2dos $LOG_DIR/$MBRST	

}

getconf_sf()
{
	
	monitor_server_ip="192.168.2.90"
	monitor_server_user="google"
	monitor_server_passwd="google"
	monitor_request="Request"
	monitor_response="Response"
        monitor_root="TMON"


	#modprobe cifs
	#/sbin/mount.cifs //$monitor_server_ip/ZGA_TM $monitor_root -o username=$monitor_user,password=$monitor_passwd
	

	$UTILS_DIR/ncftpput -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $monitor_root/$monitor_request/ $LOG_DIR/$MBRST
	if [ $? -ne 0 ]; then
		echo -ne "Put $LOG_DIR/$MBRST to $monitor_root/$monitor_request fail!!!\n"
		showfail
		exit
	fi
	rm $LOG_DIR/$MBRST
	if [ $? -ne 0 ]; then
		echo -ne "\n${redb}${whitef}Remove $LOG_DIR/$MBRST fail !!!${reset}\n"
		showfail
		exit
	fi

	count=1
	#$UTILS_DIR/ncftpget -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $LOG_DIR/ $monitor_root/$monitor_response/$MBRST 
	while [	! -e $LOG_DIR/$MBRST ] && [ $count -ne 20 ]
	do
		sleep 1
		count=$(($count+1))
		echo -ne ".......Waiting for response from shop floor......\n"
		$UTILS_DIR/ncftpget -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $LOG_DIR/ $monitor_root/$monitor_response/$MBRST 
	done

	if [ $count -eq 20 ]; then
		echo -ne "\n${redb}${whitef}.......Wait for response(FAT Request_Response)from shop floor timeout.....${reset}\n"
		showfail
		exit 1
	fi

	echo -ne "\n\n"

	sync;sync;sync

	if [ ! -e $LOG_DIR/$MBRST ]; then
		echo -ne "\n${redb}${whitef}Receive response error(FAT Request_Response) !! Please check it.  ${reset}\n"
		showfail
		exit 1
	fi

	grep 'SF_CFG_CHK=PASS' $LOG_DIR/$MBRST
 	if [ $? -ne 0 ]; then
		echo -ne "\n${redb}${whitef}Shop floor reply error !!!(FAT Request_Response)${reset}\n"
		echo -ne "\n${redb}${whitef} `less $LOG_DIR/$MBRST` ${reset}\n"
		#showfail
		exit 1
	else
		`sed -i 's/\r//g' $LOG_DIR/$MBRST`

		BIOS_SF=`grep 'BIDNum' $LOG_DIR/$MBRST | cut -d"=" -f2`
		EC_SF=`grep 'EC_VER' $LOG_DIR/$MBRST | cut -d"=" -f2`
		HWID_SF=`grep 'HWID' $LOG_DIR/$MBRST | cut -d"=" -f2 | sed 's/ /_/g'`
		KB_LAYOUT_SF=`grep 'KB_LAYOUT' $LOG_DIR/$MBRST | cut -d"=" -f2`
		LOCALE_SF=`grep 'LOCALE' $LOG_DIR/$MBRST |  cut -d"=" -f2`
 		T_ZONE_SF=`grep 'T_ZONE' $LOG_DIR/$MBRST |  cut -d"=" -f2`
		CARRIER_SF=`grep 'CARRIER' $LOG_DIR/$MBRST |  cut -d"=" -f2`

		SN_SF=`grep 'SET SN' $LOG_DIR/$MBRST | sed 's/ //g'| awk -F'=' '{print $2}'`
		SSD_SF=`grep 'hdd_size' $LOG_DIR/$MBRST | sed 's/_/:/' | sed 's/ //g'| awk -F'=' '{print $2}'`	
		CPUTYPE_SF=`grep 'cpu_type' $LOG_DIR/$MBRST | sed 's/_/:/' | sed 's/ //g'| awk -F'=' '{print $2}'`	
		CACHESIZE_SF=`grep 'cache_size' $LOG_DIR/$MBRST | sed 's/_/:/' | sed 's/ //g'| awk -F'=' '{print $2}'`
		CPUSPEED_SF=`grep 'cpu_speed' $LOG_DIR/$MBRST | sed 's/_/:/' | sed 's/ //g'| awk -F'=' '{print $2}'`
		MEMSIZE_SF=`grep 'ram_size' $LOG_DIR/$MBRST | sed 's/_/:/' | sed 's/ //g'| awk -F'=' '{print $2}'`
		CCD_SF=`grep 'ccd' $LOG_DIR/$MBRST | sed 's/_/:/' | sed 's/ //g'| awk -F'=' '{print $2}'`
		CDC_SF=`grep 'ThreeG' $LOG_DIR/$MBRST | sed 's/_/:/' | sed 's/ //g'| awk -F'=' '{print $2}'`
		BT_SF=`grep 'BT' $LOG_DIR/$MBRST | sed 's/_/:/' | sed 's/ //g'| awk -F'=' '{print $2}'`
		LCD_SF=`grep 'display_size' $LOG_DIR/$MBRST | sed 's/_/:/g' | sed 's/ //g'| awk -F'=' '{print $2}'`
		WLAN_SF=`grep 'aux1' $LOG_DIR/$MBRST | sed 's/_/:/' | sed 's/ //g'| awk -F'=' '{print $2}'`
		BAT_SF=`grep 'bat_type' $LOG_DIR/$MBRST | sed 's/_/:/g' | sed 's/ //g'| awk -F'=' '{print $2}'`
	fi

	echo "rm $monitor_root/$monitor_response/$MBRST">rmcmd.txt
	$UTILS_DIR/ncftp -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip <rmcmd.txt 
	rm -rf rmcmd.txt
	sleep 2
}

checkbios_ec()
{


	BIOS_LOC=$(crossystem fwid)
	if [ "$BIOS_LOC" != "$BIOS_SF" ];then 
		echo -ne "\n${redb}${whitef}Local BIOS fireware version is: $BIOS_LOC  not matched with SF($BIOS_SF) ,Please check it!!!${reset}\n"
		showfail
		exit 1
	fi	    

	EC_LOC=$(mosys ec info |cut -d"|" -f3|sed 's/ //g')
	if [ "$EC_LOC" != "$EC_SF" ];then 
		echo -ne "\n${redb}${whitef}Loca EC fireware version is:$EC_LOC not matched withd SF($EC_SF) ,Please check it!!!${reset}\n"
		showfail
		exit 1
	fi

}


getconf_local()
{
	# MBSN : get from setsn()

	#CPUTYPE_LOC
	CPUTYPE_LOC=$(grep "model name" /proc/cpuinfo | head -n 1 |cut -d ":" -f2 | cut -d"@" -f1| tr   a-z   A-Z | sed 's/ //g' )
	if [ "" = "$CPUTYPE_LOC" ]; then
		echo -ne "\n${redb}${whitef}Receive Error: Get local CPU type failure!!!${reset}\n"
		showfail
		exit 1
	else	
		echo "CPUTYPE_LOC=" $CPUTYPE_LOC 
	fi

	#CACHESIZE_LOC
	CACHESIZE_LOC=$(grep "cache size" /proc/cpuinfo | head -n 1 |cut -d ":" -f2|cut -d " " -f2| sed 's/ //g' )
	if [ "" = "$CACHESIZE_LOC" ]; then
		echo -ne "\n${redb}${whitef}Receive Error: Get local CPU cache failure!!!${reset}\n"
		showfail
		exit 1
	else	
		echo "CACHESIZE_LOC=" $CACHESIZE_LOC 
	fi

	#CPUSPEED_LOC
	CPUSPEED_LOC=$(grep "model name" /proc/cpuinfo | head -1 | sed 's/ //g' |cut -d "@" -f2 | cut -d "G" -f1 )
        #((CPUSPEED_LOC=CPUSPEED_LOC * 1000))
	if [ "" = "$CPUSPEED_LOC" ]; then
		echo -ne "\n${redb}${whitef}Receive Error: Get local CPU speed failure!!!${reset}\n"
		showfail
		exit 1
	else	
		echo "CPUSPEED_LOC=" $CPUSPEED_LOC 
	fi

	#MEMSIZE_LOC
         
	mem=$(grep "MemTotal" /proc/meminfo |sed 's/ //g' |cut -d ":" -f2 | cut -d "k" -f1 )
        if [ $mem -ge 1907586 ] && [ $mem -le 2098296 ];then
                 MEMSIZE_LOC=2048
        fi
	#mem=$(mosys -l memory spd print geometry|grep size_mb |cut -d"|" -f2|sed 's/ //g')
	if [ "" = "$MEMSIZE_LOC" ]; then
		echo -ne "\n${redb}${whitef}Receive Error: Get local Mem size failure!!!${reset}\n"
		showfail
		exit 1
	else	
		echo "MEMSIZE_LOC=" $MEMSIZE_LOC 
	fi


	# SSD_LOC 
	SSD_LOC=$(hdparm -I /dev/sda |grep "Model Number" | cut -d":" -f2 | tr   a-z   A-Z | sed 's/ //g' )
	if [ "" = "$SSD_LOC" ]; then
		echo -ne "\n${redb}${whitef}Receive Error: Get local SSD_Model failure!!!${reset}\n"
		showfail
		exit 1
	else	
		echo "SSD_LOC=" $SSD_LOC 
	fi

	# CCD_LOC 
#	CCD_LOC=$(dmesg |grep "ucvvideo:" | cut -d "(" -f2 | cut -b 1-9 | tr   a-z   A-Z )
        CCD_LOC=$(lsusb |grep "Chicony" | cut -d " " -f6 | cut -b 1-9 | tr   a-z   A-Z )
	if [ "" = "$CCD_LOC" ]; then
		echo -ne "\n${redb}${whitef}Receive Error: Get local Webcam_VID/PID failure!!!${reset}\n"
		showfail
		exit 1
	else
		echo "Webcam_VID:PID=" $CCD_LOC 
	fi

grep "id_3g': \[''\]" /opt/mfg/ui/grt/chromeos-hwid/components_$HWID_SF
if [ $? -eq 0 ];then
	ThreeG=0
	echo "No Gobi"
else
        ThreeG=1
	# CDC_LOC 
	CDC_LOC=$(lsusb |grep  -E "(Ericsson|Qualcomm)" | cut -d " " -f6 | cut -b 1-9 |tr   a-z   A-Z )
	if [ "" = "$CDC_LOC" ]; then
		#CDC_LOC=$(lsusb |grep  "Qualcom" | cut -d " " -f6 | cut -b 1-9|tr   a-z   A-Z)
		#if [ "" = "$CDC_LOC" ]; then
		echo -ne "\n${redb}${whitef}Receive Error: Get local CDC_VID/PID failure!!!${reset}\n"
		showfail
		exit 1
	else
		echo "CDC_LOC_VID:PID=" $CDC_LOC 
		#fi
		
	fi
fi

	# BT_LOC 
        BT_LOC=$(lsusb |grep  "0cf3:3005" | cut -d " " -f6 | cut -b 1-9 | tr   a-z   A-Z )
	if [ "" = "$BT_LOC" ]; then
		echo -ne "\n${redb}${whitef}Receive Error: Get local BT_VID/PID failure!!!${reset}\n"
		showfail
		exit 1
	else
		echo "BT_LOC_VID:PID=" $BT_LOC 
	fi

	# LCD_LOC 
	
   	  #get-edid > $LOG_DIR/EDID.log
	  edidfile=$(find /sys/devices/ -name edid | grep LVDS)
	  if [ $? -eq 0 ]; then
		 LCD_VendorName=$( parse-edid $edidfile |grep "VendorName" |cut -d "\"" -f2 |tr   a-z   A-Z)
			if [  "" = "$LCD_VendorName" ]; then
				echo -ne "\n${redb}${whitef}Receive Error: Get local LCD Vendor Name failure!!!${reset}\n"
				showfail
				exit 1
			else
				LCD_LOC=$LCD_VendorName
			fi
		 LCD_ModelName=$( parse-edid $edidfile |grep "ModelName" |cut -d "\"" -f2|tr   a-z   A-Z )
			if [ "" = "$LCD_ModelName" ]; then
				echo -ne "\n${redb}${whitef}Receive Error: Get local LCD_ModelName failure!!!${reset}\n"
				showfail
				exit 1
			else
				LCD_LOC=$LCD_LOC:$LCD_ModelName
				echo "LCD VendorName:ModelName=" $LCD_LOC
			fi
	else
		echo -ne "\n${redb}${whitef}Receive Error: Get local-edid failure!\n${reset}"
		showfail
		exit 1
	fi

	
	# WLAN_LOC 
	WLAN_LOC=$(lspci -nn |grep "Network controller" | cut -d "[" -f3 | cut -b 1-9|tr   a-z   A-Z)
	if [ "" = "$WLAN_LOC" ]; then
		echo -ne "\n${redb}${whitef}Receive Error: Get local 3G WLAN_VID/PD failure!!!${reset}\n"
		showfail
		exit 1
	else
		echo "WLAN_LOC=" $WLAN_LOC
	fi

	# BAT_LOC 
	Battery_OEM=$(cat "/proc/acpi/battery/BAT1/info" |grep "OEM info:" | cut -d ":" -f2 |tr   a-z   A-Z| sed 's/ //g')
	if [ "" = "$Battery_OEM" ]; then
		echo -ne "\n${redb}${whitef}Receive Error: Get local Battery_OEM failure!!!${reset}\n"
		showfail
		exit 1
	else
		echo "Battery_OEM=" $Battery_OEM 
		BAT_LOC=$Battery_OEM
	fi

	Battery_Model=$(cat "/proc/acpi/battery/BAT1/info" |grep "model number:" | cut -d ":" -f2|tr   a-z   A-Z | sed 's/ //g')
	if [ "" = "$Battery_Model" ]; then
		echo -ne "\n${redb}${whitef}Receive Error: Get local Battery_Model failure!!!${reset}\n"
		showfail
		exit 1
	else
		echo "Battery_Model=" $Battery_Model 
		BAT_LOC=$BAT_LOC":"$Battery_Model
	fi

	

}

checkit()
{

	if [ "$HWID_SF" == "" ] || [ "$KB_LAYOUT_SF" == "" ] || [ "$LOCALE_SF" == "" ] || [ "$T_ZONE_SF" == "" ] || [ "$CARRIER_SF" == "" ]; then
		echo -ne "\n${redb}${whitef}hwid("$HWID_SF") or kb_layout("$KB_LAYOUT_SF") or locale("$LOCALE_SF") or time_zone("$T_ZONE_SF") or carrier("$CARRIER_SF")  data from shop-floor is  empty !!{reset}\n"
		showfail
		exit 1
	fi

	
	
	# MBSN v.s MBSN_SF

	# SN v.s SN_SF
	if [ "$SN" != "$SN_SF" ]; then
		echo -ne "\n${redb}${whitef}SN in local is: $SN not matched SN from shop floor: $SN_SF${reset}\n"
		showfail
		exit 1
	else
		echo -ne "SN in local is: $SN  matched SN from shop floor: $SN_SF \n"
	fi

	# CPUTYPE_LOC v.s CPUTYPE_SF
	if [ "$CPUTYPE_LOC" != "$CPUTYPE_SF" ]; then
		echo -ne "\n${redb}${whitef}CPU type in local is: $CPUTYPE_LOC not matched CPU type from shop floor: $CPUTYPE_SF${reset}\n"
		showfail
		exit 1
	else
		echo -ne "CPU type in local is: $CPUTYPE_LOC  matched CPU type from shop floor: $CPUTYPE_SF \n"
	fi

	# CACHESIZE_LOC v.s CACHESIZE_SF
	if [ "$CACHESIZE_LOC" != "$CACHESIZE_SF" ]; then
		echo -ne "\n${redb}${whitef}Cache size in local is: $CACHESIZE_LOC not matched Cache size from shop floor: $CACHESIZE_SF${reset}\n"
		showfail
		exit 1
	else
		echo -ne "Cache size in local is: $CACHESIZE_LOC  matched Cache size from shop floor: $CACHESIZE_SF \n"
	fi

	# CPUSPEED_LOC v.s CPUSPEED_SF
	if [ "$CPUSPEED_LOC" != "$CPUSPEED_SF" ]; then
		echo -ne "\n${redb}${whitef}CPU speed in local is: $CPUSPEED_LOC not matched CPU speed from shop floor: $CPUSPEED_SF${reset}\n"
		showfail
		exit 1
	else
		echo -ne "CPU speed in local is: $CPUSPEED_LOC  matched CPU speed from shop floor: $CPUSPEED_SF \n"
	fi
	# MEMSIZE_LOC v.s MEMSIZE_SF
	if [ "$MEMSIZE_LOC" != "$MEMSIZE_SF" ]; then
		echo -ne "\n${redb}${whitef}Memory size type in local is: $MEMSIZE_LOC not matched Memory size from shop floor: $MEMSIZE_SF${reset}\n"
		showfail
		exit 1
	else
		echo -ne "Memory size in local is: $MEMSIZE_LOC  matched Memory size from shop floor: $MEMSIZE_SF \n"
	fi

	# SSD_LOC v.s SSD_SF
	if [ "$SSD_LOC" != "$SSD_SF" ]; then
		echo -ne "\n${redb}${whitef}SSD in local is: $SSD_LOC not matched SSD from shop floor: $SSD_SF ${reset}\n"
		showfail
		exit 1
	else
		echo -ne "SSD in local is: $SSD_LOC  matched SSD from shop floor: $SSD_SF \n"
	fi

	# CCD_LOC v.s CCD_SF
	if [ "$CCD_LOC" != "$CCD_SF" ]; then
		echo -ne "\n${redb}${whitef}CCD in local is: $CCD_LOC not matched CCD from shop floor: $CCD_SF ${reset}\n"
		showfail
		exit 1
	else	
		echo -ne "CCD in local is: $CCD_LOC  matched CCD from shop floor: $CCD_SF \n"
	fi




if [ $ThreeG -eq 0 ];then
	echo "No Gobi"
else
	# CDC_LOC v.s CDC_SF
	if [ "$CDC_LOC" != "$CDC_SF" ]; then
		echo -ne "\n${redb}${whitef}3G in local is: $CDC_LOC not matched 3G from shop floor: $CDC_SF ${reset}\n"
		showfail
		exit 1
	else
		echo -ne "3G in local is: $CDC_LOC   matched 3G from shop floor: $CDC_SF \n"
	fi	
fi



	# BT_LOC v.s BT_SF
	if [ "$BT_LOC" != "$BT_SF" ]; then
		echo -ne "\n${redb}${whitef}BT in local is: $BT_LOC not matched BT from shop floor: $BT_SF ${reset}\n"
	        showfail
		exit 1
	else
		echo -ne "BT in local is: $BT_LOC  matched BT from shop floor: $BT_SF \n"
	fi	

	# LCD_LOC v.s LCD_SF
	if [ "$LCD_LOC" != "$LCD_SF" ]; then
		echo -ne "\n${redb}${whitef}LCD in local is: $LCD_LOC not matched LCD from shop floor: $LCD_SF${reset} \n"
		showfail
		exit 1
	else
		echo -ne "LCD in local is: $LCD_LOC   matched LCD from shop floor: $LCD_SF \n"
	fi		

	# WLAN_LOC v.s WLAN_SF
	if [ "$WLAN_LOC" != "$WLAN_SF" ]; then
		echo -ne "\n${redb}${whitef}WLAN in local is: $WLAN_LOC not matched WLAN from shop floor: $WLAN_SF${reset}\n"
		showfail
		exit 1
	else
		echo -ne "WLAN in local is: $WLAN_LOC matched WLAN from shop floor: $WLAN_SF \n"
	fi			

	# BAT_LOC v.s BAT_SF
	if [ "$BAT_LOC" != "$BAT_SF" ]; then
		echo -ne "\n${redb}${whitef}BAT in local is: $BAT_LOC not matched BAT from shop floor: $BAT_SF ${reset}\n"
		showfail
		exit 1
	else	
		echo -ne "BAT in local is: $BAT_LOC matched BAT from shop floor: $BAT_SF \n"
	fi		

}

uploadFAT_hs()
{
	
	echo "Serial_Number=$SN" > $LOG_DIR/$MBRST
	echo "MAC=NOMAC" >> $LOG_DIR/$MBRST
	echo "MBSN=NA" >> $LOG_DIR/$MBRST
	echo "BIOS=$BIOS_LOC" >>$LOG_DIR/$MBRST

	echo "LINE=" >> $LOG_DIR/$MBRST
	$UTILS_DIR/unix2dos $LOG_DIR/$MBRST

	monitor_response="Finish"
	monitor_request="Handshake"
	
	$UTILS_DIR/ncftpput -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $monitor_root/$monitor_request/ $LOG_DIR/$MBRST
	if [ $? -ne 0 ]; then
		echo -ne "Put $LOG_DIR/$MBRST to $monitor_root/$monitor_request fail!!!\n"
		showfail
		exit
	fi
	
	rm $LOG_DIR/$MBRST
	if [ $? -ne 0 ]; then
		echo -ne "\n${redb}${whitef}Remove $LOG_DIR/$MBRST fail !!!${reset}\n"
		showfail
		exit
	fi
	count=1
	#$UTILS_DIR/ncftpget -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $LOG_DIR/ $monitor_root/$monitor_response/$MBRST 
	while [	! -e $LOG_DIR/$MBRST ] && [ $count -ne 20 ]
	do
		sleep 1
		count=$(($count+1))
		echo -ne ".......Waiting for response from shop floor......\n"
		$UTILS_DIR/ncftpget -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $LOG_DIR/ $monitor_root/$monitor_response/$MBRST 
	done

	if [ $count -eq 20 ]; then
		echo -ne "\n${redb}${whitef}.......Wait for response(FAT Handshake_Response) from shop floor timeout.....${reset}\n"
		showfail
		exit 1
	fi

	echo -ne "\n\n"

	sleep 2

	sync;sync;sync

	if [ ! -e $LOG_DIR/$MBRST ]; then
		echo -ne "\n${redb}${whitef}Receive response(FAT Handshake_Response) error !! Please check it.  ${reset}\n"
		showfail
		exit 1
	fi

	grep 'ERR_MSG=OK' $LOG_DIR/$MBRST
 	if [ $? -ne 0 ]; then
		echo -ne "\n${redb}${whitef}Shop floor reply error !!!(FAT Handshake_Response)${reset}\n"
		echo -ne "\n${redb}${whitef} `less $LOG_DIR/$MBRST` ${reset}\n"
		#showfail
		exit
	fi

	echo "rm $monitor_root/$monitor_response/$MBRST">rmcmd.txt
	$UTILS_DIR/ncftp -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip <rmcmd.txt 
	rm -rf rmcmd.txt
	sleep 2
}

uploadFRT_req()
{
		

	echo "SN=$SN" > $LOG_DIR/$MBRST
	echo "motherbrd_sn=NA" >> $LOG_DIR/$MBRST
	echo "MAC=NOMAC" >> $LOG_DIR/$MBRST
	echo "GUID=NA" >> $LOG_DIR/$MBRST
	echo "Station=FRT" >> $LOG_DIR/$MBRST
	echo "ERRCODE=PASS" >> $LOG_DIR/$MBRST
	$UTILS_DIR/unix2dos $LOG_DIR/$MBRST
	monitor_root="NFT"
	monitor_request="Request"
	monitor_response="Response"

	$UTILS_DIR/ncftpput -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $monitor_root/$monitor_request/ $LOG_DIR/$MBRST
	if [ $? -ne 0 ]; then
		echo -ne "Put $LOG_DIR/$MBRST to $monitor_root/$monitor_request fail!!!\n"
		showfail
		exit
	fi
        
	rm $LOG_DIR/$MBRST
	if [ $? -ne 0 ]; then
		echo -ne "\n${redb}${whitef}Remove $LOG_DIR/$MBRST fail !!!${reset}\n"
		showfail
		exit
	fi
	count=1
	#$UTILS_DIR/ncftpget -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $LOG_DIR/ $monitor_root/$monitor_response/$MBRST 
	while [	! -e $LOG_DIR/$MBRST ] && [ $count -ne 20 ]
	do
		sleep 1
		count=$(($count+1))
		echo -ne ".......Waiting for response from shop floor......\n"
		$UTILS_DIR/ncftpget -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip $LOG_DIR/ $monitor_root/$monitor_response/$MBRST 
	done

	if [ $count -eq 20 ]; then
		echo -ne "\n${redb}${whitef}.......Wait for response(FRT Request_response) from shop floor timeout.....${reset}\n"
		showfail
		exit 1
	fi

	echo -ne "\n\n"

	sleep 2

	sync;sync;sync

	if [ ! -e $LOG_DIR/$MBRST ]; then
		echo -ne "\n${redb}${whitef}Receive response(FRT Request_response) error !! Please check it.  ${reset}\n"
		showfail
		exit 1
	fi

	grep 'SF_CFG_CHK=PASS' $LOG_DIR/$MBRST
 	if [ $? -ne 0 ]; then
		echo -ne "\n${redb}${whitef}Shop floor reply error !!!(FRT Request_Response)${reset}\n"
		echo -ne "\n${redb}${whitef} `less $LOG_DIR/$MBRST` ${reset}\n"
		#showfail
		exit
	fi

	echo "rm $monitor_root/$monitor_response/$MBRST">rmcmd.txt
	$UTILS_DIR/ncftp -u $monitor_server_user -p $monitor_server_passwd $monitor_server_ip <rmcmd.txt 
	rm -rf rmcmd.txt
	sleep 2
}


checkadp()
{
	
	watime=1
	while [ 1 ]
	do
		$TESTS_DIR/NUVOTON -info >$LOG_DIR/batinfo.log
		grep -q "AC_status=On-line" $LOG_DIR/batinfo.log
		if [ $? -ne 0 ]; then
			echo -e "\n${redb}${whitef}There's no AC_Adapter,plese check it !!!${reset}"
			sleep 5
			watime=$(( $watime + 5 ))
			if [ $watime -ge 300 ];then
				echo -e "\n${redb}${whitef}Waiting for  AC_Adapter timed out!!!${reset}"
				echo "No ADP">$LOG_DIR/bat.log
				exit 1
			else
				:
			fi
		else
			break;
		fi
	done

	watime=1
	while [ 1 ]
	do
		$TESTS_DIR/NUVOTON -info >$LOG_DIR/batinfo.log
		grep -q " bat_status=On-line" $LOG_DIR/batinfo.log
		if [ $? -ne 0 ]; then
			echo -e "\n${redb}${whitef}There's no Battery,plese check it !!!${reset}"
			sleep 1
			watime=$(( $watime + 1 ))
			if [ $watime -ge 600 ];then
				echo -e "\n${redb}${whitef}Waiting for Battery timed out!!!${reset}"
				echo "No Battery">$LOG_DIR/bat.log
				exit 1
			else
				:
			fi
		else
			break;
		fi
	done
}


write_gbb()
{	echo "HWID=$HWID_SF"
	python /opt/mfg/ui/grt/gooftool/gooftool --write_gbb /opt/mfg/ui/grt/chromeos-hwid/components_$HWID_SF
	if [ $? -eq 0 ];then
	  echo -ne "\nDo write_gbb success!\n"
	else
	  echo -ne "\n${redb}${whitef}Do write_gbb failed!!${reset}\n"
	  showfail
	  exit 1
	fi
}

check_vpd()
{
	tmp=$(vpd -l |grep "$1" |cut -d"=" -f2|sed 's/"//g')
	if [ "$2" != "$tmp" ];then
	    echo -ne "\n${redb}${whitef}Write or Read $1 to/from VPD error !! Please check it.${reset}\n"
	    showfail
	    exit 1
	fi
}

write_vpd()
{



	vpd -s EC_VER="$EC_SF"
	check_vpd EC_VER "$EC_SF"

	vpd -s CARRIER="$CARRIER_SF"
	check_vpd CARRIER "$CARRIER_SF"

	vpd -s BIOS_VER="$BIOS_SF"
	check_vpd BIOS_VER "$BIOS_SF"

        vpd -i RO_VPD -s serial_number="$SN"
	check_vpd serial_number $SN

	vpd -i RO_VPD -s keyboard_layout="$KB_LAYOUT_SF"
	check_vpd keyboard_layout "$KB_LAYOUT_SF"

	vpd -i RO_VPD -s initial_locale="$LOCALE_SF"
	check_vpd initial_locale "$LOCALE_SF"

	vpd -i RO_VPD -s initial_timezone="$T_ZONE_SF"
	check_vpd initial_timezone "$T_ZONE_SF"

}


showpass()
{

	echo `date` > $LOG_DIR/fat.end
        cd /etc/init
        mv fat.conf fat.conf.hide
  	if [ $? -ne 0 ];then
	  mount -o remount rw, /
        fi
        mv frt.conf.hide frt.conf
        if [ ! -e frt.conf ];then
	   echo -ne "\n${redb}${whitef}Receive Error: Change stage to FRT failure!!!${reset}\n"
	   echo -ne "\n${redb}${whitef}Receive Error: Change stage to FRT failure!!!${reset}\n"
	   echo -ne "\n${redb}${whitef}Receive Error: Change stage to FRT failure!!!${reset}\n"
	   exit 1
	fi
        sleep 5
        clear
	ply-image $PICS_DIR/fatpass.png
        while true
        do
	  read -n 1 -p "Press space to shutdown!" Key
          if [ "[$Key]" == "[]" ];then
	     init 0
	     sleep 5
          fi
 	done
}



##########################################
#main()
##########################################
initializeANSI
echo "QSMC Factory test"
echo "By SDT"
echo "Version:"
cat /opt/mfg/ui/version
echo ""

checkadp


setsn

getconf_sf

checkbios_ec

getconf_local

checkit
sleep 2

uploadFAT_hs
sleep 2

uploadFRT_req


checkadp

write_gbb

checkadp

write_vpd

showpass
echo -n -e "\033[46m\033[30m #################################### \033[0m\n\n" >> /dev/tty1
echo -n -e "\033[46m\033[30m ##### FAT process finished !!! ##### \033[0m\n\n" >> /dev/tty1
echo -n -e "\033[46m\033[30m #################################### \033[0m\n\n" >> /dev/tty1

