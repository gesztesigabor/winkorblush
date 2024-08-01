
import configparser
import numpy as np
import time
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

    while ((difference < minDifference) or (learnedResponses < minLearnedResponses)) and ((fillerCount < maxFillers) or (maxFillers < 0)):
        fillerCount += 1
        trialCount = et.inc() if et else None
        if np.random.binomial(1, prefProb):
            difference += 1
            correctResponse = side(preferred)			
        else:
            difference -= 1
            correctResponse = side(1 - preferred)

        display(win, 'select', score)
        response = waitForKey(['left', 'right'])
        feedback = 'win' if response == correctResponse else 'loose'
        score += 1 if response == correctResponse else -1
        display(win, f'{correctResponse}_{feedback}', score)
        wait(1.)

        if response == side(preferred):
            learnedResponses += 1
        else:
            learnedResponses = 0

        if dataFile:
            dataFile.write(f'{subjectId},{trialCount},filler,{side(preferred)},{correctResponse},{response},{score}\n')

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
    repetitions = 1 if training else expConfig.getint('ExpTrialPerCondType', 1)
    condTypes = np.random.permutation(['normal', 'wink', 'blush', 'hint'] * repetitions)
    while np.any((condTypes[2:] == condTypes[1:-1]) & (condTypes[1:-1] == condTypes[:-2])):
        condTypes = np.random.permutation(condTypes)
    prefProb = expConfig.getfloat('PreferredProbability', 0.8)
    score = expConfig.getint('InitialScore', 100)

    for condType in condTypes:
        score = fillers(expConfig, subjectId, win, dataFile, et, preferred, score)

        trialCount = et.inc() if et else None
        display(win, 'warn')
        wait(2.)

        if condType == 'wink':
            preferred = 1 - preferred
        elif condType == 'blush':
            preferred = np.random.binomial(1, 0.5)

        if condType == 'hint':
            correctResponse = side(preferred)
            display(win, f'hint_{correctResponse}')
        else:
            correctResponse = side(preferred if np.random.binomial(1, prefProb) else 1 - preferred)
            display(win, condType)
        wait(4.)

        display(win, 'select', score)
        response = waitForKey(['left', 'right'])
        feedback = 'win' if response == correctResponse else 'loose'		
        score += 1 if response == correctResponse else -1
        display(win, f'{correctResponse}_{feedback}', score)
        wait(1.)

        if dataFile:
            dataFile.write(f'{subjectId},{trialCount},{condType},{side(preferred)},{correctResponse},{response},{score}\n')
    
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
