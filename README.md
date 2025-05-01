# Wink or blush?

This repository contains programs and data related to the paper _'Wink or blush? Pupil-linked phasic arousal signals
both change and uncertainty during assessment of changing environmental regularities'_

## Experimental scripts

PsychoPy experimental scripts are located in the _experiment_ directory.

Most parameters of the experiments can be set in _config.ini_.
The probabilistic reversal learning task is implemented in _wink.py_ and the visual control task is implemented in
_visual_control.py_.

For each execution of the experiment a _subject-XXX.csv_ file is created by the experimental program and an IDF file
is saved by the eye tracker machine. SMI utilities IDF Converter and IDF Event Detector must be used to export
pupil information to text and detect blinks. Mapped pupil diameter for both eyes and pupil confidence must be
included in the export.

## Preprocessing 

Raw data can be preprocessed with the python script located in the analysis directory.
__Data from the reported experiment is included in preprocessed form, so no need to preproces it.__

For preprocessing imput data from the probabilistic reversal learning task should be saved in directory
_analysis/rawdata/experiment_, while input data from the visual control task should be saved in directory
_analysis/rawdata/visual_. Input data must include _subject-XXX.csv_ files, exported pupil files and event
detection results keeping the original file names.

Preprocessing can be run by executing `python preprocess.py` from the _analysis_ directory. Preprocessed data
is saved in Apache Feather format to the _analysis/data_ folder (overwriting any previous data).
The data file _analysis/data/samples.feather_ is also split into pieces _analysis/data/samples.feather.XXX_ to
accomodate github file size limits. It is automatically merged by the analysis notebooks.

## Analysis

Analysis is done by the following Jupyter notebooks:

* _analysis/afternonpref.ipynb_ : In some cases the non-preferred side is selected in the last trial of the filler block. Test if it has significant effect
* _analysis/behavior.ipynb_ : Calculate behavioral task performance
* _analysis/blinkrate.ipynb_ : Test the effect of condition on blink rates during the cue presentation period
* _analysis/exclusions_report.ipynb_ : Calculate statistics of the excluded trials and interpolated data ratios
* _analysis/maximizers.ipynb_ : Test correlation of response strategy / median response time and change / uncertainty related pupil responses
* _analysis/meanresponses.ipynb_ : Analysis of the mean pupil responses, linear modeling
* _analysis/pointwise.ipynb_ : Time-course analysis of the effects of change and uncertainty on pupil-linked arousal
* _analysis/saccaderate.ipynb_ : Experimental analysis of the (micro)saccade rates in different conditions (requires raw eye tracker data)
* _analysis/wn_behavior.ipynb_ : Calculate behavioral task performance the control experiment (see supplement)
* _analysis/wn_exclusions_report.ipynb_ : Calculate statistics of the excluded trials and interpolated data ratios in the control experiment (see supplement)
* _analysis/wn_meanresponses.ipynb_ : Analysis of the mean pupil responses in the control experiment (see supplement)
* _analysis/wn_pointwise.ipynb_ : Time-course analysis of the effects of change on pupil-linked arousal in the control experiment (see supplement)

To re-run notebooks preprocessed data must be located in directory _analysis/data_.
