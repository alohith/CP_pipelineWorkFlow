#!/usr/bin/env python3.7
########################################################################
# File:histdiff.py
#  executable: histdiff.py commandGroup commandArgs
# Purpose:
#
# Author:       Akshar Lohith
# History:      AL 01/15/2022 Created
#               AL 01/17/2022  Cleaned interactive session
#               AL 01/21/2022 formalized functions and incorporated TB edits
#               AL 01/27/2022 CommandLine module
#
########################################################################

# coding: utf-8
import pandas as pd
import numpy as np
import scipy as sp
import os
# import csv
import sys
import glob
import csv
import subprocess
import time
import resource
# import numba
# import modin.pandas as pd #will use this in proper deployment perhaps in conjuction with numba

# @numba.jit()
def featureMinMaxBuffered (minMaxDict:dict):
    ''' edit feature Ranges dictionary by buffering len=0 ranges '''
    minMaxDict_buffered = dict()
    for col in minMaxDict:
        if col is not 'WellName':
            fmin, fmax = minMaxDict[col].values()
            if fmin == fmax:
                fmax = fmin +.5*fmin
            if fmin == fmax:
                fmax = fmin + 1.
            minMaxDict_buffered[col] = {'min': fmin, 'max': fmin}


    return minMaxDict_buffered

# @numba.jit(nopython=True)
def npHistonDFwargs(data, rangeDict:dict, bins=20):
    ''' wrap the numpy.histogram arguments for a convenient DF.apply.
        passing-through of mulitiple arguments directly in apply is more tricky
        than worth the effort
    '''
    histRange = (rangeDict[data.name]['min'], rangeDict[data.name]['max'])
    return np.histogram(data, bins=bins, range=histRange)[0]

# @numba.jit(nopython=True)
def exponentialSmoothingonDF(DF_original, alpha=0.25):
    n = DF_original.shape[0]
    columns = DF_original.columns
    index = DF_original.index
    DF = DF_original.to_numpy('longdouble')
    smoothedDF = np.empty_like(DF)
    smoothedDF[0] = DF[0] + alpha * (DF[1] - DF[0])
    for i in range(1, n - 1):
        smoothedDF[i] = alpha * (DF[i - 1]-DF[i]) + DF[i] + alpha * (DF[i + 1] - DF[i])
    smoothedDF[n - 1] = alpha * (DF[n - 2] - DF[n - 1]) + DF[n - 1]
    return pd.DataFrame(smoothedDF, columns=columns, index=index)

# @numba.jit(nopython=True)
def normalize(x):
    '''  generic normalize historgram by sum of all bins function '''
    return np.divide(x, x.sum(), out=np.zeros_like(x, dtype='longdouble'), where=x.sum() != 0)

# @numba.jit(vectorize=True, nopython=True)
def HistSquareDiff(exp:np.ndarray ,ctrl:np.ndarray,factor=1):
    ''' The actual workhorse HistDiff scoring function '''
    #we transpose twice to ensure the final result is a 1 x m feature score vector
    ctrl_meanProxy = ((np.arange(0,ctrl.shape[0]) * ctrl.T).T).sum(axis=0)
    exp_meanProxy = ((np.arange(0,exp.shape[0]) * exp.T).T).sum(axis=0)
    #evaluate where and when to adjust the score to be negative
    negScore = np.where(ctrl_meanProxy > exp_meanProxy,-1,1)
    diff = ctrl - (exp * factor)
    diff **= 2
    return diff.sum(axis=0) * negScore

# @numba.jit()
def applyHistSquareDiffonDF (exp_wellGroup_original, ctrl_Hist_smNorm, feature_ranges, factor=1, bins=20):
    ''' wrapper to apply all the HistSquareDiff function across all wells '''
    wellName = exp_wellGroup_original['WellName'].unique()[0]
    exp_wellGroup = exp_wellGroup_original.drop(columns='WellName')
    # print(f'successfully removed wellAnnotation {not ("WellName" in exp_wellGroup.columns)}')
    # exp_wellGroup_ranges = featureMinMaxBuffered(exp_wellGroup.describe().\
    #     loc[['min','max']].to_dict())
    exp_wellGroup = exp_wellGroup.apply(lambda col: npHistonDFwargs(col,\
        feature_ranges,bins=bins),axis=0)
    exp_wellGroup = exponentialSmoothingonDF(exp_wellGroup,.25).apply(normalize,axis=0)
    scoreOut = HistSquareDiff(exp_wellGroup, ctrl_Hist_smNorm, factor=factor)#,\
        # columns=exp_wellGroup.columns,index=[wellName])
    scoreOut.name = wellName
    # print(scoreOut.to_frame().T,type(scoreOut.to_frame().T))
    return scoreOut

# @numba.jit()
def computeCtrlHist_smNorm (ctrlWellIDs, MX_data, MX_feature_ranges, bins=20):
    MX_ctrlWells = MX_data.loc[MX_data['WellName'].isin(ctrlWellIDs)].\
        drop(columns='WellName')
    # MX_feature_ranges = featureMinMaxBuffered(MX_data.describe().\
    #     loc[['min','max']].to_dict())
    MX_ctrlWells = MX_ctrlWells.apply(lambda col: npHistonDFwargs(col,\
        MX_feature_ranges,bins=bins),axis=0)
    return exponentialSmoothingonDF(MX_ctrlWells,.25).apply(normalize,axis=0)#, MX_feature_ranges

class CommandLine(object) :
    '''
    Handle the command line, usage and help requests.

    CommandLine uses argparse, now standard in 2.7 and beyond.
    it implements a standard command line argument parser with various argument options,
    a standard usage and help, and an error termination mechanism do-usage_and_die.

    attributes:
    myCommandLine.args is a dictionary which includes each of the available command line arguments as
    myCommandLine.args['option']

    methods:
    do_usage_and_die()
    prints usage and help and terminates with an error.
    '''

    def __init__(self, inOpts=None) :
        '''
        CommandLine constructor.
        Implements a parser to interpret the command line argv string using argparse.
        '''
        import argparse
        self.parser = argparse.ArgumentParser(\
            description = 'This program will create HistDiff signatures for '+\
            'compounds in a screening experiement.',\
            add_help = True, #default is True
            prefix_chars = '-', usage = '%(prog)s')

        self.parser.add_argument("pathWriteData", action = 'store',\
                    type=os.path.abspath, default = ".",\
                    help='Path to dir to write Data.')
        # self.parser.add_argument("--CSCplateMapCSV", action = 'store',required=False\
        #             type=pd.read_csv,default=None,\
        #             help='Comma-deliminated input plateMap file.')
        self.parser.add_argument("measFile", action = 'store',\
                    type=argparse.FileType('r', encoding='unicode_escape'),\
                    help='compressed Tab-deliminated input Data file.')
        self.parser.add_argument('bins',action='store',\
                    default = 20, type = int,\
                    help='number of bins to map to.')
        self.parser.add_argument("-o","--OutFilename", action='store',\
                    default = "ActivityScore_ElbowPlot",\
                    help = 'Output File name stem.')
        # self.parser.add_argument('--ctrlWells',action='store',\
        #             typ, default=None,\
        #         help='Activity score threshold below which to output inactive wells'+\
        #         '. Required if not using plot option.')

        if inOpts is None:
            self.args = vars(self.parser.parse_args()) # parse the CommandLine options
        else :
            self.args = vars(self.parser.parse_args(inOpts)) # parse the input options

    def processPlateMap(self,plateMapCSV):
        '''digest platemap into renameDict, also determine the ctrl wells of the exp'''
        wellIDs_384 = [('%s%02d' % (chr(r), c)) for r in range(65, 81) for c in range(1, 25)]
        if plateMapCSV is not None:
            platemap = pd.read_csv(plateMapCSV)
            platemap['saveName'] = platemap['MoleculeID'].\
                astype(str)+"_"+platemap['Concentration'].astype(str)
            renameDict = dict(platemap[['Well','saveName']].set_index('Well').to_records())
            ctrlWellids_true = [well for well in wellIDs_384 if well not in renameDict]
            self.CtrlWells = ctrlWellids_true
            self.renameDict

        else:
            # wellIDs_384
            ctrlWellids_64 = [x for x in wellIDs_384 if int(x[1:]) in [1, 2, 23, 24]]
            self.CtrlWells = ctrlWellids_64

    def __del__ (self) :
        '''
        CommandLine destructor.
        '''
        # do something if needed to clean up before leaving
        pass

    def do_usage_and_die (self, str) :
        '''
        If a critical error is encountered, where it is suspected that the program is not being called with consistent parameters or data, this
        method will write out an error string (str), then terminate execution of the program.
        '''
        import sys
        print(str, file=sys.stderr)
        self.parser.print_usage()
        return 2

def main():
    tic_prog = time.perf_counter()
    platemap = pd.read_csv('SP90105.csv')
    platemap['saveName'] = platemap['MoleculeID'].astype(str)+"_"+platemap['Concentration'].astype(str)
    renameDict = dict(platemap[['Well','saveName']].set_index('Well').to_records())
    # platemap
    # wellIDs_384 = [print('%s%02d' % (chr(r), c)) for r in range(65, 81) for c in range(1, 25)]
    wellIDs_384 = [('%s%02d' % (chr(r), c)) for r in range(65, 81) for c in range(1, 25)]
    # wellIDs_384
    ctrlWellids_64 = [x for x in wellIDs_384 if int(x[1:]) in [1, 2, 23, 24]]

    ctrlWellids_true = [well for well in wellIDs_384 if well not in renameDict]
    tic_read = time.perf_counter()
    # headers = subprocess.run('gunzip -c MX4850.merged.csv.gz | head -n 1', shell=True, capture_output=True).stdout.decode().strip().split(',')

    # Alternative to read column headers
    headers = pd.read_csv('MX4850.merged.csv.gz', nrows=0, compression='gzip').columns.tolist()

    skipColumns = [
     'Orientation_IMA_Summary', 'Cell_ID', 'Instance', 'Plate_ID',
     'Run_Settings_ID', 'Series_ID', 'Site_ID', 'Well_X', 'Well_Y',
     'Cell_Vesicle_Count_Transfluor', 'Cell_Vesicle_Average_Intensity_Transfluor',
     'Cell_Vesicle_Integrated_Intensity_Transfluor', 'Cell_Vesicle_Total_Area_Transfluor',
     'Cell_Scoring_Profile_MultiWaveScoring',
     'Laser_focus_score_MultiWaveScoring',
     'Laser_focus_score_Transfluor',
     'Laser_focus_score_Micronuclei',
     'Centroid_Y_IMA_Summary',
     'Centroid_X_IMA_Summary'
     ]

    MX_merged_filtered = pd.read_csv("MX4850.merged.csv.gz", compression='gzip',\
        usecols=[i for i in headers if i not in skipColumns])
    toc_read = time.perf_counter()
    print(f"time to read header and load cell-data: {toc_read - tic_read:0.4f}",\
        file=sys.stderr)

    tic_ctrls = time.perf_counter()
    featureRange = featureMinMaxBuffered(MX_data.describe().\
        loc[['min','max']].to_dict())
    ctrlWell_Hist_smNorm = computeCtrlHist_smNorm(ctrlWellids_true, MX_merged_filtered, featureRange, 20)
    print(ctrlWell_Hist_smNorm)
    toc_ctrls = time.perf_counter()
    print(f'time to compute ctrl Well histograms: {toc_ctrls - tic_ctrls:0.4f}',\
        file=sys.stderr)

    tic_scoring = time.perf_counter()

    ##welp, apply works but looks like casts same value to all groups
    #tried some other stuff, but going to see if just for loop over the groups gives
    #differing values for each group aka exp treatment so table the Groupby.apply for now
    # and just work with a for loop
    scoredDF = MX_merged_filtered.groupby('WellName').\
        apply(lambda well: applyHistSquareDiffonDF( #**kwargs = {'ctrl_Hist_smNorm':ctrlWell_Hist_smNorm, 'bins':20, 'factor':1})
            well,ctrl_Hist_smNorm=ctrlWell_Hist_smNorm,\
            feature_ranges = featureRange, bins=20, factor=1))
    # scoredDF = pd.DataFrame()
    # #pd.DataFrame(columns=[x for x in MX_merged_filtered.columns if x != 'WellName'])
    # for well, wellGrouped in MX_merged_filtered.groupby('WellName'):
    #     scoredDF = pd.concat([scoredDF,applyHistSquareDiffonDF(
    #         wellGrouped,ctrl_Hist_smNorm=ctrlWell_Hist_smNorm,\
    #         feature_ranges = featureRange, bins=20, factor=1).to_frame()],axis=1)

    toc_scoring = time.perf_counter()
    print(f'time to compute and return all well scores: {toc_scoring - tic_scoring:0.4f}',\
        file=sys.stderr)

    scoredDF=scoredDF.T
    scoredDF.rename(index=renameDict,\
        columns={ x:f"{str(x).replace('W1','DAPI').replace('W2','EdU').replace('W3','PH3')}_EdU" for x in scoredDF.columns},inplace=True)

    scoredDF.to_csv('MX4850.histdiffpy.csv')
    toc_prog = time.perf_counter()
    print(f'total processing time: {toc_prog - tic_prog:0.4f}',\
        file=sys.stderr)

if __name__ == "__main__":
    # if program is launched alone, this is true and is exececuted. if not, nothing is\
    # executedf rom this program and instead objects and variables are made available \
    # to the program that imports this.
    main();
    resources = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f'{resources}',file=sys.stderr)
    raise SystemExit
