# Simple dummy server to test SMI integration without the actual eye-tracker

RECEIVE_ADDRESS = ('127.0.0.1', 4444)
SEND_ADDRESS = ('127.0.0.1', 5555)

import socket
import time

receive_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send(message):
    print('Sending: ', message)
    send_sock.sendto((message + '\n').encode('iso-8859-1'), SEND_ADDRESS)


receive_sock.bind(RECEIVE_ADDRESS)
receive_sock.settimeout(0.01)

streaming = False

while True:
    try:
        message, addr = receive_sock.recvfrom(1024)
        message = message.decode('iso-8859-1')
        print('Received: ', message)
        if message.startswith('ET_PNG'):
            send('ET_PNG\n')
        elif message.startswith('ET_INF dev'):
            send('ET_INF RED\n')
        elif message.startswith('ET_INF ver'):
            send('ET_INF 2.3.0\n')
        elif message.startswith('ET_SRT'):
            send('ET_SRT 100\n')
        elif message.startswith('ET_CAL') or message.startswith('ET_VLS'):
            send('ET_CAL 5')
            time.sleep(0.06)
            send('ET_CSZ 1680\t1050')
            send('ET_PNT 1 840\t525')
            send('ET_PNT 2 168 105')
            send('ET_PNT 3 168 955')
            send('ET_PNT 4 1512 955')
            send('ET_PNT 5 1512 105')
            send('ET_CHG 1')
            send('ET_CHG 1')
            time.sleep(2)
            send('ET_ACC')
            send('ET_CHG 2')
            time.sleep(0.6)
            send('ET_ACC')
            send('ET_CHG 3')
            time.sleep(0.6)
            send('ET_ACC')
            send('ET_CHG 4')
            time.sleep(0.6)
            send('ET_ACC')
            send('ET_CHG 5')
            time.sleep(0.6)
            send('ET_ACC')
            send('ET_FIN 1')
            if message.startswith('ET_VLS'):
                send('ET_VLS left 100 200 300 4º 5º')
                send('ET_VLS right 100.1 200.2 300.3 4.4º 5.5º')
        elif message.startswith('ET_STR'):
            print('Starting streaming')
            streaming = True
        elif message.startswith('ET_EST'):
            print('Ending streaming')
            streaming = False
        else:
            print("Don't know, how to answer.")
    except socket.timeout:
        if streaming:
            pupil = time.time() / 5 % 6
            send('ET_SPL %.4f %.4f 1 b' %(pupil, pupil))
