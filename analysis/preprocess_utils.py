
import numpy as np
import pandas as pd
import re
from scipy.signal import savgol_filter
import warnings


def loadbehavior(file_name):
    out = pd.read_csv(file_name, comment='#', dtype={'used':bool})
    out.condType = out.condType.apply(lambda v: v.replace("'", '').replace(' ', '_'))
    condNum = []
    fillerTrialNum = []
    fillerDifference = []
    fillerLearned = []
    lastCondNums = {}
    lastFillerTrialNum = 0
    lastFillerDifference = 0
    lastFillerLearned = 0
    for idx, row in out.iterrows():
        lastCondNums[row.condType] = lastCondNums.get(row.condType, 0) + 1
        condNum.append(lastCondNums[row.condType])
        if row.condType == 'filler':
            lastFillerTrialNum += 1
            lastFillerDifference += 1 if row.direction == row.preferred else -1
            lastFillerLearned = lastFillerLearned + 1 if row.response == row.preferred else 0
        else:
            lastFillerTrialNum = 0
            lastFillerDifference = 0
            lastFillerLearned = 0
        fillerTrialNum.append(lastFillerTrialNum)
        fillerDifference.append(lastFillerDifference)
        fillerLearned.append(lastFillerLearned)
    out['condNum'] = condNum
    out['fillerTrialNum'] = fillerTrialNum
    out['fillerDifference'] = fillerDifference
    out['fillerLearned'] = fillerLearned
    return out


def loadsamples(file_name, behavior=None):
    out = pd.read_csv(file_name, sep='\t', comment='#', usecols=['Time','Type','Trial','L Mapped Diameter [mm]','R Mapped Diameter [mm]','Pupil Confidence'])
    assert out[out.Type == 'MSG'].Trial.tolist() == list(range(2, out.Trial.max() + 1)), 'Missing trial messages!'
    out = out[out.Type == 'SMP']
    correction = trialcorrection(file_name)
    if correction != 0:
        warnings.warn('Trial number correction (%d) for file %s!' %(correction, file_name))
        out['Trial'] = out.Trial - correction
    if behavior is not None:
        out = out[out.Trial.between(behavior.trialCount.min(), behavior.trialCount.max())]
    else:
        out = out[out.Trial > 0]
    out['Pupil'] = (out['R Mapped Diameter [mm]'] + out['L Mapped Diameter [mm]']) / 2.0
    out.loc[~(out['Pupil Confidence'] == 1), 'Pupil'] = np.nan
    out['Time'] = pd.to_datetime(out.Time, unit='us')
    out = out[['Time', 'Trial', 'Pupil']]
    return out


def trialcorrection(file_name):
    pattern = re.compile('[^\t]+\tMSG\t([^\t]+)\t# Message:(.*)\n?')
    correction = 0
    with open(file_name) as f:
        for line in f:
            match = pattern.fullmatch(line)
            if match:
                difference = int(match.group(1)) - int(match.group(2)) - correction
                if difference != 0:
                    assert difference > 0
                    assert correction == 0
                    correction = difference
    return correction


def loadevents(file_name):
    out = pd.read_csv(file_name, skiprows=list(range(15))+list(range(16,20)), sep='\t', usecols=['Event Type','Start','End'], index_col=False)
    out = out[out['Event Type'].isin(['Blink L', 'Blink R'])]
    out['Start'] = pd.to_datetime(out.Start.astype(np.int64), unit='us')
    out['End'] = pd.to_datetime(out.End.astype(np.int64), unit='us')
    return mergeintervals(out[['Start', 'End']])


def mergeintervals(intervals):
    out = []
    first = True
    for idx, row in intervals.sort_values('Start').iterrows():
        start, end = row.Start, row.End
        assert end >= start, 'Interval start is greater than end!'
        if first:
            current_start, current_end = start, end
            first = False
        if start > current_end:
            out.append((current_start, current_end))
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
    out.append((current_start, current_end))
    return pd.DataFrame(out, columns=['Start', 'End'])


def extendartifacts(artifacts, samples, half_window, change_threshold):
    out = []
    changes = samples[samples.Pupil.diff().abs() > change_threshold].Time
    for idx, row in artifacts.iterrows():
        start, end = row.Start, row.End
        preceding_changes = changes[changes.between(start - half_window, start)]
        extended_start = start if preceding_changes.empty else preceding_changes.min()
        following_changes = changes[changes.between(end, end + half_window)]
        extended_end = end if following_changes.empty else following_changes.max()
        out.append((extended_start, extended_end))
    return mergeintervals(pd.DataFrame(out, columns=['Start', 'End']))


def deleteartifacts(artifacts, samples):
    out = samples.copy()
    for idx, row in artifacts.iterrows():
        out.loc[out.Time.between(row.Start, row.End), 'Pupil'] = np.nan
    return out


def detectoutliers(samples, z_treshold, half_window):
    stats = samples[['Trial', 'Pupil']].groupby('Trial').agg(['mean', 'std'])
    stats.columns = stats.columns.get_level_values(1)
    merged = samples.merge(stats, left_on='Trial', right_index=True)
    assert len(merged) == len(samples), 'Merged and samples size does not match!'
    outlier_times = merged[(merged['Pupil'] - merged['mean']).abs() > merged['std'] * z_treshold].Time
    outliers = pd.DataFrame()
    outliers['Start'] = outlier_times - half_window
    outliers['End'] = outlier_times + half_window
    return mergeintervals(outliers)


def interpolatesamples(samples, resample_rule, savgol_window, savgol_order):
    resampled = samples.resample(rule=resample_rule, on='Time')
    out = pd.DataFrame()
    for field in ['Trial']:
        out[field] = resampled[field].first().interpolate('zero').astype(int)
    out['Pupil'] = resampled.Pupil.mean()
    out['interpolated'] = out.Pupil.isnull()
    out['Pupil'] = savgol_filter(out.Pupil.interpolate('linear', limit_direction='both'), savgol_window, savgol_order, mode='mirror')
    assert out[out.Pupil.isnull()].empty, 'Null interpolated pupil value!'
    out = out.reset_index()
    return out
