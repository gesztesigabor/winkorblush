
from load_data import *
from dataclasses import dataclass
import pingouin as pg
import statsmodels.formula.api as smf
from statsmodels.tools.sm_exceptions import ConvergenceWarning
import warnings

print(f'(Re)loading {__name__}')


def checkNormal(data):
    if len(data) <= 200:
        print(stats.shapiro(data))
    fig = plt.figure(figsize=(12, 5), dpi=300)
    ax1, ax2 = fig.subplots(nrows=1, ncols=2)
    ax1.hist(data, bins='auto')
    pg.qqplot(data, dist='norm', ax=ax2)


def checkResiduals(model):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', ConvergenceWarning)
        fit = model.fit(method='cg', reml=False)
    if hasattr(fit, 'converged'):
        assert fit.converged
    checkNormal(fit.resid)


def condTypeBarChart(data, dv, ax=None, faceAlpha=0.2, condTypes=condTypes, condColors=condColors, gap=0.6):
    if ax is None:
        ax = plt.figure(figsize=(6, 5), dpi=100).subplots()
    ax.set_xlabel('Condition')
    ax.spines.right.set_visible(False)
    ax.spines.top.set_visible(False)

    y = [data.query('condType==@c')[dv].mean() for c in condTypes]
    yerr = [data.query('condType==@c')[dv].sem() for c in condTypes]
    edgeColor = [(condColors[c], 1.) for c in condTypes]
    faceColor = [(condColors[c], faceAlpha) for c in condTypes]
    xticks = np.arange(len(condTypes), dtype=type(gap))
    xticks[2:] += gap
    ax.bar(xticks, y, yerr=yerr, width=1, capsize=5, edgecolor=edgeColor, fc=faceColor)
    ax.set_xticks(xticks, condTypes)
    return ax


def sigLabel(ax, condType1, condType2, s, ylim=None, condTypes=condTypes, gap=0.6):
    ymin, ymax = ax.get_ylim() if ylim is None else ylim
    dy = (ymax - ymin) / 100.
    xticks = np.arange(len(condTypes), dtype=type(gap))
    xticks[2:] += gap
    x1, x2 = xticks[condTypes.index(condType1)], xticks[condTypes.index(condType2)]
    ax.plot([x1, x1, x2, x2], [ymax, ymax+3*dy, ymax+3*dy, ymax], color='black')
    ax.text(x=(x1+x2)/2., y=ymax+5*dy, s=s, ha='center')
    ax.set_ylim(ymax=ax.get_ylim()[1]+2*dy)


def formatPval(pval):
    assert 0. < pval < 1.
    if pval < 0.001:
        return 'p < .001'
    formatted = f'{np.round(pval, 3):.03f}' if pval < 0.1 else f'{pval:.2f}'
    return f'p = {formatted[1:]}'


def sigLabels(ax, data, dv, condTypes=condTypes, sigLevel=0.05):
    ylim = ax.get_ylim()
    for condType1, condType2 in [condTypes[:2], condTypes[2:]]:
        pval = stats.ttest_rel(data.query('condType==@condType1')[dv], data.query('condType==@condType2')[dv]).pvalue
        if sigLevel is None or pval < sigLevel:
            sigLabel(ax, condType1, condType2, formatPval(pval), ylim=ylim)


def createModel(formula, data, mixed=True):
    if mixed:
        return smf.mixedlm(formula, data, groups='subjectId')
    else:
        return smf.ols(formula, data)


def createModels(dependent, data, mixed=True):
    models = {}
    models['null'] = createModel(f'{dependent} ~ 1', data)
    models['kld'] = createModel(f'{dependent} ~ kld', data)
    models['entropy'] = createModel(f'{dependent} ~ entropy', data)
    models['kldEntropy'] = createModel(f'{dependent} ~ kld + entropy', data)
    models['condType'] = createModel(f'{dependent} ~ C(condType)', data)
    return models


def fitModel(model):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', ConvergenceWarning)
        fit = model.fit(reml=False)
        if hasattr(fit, 'converged'):
            assert fit.converged
    return fit


@dataclass
class Chi2Result:
    df: int
    statistic: float
    pvalue: float


def likelihoodRatio(specific, general):
    specificFit = fitModel(specific)
    generalFit = fitModel(general)
    df = (len(generalFit.params) + general.k_constant) - (len(specificFit.params) + specific.k_constant)
    assert df > 0
    statistic = 2. * (generalFit.llf - specificFit.llf)
    assert statistic > 0.
    pvalue = stats.chi2.sf(statistic, df)
    return Chi2Result(df=df, statistic=statistic, pvalue=pvalue)


def bayesFactor(model, ref):
    modelFit = fitModel(model)
    refFit = fitModel(ref)
    return np.exp(-0.5 * (modelFit.bic - refFit.bic))


def relativeBICs(modelList):
    bics = np.array([fitModel(model).bic for model in modelList])
    return bics - bics.min()


def bayesWeights(modelList):
    weights = np.exp(-0.5 * relativeBICs(modelList))
    return weights / weights.sum()
    #ref = modelList[-1]
    #bfs = np.array([bayesFactor(model, ref) for model in modelList])
    #return bfs / bfs.sum()


def compareModelPairs(models, specificName, generalName, sigValue=0.05):
    specific, general = models[specificName], models[generalName]
    res = likelihoodRatio(specific, general)
    sig = res.pvalue < sigValue
    out = res if sig else f'{res}, B={bayesFactor(specific, general)}'
    print(f'{specificName}->{generalName}: {out}')
    return sig


def compareModels(models, sigValue=0.05, ax=None):
    sigKld = compareModelPairs(models, 'null', 'kld')
    sigEntropy = compareModelPairs(models, 'null', 'entropy')
    sigKldEntropy = sigKld and compareModelPairs(models, 'kld', 'kldEntropy')
    sigEntropyKld = sigEntropy and compareModelPairs(models, 'entropy', 'kldEntropy')
    if sigKldEntropy or sigEntropyKld:
        compareModelPairs(models, 'kldEntropy', 'condType')
    else:
        if sigKld:
            compareModelPairs(models, 'kld', 'condType')
        if sigEntropy:
            compareModelPairs(models, 'entropy', 'condType')

    names = ['null', 'kld', 'entropy', 'kldEntropy', 'condType']
    legend = ['intercept\nonly', 'KLD', 'entropy', 'KLD +\nentropy', 'condition']
    weights = bayesWeights([models[name] for name in names])
    if ax is None:
        ax = plt.figure(figsize=(6, 5), dpi=100).subplots()
    ax.bar(legend, weights, edgecolor='black', fc=('black', 0.2))
    ax.set_xlabel('Model')
    ax.set_ylabel('Bayesian model weight')
    ax.set_ylim(ymin=0., ymax=1.)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.))
    ax.spines.right.set_visible(False)
    ax.spines.top.set_visible(False)

    res = pd.DataFrame()
    res['model'] = names
    res['relativeBIC'] = relativeBICs([models[name] for name in names])
    res['bayesWeight'] = weights
    return res
