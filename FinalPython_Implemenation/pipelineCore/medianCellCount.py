import pandas as pd, numpy as np
import os, sys


def cleanColNames(colName):
    return (
        colName.strip()
        .replace("\t", ",")
        .replace("%", "Pct")
        .replace(" - ", "-")
        .replace(" ", "_")
        .replace("µ", "u")
        .replace("²", "^2")
        .replace("_(RAWcells-CP2-Cyto_BMR)", "")
        .replace("_(RAWcells-CP2-EdU_BMR)", "")
    )


def findCommonFeats(trueFeats: list, badFeats: list):
    """
    Finds the common features between a bad features list and the true features
    Args:
        trueFeats (list): list of the true features
        badFeats (list): list of bad/ignored features

    Returns:
        list: returns a list of the common features
    """
    commonFeats = list(set(trueFeats) & set(badFeats))
    for feat in trueFeats:
        if any([i in feat for i in badFeats if len(i) > 2]) and feat not in commonFeats:
            commonFeats.append(feat)
        if (
            any([i == feat for i in badFeats if len(i) <= 2])
            and feat not in commonFeats
        ):  # check for the small substrings like 'X' or 'Y'
            commonFeats.append(feat)

    # print(*commonFeats, sep="\n", file=sys.stderr)
    return commonFeats


def cleanWellNameList(x: list) -> list:
    """Cleans Well Names to be <LETTER><1-digit well number>"""
    return ["".join([i[0], str(int(i[1:]))]) for i in x]


def createDTypes(headers: list, uselessFeats: list = None):
    """
    Cell ID related opbjects are identified as strings (from uselessFeats section)
    while important features are given as floats
    """
    if uselessFeats is not None:
        dtypes = {feat: str for feat in uselessFeats}
        dtypes.update({feat: float for feat in headers if feat not in uselessFeats})
    else:
        dtypes = {feat: float for feat in headers}
    return dtypes


def getFeatures(df: pd.DataFrame):
    """Grab Features from tsv file"""
    nrowDf = pd.read_table(df, nrows=0)
    return nrowDf.columns.to_list()


def preProcessDataFrame(df: pd.DataFrame, idFeats, badFeats):
    """Format a df so we are left only with the actual good features"""
    df = df.copy()

    def row(x):
        strs = map(str, x[idFeats])
        return "_".join(strs)

    df["id"] = df.apply(lambda x: row(x), axis=1) if len(idFeats) > 1 else df[idFeats]
    df.set_index("id", inplace=True)
    df.drop(badFeats, axis=1, inplace=True)
    df.rename(columns=lambda x: cleanColNames(x), inplace=True)
    df.rename(index=lambda x: "".join([x[0], str(int(x[1:]))]), inplace=True)

    goodFeatVerification = [feat for feat in df.columns if feat in badFeats]
    if len(goodFeatVerification) > 0:
        print(
            f"Bad feats still in good features:\n {goodFeatVerification}",
            file=sys.stderr,
        )
        raise ValueError

    return df, df.index.to_list()


def problematicFeats(
    chunks: pd.DataFrame, idFeats, badFeats, verbose=True, probOut=None
) -> list:
    """
    find all the problematic features in a given data frame.

    Args:
        chunks (pd.DataFrame): chunked dataframe (typically chunked but works on whole DFs)
        idFeats (list): the list of columns to be used as the index
        badFeats (list): list of the features to ignore
        verbose (bool, optional): Verbose output of operations. Defaults to True.
        probOut (str, optional): The output file path for the problematic features (depricated). Defaults to None.

    Returns:
        list: outputs a list of good features that are not NA
    """
    xlow = []
    xHigh = []

    feats = []

    for count, chunk in enumerate(chunks, start=1):
        currDf, ids = preProcessDataFrame(df=chunk, idFeats=idFeats, badFeats=badFeats)
        currDf = currDf.replace(to_replace=-np.inf, value=np.nan)
        currDf = currDf.replace(to_replace=np.inf, value=np.nan)

        if count == 1:
            feats = currDf.columns.to_list()

        xlow.append(currDf.min(axis=0).to_list())
        xHigh.append(currDf.max(axis=0).to_list())

    xlow = pd.DataFrame(xlow).min(axis=0)
    xhigh = pd.DataFrame(xHigh).max(axis=0)

    min_max = pd.DataFrame(
        {"xlow": xlow.to_list(), "xhigh": xhigh.to_list()}, index=feats
    )

    min_max.dropna(inplace=True)
    good_features = min_max.index.values.tolist()
    print(f"length of good features is: {len(good_features)}", file=sys.stderr)

    return good_features


def calculateZScore(df: pd.DataFrame, controls: list):
    """Calculates the Z score of a given DF"""
    controlsDf = df[df.index.str.contains("|".join(controls))]
    return (
        df - controlsDf.mean()
    ) / controlsDf.std()  # mean and std should be for controls (DMSO)


def getMedianWellValue(
    filePath: str,
    idFeats: list,
    controls: list,
    featuresIgnore: list,
    featureDtypes: dict,
    chunkSize: int = 50000,
    probOut: str = None,
    zScore=False,
) -> pd.DataFrame:
    """
    Calculates the well median values from given cell data
    as well as zscores (optional)

    Args:
        filePath (str): cell by cell data file path
        idFeats (list): list of features used for df index
        controls (list): list of control wells used for zscore calculations
        featuresIgnore (list): list of features that are useless
        featureDtypes (dict): dtypes for all the columns in the df
        chunkSize (int, optional): size of each chunk to read into DF. Defaults to 50000.
        probOut (str, optional): outpath of csv file of problematic features. Defaults to None.
        zScore (bool, optional): determines if the zscore should be calculated. Defaults to False.

    Returns:
        pd.DataFrame: The final well median results
    """
    chunks = pd.read_table(
        filePath,
        chunksize=chunkSize,
        dtype=featureDtypes,
        usecols=featureDtypes,
        on_bad_lines="skip",
    )

    good_features = problematicFeats(
        chunks=chunks,
        idFeats=idFeats,
        badFeats=featuresIgnore,
        verbose=True,
        probOut=probOut,
    )

    # df = pd.read_table(filePath, dtype=featureDtypes, usecols=featureDtypes)
    # df, ids = preProcessDataFrame(df=df, idFeats=idFeats, badFeats=featuresIgnore)
    # df = df[good_features]
    # return df.groupby(level="id").agg("median")

    chunks = pd.read_table(
        filePath,
        chunksize=chunkSize,
        dtype=featureDtypes,
        usecols=featureDtypes,
        on_bad_lines="skip",
    )

    medians = {}
    groupSize = {}

    for chunk in chunks:
        currDf, ids = preProcessDataFrame(
            df=chunk, idFeats=idFeats, badFeats=featuresIgnore
        )
        currDf = currDf[good_features]

        for well, wellDf in currDf.groupby(level="id"):  # group by id
            if well not in medians:  # instantiate new list objects in dict
                medians[well] = []
                groupSize[well] = []

            groupSize[well].append(
                wellDf.shape[0]
            )  # just incase i want to do weighted medians

            wellDf = wellDf.median().to_frame().T
            wellDf.index = [well]

            medians[well].append(wellDf)

    finalMedians = []
    for k, v in medians.items():  # calculate the median of medians
        medianDf = pd.concat(v, axis=0)
        median = medianDf.median().to_frame().T
        median.index = [k]

        finalMedians.append(median)

    median = pd.concat(finalMedians, axis=0)

    return calculateZScore(median, controls=controls) if zScore else median


class CommandLine:
    """Command line module"""

    def __init__(self, inOpts=None) -> None:
        import argparse

        self.parser = argparse.ArgumentParser(
            description="Calculates well medians as well as its zscores (optionals)",
            prog="medianCellCount.py",
            usage="python %(prog)s -[arguments] [value]",
            add_help=True,
            prefix_chars="-",
        )

        self.parser.add_argument(
            "-i",
            "--input",
            action="store",
            nargs="?",
            required=True,
            type=str,
            help="Cell by Cell data path as a tab-delimited file",
        )
        self.parser.add_argument(
            "-o",
            "--output",
            nargs="?",
            required=True,
            type=str,
            help="output name for final median results as .csv",
        )
        self.parser.add_argument(
            "-z",
            "--zscore",
            action="store_true",
            default=False,
            help="Enables zscore calculation of the median wells (def: False)",
        )

        self.parser.add_argument(
            "-c",
            "--controls",
            action="store",
            nargs="?",
            default=True,
            help="csv file path to a plate map containing all the control wells needed for zscore calculation",
        )

        if inOpts is None:
            self.args = self.parser.parse_args()
        else:
            self.args = self.parser.parse_args(inOpts)


def main(inOpts=None):
    # testData = "/mnt/c/Users/derfelt/Desktop/LokeyLabFiles/ImmunoCP/designer mixture cellbycell/MX5090.txt"
    # testData = "/mnt/c/Users/derfelt/Desktop/LokeyLabFiles/TargetMol/cellData_examples/10uM/2bffddea-8a23-11ee-ac86-02420a000112_cellbycell.tsv"
    cl = CommandLine(inOpts=inOpts)

    cellDf = cl.args.input
    outPath = cl.args.output
    zScores = cl.args.zscore
    controls = cl.args.controls

    controls = pd.read_csv(cl.args.controls)
    controls.reset_index(inplace=True)
    controls.rename(columns=lambda x: str(x).upper(), inplace=True)
    controls.set_index("384_WELL", inplace=True)
    controls = controls[["Sample_type".upper()]]
    controls = controls[controls["Sample_type".upper()] == "REFERENCE"]

    controls = [
        "".join([i[0], str(int(i[1:]))]) for i in controls.index.unique().to_list()
    ]

    badFeats = [
        "ScreenName",
        "ScreenID",
        "PlateName",
        "PlateID",
        "MeasurementDate",
        "MeasurementID",
        "WellName",
        "Row",
        "Column",
        "Timepoint",
        "Field",
        "RefId",
        "Object Number",
        "X",
        "Y",
        "Bounding Box",
        "ax",
        "ay",
        "Cell Count",
        "Cell ID",
        "Instance",
        "Laser focus score",
        "Plate ID",
        "Run Settings ID",
        "Series ID",
        "Site ID",
        "Well Name",
        "Well X",
        "Well Y",
    ]

    feats = getFeatures(cellDf)
    badFeats = findCommonFeats(trueFeats=feats, badFeats=badFeats)
    dtypes = createDTypes(headers=feats, uselessFeats=badFeats)

    idFeats = ["WellName"] if "WellName" in badFeats else ["Well Name"]

    medianWells = getMedianWellValue(
        filePath=cellDf,
        idFeats=idFeats,
        featuresIgnore=badFeats,
        featureDtypes=dtypes,
        zScore=zScores,
        controls=controls,
    )

    medianWells.to_csv(outPath)
    return


if __name__ == "__main__":
    main()
