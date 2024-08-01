# Wink or blush?

This package contains programs related to the paper _'Wink or blush? Pupil-linked brain arousal signals
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
__Data from the reported experiment is published in preprocessed form, so no need to preproces it.__

For preprocessing imput data from the probabilistic reversal learning task should be saved in directory
_analysis/rawdata/experiment_, while input data from the visual control task should be saved in directory
_analysis/rawdata/visual_. Input data must include _subject-XXX.csv_ files, exported pupil files and event
detection results keeping the original file names.

Preprocessing can be run by executing `python preprocess.py` from the _analysis_ directory. Preprocessed data
is saved in Apache Feather format to the _analysis/data_ folder (overwriting any previous data).

## Analysis

Analysis is done by the following Jupyter notebooks:

* _analysis/exclusions.ipynb_ : Calculate statistics for excluded trials and interpolated data ratios
* _analysis/behavior.ipynb_ : Calculate behavioral task performance results
* _analysis/pointwise.ipynb_ : calculate the effects of change and uncertainty on pupil-linked brain arousal

To re-run notebooks preprocessed data must be located in directory _analysis/data_.
