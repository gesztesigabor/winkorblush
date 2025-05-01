
from load_data import *
from mne.stats import permutation_cluster_1samp_test

print(f'(Re)loading {__name__}')


def compareWithinSubject(
    s, condType1, condType2,
    testType='t', sigLevel=0.05, showAllClusters=False,
    minOffset='-0.5s', maxOffset='5s', filterOffset=True,
    title=None, ax=None, condColors=condColors):

    if filterOffset:
        minOffset = max(pd.to_timedelta(minOffset), s.groupby(['subjectId', 'session', 'trialCount']).offsetFromStim.min().max())
        maxOffset = min(pd.to_timedelta(maxOffset), s.groupby(['subjectId', 'session', 'trialCount']).offsetFromStim.max().min())
        s = s[s.offsetFromStim.between(minOffset, maxOffset)]
    
    if ax is None:
        ax = plt.figure(figsize=(6, 5), dpi=100).subplots()
    if title:
        ax.set_title(title)
        print(f'********** {title} **********')
    ax.set_xlabel('Time relative to cue onset [sec]')
    ax.set_ylabel('Pupil size change [mm]')
    ax.spines.right.set_visible(False)
    ax.spines.top.set_visible(False)

    xValues = s.groupby('offsetFromStim').first().index.to_series() / pd.to_timedelta('1s')
    sg = s.groupby(['condType', 'offsetFromStim', 'subjectId']).Pupil.mean()
    for condType in (condType1, condType2):
        aggVals = sg.loc[condType].groupby('offsetFromStim').agg(['mean', 'sem'])
        color = condColors[condType]
        ax.plot(xValues, aggVals['mean'], color=color, label=condType)
        ax.fill_between(xValues, aggVals['mean'] - aggVals['sem'], aggVals['mean'] + aggVals['sem'], alpha=0.2, linewidth=0, color=color)

    ax.axvline(0., ls=':', color='grey')
    xFeedback = 4.
    if xValues.iloc[-1] > xFeedback:
        ax.axvline(xFeedback, ls=':', color='grey')

    c1 = sg.loc[condType1].unstack('offsetFromStim').to_numpy()
    c2 = sg.loc[condType2].unstack('offsetFromStim').to_numpy()
    if c1.shape[0] > 1:
        if testType == 't':
            _, clusters, cluster_p_values, _ = permutation_cluster_1samp_test(
                c1 - c2,
                seed=42,
                n_permutations=1000,
                threshold=stats.distributions.t.ppf(1 - sigLevel / 2, df=c1.shape[0] - 1),
                tail=0,
                n_jobs=None,
                out_type='mask')
        else:
            wilcox = lambda x: stats.wilcoxon(x, method='approx').zstatistic
            _, clusters, cluster_p_values, _ = permutation_cluster_1samp_test(
                c1 - c2,
                seed=42,
                n_permutations=1000,
                stat_fun=wilcox,
                threshold=stats.distributions.norm.ppf(1 - sigLevel / 2),
                tail=0,
                n_jobs=None,
                out_type='mask')
        #print(clusters, cluster_p_values)

        yPos = ax.get_ylim()[0]
        for c, p in zip(clusters, cluster_p_values):
            c = c[0]
            xMin, xMax = xValues.iloc[c.start], xValues.iloc[c.stop - 1]
            if p < sigLevel:
                ax.hlines(yPos, xMin, xMax, color='black', linewidth=4)
                print(f'Significant cluster from {xMin} to {xMax} seconds (p={p}).')
            else:
                if showAllClusters:
                    ax.hlines(yPos, xMin, xMax, color='black', linewidth=4, alpha=0.2)
                print(f'Non-significant cluster from {xMin} to {xMax} seconds (p={p}).')
            
    ax.legend(frameon=True, loc='upper left')


def compareAndPlot(df, condType1, condType2, testType='t', showAllClusters=False, saveAs=None, outputDir=output_dir):
    fig = plt.figure(figsize=(12, 5), dpi=300)
    ax1, ax2 = fig.subplots(nrows=1, ncols=2)
    compareWithinSubject(
        df[df.session.str.endswith('experiment')], condType1, condType2, testType=testType, showAllClusters=showAllClusters,
        title='A) Experimental session', ax=ax1)
    compareWithinSubject(
        df[df.session.str.endswith('visual')], condType1, condType2, testType=testType, showAllClusters=showAllClusters,
        title='B) Visual control session', ax=ax2)

    yLim = min(ax1.get_ylim()[0], ax2.get_ylim()[0]), max(ax1.get_ylim()[1], ax2.get_ylim()[1])
    ax1.set_ylim(yLim)
    ax2.set_ylim(yLim)
    
    plt.tight_layout()
    plt.rcParams['pdf.fonttype'] = 42
    if saveAs is not None:
        fig.savefig(os.path.join(outputDir, f'{saveAs}.png'))
        fig.savefig(os.path.join(outputDir, f'{saveAs}.pdf'))
    plt.show()
