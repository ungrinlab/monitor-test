#!/bin/bash

#INSTALLING PHIDGET COMPATIBILITY MODULES

#update mirror links
sudo apt-get update

cd /home/pi/
mkdir phidgets
mkdir scripts

cd /home/pi/phidgets/

echo "INSTALLING PHIDGET COMPATIBILITY MODULES"

#Download Phidget Libraries- this will save it to /home/pi/phidgets
sudo wget https://raw.githubusercontent.com/ungrinlab/monitor/master/libphidget.tar.gz
sudo wget https://raw.githubusercontent.com/ungrinlab/monitor/master/libusb-1.0.9.tar.bz2
sudo wget https://raw.githubusercontent.com/ungrinlab/monitor/master/PhidgetsPython.zip

#Extract Libraries
tar -xzvf libphidget.tar.gz
tar xvjf libusb-1.0.9.tar.bz2
unzip PhidgetsPython.zip

#Clean up - remove phidget library tar file - unneccessary now
rm -f libphidget.tar.gz
rm -f libusb-1.0.9.tar.bz2
rm -f PhidgetsPython.zip

#Install Libusb
cd /home/pi/phidgets/libusb-1.0.9 #move into the directory
./configure
make
sudo make install

#Install Libphidget
cd /home/pi/phidgets/libphidget-2.1.8.20140319 #move into the directory
./configure
make
sudo make install

#Install Python Phidget Module
cd /home/pi/phidgets/PhidgetsPython
sudo python setup.py install

#Install ntpdate
cd /home/pi
sudo apt-get install ntpdate

#If the script errors you can follow these commands step by step on terminal while ssh'd into the pi@ip address.

#INSTALLING LIGHTTPD
echo "INSTALLING LIGHTTPD"

#install Lighttpd
sudo apt-get -y install lighttpd

#Install PHP
sudo apt-get -y install php5-common php5-cgi php5

#Then enable the Fastcgi module which will handle the PHP pages :
sudo lighty-enable-mod fastcgi-php

#Install GD Extension for pCHart to work:
sudo apt-get install php5-gd

#Change the lighttpd default directory
sudo cat /etc/lighttpd/lighttpd.conf | perl -pe "s/(server.document-root\s*= )\".*?\"/\1\"\/var\/www\"/g" | sudo tee /etc/lighttpd/lighttpd.conf.repl
sudo rm -f /etc/lighttpd/lighttpd.conf
sudo mv  /etc/lighttpd/lighttpd.conf.repl /etc/lighttpd/lighttpd.conf



#Once these packages are installed we can restart the Lighttpd service to pick up the changes :
sudo service lighttpd force-reload

#Now we will adjust some permissions to ensure the “Pi” user account can write files to the location where Lighttpd expects to find web pages. The /var/www directory is currently owned by the “root” user. So let’s make the “www-data” user and group the owner of the /var/www directory.

sudo chown www-data:www-data /var/www

#Now we will allow the “www-data” group permission to write to this directory.
sudo chmod 775 /var/www

#Finally we can add the “Pi” user to the “www-data” group.
sudo usermod -a -G www-data pi

#For these permissions to take effect it is best to reboot your Pi at this point using :
#sudo reboot

#Step 11 – Replace the placeholder page
#Just save a .txt file to /var/www and you can access it by typing in, for example:136.159.176.118/example.txt

#INSTALLING PCHART MODULES
echo "INSTALLING PCHART MODULES"

#move to /var/www
cd /var/www

#Download pChart package
sudo wget https://raw.githubusercontent.com/ungrinlab/monitor/master/pChart2.1.3.tar

#Extract
sudo tar -xvf pChart2.1.3.tar

#Rename
sudo mv pChart2.1.3 pChart

#Delete the tar file
sudo rm -f pChart2.1.3.tar

#Downloading script package and necessary monitoring system files
echo "Downloading necessary monitoring system scripts..."
cd /var/www
sudo wget https://raw.githubusercontent.com/ungrinlab/monitor/master/web_files.zip
sudo unzip web_files.zip
sudo rm -f web_files.zip

cd /home/pi/phidgets
sudo wget https://raw.githubusercontent.com/ungrinlab/monitor/master/monitoringsystem.py


#install script to blink out the IP address using the Pi's red LED, so user does not need to hook up a monitor to find the machine if the IP changes
cd /home/pi/scripts
sudo wget https://raw.githubusercontent.com/ungrinlab/monitor/master/blink_IP.sh
sudo chmod a+x blink_IP.sh

#Setting up CRONJOB
sudo mkdir /var/www/logs
line='*       *       *       *       *       python /home/pi/phidgets/monitoringsystem.py  > /var/www/logs/most_recent_scan.log'
(sudo crontab -u root -l; echo "$line" ) | sudo crontab -u root -
line='*     *       *       *       *       /home/pi/scripts/blink_IP.sh 1 &> /dev/null'
(sudo crontab -u root -l; echo "$line" ) | sudo crontab -u root -

#Clean up some memory
sudo apt-get autoclean
sudo apt-get clean

read -n 1 -p "Can we log this installation to give us an idea of how many people are using the software? Only this machine's IP address will be recorded. (Y/n)" answer
if [ -z $answer ] || [ $answer = "y" ] || [ $answer = "Y" ]
        then
                echo
                echo "IP address submitted"
                wget http://136.159.176.175/monitor_install_log.php?message=NEW_INSTALL -O - &> /dev/null
        else
                echo
                echo "Nothing transmitted"
        fi

#If the script errors you can follow these commands step by step on terminal while ssh'd into the pi@ip address.

IP=$(/sbin/ifconfig | grep addr: | perl -pe "s/.*addr:(.*?) .*/\1/g" | head -n 1 )

echo "Installation complete! You should now be able to control the monitoring system via the web at http://$IP"
echo "Whoever is in charge of your network administration should be able to assign a static IP address to this machine so it will remain the same in the future"
echo "If you are using a Raspberry Pi the LEDs should blink out the IP address once per minute in case you forget, or the address changes."
echo "This software is copyright Akshay Gurdita and Mark Ungrin (2015), and is distributed under the Gnu General Public License Version 3 (GPLv3) - for more information on copyright click on the copyright symbol from the web link above."
