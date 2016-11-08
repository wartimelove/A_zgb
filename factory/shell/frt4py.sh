#!/bin/bash
LOG_DIR=/opt/mfg/ui/log
MFG_DIR=/opt/mfg/ui
UTILS_DIR=/opt/mfg/ui/utils
SCRIPTS_DIR=/opt/mfg/ui/scripts
TESTS_DIR=/opt/mfg/ui/tests
WAVS_DIR=/opt/mfg/ui/wavs
PICS_DIR=/opt/mfg/ui/pics


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
suspend_test()
{
    
    awake_time=`cat /sys/class/rtc/rtc0/since_epoch`
    ((awake_time=awake_time+20))
    echo 'clear' > /sys/class/rtc/rtc0/wakealarm
    echo "$awake_time" > /sys/class/rtc/rtc0/wakealarm
    echo `date` >> $LOG_DIR/s3.log
    wake_alarm=$(cat /sys/class/rtc/rtc0/wakealarm)
    while [ "$awake_time" != "$wake_alarm" ]
    do
        echo "wake_alarm time error" >> $LOG_DIR/s3.log
        sleep 1
        echo 'clear' > /sys/class/rtc/rtc0/wakealarm
        awake_time=`cat /sys/class/rtc/rtc0/since_epoch`
        ((awake_time=awake_time+20))
        echo "$awake_time" > /sys/class/rtc/rtc0/wakealarm
        wake_alarm=$(cat /sys/class/rtc/rtc0/wakealarm)
    done
    sleep 5
    if [ -e /usr/bin/powerd_suspend ];then
	/usr/bin/powerd_suspend
    else
        echo "mem" >/sys/power/state
    fi
    sleep 1
    exit 0
}
     

suspend_test_bak()
{
        	`hwclock --hctosys`
                echo 0 > /sys/class/rtc/rtc0/wakealarm
		awake_time=`hwclock --debug --directisa|grep "Hw clock"|cut -d"=" -f2|cut -d" " -f2`

		((awake_time=awake_time+30))
		echo "$awake_time" > /sys/class/rtc/rtc0/wakealarm
		echo `date` >> $LOG_DIR/s3.log
		wake_alarm=$(cat /sys/class/rtc/rtc0/wakealarm)
		while [ "$awake_time" != "$wake_alarm" ]
		do
		    echo "wake_alarm time error" >> $LOG_DIR/s3.log
		    sleep 1
		    echo 0 > /sys/class/rtc/rtc0/wakealarm
		    awake_time=`hwclock --debug --directisa|grep "Hw clock"|cut -d"=" -f2|cut -d" " -f2`
		    ((awake_time=awake_time+30))
		    echo "$awake_time" > /sys/class/rtc/rtc0/wakealarm
		    wake_alarm=$(cat /sys/class/rtc/rtc0/wakealarm)
		done
		sleep 5
		#/usr/bin/powerd_suspend
		echo "mem" >/sys/power/state
		
		#count=$(wc -l $LOG_DIR/s3.log |cut -d" " -f1)
		#((count=count-1))
		#echo "S3 count =" $count
	        exit 0
}

burncpu()
{

         $TESTS_DIR/cpuburn-in 1 >$LOG_DIR/cpuburn.log  &
         
        a=1
        while [ $a -ne 0 ]
         do
         
         ps |grep  -q "cpuburn-in"
          if [ $? -eq 0 ]
          then
           echo  -ne "\n \033[46m\033[30m ##    CPUBURN testing$a..............##\033[0m\n"
	   echo ""
           sleep 1
             ((a=a+1))
           else
          break
        fi
        done
        
        cat $LOG_DIR/cpuburn.log|grep -q "No errors were found "
        if [  $? -eq 0 ]
          then
         echo -ne "\n \033[46m\033[30m ##   The cpuburn is all right!!   ##\033[0m\n"
        else
         echo -ne "\n \033[41m\033[30m ##   ERROR:The cpuburn is failed! ##\033[0m\n"
           exit 1
        fi 
         echo -ne "\n \033[46m\033[30m ##   CPUBURN testing finished.!!  ## \033[0m\n"
         echo -ne "\n \033[46m\033[30m #####################################\033[0m\n"
       rm $LOG_DIR/cpuburn.log
       exit 0
}

burnssd()
{

         $TESTS_DIR/hdparm -Tt /dev/sda1 > $LOG_DIR/hdparm.log  &
       
          b=1
        while [ $b -ne 0 ]
         do
         
         ps |grep  -q "hdparm"
          if [ $? -eq 0 ]
          then
           echo  -ne "\n \033[46m\033[30m ##    SSD testing$b..............##\033[0m\n"
	  echo ""
           sleep 1
             ((b=b+1))
           else
          break
        fi
        done
       
        cache=`cat $LOG_DIR/hdparm.log | grep 'cached' |  cut -d'=' -f 2`  
        buffer=`cat $LOG_DIR/hdparm.log | grep 'buffered' |  cut -d'=' -f 2` 
        if [ $? -eq 1 ];then
		exit 1
	fi
       echo -ne "\n \033[46m\033[30m ##  The Read Speed of sda1 buffer is $buffer ## \033[0m\n"
       echo -ne "\n \033[46m\033[30m ##  The Read Speed of sda1 cache is $cache##### \033[0m \n"
     
       echo -ne "\n \033[46m\033[30m ##       SSD testing finished.!              ## \033[0m\n"
       echo -ne "\n \033[46m\033[30m #############################################\033[0m\n"
       rm $LOG_DIR/hdparm.log
       exit 0
}

burnmem()
{

      $TESTS_DIR/memtester  30 3 > $LOG_DIR/mem.log &

           c=1
        while [ $c -ne 0 ]
         do
         
         ps |grep  -q "memtester"
          if [ $? -eq 0 ]
          then
           echo  -ne "\n \033[46m\033[30m ##    Memory testing$c..............##\033[0m\n"
	echo ""
           sleep 1
             ((c=c+1))
           else
          break
        fi
        done
        
        num=`cat $LOG_DIR/mem.log |grep ok | wc -l`
         
       if [  $num = 48 ];then
              echo -ne "\n \033[46m\033[30m ##   The Memory is all right!      ##\033[0m\n"
        else
              echo -ne "\n \033[41m\033[30m ##   The Memory test failed!  ##\033[0m\n"
       
            exit 1
        fi

              echo -ne "\n \033[46m\033[30m ##  MEMORY testing finished!       ##\033[0m \n"
              echo -ne "\n \033[46m\033[30m #####################################\033[0m\n"
        rm $LOG_DIR/mem.log
	exit 0
	
}

burnlcd()
{
	
	$TESTS_DIR/glxgears -t $1 >$LOG_DIR/3d.log &
	d=1
        while [ $d -ne 0 ]
         do
               ps uax|grep glxgears|grep -v grep
               if [ $? -eq 0 ];then
	            echo  -ne "\n \033[46m\033[30m ##    3D testing$c..............##\033[0m\n"
	     	   echo ""
            	   sleep 1
             		 ((d=d+1))
              else
         	 break
       	      fi
        done
        
        num=`wc -l < $LOG_DIR/3d.log`
         
       if [  $num -ne 0 ];then
              echo -ne "\n \033[46m\033[30m ##   The 3D is all right!      ##\033[0m\n"
        else
              echo -ne "\n \033[41m\033[30m ##   The 3D test failed !  ##\033[0m\n"
       
            exit 1
        fi

              echo -ne "\n \033[46m\033[30m ## 3D testing finished!       ##\033[0m \n"
              echo -ne "\n \033[46m\033[30m #####################################\033[0m\n"
        rm $LOG_DIR/3d.log
	exit 0
	
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
			if [ $watime -ge 30 ];then
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
			if [ $watime -ge 30 ];then
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

burnbat()
{
           checkadp

	$TESTS_DIR/NUVOTON -info >$LOG_DIR/batinfo.log
	relst=`grep "relative_state" $LOG_DIR/batinfo.log | cut -d "=" -f2 `

	if [ $relst -gt 95 ];then

		$TESTS_DIR/NUVOTON -discharge  -m	
		sleep 10
		
		while [ 1 ]
		do 

			$TESTS_DIR/NUVOTON -info >$LOG_DIR/batinfo.log
			currah=`grep "current" $LOG_DIR/batinfo.log | cut -d "=" -f2 `	
			if [ $currah -gt 0 ];then
				echo  -e "\n${redb}${whitef}Discharge error !!!${reset}"
				echo "Discharge error">$LOG_DIR/bat.log
				exit 1
			else
				echo -ne "\033[46m\033[30m Discharging...... \033[0m\n\n" 
			fi
			currcap=`grep "relative_state" $LOG_DIR/batinfo.log | cut -d "=" -f2 `	
			if [ $currcap -lt $(($relst - 6 )) ];then
				echo -ne "\033[46m\033[30m Discharge successed!!! \033[0m\n\n" 
				$TESTS_DIR/NUVOTON -info >$LOG_DIR/batinfo.log
				relst=`grep "relative_state" $LOG_DIR/batinfo.log | cut -d "=" -f2 `
				$TESTS_DIR/NUVOTON -charge  -m	
				sleep 10
	
				while [ 1 ]
				do 
	
					$TESTS_DIR/NUVOTON -info >$LOG_DIR/batinfo.log
					currah=`grep "current" $LOG_DIR/batinfo.log | cut -d "=" -f2 `	
					if [ $currah -lt 0 ];then
						echo  -e "\n${redb}${whitef}Charge error !!!${reset}"
						echo "Charge error">$LOG_DIR/bat.log
						exit 1
					else
					echo -ne "\033[46m\033[30m Charging...... \033[0m\n\n" 
					fi
					currcap=`grep "relative_state" $LOG_DIR/batinfo.log | cut -d "=" -f2 `	
					if [ $currcap -gt $(($relst + 1 )) ];then
						echo -ne "\033[46m\033[30m Charge successed!!! \033[0m\n\n" 
						break
					else
						:
					fi
					sleep 10
				done

				break
			else
				:
			fi
		  	sleep 10
		done
	else
		$TESTS_DIR/NUVOTON -charge  -m	
		sleep 10
		
		while [ 1 ]
		do 

			$TESTS_DIR/NUVOTON -info >$LOG_DIR/batinfo.log
			currah=`grep "current" $LOG_DIR/batinfo.log | cut -d "=" -f2 `	
			if [ $currah -lt 0 ];then
				echo  -e "\n${redb}${whitef}Charge error !!!${reset}"
				echo "charge error">$LOG_DIR/bat.log
				exit 1
			else
				echo -ne "\033[46m\033[30m Charging...... \033[0m\n\n" 
			fi
			currcap=`grep "relative_state" $LOG_DIR/batinfo.log | cut -d "=" -f2 `	
			if [ $currcap -gt $(($relst + 2 )) ];then
				echo -ne "\033[46m\033[30m Charge successed!!! \033[0m\n\n" 
				$TESTS_DIR/NUVOTON -info >$LOG_DIR/batinfo.log
				relst=`grep "relative_state" $LOG_DIR/batinfo.log | cut -d "=" -f2 `
				$TESTS_DIR/NUVOTON -discharge  -m	
				sleep 10
	
				while [ 1 ]
				do 
	
					$TESTS_DIR/NUVOTON -info >$LOG_DIR/batinfo.log
					currah=`grep "current" $LOG_DIR/batinfo.log | cut -d "=" -f2 `	
					if [ $currah -gt 0 ];then
						echo  -e "\n${redb}${whitef}Discharge error !!!${reset}"
						echo "Discharge error">$LOG_DIR/bat.log
						exit 1
					else
					echo -ne "\033[46m\033[30m Discharging...... \033[0m\n\n" 
					fi
					currcap=`grep "relative_state" $LOG_DIR/batinfo.log | cut -d "=" -f2 `	
					if [ $currcap -lt $(($relst - 1 )) ];then
						echo -ne "\033[46m\033[30m Discharge successed!!! \033[0m\n\n" 
						break
					else
						:
					fi
					sleep 10
				done

				break
			else
				:
			fi
		  	sleep 10
		done
	fi

	$TESTS_DIR/NUVOTON -charge  -m	
        exit 0
}

chkbt()
{
        #bluetoothd &
        bt_flag=0
        start_time=`cat /sys/class/rtc/rtc0/since_epoch`
        end_time=$(($start_time + 300))

        hciconfig hci0 iscan
	echo "Bluetooth Scanning ......."
        while [ 1 ]
        do
          	
          if [ $bt_flag -eq 0 ];then
            $TESTS_DIR/btool -s 1
            if [ $? -eq 0 ];then
               bt_flag=1
            fi
          fi
          cur_time=`cat /sys/class/rtc/rtc0/since_epoch`
          if [ $cur_time -gt $end_time ];then
             hciconfig hci0 noscan
             if [ $bt_flag -eq 1 ];then
               exit 0
             else
               exit 1
             fi
          fi
          sleep 1
        done       
        

}

checkbat()
{
	cd $TESTS_DIR
        sudo ./NUVOTON -info | grep "bat_status" | grep On
        if [ $? == 0 ]; then 
             #cap_value=0
             #min_value=0.80 
             cap_value=$(sudo ./NUVOTON  -info | grep "relative" | cut -d= -f2)
                  # cap_value=`awk BEGIN'{printf "%.2f\n",'$remain' / '$design'}'`
             echo "now Battery capacity is "$cap_value"%" 
                  if [ $cap_value -le "80" ]; then
                        echo "now Battery capacity is "$cap_value"%"
                        echo "now Battery capacity is "$cap_value"%" >> $LOG_DIR/showallFFTfail.log
                        echo -ne "\033[41m\033[30m =========== Battery capacity is not enough for shipping [failed] !!! =========== \033[0m\n\n" >> $LOG_DIR/showallFFTfail.log
                        sleep 3
			exit 1
                  else
                       echo -e "\033[42;30m ******************************************************** \033[0m"
                       echo -e "\033[42;30m **Battery capcity is enough for shipping [passed] !!!!** \033[0m"
                       echo -e "\033[42;30m ******************************************************** \033[0m"  
                       sleep 3
		       exit 0
                 fi
        else 
              echo -ne "\033[41m\033[30m =====================No Battery===========================\033[0m\n\n "
                         echo "=====================No Battery===========================\n" >> $LOG_DIR/showallFFTfail.log
                        fail_flag=$(($fail_flag + 1))
		        sleep 3	
		exit 1

        fi 

}


##########################################
#main()
##########################################

initializeANSI
#options:
#options:
# -a:brunbat (battery dis/charge)
# -b:chkbt
# -c:burncpu
# -d:burnssd
# -e:checkbat (CAP)
# -g:burnlcd
# -m:burnmem
# -r:s5
# -s:s3

if [ "$1" == "" ];then
	exit 1
fi

checkadp

while getopts "abcdeg:mrs" arg 
do
        case $arg in
             a)
		burnbat
                ;;
             b)
		chkbt
                ;;
             c)
		burncpu
                ;;
             d)
		burnssd
                ;;
             e)
		checkbat
                ;;
             g)
		burnlcd $OPTARG
                ;;
             m)
		burnmem
                ;;
             r)
		exit 0
                ;;
             s)
		suspend_test
                ;;
	     *)
		 echo "Unkonw argument"
       		 exit 1
      		;;
        esac

done
exit 1

