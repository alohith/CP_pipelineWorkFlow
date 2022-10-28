#!/usr/bin/env python3.7
import os, sys, csv, resource, time, shelve, numba
import numpy as np, pandas as pd

class Hist1D(object): #(object)
    ''' taken from https://stackoverflow.com/a/45092548'''
    def __init__(self, nbins, xlow, xhigh):
        self.nbins = nbins
        self.xlow  = xlow
        self.xhigh = xhigh
        self.hist, edges = np.histogram([], bins=nbins, range=(xlow, xhigh))
        self.bins = (edges[:-1] + edges[1:]) / 2.

    def fill(self, arr):
        hist, edges = np.histogram(arr, bins=self.nbins, range=(self.xlow, self.xhigh))
        self.hist += hist

    @property
    def data(self):
        return self.bins, self.hist

    # @property
    # def len(self):
    #     return len(self.hist)

@numba.vectorize()
def histSquareDiff (exsmooth,bxsmooth,factor):
    sum = 0
    bxsum = 0
    exsum = 0

    for i,(bx,ex) in enumerate(zip(bxsmooth,exsmooth)):
        #should we instead be incrementing i+1 to get the mean proxy,
        # such that the first bin is not entirely depriortized??????
        bxsum += bx *i
        exsum += ex *i
        diff = bx - (ex * factor)
        diff *= diff
        sum += diff

    if bxsum > exsum:
        sum = -sum

    return sum

@numba.vectorize()
def exponentialSmoothing (x, alpha):
    n = len(x)
    s = list()
    for i,x_i in enumerate(x):
        if i==0:
            s.append( x_i + alpha * (x[i+1]-x_i))
        elif i == n-1:
            s.append(alpha*(x[i-1]-x_i) + x_i)
        else:
            s.append(alpha*(x[i-1]-x_i) + x_i + alpha*(x[i+1]-x_i))
    # s = [0.]*n
    # s[0] = x[0] + alpha*(x[1]-x[0])
    # for i in range(1,n-1):
    #     s[i] = alpha*(x[i-1]-x[i]) + x[i] + alpha*(x[i+1]-x[i])
    #
    # s[n-1] = alpha*(x[n-2]-x[n-1])+x[n-1]

    return s

@numba.jit(nopython=True)
def normalize(bins):
    sum = np.sum(bins)
    normbins = [0.]*len(bins)
    for i,b in enumerate(bins):
        if sum == 0:
             normbins[i] = 0
        else:
            normbins[i] = b/sum
    return normbins

# @numba.jit()
def getStatisticForCpM(comp,cpmByFeature, feature, numBins,bxnorm):
    values = list()
    cpmFeature = comp+feature
    experimentalHist = cpmByFeature[cpmFeature]
    if experimentalHist == None:
        print(f"WARNING: Null distribution at {CpMFeature}",file=sys.stderr)
        return None

    print(f'going to compute HDscore for {cpmFeature}',file=sys.stderr)
    ex = experimentalHist.hist
    exsmooth = exponentialSmoothing(ex,0.25)
    exnorm = normalize(exsmooth)
    return histSquareDiff(exnorm,bxnorm,factor=1)

def makeColMap(header):
    return {head:i for i,head in enumerate(header)}

# @numba.jit()
def computeFeatureBins(dataFile,skipColumns):
    ''' is this effectively pd.read_table.to_records()??? ,except we are calculating minMax, probably'''
    featureBins = dict()
    with open(dataFile,'r') as datFile:
        headings = datFile.readline().strip().split(',')
        # print(headings,file=sys.stderr)
        lineCount = 0
        for line in datFile:
            fields = line.strip().split(',') #issue with the .strip()???
            lineCount += 1
            # if (lineCount % 10000)==0:
            #     print(f"Preprocessing line {lineCount}",file=sys.stderr)

            for i, featureValue in enumerate(fields):
                featureName = headings[i]
                if featureName in skipColumns:
                    continue
                if featureValue is None:
                    continue
                if featureValue.startswith('"'):
                    continue

                try:
                    if featureName in featureBins:
                        if featureBins[featureName]['max'] < np.float64(featureValue):
                            featureBins[featureName]['max'] = np.float64(featureValue)
                        if featureBins[featureName]['min'] > np.float64(featureValue):
                            featureBins[featureName]['min'] = np.float64(featureValue)
                    else:
                        featureBins[featureName] = {'min': np.float64(featureValue),\
                                                    'max': np.float64(featureValue)}
                        # featureBins[featureName]['fbin']=list()

                    # featureBins['fbin'].append(float(featureValue))
                except ValueError:
                    # print(f"ValueError creating FeatureBin for {featureName}",file=sys.stderr)
                    continue
    # [print(f"computed featureBins for {feat}",file=sys.stderr) for feat in headings if feat in featureBins.keys()]
    print(len(featureBins),len(headings),len(skipColumns),len(headings)-len(skipColumns),file=sys.stderr)
    #truly just to obtain min/max of the feature across the entire plate!
    return featureBins

@numba.jit()
def getCpMByFeatureMap(dataFileName, numBins:int, featureBins:dict, well2compound:dict, well2molarity:dict, skipColumns,CpMSet:set):
    # CpMSet = set() #instead do list(dict.fromkeys(CpMSet))
    with open(dataFileName,'r') as datFile:
        # datFileReader = csv.reader(datFile,delimiter=",")
        headings = datFile.readline().strip().split(',')
        headings2ColMap = makeColMap(headings)
        wellCol = headings2ColMap['WellName']
        CpMByFeature = dict()
        lineCount = 0
        for line in datFile:
            fields = line.split(',')
            well = fields[wellCol]
            lineCount +=1
            # if (lineCount % 10000) == 0:
            #      print(f"Processing line {lineCount}",file=sys.stderr);

            if len(well) <=2:
                # print(f'getCpMByFeatureMap ERROR: Empty well name: {well}'.file=sys.stderr)
                # print(f'offending Line:{lineCount}:\t{line}'.file=sys.stderr)
                return None

            well = well.replace('"',"")
            try:
                compound = well2compound[well]
            except KeyError:
                compound = ""

            molarity =""
            if compound == "":
                compound = "Blank"
            if compound == 'Blank':
                molarity = "0"
            else:
                molarity = well2molarity[well]

            if molarity == "":
                molarity = "0"

            CpM = f'{compound}_{molarity}'
            CpMSet.add(CpM)
            if CpM == 'Blank_0':
                CpM_ctrl = f'Bx-{well}_0'
            else:
                CpM_ctrl= None

            # if CpM_ctrl is not None:
            #     CpMSet.add(CpM_ctrl)
                # if ((lineCount % 10000) == 0):
                #     print(f'well: {well} = compound:{CpM_ctrl}',file=sys.stderr)

            for i,featureVal in enumerate(fields):
                if featureVal == "":
                    continue
                if len(featureVal) ==0:
                    continue

                featureName = headings[i]
                if featureName in skipColumns:
                    continue

                CpMFeature = CpM+featureName
                if CpM_ctrl is not None:
                    CpMFeature_bx = CpM_ctrl+featureName
                else:
                    CpMFeature_bx = None

                #some funny business going on below in here...
                if CpMFeature in CpMByFeature:
                    hist = CpMByFeature[CpMFeature]
                    if hist is None:
                        print(f'cyto.DataUtils Error: hist None for {CpMFeature}',file=sys.stderr)
                        continue
                    hist.fill(np.float64(featureVal))
                    # if CpMFeature_bx in CpMByFeature:
                    #     hist_bx = CpMByFeature[CpMFeature_bx]
                    #     if hist is None:
                    #         print(f'cyto.DataUtils Error: hist None for {CpMFeature_bx}',file=sys.stderr)
                    #         continue
                    #     hist_bx.fill(np.float64(featureVal))
                else:
                    fbin = featureBins[featureName]
                    if fbin is None:
                        print(f'featureBin is None for: {featureName}',file=sys.stderr)
                        continue
                    featureMin,featureMax = featureBins[featureName]['min'], featureBins[featureName]['max']
                    #the follwoing is from the decompiled version...
                    if featureMin == featureMax:
                        featureMax = featureMin + 0.5*featureMin
                    if featureMin == featureMax:
                        featureMax = featureMin + 1.0
                    # if(featureMin != featureMax): #When do we buffer the min/max!?!?!?
                    hist = Hist1D(numBins,featureMin,featureMax)
                    if hist is None:
                        print(f'cyto.DataUtils Error: hist null for {CpMFeature}',file=sys.stderr)
                        continue

                    hist.fill(np.float64(featureVal))
                    CpMByFeature[CpMFeature] = hist
                    # if CpM_ctrl is not None:
                    #     hist_bx = Hist1D(numBins,featureMin,featureMax)
                    #     hist_bx.fill(np.float64(featureVal))
                    #     CpMByFeature[CpMFeature_bx] = hist_bx
                    #     print(f'global control {CpMFeature} successfully added to dict of Hist1d: {CpMFeature in CpMByFeature}',file=sys.stderr)
    print(len(CpMSet),len(CpMByFeature),len(CpMSet)*len(featureBins),file=sys.stderr)
    if len(CpMByFeature) != len(CpMSet)*len(featureBins):
        print("WARNING MISMATCHED COLLECTED HISTOGRAMS VS PROBABLE HISTOGRAMS",file=sys.stderr)
    return CpMByFeature#,list(CpMSet)

def readPlateMapFile(plateMapFile):
    WellHeadingCol = "Well"
    CompoundHeadingCol = "MoleculeID"
    ConcentrationHeadingCol = "Concentration"
    well2compound = dict()
    well2molarity = dict()
    with open(plateMapFile,'r') as pmap:
        headings = pmap.readline().split(',')
        headings2ColMap = makeColMap(headings)
        wellIdx = headings2ColMap[WellHeadingCol]
        compoundIdx = headings2ColMap[CompoundHeadingCol]
        molarityIdx = headings2ColMap[ConcentrationHeadingCol]

        print(f'wellIdx={wellIdx}, compoundIdx ={compoundIdx},molarityIdx={molarityIdx}',file=sys.stderr)
        for line in pmap:
            fields = line.split(',')
            well = fields[wellIdx]
            compound = fields[compoundIdx]
            molarity = fields[molarityIdx]

            well2compound[well] = compound
            well2molarity[well] = molarity

    return (well2compound,well2molarity)

def main():
    skipColumns = [
     'Orientation_IMA_Summary', 'Cell_ID', 'Instance', 'Plate_ID',
     'Run_Settings_ID', 'Series_ID', 'Site_ID', 'Well_X', 'Well_Y', 'WellName',
     'Cell_Vesicle_Count_Transfluor', 'Cell_Vesicle_Average_Intensity_Transfluor',
     'Cell_Vesicle_Integrated_Intensity_Transfluor', 'Cell_Vesicle_Total_Area_Transfluor',
     'Cell_Scoring_Profile_MultiWaveScoring',
     'Laser_focus_score_MultiWaveScoring',
     'Laser_focus_score_Transfluor',
     'Laser_focus_score_Micronuclei',
     'Centroid_Y_IMA_Summary',
     'Centroid_X_IMA_Summary'
     ]

    args = sys.argv
    datafile = args[1] #MX*.merged.csv
    plateMapFile = args[2] #SP*.csv
    numBins = int(args[3]) #20
    if args[4]: #for backward compatability only(?) maybe not needed
        scoreMetric = args[4] #histdiff

    well2compound,well2molarity = readPlateMapFile(plateMapFile)
    featureBins = computeFeatureBins(datafile,skipColumns)
    CpMSet = set()
    CpMByFeature = getCpMByFeatureMap(datafile,numBins,featureBins,
        well2compound,well2molarity,skipColumns,CpMSet)
    print(len(well2compound),len(well2molarity),file=sys.stderr)
    CpMSet = list(CpMSet)
    print(CpMSet,file=sys.stderr)
    # sys.exit(0)

    with open(f"{datafile.split('.')[0]}.histdiffempy.csv",'w', newline='\n') as outfile:
        outCSV = csv.writer(outfile,delimiter=',')

        controlCompound = 'Blank_0'
        headline = ['Features'] +CpMSet
        print(",".join(headline),file=sys.stdout)
        outCSV.writerow(headline)
        scoresOut = dict()
        # print(featureBins.keys(),file=sys.stderr)
        for feature in featureBins:
            CpMFeature = controlCompound+feature
            try:
                blankHist = CpMByFeature[CpMFeature]
                if blankHist is None:
                    print(f'blankHist null for {CpMFeature}',file=sys.stderr)
                bx = blankHist.hist #hist should alread by np.array so no need for bxtemp
                bxsmooth = exponentialSmoothing(bx,0.25)
                bxnorm = normalize(bxsmooth)

                values = list()
                for CpM in CpMSet:
                    measure = getStatisticForCpM(CpM,CpMByFeature,feature,numBins,bxnorm)
                    values.append(measure)

                scoresOut[feature] = values
                outline = [feature]+["-1" if x is np.nan else str(x) for x in values]
                print(",".join(outline),file=sys.stdout)
                outCSV.writerow(outline)
            except KeyError:
                print(f'blankHist KeyError for {CpMFeature}',file=sys.stderr)

    # with shelve.open("histdiff_element.shelve",'n',writeback=True) as shelveFile:
    #     shelveFile['CpMSet'] = CpMSet
    #     shelveFile['headline'] = headline
    #     shelveFile['featureBins'] = featureBins
    #     shelveFile['CpMByFeature'] = CpMByFeature
    #     shelveFile['HDscores'] = scoresOut
    #
    # scoredDF = pd.read_csv(f"{datafile.split('.')[0]}.histdiffempy.csv",index_col=0).T
    # scoredDF.rename(columns={ x:f"{str(x).replace('W1','DAPI').replace('W2','EdU').replace('W3','PH3')}_EdU" for x in scoredDF.columns},inplace=True)
    #
    # # .rename(columns={ x:f"{str(x).replace('W1','DAPI').replace('W2','Tubulin').replace('W3','Actin')}_cyto" for x in scoredDF.columns},inplace=True)
    # scoredDF.to_csv(f"{datafile.split('.')[0]}.histdiffempy.csv")

if __name__ == "__main__":
    # if program is launched alone, this is true and is exececuted. if not, nothing is\
    # executedf rom this program and instead objects and variables are made available \
    # to the program that imports this.
    tic = time.perf_counter()
    main();
    toc = time.perf_counter()
    resources = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f'RAM usage: {resources}, run-time (s): {toc - tic:0.4f}',file=sys.stderr)
    raise SystemExit
