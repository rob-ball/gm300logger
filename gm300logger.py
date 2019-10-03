#!/usr/bin/env python2
# log data from gq gmc 300e (works with all 300 series, might need to change baud rate to 115200, or set on device)
#
# Author: Paul W. Rogers  (SkyPi)
# (c) 2018 P.W. Rogers, Free for personal use.
# follow instructions here for setting up a udev rule (so you know that /dev/usb device N is most probably a gq electronics gmc device)
# 
# https://sourceforge.net/p/gqgmc/wiki/Home/
#
# read the GQ electronics docs for info on the command set
#
import time
import serial
from datetime import datetime
import statistics

class movingaverage() :
  def __init__(self,size=20,expsmooth=True,expfact = 0.5) :
    self.dataset = []
    self.maxsize=size
    self.datasetsize = 0
    self.expsmooth = expsmooth
    self.expfact = expfact
    self.smoothed = 0
    
  def addpoint(self,data) :
    # might want to check not adding non numeric type and try convert, numpties abound eh!
    # can do the convert at level above...
    if self.expsmooth :
      if self.datasetsize == 0 :
        self.smoothed = data
      else :
        self.smoothed = self.expfact * data + (1-self.expfact) * self.smoothed    
    if self.datasetsize == self.maxsize :
      self.dataset.pop(0)
    else :
      self.datasetsize += 1
    self.dataset.append(data)

  def median(self) :
    return statistics.median(self.dataset)

  def mean(self) :
    return statistics.mean(self.dataset)

  def expsmoothed(self) :
    return self.smoothed
    
    
    
ser = serial.Serial('/dev/gqgmc', 57600,timeout=5)

# only low 6 bits of high byte are valid data for the heartbeat message
hbmask = 0b00111111

f = open('radiation_cps_log.txt','a')

# reset stream and set heartbeat on 

ser.write("<HEARTBEAT0>>") # heartbeat off
time.sleep(1)

# clear serial buffer

while ser.in_waiting > 0 :
  ser.read(1)
  time.sleep(0.007)

time.sleep(1)

# start heartbeat transmission 

ser.write("<HEARTBEAT1>>") # heartbeat on

# read and log the cps messages

avgpermin = 0
mavgmin = movingaverage(60) # 1 min of samples
mavgminper10 = movingaverage(600) # 10 mins of samples
mavgminper30 = movingaverage(1800) # 30 mins of samples
mavgminper60 = movingaverage(3600) # 60 mins of samples

try :
  while True:
    logline = ser.read(2)
    cpsval = ord(logline[0]) & hbmask
    cpsval = cpsval << 8
    cpsval += ord(logline[1])
    mavgmin.addpoint(cpsval)
    mavgminper10.addpoint(cpsval)
    mavgminper30.addpoint(cpsval)
    mavgminper60.addpoint(cpsval)
    
    #print ord(logline[0]), ord(logline[1]), cpsval # debug
    logline = datetime.now().strftime('%Y-%m-%d, %H:%M:%S, ')+str(cpsval)+", "+"{:.2f}".format(mavgmin.mean()*60)   + \
         ", "+"{:.2f}".format(mavgminper10.mean()*60) +", "+"{:.2f}".format(mavgminper30.mean()*60) +", "+"{:.2f}".format(mavgminper60.mean()*60)
    f.write(logline)
    print logline  

except Exception as e :
  print e
  ser.close()
