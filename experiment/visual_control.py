
import configparser
import numpy as np
import time
from utils import *


def experiment(config, subjectId, win, et):
    dataFile = open(f'subject_{subjectId}_{int(time.time())}.csv', 'w')
    dataFile.write('subjectId,trialCount,condType\n')
    instruct(win, 'Nyomj le egy gombot, ha indulhat a kísérlet!')
    et.record()
    wait(.5)

    expConfig = config['experiment']
    seed = expConfig.getint('RandomSeed', None)
    if seed is not None:
        np.random.seed(seed)
    repetitions = expConfig.getint('ExpTrialPerCondType', 1)
    condTypes = np.random.permutation(['normal', 'wink', 'blush', 'hint'] * repetitions)
    while np.any((condTypes[2:]==condTypes[1:-1]) & (condTypes[1:-1]==condTypes[:-2])):
        condTypes = np.random.permutation(condTypes)

    for condType in condTypes:
        trialCount = et.inc()
        display(win, 'warn')
        wait(2.)

        if condType == 'hint':
            display(win, 'hint_right' if np.random.binomial(1, 0.5) else 'hint_left')
        else:
            display(win, condType)
        wait(4.)

        dataFile.write(f'{subjectId},{trialCount},{condType}\n')
        checkQuit()
    dataFile.close()


def main():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8-sig')

    subjectId = getSubjectId()

    win = initWindow(config)
    et = setupEyeTracker(config, subjectId, win)
    experiment(config, subjectId, win, et)
    teardown(win, et)


if __name__ == '__main__':
	main()
