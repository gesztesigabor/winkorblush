
import configparser
import numpy as np
import time
from plan_conds import planConds
from utils import *


def side(val):
    return 'right' if val else 'left'


def fillers(expConfig, subjectId, win, dataFile, et, preferred, score):
    prefProb = expConfig.getfloat('PreferredProbability', 0.8)
    difference = 0
    minDifference = expConfig.getint('FillerMinDifference', 0)
    learnedResponses = 0
    minLearnedResponses = expConfig.getint('FillerMinLearnedResponses', 0)
    fillerCount = 0
    maxFillers = expConfig.getint('FillerMaxTrials', -1)
    feedbackTime = expConfig.getfloat('FeedbackTime', 1.)
    xEyePostfix = 'x' if expConfig.getboolean('XEye', False) else ''

    while ((difference < minDifference) or (learnedResponses < minLearnedResponses)) and ((fillerCount < maxFillers) or (maxFillers < 0)):
        fillerCount += 1
        trialCount = et.inc() if et else None
        if np.random.binomial(1, prefProb):
            difference += 1
            direction = side(preferred)			
        else:
            difference -= 1
            direction = side(1 - preferred)

        display(win, f'select{xEyePostfix}', score)
        response = waitForKey(['left', 'right'])
        feedback = 'win' if response == direction else 'loose'
        score += 1 if response == direction else -1
        display(win, f'{direction}_{feedback}{xEyePostfix}', score)
        wait(feedbackTime)

        if response == side(preferred):
            learnedResponses += 1
        else:
            learnedResponses = 0

        if dataFile:
            dataFile.write(f'{subjectId},{trialCount},filler,{side(preferred)},{direction},{response},{score}\n')

    return score


def experiment(config, subjectId, win, training, et=None):
    expConfig = config['experiment']
    if not training:
        dataFile = open(f'subject_{subjectId}_{int(time.time())}.csv', 'w')
        dataFile.write('subjectId,trialCount,condType,preferred,direction,response,score\n')
        instruct(win, 'Nyomj le egy gombot, ha indulhat a kísérlet!')
        if et is not None:
            et.record()
        wait(.5)
        seed = expConfig.getint('RandomSeed', None)
        if seed is not None:
            np.random.seed(seed)
    else:
        dataFile = None
 
    preferred = np.random.binomial(1, 0.5)
    prefProb = expConfig.getfloat('PreferredProbability', 0.8)
    score = expConfig.getint('InitialScore', 100)
    preparationTime = expConfig.getfloat('PreparationTime', 2.)
    cueTime = expConfig.getfloat('CueTime', 4.)
    feedbackTime = expConfig.getfloat('FeedbackTime', 1.)
    afterCueKey = expConfig.get('AfterCueKey', '')
    xEyePostfix = 'x' if expConfig.getboolean('XEye', False) else ''

    for condType in planConds(expConfig, training):
        score = fillers(expConfig, subjectId, win, dataFile, et, preferred, score)

        trialCount = et.inc() if et else None
        display(win, 'warn')
        wait(preparationTime)

        if condType == 'wink':
            preferred = 1 - preferred
        elif condType == 'blush':
            preferred = np.random.binomial(1, 0.5)

        if condType == 'hint':
            direction = side(preferred)
            display(win, f'hint_{direction}')
        else:
            direction = side(preferred if np.random.binomial(1, prefProb) else 1 - preferred)
            display(win, condType)
        wait(cueTime)

        if afterCueKey != '':
            display(win, f'aftercue_{afterCueKey}')
            waitForKey([afterCueKey])

        display(win, f'select{xEyePostfix}', score)
        response = waitForKey(['left', 'right'])
        feedback = 'win' if response == direction else 'loose'		
        score += 1 if response == direction else -1
        display(win, f'{direction}_{feedback}{xEyePostfix}', score)
        wait(feedbackTime)

        if dataFile:
            dataFile.write(f'{subjectId},{trialCount},{condType},{side(preferred)},{direction},{response},{score}\n')
    
    if dataFile:
        dataFile.close()


def main():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8-sig')

    subjectId = getSubjectId()

    win = initWindow(config)
    while True:
        if instruct(win, 'Szeretnél gyakorolni (i/n)?', allowOnly=('i', 'n')) == 'n':
            break
        experiment(config, subjectId, win, training=True)
    et = setupEyeTracker(config, subjectId, win)
    experiment(config, subjectId, win, training=False, et=et)
    teardown(win, et)


if __name__ == '__main__':
	main()
