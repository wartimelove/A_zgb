#!/bin/bash
initctl stop wpasupplicant
wpa_supplicant -iwlan0 -c /opt/mfg/ui/config/wpa_conn.conf &
dhclient wlan0
sudo iwconfig wlan0 | grep -q 'Not-Associated'
if [ $? -eq 0 ] 
then 
	echo "one more time"
	sleep 2
        dhclient wlan0
        iwconfig wlan0 | grep -q 'Not-Associated'
        if [ $? -eq 0 ] 
        then 
	  echo "Not connected to AP, aborting RSSI check"
          exit 1
        else 
          echo "The wireless is  connected"
          exit 0
	fi
fi  

