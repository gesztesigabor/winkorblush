
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import os
import pandas as pd
import scipy.stats as stats
import seaborn
from split_file import checkedMerge


seaborn.set(style='ticks')

data_dir = 'data'
output_dir = 'output'

condTypes = ['normal', 'wink', 'hint', 'blush']
condColors = {'normal': 'orange', 'wink': 'red', 'hint': 'cyan', 'blush': 'blue'}


checkedMerge(os.path.join(data_dir, 'samples.feather'))

debriefing = pd.read_feather(os.path.join(data_dir, 'debriefing.feather'))
behavior = pd.read_feather(os.path.join(data_dir, 'behavior.feather'))
samples = pd.read_feather(os.path.join(data_dir, 'samples.feather'))
blinks = pd.read_feather(os.path.join(data_dir, 'blinks.feather'))
