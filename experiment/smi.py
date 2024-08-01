
import re
import socket
import time

# Helper class for integration with the SMI eye-tracker machine
class EyeTracker(object):

    def __init__(self, config, subjectId):
        self.enabled = config.getboolean('Enabled', True)
        self.trialCount = 0
        if self.enabled:
            self.config = config
            self.subjectId = subjectId
            self.timeOut = config.getint('TimeOut', 10)
            self.receiveSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.receiveSock.settimeout(self.timeOut)
            self.receiveSock.bind((config.get('ReceiveIp', '127.0.0.1'), config.getint('ReceivePort', 5555)))
            self.sendSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            self.send('ET_PNG')
            self.send('ET_EST')
            self.send('ET_STP')
            self.send('ET_CLR')
            time.sleep(0.5)


    def receive(self):
        if self.enabled:
            msg, addr = self.receiveSock.recvfrom(2048)
            msg = msg.decode('iso-8859-1')
            print("Received: ", msg)
            parsed = re.split('[ \t\r\n]+', msg)
            return (parsed[0], parsed[1:])


    def send(self, msg):
        if self.enabled:
            print("Sending: ", msg)
            self.sendSock.sendto((msg + '\n').encode('iso-8859-1'), (self.config.get('SendIp', '127.0.0.1'), self.config.getint('SendPort', 4444)))


    def calibration(self, showPoint, validate=False):
        if self.enabled:
            self.send('ET_VLS' if validate else 'ET_CAL')

            calPoints = {}
            leftResult = None
            rightResult = None
            timeoutTime = time.time() + self.timeOut
            while True:
                cmd, pars = self.receive()
                if cmd == 'ET_PNT':
                    calPoints[int(pars[0])] = (int(pars[1]), int(pars[2]))
                elif cmd == 'ET_CHG':
                    pointNum = int(pars[0])
                    pointX, pointY = calPoints[pointNum]
                    showPoint(pointX, pointY)
                    if validate:
                        self.send('ET_ACC')
                elif cmd == 'ET_FIN':
                    if not validate:
                        return
                elif cmd == 'ET_VLS':
                    result = 'x=%s y=%s d=%s xd=%s yd=%s' %tuple(pars[1:6])
                    if pars[0] == 'left':
                        print('Left validation result: ', result)
                        leftResult = result
                    elif pars[0] == 'right':
                        print('Right validation result: ', result)
                        rightResult = result
                    if leftResult is not None and rightResult is not None:
                        return leftResult, rightResult

                if time.time() > timeoutTime:
                    raise Exception('Timeout waiting for calibration point!')


    def closeReceive(self):
        if self.enabled:
            self.receiveSock.close()


    def record(self):
        self.trialCount += 1
        self.send('ET_REC')


    def stop(self):
        self.send('ET_STP')


    def inc(self):
        self.send('ET_INC')
        self.trialCount += 1
        self.send('ET_REM %d' %self.trialCount)
        return self.trialCount


    def close(self):
        if self.enabled:
            self.send('ET_SAV "%ssubject_%d_%d.idf"' %(self.config.get('SavePath', ''), self.subjectId, int(time.time())))
            self.sendSock.close()
