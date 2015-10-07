#!/bin/bash





function blinkN()
{
	echo none >/sys/class/leds/led0/trigger
	COUNTER="0"
	#echo "Blinking $num times"
	while [ $COUNTER -lt $num ]
	do
		#echo ON
		echo 1 >/sys/class/leds/led0/brightness
		echo 1 >/sys/class/leds/led1/brightness
		sleep $on_len
		#echo OFF
		echo 0 >/sys/class/leds/led0/brightness
		echo 0 >/sys/class/leds/led1/brightness
		sleep $off_len
		COUNTER=$[$COUNTER+1]
	done
}

function flicker()
{
	on_len=0.05
	off_len=0.05
	num=10
	inter_len=1
	blinkN
	sleep $inter_len
}


IP=$(/sbin/ifconfig | grep addr: | perl -pe "s/.*addr:(.*?) .*/\1/g" | head -n 1 )


function display_IP()
{
	flicker

	for (( i=0; i<${#IP}; i++ )); do
	  num=${IP:$i:1}
	  if [ $num == "." ]; then
		on_len=2
		off_len=0
		inter_len=1
		num=1
	  else
		  on_len=0.2
		  off_len=0.2
		  inter_len=1
	  fi
	  blinkN
	  sleep $inter_len
	done

	flicker
}


for (( j=0; j<$1; j++ )); do
	echo "IP is $IP (count $j of $1)"
	display_IP
done
