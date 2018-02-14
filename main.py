# Infinity Mirror LEDs
# By Jonathan Nguyen (c) 2018
# Adapts Adafruit NeoPixel code

import board
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogOut, AnalogIn
import touchio
import adafruit_dotstar as dotstar
import time
import neopixel
import random

# One pixel connected internally!
dot = dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1, brightness=0.2)

# Built in red LED
led = DigitalInOut(board.D13)
led.direction = Direction.OUTPUT

# Capacitive touch on D3
touch = touchio.TouchIn(board.D3)

# NeoPixel strip (of 16 LEDs) connected on D4
NUMPIXELS = 12
neopixels = neopixel.NeoPixel(board.D0, NUMPIXELS, brightness=0.2, auto_write=False)

SNAKELENGTH = 3
SNAKECOLOR = 1

FADESPEED = 10

STARS = 4
randomArray = []

# Touch variables
lastState = 0
mode = 0

#random pulse
randR = []
randG = []
randB = []

#time
seconds = 0
minutes = 0
hours = 0

setMinutes = 50
setHours = 19
######################### HELPERS ##############################

# Helper to convert analog input to voltage
def getVoltage(pin):
    return (pin.value * 3.3) / 65536

# Helper to give us a nice color swirl
def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if (pos < 0) or (pos > 255):
        return (0, 0, 0)
    if pos < 85:
        return (int(255 - pos*3), int(pos*3), 0)
    elif pos < 170:
        pos -= 85
        return (0, int(255 - (pos*3)), int(pos*3))
    else:
        pos -= 170
        return (int(pos*3), 0, int(255 - pos*3))

def colorCycler(index):
    # make the neopixels shift colors
    for p in range(NUMPIXELS):
        idx = int ((p * 256 / NUMPIXELS) + i)
        neopixels[p] = wheel(idx & 255)
    neopixels.show()

def snake(index):
    # make neopixels chase themselves
    neopixels.fill((0, 0, 0))
    step = round(index % NUMPIXELS)
    print(step)
    for p in range(1,SNAKELENGTH+1):
        if SNAKECOLOR == 0:
            neopixels[(step + p) % NUMPIXELS] = (int(255 / p), int(255 / p), int(255 / p))
        else:
            idx = int ((p * 256 / NUMPIXELS) + i)
            neopixels[(step + p) % NUMPIXELS] = wheel(idx & 255)
    neopixels.show()
    
def clunk(index, lastState):
    #fill up the strip gradually
    step = round(index % (NUMPIXELS + 1))
    for p in range(0, NUMPIXELS - step + 1):
            for intensity in range(0,255,FADESPEED):
                if p < NUMPIXELS and step != 0:
                    neopixels[p] = (intensity, intensity, intensity)
                if p > 0:
                    neopixels[p - 1] = (255 - intensity, 255 - intensity, 255 - intensity)
                neopixels.show()
                [newState, newMode] = pollButton(lastState, 2)
                if newMode != 2:
                    return newMode-1
            if step == 12:
                time.sleep(1)
    return 2

def starfield(index, randomArray):
    #light up random neopixels
    randomPool = list(set(range(0, NUMPIXELS)).difference(randomArray))
    if len(randomArray) < STARS:
        randomArray.insert(0, random.choice(randomPool))
        for intensity in range(0,255,FADESPEED):
            neopixels[randomArray[0]] = (intensity, intensity, intensity)
            neopixels.show()
    else:
        randomArray.insert(0, random.choice(randomPool))
        removeRandom = random.randint(1,STARS)
        for intensity in range(0,255,FADESPEED):
            neopixels[randomArray[removeRandom]] = (255-intensity, 255-intensity, 255-intensity)
            neopixels[randomArray[0]] = (intensity, intensity, intensity)
            neopixels.show()
        randomArray.pop(removeRandom)

def pulse(lastState):
    #pulse fill random colors
    for p in range(NUMPIXELS):
        randR.append(random.randint(0,128))
        randG.append(random.randint(0,128))
        randB.append(random.randint(0,128))
    for intensity in range(0,255,FADESPEED):
        for p in range(NUMPIXELS):
            neopixels[p] = (int(randR[p]*intensity/255),int(randG[p]*intensity/255),int(randB[p]*intensity/255))
            [newState, newMode] = pollButton(lastState, 4)
            if newMode != 4:
                return newMode-1
        neopixels.show()
    for intensity in range(255,0,-1*FADESPEED):
        for p in range(NUMPIXELS):
            neopixels[p] = (int(randR[p]*intensity/255),int(randG[p]*intensity/255),int(randB[p]*intensity/255))
            [newState, newMode] = pollButton(lastState, 4)
            if newMode != 4:
                return newMode-1
        neopixels.show()
    randR.clear()
    randG.clear()
    randB.clear()
    
def clock(seconds, minutes, hours, index):
    #clock function
    neopixels.fill((0,0,0))
    clockOffset = 7
    if int(minutes/5) > hours%12:
        for p in range(int(minutes/5)+1):
            neopixels[(p+clockOffset)%12] = wheel(index & 255)
        for p in range((hours%12)+1):
            neopixels[(p+clockOffset)%12] = wheel((index+128)%256 & 255)
        neopixels[(int(seconds/5)+clockOffset)%12] = (255, 255, 255)
        neopixels.show()
    elif int(minutes/5) < hours%12:
        for p in range((hours%12)+1):
            neopixels[(p+clockOffset)%12] = wheel((index+128)%256 & 255)
        for p in range(int(minutes/5)+1):
            neopixels[(p+clockOffset)%12] = wheel(index & 255)
        neopixels[(int(seconds/5)+clockOffset)%12] = (255, 255, 255)
        neopixels.show()
    else:
        for p in range((hours%12)+1):
            neopixels[(p+clockOffset)%12] = wheel((index+128)%256 & 255)
        neopixels[(int(seconds/5)+clockOffset)%12] = (255, 255, 255)
        neopixels.show()

def pollButton(lastState,mode):
    #read button input
    # use D3 as capacitive touch to turn on internal LED
    if touch.value & (lastState == 0):
      print("D3 touched!")
      neopixels.fill((0,0,0))
      neopixels.show()
      i = 0
      mode = (mode+1)%6
      return [1, mode]
    elif (not touch.value) & lastState == 1:
      print("D3 released!")
      return [0, mode]
    return [0, mode]
######################### MAIN LOOP ##############################
mode = 5
i = 0
neopixels.fill((0,0,0))
neopixels.show()

initialSecond = time.monotonic()

while True:
  # spin internal LED around! autoshow is on
  dot[0] = wheel(i & 255)
  
  if mode == 0:
    colorCycler(i)
  elif mode == 1:
    snake(i)
  elif mode == 2:
    mode = clunk(i, lastState)
  elif mode == 3:
    starfield(i, randomArray)
  elif mode == 4:
    pulse(lastState)
  elif mode == 5:
    clock(seconds, minutes, hours, i)
  
  seconds = int(time.monotonic()-initialSecond)%60
  minutes = (int((time.monotonic()-initialSecond)/60)+setMinutes)%60
  hours = (int((time.monotonic()-initialSecond)/1440)+setHours)%24
  
  #print([hours, minutes, seconds], sep = ":", end = "\n")
  
  
  [newState, newMode] = pollButton(lastState, mode)
  lastState = newState
  if not(mode == newMode):
      i = 0
      mode = newMode

  i = (i+1) % 256  # run from 0 to 255
  time.sleep(0.5) # make bigger to slow down