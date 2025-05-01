
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import os
import pandas as pd
import scipy.stats as stats
import seaborn
from split_file import checkedMerge

print(f'(Re)loading {__name__}')


seaborn.set(style='ticks')

data_dir = 'data'
output_dir = 'output'

condTypes = ['normal', 'wink', 'hint', 'blush']
#condColors = {'normal': 'orange', 'wink': 'red', 'hint': 'cyan', 'blush': 'blue'}
condColors = {'normal': '#FFA500', 'wink': '#FF0000', 'hint': '#00FFFF', 'blush': '#0000FF'}


checkedMerge(os.path.join(data_dir, 'samples.feather'))

debriefing = pd.read_feather(os.path.join(data_dir, 'debriefing.feather'))
behavior = pd.read_feather(os.path.join(data_dir, 'behavior.feather'))
samples = pd.read_feather(os.path.join(data_dir, 'samples.feather'))
blinks = pd.read_feather(os.path.join(data_dir, 'blinks.feather'))


def getExcSubjects():
    print('Subjects not selecting the preferred option in more than half of both normal and wink trials:')
    checkedTrials = behavior[(behavior.session=='experiment') & behavior.condType.isin(['normal', 'wink'])].copy()
    checkedTrials['prefSel'] = (checkedTrials.response==checkedTrials.preferred)
    minProportions = checkedTrials.groupby(['subjectId', 'condType']).prefSel.mean().groupby('subjectId').min()
    excSubjects = minProportions[minProportions <= 0.5].index.tolist()
    print('\t', excSubjects)
    return excSubjects


def baselineCorrect(df, baselineStart='-0.5s', baselineEnd='0s'):
    trialKeyFields = ['subjectId', 'session', 'trialCount']
    baseData = df[df.offsetFromStim.between(pd.to_timedelta(baselineStart), pd.to_timedelta(baselineEnd))]
    baseline = baseData.groupby(trialKeyFields, as_index=False).Pupil.mean()
    corrected = df.merge(baseline.rename(columns={'Pupil': 'Baseline'}), on=trialKeyFields)
    corrected.Pupil = corrected.Pupil - corrected.Baseline
    return corrected.drop(columns='Baseline')
