import time

def interpolate(ca, ta, cb, tb):
    return cb+(ca/ta)*(tb-cb)

def clip(val):
    return max(min(val, 255), 0)

DEF_OPTS = {
    "fade_in": True,
    "fade_out": True,
    "fade_between": True,
    "fade_in_time": 800,
    "fade_out_time": 800,
    "fade_between_time": 800,
    "color": (255, 255, 255)
}
OFF = 0
FADE_IN = 1
ON = 2
TRANSITION = 3
FADE_OUT = 4

class Led:
    def __init__(self, pixels_instance, idx, opts={}):
        self.idx = idx
        self.pixels = pixels_instance

        self.fade_in = opts.get("fade_in", DEF_OPTS["fade_in"]) 
        self.fade_out = opts.get("fade_out", DEF_OPTS["fade_out"])
        self.fade_between = opts.get("fade_between", DEF_OPTS["fade_between"]) 
        
        # fade times in milliseconds
        self.fade_in_time = opts.get("fade_in_time") or DEF_OPTS["fade_in_time"]
        self.fade_out_time = opts.get("fade_out_time") or DEF_OPTS["fade_out_time"]
        self.fade_between_time = opts.get("fade_between_time") or DEF_OPTS["fade_between_time"]

        if opts.get("color"):
            self.r = opts["color"][0]
            self.g = opts["color"][1]
            self.b = opts["color"][2]
        else:
            self.r = DEF_OPTS["color"][0]
            self.g = DEF_OPTS["color"][1]
            self.b = DEF_OPTS["color"][2]

        self.state = OFF
        self.curr_r = 0
        self.curr_g = 0
        self.curr_b = 0
        self.base_time = time.monotonic()
        self.base_r = 0
        self.base_g = 0
        self.base_b = 0
        self.target_r = 0
        self.target_g = 0
        self.target_b = 0

    def setOpts(self, opts):
        self.fade_in = opts.get("fade_in", self.fade_in)
        self.fade_out = opts.get("fade_out", self.fade_out)
        self.fade_between = opts.get("fade_between", self.fade_between)
        
        # fade times in milliseconds
        self.fade_in_time = opts.get("fade_in_time", self.fade_in_time)
        self.fade_out_time = opts.get("fade_out_time", self.fade_out_time)
        self.fade_between_time = opts.get("fade_between_time", self.fade_between_time)

        if opts.get("color"):
            self.r = opts["color"][0]
            self.g = opts["color"][1]
            self.b = opts["color"][2]

    def setTargetColor(self, color):
        self.target_r = clip(color[0])
        self.target_g = clip(color[1])
        self.target_b = clip(color[2])
    
        return self.getTargetColor()
    
    def getTargetColor(self):
        return (self.target_r, self.target_g, self.target_b)

    def setCurrentColor(self, color):
        self.curr_r = clip(color[0])
        self.curr_g = clip(color[1])
        self.curr_b = clip(color[2])

        return self.getCurrentColor()

    def getCurrentColor(self):
        return (self.curr_r, self.curr_g, self.curr_b)
    
    def setBaseColor(self, color):
        self.base_r = clip(color[0])
        self.base_g = clip(color[1])
        self.base_b = clip(color[2])

        return self.getBaseColor()

    def getBaseColor(self):
        return (self.base_r, self.base_g, self.base_b)

    def getDeltaT(self):
        return (time.monotonic() - self.base_time) * 1000

    def refresh(self):
        if self.state == ON and (self.getCurrentColor() != self.getTargetColor()):
            self.pixels[self.idx] = self.getTargetColor()
            self.setCurrentColor(self.getTargetColor())
        elif self.state == OFF and (self.getCurrentColor() != (0,0,0)):
            self.pixels[self.idx] = (0,0,0)
            self.setCurrentColor((0,0,0))
        elif self.state == FADE_IN or self.state == FADE_OUT or self.state == TRANSITION:      
            dt = self.getDeltaT()
            fade_time = self.fade_in_time if self.state == FADE_IN else self.fade_out_time if self.state == FADE_OUT else self.fade_between_time
            if dt < fade_time:
                self.setCurrentColor((
                    int(interpolate(dt, fade_time, self.base_r, self.target_r)),
                    int(interpolate(dt, fade_time, self.base_g, self.target_g)),
                    int(interpolate(dt, fade_time, self.base_b, self.target_b))
                ))
            else:
                self.setCurrentColor((0,0,0) if self.state == FADE_OUT else self.getColor())
                self.state = OFF if self.state == FADE_OUT else ON
            self.pixels[self.idx] = self.getCurrentColor()

    def on(self):
        if self.state == OFF or self.state == FADE_OUT:
            if self.fade_in == True:
                self.setBaseColor(self.getCurrentColor())
                self.setTargetColor(self.getColor())
                self.state = FADE_IN
                self.base_time = time.monotonic()
            else:
                self.setTargetColor(self.getColor())
                self.state = ON
    
    def off(self):
        if (self.state != FADE_OUT) and (self.state != OFF):
            if self.fade_out == True:
                self.setBaseColor(self.getCurrentColor())
                self.setTargetColor((0,0,0))
                self.state = FADE_OUT
                self.base_time = time.monotonic()
            else:
                self.setTargetColor((0,0,0))
                self.state = OFF

    def getColor(self):
        return (self.r, self.g, self.b)

    def setColor(self, color):
        self.r = clip(color[0])
        self.g = clip(color[1])
        self.b = clip(color[2])
        if self.fade_between == True and (self.state == ON or self.state == FADE_IN):
            self.state = TRANSITION
            self.base_time = time.monotonic()
            self.setBaseColor(self.getCurrentColor())
            self.setTargetColor(color)
        elif self.state == FADE_IN:
            self.setTargetColor(color)
        elif self.state != TRANSITION:
            self.setTargetColor(color)