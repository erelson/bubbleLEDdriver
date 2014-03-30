from multiprocessing import Process, Pipe
from time import time, sleep
import sys


def main():

    starttime = time()

    # Paths for pins
    pA = "/sys/class/gpio/gpio139/" # 33
    pB = "/sys/class/gpio/gpio141/" # 35
    pC = "/sys/class/gpio/gpio143/" # 37
    pD = "/sys/class/gpio/gpio205/" # 39
    pE = "/sys/class/gpio/gpio35/"  # 41
    pF = "/sys/class/gpio/gpio33/"  # 43
    pG = "/sys/class/gpio/gpio144/" # 45
    pH = "/sys/class/gpio/gpio89/"  # 47
    pX = "/sys/class/gpio/gpio104/" # 49
    pY = "/sys/class/gpio/gpio56/"  # 51
    pZ = "/sys/class/gpio/gpio88/"  # 53

    paths = [pA, pB, pC, pD, pE, pF, pG, pH, pX, pY, pZ] 

    for path in paths:
        with open(path + "direction", 'w') as f:
            f.write('out')
            f.flush()

    with open(pA + "value", 'w') as fA, \
            open(pB + "value", 'w') as fB, \
            open(pC + "value", 'w') as fC, \
            open(pD + "value", 'w') as fD, \
            open(pE + "value", 'w') as fE, \
            open(pF + "value", 'w') as fF, \
            open(pG + "value", 'w') as fG, \
            open(pH + "value", 'w') as fH, \
            open(pX + "value", 'w') as fX, \
            open(pY + "value", 'w') as fY, \
            open(pZ + "value", 'w') as fZ:
        pinslist = [
                (fA, 'A'),
                (fB, 'B'),
                (fC, 'C'),
                (fD, 'D'),
                (fE, 'E'),
                (fF, 'F'),
                (fG, 'G'),
                (fH, 'H'),
                ]
        digipinslist = [
                (fX, 'X', 0),
                (fY, 'Y', 1),
                (fZ, 'Z', 2),
                ]


        # ... used to determine which segments to enable for each digit
        val_to_segdict = {
            '0' : ['A', 'B', 'C', 'D', 'E', 'F'],
            '1' : ['B', 'C'],
            '2' : ['A', 'B', 'D', 'E', 'G'],
            '3' : ['A', 'B', 'C', 'D', 'G'],
            '4' : ['B', 'C', 'F', 'G'],
            '5' : ['A', 'C', 'D', 'F', 'G'],
            '6' : ['A', 'C', 'D', 'E', 'F', 'G'],
            '7' : ['A', 'B', 'C'],
            '8' : ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
            '9' : ['A', 'B', 'C', 'D', 'F', 'G']}

        myDisp = LED_display_updater(pinslist, digipinslist, val_to_segdict)

        # create parent/child ends of a pipe
        ppipe, cpipe = Pipe()

        updater = Process(target=myDisp.update, args=(cpipe,))
        updater.start()
        #updater.join()

        try:
            # use pipe to update digit every 1/10 sec
            while 1:
                sleep(0.1)
                newval = int(time() - starttime)
                ppipe.send(newval)

        except:
            # kill the updater and turn off LEDs and reset pins to inputs
            myDisp.kill = True
            sleep(0.5)

            for pinf, _ in pinslist:
                pinf.write('0')
                pinf.flush()
            for pinf, _, _ in digipinslist:
                pinf.write('0')
                pinf.flush()
            for path in paths:
                with open(path + "direction", 'w') as f:
                    f.write('in')
                    f.flush()
            print '\nSafely exited: set all pins in use low, and as inputs.'
            sys.exit()
        


class LED_display_updater():

    def __init__(self, pinslist, digipinslist, val_to_segdict, nLEDs=3):
        self.val = 123
        self.digit = 0
        self.kill = False # If true, update stops updating.
        self.pinslist = pinslist
        self.digipinslist = digipinslist
        self.val_to_segdict = val_to_segdict
        self.pinstatdict = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0,
                            'G': 0, 'H': 0, 'X': 0, 'Y': 0, 'Z': 0}
        self.xyzdict = {'X':'Y', 'Y':'Z', 'Z':'X'}

        # List for iterating through the three digits
        self.update_digit = range(1, nLEDs) + [0]

    def update(self, pipe):
        """
        """
        try:
            while 1:
                    if self.kill:
                        return
                    
                    if pipe.poll():
                        self.val = pipe.recv()

                    self.digit = self.update_digit[self.digit]

                    self.set_leds()

                    sleep(0.005)

        except KeyboardInterrupt:
            return

    def set_leds(self):
        """
        """
        val = "{0:0>3}".format(self.val)

        #xx = self.pinstatdict.keys()
        #xx.sort()
        #print val, self.digit, "".join([str(self.pinstatdict[i]) for i in xx])

        for pinf, pin in self.pinslist:
            if self.pinstatdict[pin] != int(pin in \
                    self.val_to_segdict[val[self.digit]]):
                self.pinstatdict[pin] = 0 if self.pinstatdict[pin] else 1 
                pinf.write(str(self.pinstatdict[pin]))
                pinf.flush()

        for pinf, pin, digit in self.digipinslist:
            # if current digit pin status does not match
            # [digit same as active digit]
            if self.pinstatdict[pin] != int(digit == self.digit):
                # toggle digit status
                self.pinstatdict[pin] = 0 if self.pinstatdict[pin] else 1
                # write opposite of digit status (since using PNP transistors)
                pinf.write('0' if self.pinstatdict[pin] else '1')
                pinf.flush()

if __name__ == "__main__":
    main()
