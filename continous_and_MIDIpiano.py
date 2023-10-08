from machine import mem32

class PWMCounter:
    high = 1
    risingEdge = 2
    fallingEdge = 3
    
    def __init__(self, pin, condition = high):
        assert pin < 30 and pin % 2, "Invalid pin number"
        slice_offset = (pin % 16) // 2 * 20
        self._pin_reg = 0x40014000 | (0x04 + pin * 8)
        self._csr = 0x40050000 | (0x00 + slice_offset)
        self._ctr = 0x40050000 | (0x08 + slice_offset)
        self._div = 0x40050000 | (0x04 + slice_offset)
        self._condition = condition
        self.setup()
    
    def setup(self):
        # Set pin to PWM
        mem32[self._pin_reg] = 4
        # Setup PWM counter for selected pin to chosen counter mode
        mem32[self._csr] = self._condition << 4
        self.reset()
    
    def start(self):
        mem32[self._csr + 0x2000] = 1
        
    def stop(self):
        mem32[self._csr + 0x3000] = 1
    
    def reset(self):
        mem32[self._ctr] = 0
    
    def read(self):
        return mem32[self._ctr]
    
    def readAndReset(self):
        tmp = self.read()
        self.reset()
        return tmp
    
    def setDiv(self, int_ = 1, frac = 0):
        if int_ == 256: int_ = 0
        mem32[self._div] = (int_ & 0xff) << 4 | frac & 0xf
        

def toneOut(note, octv):
    if note < 4:
        return 10
    if note < 9:
        return octv[0]
    if note < 12:
        return octv[1]
    if note < 16:
        return octv[2]
    if note < 20:
        return octv[3]
    if note < 25:
        return octv[4]
    if note < 32:
        return octv[5]
    if note < 39:
        return octv[6]
    if note < 47:
        return octv[7]
    if note < 55:
        return octv[8]
    if note < 70:
        return octv[9]
    if note < 100:
        return octv[10]
    if note >= 100:
        return octv[11]
    return 10

def choseOct(i):
    if i < 200:
        return 0
    if i < 400:
        return 1
    if i < 700:
        return 2
    if i < 900:
        return 3
    if i > 1500:
        return 4
    return 3

if __name__ == "__main__":
    from machine import *
    from time import *

# Set counter to count rising edge of pitch osc
    counter = PWMCounter(15, PWMCounter.risingEdge)
# Set divisor to 1
    counter.setDiv()
# Start counter
    counter.start()
 
# Set counterVol to count rising edge of pitch osc 
    counterVol = PWMCounter(11, PWMCounter.risingEdge)
# Set divisor to 1
    counterVol.setDiv()
# Start counter
    counterVol.start()    

    
        
# Set sampling time in ms for the piano theremin
    sampling_time = 50
# Set desired count for continous theremin    
    countDesired = 10000

# initialise variables
    n = 0
    i = 0
    avTone = 0
    avVol = 0
    lastCheck = ticks_us()
    pinOut = PWM(Pin(1))

    toneList = []
    volList = []
    onInd = 0
    count = 0
    timerCheck = 0
    timerSwitch = 0
    
    oct = [[65, 69, 73, 77, 82, 87, 92, 97, 103, 110, 116, 123],
           [130, 138, 146, 155, 164, 174, 184, 195, 207, 220, 223, 246],
           [261, 277, 293, 311, 329, 349, 369, 391, 415, 440, 466, 493],
           [523, 544, 587, 622, 659, 698, 739, 789, 830, 880, 932, 987],
           [1046, 1108, 1174, 1244, 1318, 1396, 1480, 1568, 1661, 1760, 1864, 1975]]
    
    def playTone(freq, volume):
        pinOut.freq(freq)
        pinOut.duty_u16(volume)
        if freq == 10:
            pinOut.duty_u16(0)
            
    switch = True       
    while True:
        if switch:
            if counter.read() >= countDesired:
                diff = ticks_diff(tmp := ticks_us(), lastCheck)
            # Print calculated frequency in Hz - should show 1000 with default setup
                tone = counter.readAndReset() / (diff / 1000000)/21
                vol = counterVol.readAndReset() / (diff / 1000000)
                print(tone*21,"      ", vol)

                lastCheck = tmp

                if n < 100:
                    toneList.append(tone)
                    volList.append(vol)
                    n+=1
                if n == 100:
                    print("\n \n \n \n \n ------------------------- \n \n \n \n \n -----------------READY------------------ \n \n \n \n \n ----------------------------- \n \n \n \n \n")
                    avTone = sum(toneList) / len(toneList)
                    avVol = sum(volList) / len(volList)
                    print(avTone, "      " , avVol)

                    n = 101
                    
                tone -= avTone
                vol -= avVol
                
                toneIn = tone * -1
                volIn = vol *-1
                
                volume = int(volIn)
                pitch = int(toneIn)
                
                currentTime = ticks_ms()
                if volume > 20000 and (currentTime - timerCheck) > 300 :
                    count += 1
                    if count == 1:
                        timerSwitch = ticks_ms()
                    timerCheck = ticks_ms()
                if count >= 5 and (currentTime - timerSwitch) < 10000:
                    print("switch")
                    playTone(10,0)
                    switch = False
                    count = 0
                    sleep_ms(2000)
                    lastCheck = ticks_ms()
                    timerSwitch = 0
                if (currentTime - timerSwitch) > 10000:
                    count = 0
                    timerSwitch = 0
                
                octInd = choseOct(volume)
                toneIn = toneIn/10-35
                
                if volume < 2000:
                    volume = 0
                if volume > 32768:
                    volume = 32768
                    
                  
                if pitch > 4186:
                    pitch = 4186
                if pitch < 33:
                    pitch = 10

                
                playTone(pitch, volume)
                
        else:
            if ticks_diff(tmp := ticks_ms(), lastCheck) >= sampling_time:
                diff = ticks_diff(tmp := ticks_ms(), lastCheck)
            # Print calculated frequency in Hz - should show 1000 with default setup
                tone = counter.readAndReset() / (sampling_time / 1000)/21
                vol = counterVol.readAndReset() / (sampling_time / 1000)/10
                print(tone*21, "      ", vol*10)

                tone -= avTone
                vol -= avVol/10
                
                lastCheck = tmp
                toneIn = tone * -1
                volIn = vol *-1
                
                volume = int(volIn)
                currentTime = ticks_ms()
                
                if volume > 20000 and (currentTime - timerCheck) > 300 :
                    count += 1
                    if count == 1:
                        timerSwitch = ticks_ms()
                    timerCheck = ticks_ms()
                if count >= 5 and (currentTime - timerSwitch) < 10000:
                    print("switch")
                    switch = True
                    playTone(10,0)
                    count = 0
                    sleep_ms(2000)
                    timerSwitch = 0
                if (currentTime - timerSwitch) > 10000:
                    count = 0
                    timerSwitch = 0
                
                octInd = choseOct(volume)
                toneIn = toneIn/10

                if toneIn < 0:
                    toneIn = 0
                    
                toneIn = int(toneIn)

                pitch = int(toneOut(toneIn, oct[octInd]))
                
                
                playTone(pitch,20000)

        
                    
            

            
            
            
            
            
                    
            
        





