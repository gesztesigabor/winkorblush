
import pandas as pd


def exclusion(behavior, samples, threshold=0.25, minCount=4, excludedSubjects=None):
    excluded = behavior.condType == 'filler'

    if excludedSubjects is not None:
        excluded |= behavior.subjectId.isin(excludedSubjects)

    iRates = samples.groupby(['subjectId', 'session', 'Trial']).interpolated.mean()
    excluded |= behavior.merge(iRates, left_on=['subjectId', 'session', 'trialCount'], right_index=True).interpolated >= threshold

    excluded |= ~(behavior.session.str.endswith('visual')) & ((behavior.fillerDifference.shift() < 4) | (behavior.fillerLearned.shift() < 3))

    countKey = ['subjectId', 'session', 'condType']
    counts = pd.DataFrame()
    counts['total'] = behavior[~(behavior.condType == 'filler')].groupby(countKey).trialCount.count()
    counts['excluded'] = behavior[~(behavior.condType == 'filler') & excluded].groupby(countKey).trialCount.count()
    counts['remaining'] = counts.total - counts.excluded.fillna(0).astype(int)
    counts = counts.reset_index()
    minRemaining = counts.groupby(['subjectId', 'session']).remaining.min()
    excluded |= behavior.merge(minRemaining, left_on=['subjectId', 'session'], right_index=True).remaining < minCount

    return excluded
