
from psychopy import core, gui, event, visual
from smi import EyeTracker


def getSubjectId():
    expInfo = {'subject': 1}
    dlg = gui.DlgFromDict(expInfo, title='Specify subject ID')
    subjectId = expInfo['subject']
    if not dlg.OK or not subjectId > 0:
        core.quit()
    return subjectId


def initWindow(config):
    displayConfig = config['display']
    win = visual.Window(
        size=(displayConfig.getint('ResolutionX', 1600), displayConfig.getint('ResolutionY', 900)),
        monitor=displayConfig.get('MonitorName', 'testMonitor'),
        fullscr=displayConfig.getboolean('FullScreen', True),
        color='#B4B4B4',
        units='pix')
    win.mouseVisible = False
    return win


def checkQuit():
    if 'escape' in event.getKeys():
        core.quit()


def waitForKey(allowOnly=None):
    while True:
        for key in event.waitKeys():
            if key == 'escape':
                core.quit()
            elif allowOnly is None or key in allowOnly:
                event.clearEvents()
                return key


def wait(seconds):
    core.wait(seconds)


def instruct(win, text, color='white', allowOnly=None):
    textStim = visual.TextBox2(win, text=text, font='Open Sans', letterHeight=36, color=color, size=(1200, 400))
    textStim.draw()
    win.flip()
    return waitForKey(allowOnly)


def showPoint(win, x, y, color='white'):
    dot = visual.Circle(win, radius=5, lineColor=color, lineWidth=4, pos=(x-win.size[0]/2, win.size[1]/2-y))
    dot.draw()
    win.flip()


def display(win, name, score=None):
    if score:
        score = visual.TextStim(win, text=str(score), pos=(0, 92), font='Arial', color='white', height=36)
        score.draw()
    img = visual.ImageStim(win, f'images/{name}.png')
    img.draw()
    win.flip()


def setupEyeTracker(config, subjectId, win):
    et = EyeTracker(config['smi'], subjectId)
    calibrate = et.enabled
    while calibrate:
        instruct(win, 'A szemmozgáskövető kalibrációjához nézz a megjelenő pontokra!\n\nNyomj le egy gombot, ha kezdhetjük!')
        et.calibration(lambda x, y: showPoint(win, x, y))

        instruct(win, 'A validáláshoz is nézz a megjelenő pontokra és közben nyomj le egy billentyűt!\n\nNyomj le egy gombot, ha kezdhetjük!', color='yellow')
        leftRes, rightRes = et.calibration(lambda x, y: (showPoint(win, x, y, color='yellow'), waitForKey()), validate=True)

        response = instruct(win, f'A validáció eredménye:\n\nBal szem: {leftRes}\nJobb szem: {rightRes}\n\nMegfelelő a kalibráció (i/n)?', color='yellow', allowOnly=('i', 'n'))
        calibrate = not(response == 'i')

    et.closeReceive()
    return et


def teardown(win, et):
    et.inc()
    wait(.5)
    et.stop()
    et.close()
    instruct(win, 'Vége!\n\nNyomj le egy gombot!')
    win.close()
    core.quit()
