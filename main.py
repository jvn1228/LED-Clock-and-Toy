import time
import board
import neopixel
from led import led, OFF, FADE_IN, ON, TRANSITION, FADE_OUT

NUMPIXELS = 12
neopixels = neopixel.NeoPixel(board.D0, NUMPIXELS, brightness=0.2, auto_write=False)

class ledGroup:
    def __init__(self, neopixels_instance, opts={}, leds=[]):
        self.pixels = neopixels_instance
        if len(leds) == 0:
            self.leds = [led(self.pixels, i, opts) for i in range(NUMPIXELS)]
        else:
            self.leds = leds
    
    def onAll(self):
        for led in self.leds:
            led.on()
    
    def offAll(self):
        for led in self.leds:
            led.off()
    
    def onStrip(self, start, end):
        for led in self.leds[start:end]:
            led.on()
    
    def offStrip(self, start, end):
        for led in self.leds[start:end]:
            led.off()

    def setColorStrip(self, start, end, color):
        for led in self.leds[start:end]:
            led.setColor(color)
    
    def setColorAll(self, color):
        for led in self.leds:
            led.setColor(color)

    def setOptsAll(self, opts):
        for led in self.leds:
            led.setOpts(opts)
    
    def refresh(self):
        for led in self.leds:
            led.refresh()
        self.pixels.show()
    
    def getStates(self):
        return [led.state for led in self.leds]
    
    def __getitem__(self, key):
        return self.leds[key]

def counter(interval=NUMPIXELS, period=1000):
    return int(((time.monotonic()*1000) // period) % interval)

class clock:
    DAY = 24*60*60

    def __init__(self, h=0, m=0, s=0):
        self.h = h
        self.m = m
        self.s = s
        self.base_time = time.monotonic() - (h*60*60 + m*60 + s)
    
    def time(self):
        d_t = time.monotonic() - self.base_time
        if d_t > self.DAY:
            self.h = 0
            self.m = 0
            self.s = d_t - self.DAY
            self.base_time = time.monotonic()
        else:
            self.h = d_t / 60 // 60
            self.m = (d_t - (self.h * 3600)) // 60
            self.s = d_t - (self.h * 3600) - (self.m * 60)
        return (int(self.h), int(self.m), int(self.s))

ledGrp = ledGroup(neopixels, {"fade_in": True, "fade_out": True, "fade_in_time": 1000, "fade_out_time": 1000})
clk = clock(22, 30)

def wrapRefresh(action, timeout=1000):
    action()
    time_base = time.monotonic()

    while (time.monotonic() - time_base)*1000 < timeout:
        ledGrp.refresh()

time_base = time.monotonic()
prev_hr_idx = None
prev_min_idx = None
prev_sec_idx = None
ledGrp.offAll()
while True:
    if time.monotonic() - time_base > 0.017:
        ct = clk.time()

        ledGrp.refresh()

        hr_idx = (ct[0]+7) % 12
        min_idx = ((ct[1] // 5) + 7) % 12
        sec_idx = ((ct[2] // 5) + 7) % 12

        if hr_idx != prev_hr_idx:
            ledGrp[hr_idx].setColor((0,255,0))
            ledGrp[hr_idx].on()
            ledGrp[hr_idx-1].off()

            prev_hr_idx = hr_idx
        
        if min_idx != prev_min_idx:
            if ledGrp[min_idx].state == OFF:
                ledGrp[min_idx].setColor((0,0,255))
                ledGrp[min_idx].on()
            if (min_idx - 1) != hr_idx:
                ledGrp[min_idx-1].off()
        
            prev_min_idx = min_idx
        
        if sec_idx != prev_sec_idx:
            if ledGrp[sec_idx].state == OFF:
                ledGrp[sec_idx].setColor((255,0,0))
                ledGrp[sec_idx].on()
            if ((sec_idx - 1) != hr_idx) and ((sec_idx -1) != min_idx):
                ledGrp[sec_idx-1].off()
            
            prev_sec_idx = sec_idx

        time_base = time.monotonic()