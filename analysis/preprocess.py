
from collections import defaultdict
from exclusion import exclusion
import os
import pandas as pd
from preprocess_utils import *
import re
from split_file import splitFile
import sys


rawdata_dir = 'rawdata'
data_dir = 'data'


def processsubject(subject, session):
    print('Subject: ', subject)
    print('Session: ', session)
    session_dir = os.path.join(rawdata_dir, session)
    metadata = {}

    behavior_files = [f for f in os.listdir(session_dir) if re.match('subject_%d_\\d+.csv' %subject, f)]
    assert len(behavior_files) == 1, 'Ambigous or nonexistent behavior file!'
    behavior = loadbehavior(os.path.join(session_dir, behavior_files[0]))
    assert (behavior.subjectId == subject).all(), 'Behavior file contains records of a different subject!'
    print('Behavior records: ', len(behavior))

    samples_files = [f for f in os.listdir(session_dir) if re.match('subject_%d_\\d+ Samples.txt' %subject, f)]
    assert len(samples_files) == 1, 'Ambigous or nonexistent samples file!'
    samples = loadsamples(os.path.join(session_dir, samples_files[0]), behavior)
    print('Samples: ', len(samples))
    print('Trials: ', len(samples.Trial.unique()))

    blinks = loadevents(os.path.join(session_dir, samples_files[0].replace('Samples', 'Events')))
    metadata['blink_num'] = blink_num = len(blinks)
    print('Blinks: ', blink_num)

    samples = deleteartifacts(blinks, samples)
    outliers = detectoutliers(samples, 3.0, pd.to_timedelta('40ms'))
    metadata['outlier_num'] = outlier_num = len(outliers)
    print('Outliers: ', outlier_num)

    interpolated_intervals = mergeintervals(pd.concat([blinks, outliers], ignore_index=True))
    metadata['total_num'] = total_num = len(interpolated_intervals)
    print('Total interpolated intervals: ', total_num)

    samples = interpolatesamples(deleteartifacts(outliers, samples), '20ms', 9, 4)
    metadata['total_dr'] = total_dr = len(samples[samples.interpolated]) * 1. / len(samples)
    print('Total interpolated data ratio: ', total_dr)

    stimulus_offset = pd.to_timedelta('2s')
    trial_starts = samples.groupby('Trial', as_index=False).Time.min()
    samples['offsetFromStim'] = samples.Time - samples[['Trial']].merge(trial_starts, on='Trial').Time - stimulus_offset
    assert samples.offsetFromStim.notnull().all()

    samples.insert(0, 'subjectId', subject)
    blinks.insert(0, 'subjectId', subject)
    behavior.insert(1, 'session', session)
    samples.insert(1, 'session', session)
    blinks.insert(1, 'session', session)

    sys.stdout.flush()
    return (metadata, behavior, samples, blinks)


def preprocess():
    subjects = []
    sessions = []
    for session in os.listdir(rawdata_dir):
        session_dir = os.path.join(rawdata_dir, session)
        session_subjects = [int(re.search('(?<=subject_)\\d+(?=_)', f).group(0)) for f in os.listdir(session_dir) if re.match('.+\\.csv$', f)]
        subjects.extend(session_subjects)
        sessions.extend([session] * len(session_subjects))

    debriefing = pd.DataFrame()
    debriefing['subjectId'] = subjects
    debriefing['session'] = sessions
    assert set(debriefing[debriefing.session=='experiment'].subjectId) == set(debriefing[debriefing.session=='visual'].subjectId), 'Each experimental subject must have a visual session (and noone else)!'

    behavior, samples, blinks = (pd.DataFrame() for i in range(3))
    metadata = defaultdict(list)
    for _, row in debriefing.iterrows():
        subj_metadata, subj_behavior, subj_samples, subj_blinks = processsubject(row.subjectId, row.session)

        for key, value in subj_metadata.items():
            metadata[key].append(value)

        behavior = pd.concat([behavior, subj_behavior], ignore_index=True)
        samples = pd.concat([samples, subj_samples], ignore_index=True)
        blinks = pd.concat([blinks, subj_blinks], ignore_index=True)

    for key, value in metadata.items():
        debriefing[key] = value

    behavior['excluded'] = exclusion(behavior, samples)

    for var in ['debriefing', 'behavior', 'samples', 'blinks']:
        eval(var).to_feather(os.path.join(data_dir, f'{var}.feather'), compression='zstd')

    splitFile(os.path.join(data_dir, 'samples.feather'), 20 * 1024 ** 2)


if __name__ == '__main__':
    preprocess()

