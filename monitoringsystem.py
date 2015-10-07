# coding: utf-8
# MonitoringSystem.py
# This script outputs the phidget sensor data from an InterfaceKit or from a Thermocouple into a log file and evaluates whether the sensor input is within a valid range. Settings for the ranges, and script variables such as email addresses and device information should be placed into the config.txt file.

#By Akshay Gurdita
# Last Modified: June 26 2015

#This code has been adapted from examples provided at phidgets.com

#Basic imports
from ctypes import *
import sys
import random
import os
import time #for the timestamp
import datetime #for the timestamp
import smtplib # for the email send
import ConfigParser # for the config file/preference sheet
import subprocess
import re
import gc

#Phidget specific imports
from Phidgets.Devices.InterfaceKit import InterfaceKit
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, TemperatureChangeEventArgs
from Phidgets.Devices.TemperatureSensor import TemperatureSensor, ThermocoupleType
#import methods for sleeping
from time import sleep

#Global Variables
#Setting up Log Files and Graphing Files
logfile= open("/var/www/monitor_log.txt", "a+") #Opens the logfile from the interface kit
alert_log = open("/var/www/alert_log.txt","a+") #Opens a log file that stores alert data from emails that are sent for the digital ports

config = ConfigParser.ConfigParser() #Use configParser to obtain string information from config.txt file
config.read("/var/www/sensor_config.php") #Directory for config.txt can be changed

#Note that /var/www/ is the directory in the Raspberry Pi where you can access the log files easiest by simplying typing: "pi ip address/filename.txt"
#Make sure that these files also have all users or "others" read, write and execute permissions

#Analog Inputs for the Interface Kit ports. String data associated with each port (the labels for the sensors) is obtained.
#Analog inputs are the inputs connected to the phidget sensors

port0_kit = str(config.get("InterfaceKit_settings", "Port M0"))
port1_kit = str(config.get("InterfaceKit_settings", "Port M1"))
port2_kit = str(config.get("InterfaceKit_settings", "Port M2"))
port3_kit = str(config.get("InterfaceKit_settings", "Port M3"))
port4_kit = str(config.get("InterfaceKit_settings", "Port M4"))
port5_kit = str(config.get("InterfaceKit_settings", "Port M5"))
port6_kit = str(config.get("InterfaceKit_settings", "Port M6"))
port7_kit = str(config.get("InterfaceKit_settings", "Port M7"))

ports_kit = [port0_kit, port1_kit, port2_kit, port3_kit, port4_kit, port5_kit, port6_kit, port7_kit]

#Analog Inputs for the thermocouple ports. These would be connected to thermocouples only.

port0_couple = str(config.get("Thermocouple_settings", "Port T0"))
port1_couple = str(config.get("Thermocouple_settings", "Port T1"))
port2_couple = str(config.get("Thermocouple_settings", "Port T2"))
port3_couple = str(config.get("Thermocouple_settings", "Port T3"))

ports_couple = [port0_couple,port1_couple,port2_couple,port3_couple]

#Digital Inputs for the Interface Kit ports. These are connected to digital inputs such as mangetic proximity sensors.

port0_dig = str(config.get("InterfaceKit_settings", "Port D0"))
port1_dig = str(config.get("InterfaceKit_settings", "Port D1"))
port2_dig = str(config.get("InterfaceKit_settings", "Port D2"))
port3_dig = str(config.get("InterfaceKit_settings", "Port D3"))
port4_dig = str(config.get("InterfaceKit_settings", "Port D4"))
port5_dig = str(config.get("InterfaceKit_settings", "Port D5"))
port6_dig = str(config.get("InterfaceKit_settings", "Port D6"))
port7_dig = str(config.get("InterfaceKit_settings", "Port D7"))

ports_dig = [port0_dig, port1_dig, port2_dig, port3_dig, port4_dig, port5_dig, port6_dig, port7_dig]

#Determine if an InterfaceKit or Thermocouple or both are connected to the RPi. If they are connected the config.txt file should have 'Y' under the section.
kit_connected = str(config.get("General_settings", "InterfaceKit connected"))
couple_connected = str(config.get("General_settings", "Thermocouple connected"))

#Create an interfacekit and/or thermocouple object
try:
    if kit_connected == "Y":
        interfaceKit = InterfaceKit()
    if couple_connected == "Y":
        temperatureSensor = TemperatureSensor()
except RuntimeError as e:
    print("Runtime Exception: %s" % e.details)
    print("Exiting....")
    exit(1)


# InterfaceKit Information Display Function -> Taken from phidgets.com
def displayDeviceInfo():
    print("|------------|----------------------------------|--------------|------------|")
    print("|- Attached -|-              Type              -|- Serial No. -|-  Version -|")
    print("|------------|----------------------------------|--------------|------------|")
    print("|- %8s -|- %30s -|- %10d -|- %8d -|" % (interfaceKit.isAttached(), interfaceKit.getDeviceName(), interfaceKit.getSerialNum(), interfaceKit.getDeviceVersion()))
    print("|------------|----------------------------------|--------------|------------|")
    print("Number of Digital Inputs: %i" % (interfaceKit.getInputCount()))
    print("Number of Digital Outputs: %i" % (interfaceKit.getOutputCount()))
    print("Number of Sensor Inputs: %i" % (interfaceKit.getSensorCount()))

# InterfaceKit Event Handler Callback Functions -> Taken from phidgets.com
def interfaceKitAttached(e):
    attached = e.device
    print("InterfaceKit %i Attached!" % (attached.getSerialNum()))

def interfaceKitDetached(e):
    detached = e.device
    print("InterfaceKit %i Detached!" % (detached.getSerialNum()))

def interfaceKitError(e):
    try:
        source = e.device
        if source.isAttached:
            print("InterfaceKit %i: Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))

#Thermocouple Information Display Function -> Taken from phidgets.com
def DisplayDeviceInfo():
    inputCount = temperatureSensor.getTemperatureInputCount()
    print("|------------|----------------------------------|--------------|------------|")
    print("|- Attached -|-              Type              -|- Serial No. -|-  Version -|")
    print("|------------|----------------------------------|--------------|------------|")
    print("|- %8s -|- %30s -|- %10d -|- %8d -|" % (temperatureSensor.isAttached(), temperatureSensor.getDeviceName(), temperatureSensor.getSerialNum(), temperatureSensor.getDeviceVersion()))
    print("|------------|----------------------------------|--------------|------------|")
    print("Number of Temperature Inputs: %i" % (inputCount))
    for i in range(inputCount):
        print("Input %i Sensitivity: %f" % (i, temperatureSensor.getTemperatureChangeTrigger(i)))

#Event Handler Callback Functions -> Taken from phidgets.com
def TemperatureSensorAttached(e):
    attached = e.device
    print("TemperatureSensor %i Attached!" % (attached.getSerialNum()))

def TemperatureSensorDetached(e):
    detached = e.device
    print("TemperatureSensor %i Detached!" % (detached.getSerialNum()))

def TemperatureSensorError(e):
    try:
        source = e.device
        if source.isAttached():
            print("TemperatureSensor %i: Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        print("2")

#Pressure and Temperature Sensor Input and Logging for either Interface Kit and Thermocouple
def SensorValue():
    port_values_kit = {} #set up an array of values for each group of ports on the kit and thermocouple
    port_values_couple = {}
    ports_values_dig = {}
    
    log = [] # These log arrays twill be appended to as the script runs and then writen to the associated log files
    
    if kit_connected == "Y":
               
        # Get status from magnetic switch port on interface kit. Use 'try' incase no digital ports are in use
        try:
            
            for input_,input_number in zip(ports_dig,range(8)): #input_ is the string label associated with the port, input_number is the index for the range
                if input_ =="" or input_=='NONE' or input_==' ': #If there is no string data from the config.txt file for the port, assume that there is nothing connected to it and pass
                    pass
                else:
                    ports_values_dig[input_number] = interfaceKit.getInputState(input_number) #returns a TRUE or FALSE value for the input_number associated with the digital port and appends to the an array of values
                    log.append("%s@D%d=%s" % (input_,input_number, ports_values_dig[input_number]))
                    print("%s on port D%d reports %s" % (input_,input_number, ports_values_dig[input_number]))
        except:
            pass
        
        # Get inputs from each sensor.
        
        for port_number in range(8):
            port_values_kit[port_number] = interfaceKit.getSensorValue(port_number) #Obtains an array of values for analog inputs on the interfacekit.

        # Evaluate the sensor values based on the type of sensor that has been described in the config.txt file.
        for index, port in enumerate(ports_kit): # index is range 8 and port is the corresponding string from the array ports_kit. 
            if 'pressure' and '1140' in port:
                port_values_kit[index] = (port_values_kit[index] / 16.697) + 0.504
                log.append("%s@M%d=%s psi" % (port, index, port_values_kit[index]))
                print("%s on port M%d is %s psi" % (port, index, port_values_kit[index]))
            
            if 'pressure' and '1115' in port:
                port_values_kit[index] = ((((port_values_kit[index] / 4) + 10) * 0.145037738))
                log.append("%s@M%d=%s psi" % (port, index, port_values_kit[index]))
                print("%s on port M%d is %s psi" % (port, index, port_values_kit[index]))
            
            if 'pressure' and '1141' in port:
                port_values_kit[index] = ((port_values_kit[index] / 63.45) + 1.54)
                log.append("%s@M%d=%s psi" % (port, index, port_values_kit[index]))
                print("%s on port M%d is %s psi" % (port, index, port_values_kit[index]))
            
            if 'temperature' in port:
                port_values_kit[index] = (port_values_kit[index] * 0.2222) - 61.111
                log.append("%s@M%d=%s C" % (port, index, port_values_kit[index]))
                print("%s on port M%d is %s C" %(port, index, port_values_kit[index]))                

    if couple_connected == "Y":
        
        # Get inputs from each sensor.
        
        #If no thermocouple is attached to a port, the port_value is set to 0
        for port, port_number in zip(ports_couple,range(4)): #port is the string from the config file. Port_number is the index number.
            if port =="" or port =='NONE' or port ==' ':# if the config file has no description for the port then assume no thermocouple is connected and set the value to zero
                port_values_couple[port_number] = 0 # This is to avoid some error from .getTemperature function
            else:
                port_values_couple[port_number] = temperatureSensor.getTemperature(port_number)

        # Append sensor values to log files. Sensor converts value to Celsius so no need to evaluate further.
        for index, port in enumerate(ports_couple):
            if port =="" or port =='NONE' or port ==' ':
                pass
            else:
                log.append("%s@T%d=%s C" % (port, index, port_values_couple[index]))
                print("%s on port T%d is %s C" % (port, index, port_values_couple[index]))

    #Date/Time stamp for Sensor Reading and Writing to the Log Files
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(timestamp, pattern))) #This is used for pChart since it requires Epoch time. 
    #log.append("")    
    log = ("|".join(log))
        
    print("Data sent to online charts")
        
    logfile = open("/var/www/monitor_log.txt", "a+") #Opens the logfile for both the interfacekit and thermocouple
    logfile.write ("\n%s|%s" %(timestamp,log))
    logfile.flush()
    os.fsync(logfile)
    logfile.close()
    print("%s, Log files updated...." % (timestamp))	
    
    #Call Email Notification
    emailnotif(ports_values_dig, port_values_kit,port_values_couple,timestamp)

#Turn LED on for a second then turn it off.
def LEDon_off():
    LED = interfaceKit.setOutputState(0,True)
    print("LED Turned ON")
    time.sleep(1)
    LED = interfaceKit.setOutputState(0,False)
    print("LED Turned OFF")

#time_since_last_timestamp is used to determine the last time an alert_log file was modified.
#After an email is sent the alert information is stored in a corresponding file for the type of port.
# By comparing the last time an email was sent we can control how often email alerts should be completed if a sensor is continually out of range
# for an extended period of time.


# determines the time since the alert_log.txt was last modified, which would have been the last time the Email was sent and recorded in the file.
def time_since_last_timestamp(alert_str, attempt_alert_str):
    from datetime import datetime
    try:
        timer = int(config.get("General_settings", "Email Timer"))
    except:
        timer = 60
            
    for line in reversed(open("/var/www/alert_log.txt").readlines()):
            if alert_str in line:
                print("Checking alert log for last time an email was sent...")
                parse = line.split("|") # splits log file by | delimiter
                parse = parse[0] # timestamp is always at the start of the log with index 0                    
                d1=datetime.strptime(parse,'%Y-%m-%d %H:%M:%S ')
                less_timer =(datetime.now()-d1).total_seconds()/60
                return less_timer                
                break #Cuts loop so it only takes the last email timestamp and doesnt read through the whole file 
            elif attempt_alert_str in line:
                print("Checking alert log for last attempted email sent...")
                parse = line.split("|") # splits log file by | delimiter
                parse = parse[0] # timestamp is always at the start of the log with index 0                    
                d1=datetime.strptime(parse,'%Y-%m-%d %H:%M:%S ')
                less_timer =(datetime.now()-d1).total_seconds()/60
                return less_timer                
                break #Cuts loop so it only takes the last email timestamp and doesnt read through the whole file
    else: 
        # if alert string or attempted alert string not found in log
        greater_timer = timer + 100
        return greater_timer

# Actual email send using GMAIL servers. 
def email_send(text):
    #To and From addresses and subject line for Email. Obtained from Config file.
    fromaddr = str(config.get("General_settings", "From Address"))
    toaddrs  = str(config.get("General_settings", "To Address"))

    result=subprocess.check_output(["/sbin/ifconfig"], shell=False)
    matchObj = re.match( r'.*?addr:(.*?) .*', result, re.M|re.DOTALL)
    if matchObj:
        textout = matchObj.group(1)
    else:
        textout = "IP not detected"

    subject = "Sensor Alert ("+textout+")!"
   
    # Credentials (if needed). Obtained from Config file.
    username = str(config.get("General_settings", "From Address"))
    password = str(config.get("General_settings", "Password"))
    
    if "@" and "." in fromaddr and toaddrs:
        if username and password != "":
            try:
                print("Accessing server...")
#                msg = """fromaddr: %s\ntoaddrs: %s\nsubject: %s\n\n%s""" % (fromaddr, toaddrs, subject, text)
                msg = """fromaddr: %s\ntoaddrs: %s\nsubject: %s\n\n%s\n\nhttp://%s""" % (fromaddr, toaddrs, subject, text, textout)
                server = smtplib.SMTP('smtp.gmail.com:587')
                server.ehlo()
                server.starttls()
                server.login(username,password)  
                server.sendmail(fromaddr, toaddrs, msg)
                server.quit()
                print("Email Sent!")
                return True
            except:
                print("Email could not be sent, try re-entering notification credentials")
                return False
        else:
            print("Email could not be sent, check the notification settings username or password")
            return False
    else:
        print("Email could not be sent, check the notification settings from or to address")
        return False

#Email Notifications for Sensor Changes. This function evaluates the sensor value from each port and then determines whether or not an email should be sent based on a set of conditions.
def emailnotif(ports_values_dig,port_values_kit,port_values_couple,timestamp):
  '''port_values: key is port number, and value is the sensor reading.'''

  timer = int(config.get("General_settings", "Email Timer")) #Timer in seconds for how long to wait between sending emails, from config.txt
  
  # alert log strings from each component that will be concatenated and printed at the end of the function as a single line
  prox_alert_string = []
  kit_alert_string = []
  couple_alert_string = []

                               
  if kit_connected == "Y":

    #Check magnetic proximity sensor. If a proximity sensor returns false an email should be sent, unless an email was sent less than the email timer ago.
    
    try:
      print("Checking magnetic proximity sensors...")      
      for d, dig in zip(ports_dig,ports_values_dig): 
         #d,dig = port name, port index
         sensor_status = str(ports_values_dig[dig])
         if sensor_status == "True":
            sensor_status = "TRUE"
         else:
            sensor_status = "FALSE"
            desired_state = str(config.get('InterfaceKit_settings', 'desired state D%s'%(dig)))
         try:
            state_timeout = int(config.get('InterfaceKit_settings', 'state timeout D%s'%(dig)))
         except:
            state_timeout = timer
         alert_str = str("Email Alert Sent! (DIG) Check Proximity Sensor on port D%s"%(dig))
         attempt_alert_str = str("Attempted to send email! (DIG) Check Proximity Sensor on port D%s" % (dig))
         if os.path.isfile("/var/www/alert_log.txt") == True:           
            if sensor_status != desired_state:
                if time_since_last_timestamp(alert_str,attempt_alert_str) > state_timeout: #If time since last timestamp in alert log is greater than the email timer, send email/
                    text = ("%s on port D%s was recorded to be %s at %s \n" % (d, dig, sensor_status, timestamp))                      
                    if email_send(text) == True:
                        prox_alert_string.append("|Email Alert Sent! (DIG) Check Proximity Sensor on port D%s" % (dig))
                        print("Email Alert Sent! (DIG) Check Proximity Sensor on port D%s" % (dig))
                    else:
                        prox_alert_string.append("|Attempted to send email! (DIG) Check Proximity Sensor on port D%s" % (dig))
                        print("Attempted to send email! (DIG) Check Proximity Sensor on port D%s" % (dig))                
         
                else:                
                    prox_alert_string.append("|Check Proximity Sensor on port D%s"%(dig))
                    print("Check Proximity Sensor on port D%s "%(dig))
            else:
                print("Magnetic Proximity Sensor D%s Okay" %(dig))
         else:
            if sensor_status != desired_state:
                text = ("%s on port D%s was recorded to be %s at %s \n" % (d, dig, sensor_status, timestamp))            
                prox_alert_string.append("|Email Alert Sent! (DIG) Check Proximity Sensor on port D%s"%(dig))            
                if email_send(text) == True:
                    prox_alert_string.append("|Email Alert Sent! (DIG) Check Proximity Sensor on port D%s" % (dig))
                    print("Email Alert Sent! (DIG) Check Proximity Sensor on port D%s" % (dig))
                else:
                    prox_alert_string.append("|Attempted to send email! (DIG) Check Proximity Sensor on port D%s" % (dig))
                    print("Attempted to send email! (DIG) Check Proximity Sensor on port D%s" % (dig))
            else:
                print("Magnetic Proximity Sensor D%s Okay" %(dig))

    except:
        print("Checking magnetic proximity sensors failed!")
        pass
                               
   # upper and lower limits taken from config file
    print("Checking upper and lower limits for Interface Kit...")
    limits = {'upper': {}, 'lower': {}}
    for limit_number in range(8):
        for x in ['upper', 'lower']:
            limits[x][limit_number] = int(config.get('InterfaceKit_settings', '%s limit M%d' % (x, limit_number)))
     
     #Mail send for each port.
     # If a port_value is outside the limits and the port_value is not 0 (no sensor attached to that port) then an email will send
    
    for p, port in  zip(ports_kit, port_values_kit):
        if p != '':
        # if the port name is not empty or a space then check its associated value (port_value) for alerts
            port_value = port_values_kit[port]
            alert_str = str("Email Alert Sent! (KIT) Limit breached for %s on port M%s"%(p,port))
            attempt_alert_str = str("Attempted to send email! (KIT) Limit breached for %s on port M%s "%(p,port))
            if os.path.isfile("/var/www/alert_log.txt") == True:
                if (limits['lower'][port] > port_value or port_value > limits['upper'][port]) and port_value != 0:
                    if time_since_last_timestamp(alert_str, attempt_alert_str) > timer: 
    		    #If time since last timestamp in alert_log is greater than 3 hours
                        text = ("%s on port M%s was recorded to be %s at %s" % (p, port, port_value, timestamp))           
                        if email_send(text) == True:
                            kit_alert_string.append("|Email Alert Sent! (KIT) Limit breached for %s on port M%s"%(p,port))
                            print("Email Alert Sent! (KIT) Limit breached for %s on port M%s "%(p,port))
                        else:
                            kit_alert_string.append("|Attempted to send email! (KIT) Limit breached for %s on port M%s"%(p,port))
                            print("Attempted to send email! (KIT) Limit breached for %s on port M%s "%(p,port))
                    else:
                        kit_alert_string.append("|Limit breached for %s on port M%s"%(p,port))           
                        print("Limit breached for %s on port M%s "%(p,port))                
                elif (limits['lower'][port] < port_value < limits['upper'][port]):
                    print("Readings are normal for %s on port M%s"%(p,port))
            else:
                if (limits['lower'][port] > port_value or port_value > limits['upper'][port]) and port_value != 0:
                    text = ("%s on port M%s was recorded to be %s at %s" % (p, port, port_value, timestamp))           
                    if email_send(text) == True:
                        kit_alert_string.append("|Email Alert Sent! (KIT) Limit breached for %s on port M%s"%(p,port))
                        print("Email Alert Sent! (KIT) Limit breached for %s on port M%s "%(p,port))
                    else:
                        kit_alert_string.append("|Attempted to send email! (KIT) Limit breached for %s on port M%s"%(p,port))
                        print("Attempted to send email! (KIT) Limit breached for %s on port M%s "%(p,port))
                else:
                    print("Readings are normal for %s on port M%s"%(p,port))       
 
  if couple_connected == "Y":
 
      # upper and lower limits taken from config file
    print("Checking upper and lower limits for Thermocouple...")
    limits = {'upper': {}, 'lower': {}}
    for limit_number in range(4):
        for x in ['upper', 'lower']:
            limits[x][limit_number] = int(config.get('Thermocouple_settings', '%s limit T%d' % (x, limit_number)))
         
         #Mail send for each port.
         # If a port_value is outside the limits and the port_value is not 0 (no sensor attached to that port)
     
    for p, port in  zip(ports_couple, port_values_couple):
        port_value = port_values_couple[port]
        alert_str = str("Email Alert Sent! (THERMO) Limit breached for %s on port T%s"%(p,port))
        attempt_alert_str = str("Attempted to send email! (THERMO) Limit breached for %s on port T%s "%(p,port))
        if os.path.isfile("/var/www/alert_log.txt") == True: 
            if (limits['lower'][port] > port_value or port_value > limits['upper'][port]) and port_value != 0:
                if time_since_last_timestamp(alert_str, attempt_alert_str) > timer: #If time since last timestamp in alert_log is greater than 3 hours
                    text = ("%s on port T%s was recorded to be %s at %s" % (p, port, port_value, timestamp))           
                    if email_send(text) == True:
                        couple_alert_string.append("|Email Alert Sent! (THERMO) Limit breached for %s on port T%s"%(p,port))
                        print("Email Alert Sent! (THERMO) Limit breached for %s on port T%s "%(p,port))
                    else:
                        couple_alert_string.append("|Attempted to send email! (THERMO) Limit breached for %s on port T%s"%(p,port))
                        print("Attempted to send email! (THERMO) Limit breached for %s on port T%s "%(p,port))
            elif limits['lower'][port] < port_value < limits['upper'][port]:
                print("Readings are normal for %s on port T%s"%(p,port))
         
        else:
            if (limits['lower'][port] > port_value or port_value > limits['upper'][port]) and port_value != 0:
                text = ("%s on port T%s was recorded to be %s at %s" % (p, port, port_value, timestamp))           
                if email_send(text) == True:
                    couple_alert_string.append("|Email Alert Sent! (THERMO) Limit breached for %s on port T%s"%(p,port))
                    print("Email Alert Sent! (THERMO) Limit breached for %s on port T%s "%(p,port))
                else:
                    couple_alert_string.append("|Attempted to send email! (THERMO) Limit breached for %s on port T%s"%(p,port))
                    print("Attempted to send email! (THERMO) Limit breached for %s on port T%s "%(p,port)) 
            else:
                print("Readings are normal for %s on port T%s"%(p,port)) 

  prox_alert_string = ",".join(prox_alert_string)
  kit_alert_string = ",".join(kit_alert_string)
  couple_alert_string = ",".join(couple_alert_string)

  concat_alert_string = (prox_alert_string+kit_alert_string+couple_alert_string)
  if concat_alert_string != "":
    alert_log = open("/var/www/alert_log.txt","a+")             
    alert_log.write("\n%s %s " %(timestamp,concat_alert_string))
    alert_log.flush()
    os.fsync(alert_log)            
    alert_log.close()
  else:
    pass

     
#MAIN RUNNING SCRIPT
try:
   if kit_connected == "Y":
       interfaceKit.setOnErrorhandler(interfaceKitError)

except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)

print("Opening phidget objects....")

#Open phidget interface kit
try:
   if kit_connected == "Y":
       interfaceKit.openPhidget()
except PhidgetException as e:
   print("Phidget Exception %i: %s" % (e.code, e.details))
   print("Could not open InterfaceKit. Exiting....")
   exit(1)
#Open phidget temperature sensor
try:   
   if couple_connected == "Y":
       temperatureSensor.openPhidget()
except PhidgetException as e:
   print("Phidget Exception %i: %s" % (e.code, e.details))
   print("Could not open thermocouple. Exiting....")
   exit(1)


print("Waiting for attach....")

# Make sure interfaceKit is attached
try:
    if kit_connected == "Y":
       interfaceKit.waitForAttach(10000)
       print("InterfaceKit connected")
except PhidgetException as e:
   print("Phidget Exception %i: %s" % (e.code, e.details))
   try:
       if kit_connected == "Y":
           interfaceKit.closePhidget()
   except PhidgetException as e:
       print("Phidget Exception %i: %s" % (e.code, e.details))
       print("Could not close InterfaceKit. Exiting....")
       exit(1)
   print("Could not connect to InterfaceKit. Exiting....")
   exit(1)
else:
   if kit_connected == "Y":
       displayDeviceInfo()

# Make sure thermocouple is attached
try:
    if couple_connected == "Y":
       temperatureSensor.waitForAttach(10000)
       print("Thermocouple connected")
except PhidgetException as e:
   print("Phidget Exception %i: %s" % (e.code, e.details))
   try:
       if couple_connected == "Y":
           temperatureSensor.closePhidget()
   except PhidgetException as e:
       print("Phidget Exception %i: %s" % (e.code, e.details))
       print("Could not close Thermocouple. Exiting....")
       exit(1)
   print("Could not connect to Thermocouple. Exiting....")
   exit(1)
else:
   if couple_connected == "Y":
       DisplayDeviceInfo()

#Main function: Sensor Value -> Email -> LEDFlash
try:
   SensorValue()
   if kit_connected == "Y":
       LEDon_off()

except KeyboardInterrupt: #Use Ctrl+C to exit the loop through the main() function
   print("Closing...")
   pass

#Close phidgets interface kit
try:
   if kit_connected == "Y":
       interfaceKit.closePhidget()
   if couple_connected == "Y":
       temperatureSensor.closePhidget()
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)

#Close all log files
logfile.close()
alert_log.close()

print("Done.")
gc.collect()
exit(0)



   


