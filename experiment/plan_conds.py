
import numpy as np


def planConds(expConfig, training=False):
    condTypes = expConfig.get('CondTypes', 'normal,wink,blush,hint')
    condTypes = [c.strip('\n\t ').lower() for c in condTypes.split(',')]
    numRepeat = expConfig.getint('TrainingTrialPerCondType', 1) if training else expConfig.getint('ExpTrialPerCondType', 1)
    maxSubsequent = expConfig.getint('MaxSubsequent', 2)
    if expConfig.get('PlanCondsMethod', 'rejection') == 'rejection':
        return planCondsRejection(condTypes, numRepeat, maxSubsequent)
    else:
        return planCondsInsert(condTypes, numRepeat, maxSubsequent)


def planCondsRejection(condTypes, numRepeat, maxSubsequent):
    assert maxSubsequent == 2, 'Rejection sampling is only implemented for MaxSubsequent=2!'
    assert len(condTypes) == 4 and numRepeat <= 40, 'Use rejection sampling only for 4 conditions and ExpTrialPerCondType<=40! Otherwise it may be extremely slow.'

    conds = np.random.permutation(list(condTypes) * numRepeat)
    while np.any((conds[2:]==conds[1:-1]) & (conds[1:-1]==conds[:-2])):
        conds = np.random.permutation(conds)
    return conds


def planCondsInsert(condTypes, numRepeat, maxSubsequent):
    conds = []
    for value in list(condTypes) * numRepeat:
        prevNums = countSubsequent(conds, value)
        nextNums = countSubsequent(conds, value, forward=False)
        i = np.random.choice((prevNums + nextNums < maxSubsequent).nonzero()[0])
        conds.insert(i, value)
    return conds


def countSubsequent(conds, value, forward=True):
    nums = np.zeros(len(conds) + 1, dtype=int)
    for i, v in enumerate(conds if forward else reversed(conds)):
        if v == value:
            nums[i + 1] = nums[i] + 1
    return nums if forward else np.flip(nums)

