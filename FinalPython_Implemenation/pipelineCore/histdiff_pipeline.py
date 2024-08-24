#!/usr/bin/env python

import os, time, sys, resource, glob
import pandas as pd
import numpy as np
import io
from zipfile import ZipFile
from string import ascii_uppercase


class Hist1D(object):
    """taken from https://stackoverflow.com/a/45092548"""

    def __init__(self, nbins, xlow, xhigh):
        self.nbins = nbins
        self.xlow = xlow
        self.xhigh = xhigh
        self.hist, edges = np.histogram([], bins=nbins, range=(xlow, xhigh))
        self.bins = (edges[:-1] + edges[1:]) / 2.0

    def fill(self, arr):
        hist, edges = np.histogram(arr, bins=self.nbins, range=(self.xlow, self.xhigh))
        self.hist += hist

    @property
    def data(self):
        return self.bins, self.hist


def HistSquareDiff(exp, ctrl, factor=1):
    """The actual workhorse HistDiff scoring function"""

    # we transpose twice to ensure the final result is a 1 x m feature score vector
    ctrl_meanProxy = (np.arange(1, ctrl.shape[0] + 1) * ctrl.T).T.sum(axis=0)
    exp_meanProxy = (np.arange(1, exp.shape[0] + 1) * exp.T).T.sum(axis=0)

    # evaluate where and when to adjust the score to be negative
    negScore = np.where(ctrl_meanProxy > exp_meanProxy, -1, 1)
    diff = ctrl - (exp.T * factor)
    diff **= 2

    return diff.sum(axis=1) * negScore


def exponentialSmoothing(x, alpha=0.25):
    """

    :param x:
    :param alpha:
    :return:
    """
    n = len(x)
    s = list()
    for i, x_i in enumerate(x):
        if i == 0:
            s.append(x_i + alpha * (x[i + 1] - x_i))
        elif i == n - 1:
            s.append(alpha * (x[i - 1] - x_i) + x_i)
        else:
            s.append(alpha * (x[i - 1] - x_i) + x_i + alpha * (x[i + 1] - x_i))
    return np.array(s)


def normalize(x):
    """generic normalize histogram by sum of all bins function"""
    # TODO: In numpy 1.23.5 I had to extend the where part of the function to the length of x for it to work
    #  It would run with the simple x.sum() != 0 statement before, but now throws a np.putmask-related error.
    #  This might be a specific Mac issue for whatever reason, since this was not encountered on Windows
    return np.divide(
        x,
        x.sum(),
        out=np.zeros_like(x, dtype="longdouble"),
        where=np.repeat(x.sum(), len(x)) != 0,
    )


def calcHistDiffScores(
    cellData: str,
    idFeats: list,
    featuresIgnore: list,
    featureDtypes: dict,
    vehicleCntrlWells: tuple,
    nBins: int = 20,
    chunkSize: int = 50000,
    probOut=None,
    blockCalc=False,
):
    chunks = pd.read_table(
        cellData,
        chunksize=chunkSize,
        dtype=featureDtypes,
        usecols=featureDtypes,
        on_bad_lines="skip",
    )

    # Remove np.nan min max features from table, but report them separately
    min_max, good_features, problematic_features_df, ids = getMinMaxPlate(
        chunks=chunks,
        idFeats=idFeats,
        badFeats=featuresIgnore,
        verbose=True,
        probOut=probOut,
    )

    featureNames = good_features

    def createHistRow():
        histRow = min_max.apply(
            lambda x: Hist1D(nbins=nBins, xlow=x["xlow"], xhigh=x["xhigh"]), axis=1
        )
        histRow = pd.DataFrame(histRow).T
        return histRow

    dtypes = createDTypes(headers=good_features)
    chunks = pd.read_table(
        cellData, chunksize=chunkSize, dtype=dtypes, on_bad_lines="skip"
    )

    for count, chunk in enumerate(chunks, start=1):
        currDf, ids = preProcessDataFrame(
            df=chunk, idFeats=idFeats, badFeats=featuresIgnore
        )
        currDf = currDf[featureNames]

        wells_used = currDf.index.unique()

        # first iter
        if count == 1:
            hist_df = pd.concat([createHistRow() for _ in range(len(wells_used))])
            hist_df.index = wells_used

        # Add new wells if encountered
        unencountered_wells = set(wells_used).difference(set(hist_df.index))
        if len(unencountered_wells) > 0:
            hist_df_temp = pd.concat(
                [createHistRow() for _ in range(len(unencountered_wells))]
            )
            hist_df_temp.index = unencountered_wells
            hist_df = pd.concat([hist_df, hist_df_temp])

        for well in wells_used:
            well_chunk = currDf[currDf.index == well]
            hist_df[hist_df.index == well].apply(
                lambda x: x[well].fill(well_chunk.loc[:, x.name])
            )

    # Unpack the histogram objects, just leave the .hist array
    print(f"Unpack histograms", file=sys.stderr)
    hist_df = hist_df.map(lambda x: x.hist)

    if not blockCalc:
        if not isinstance(vehicleCntrlWells, list):
            vehicle_control_wells = vehicleCntrlWells[0]
            special_vehicle_control_wells = vehicleCntrlWells[1]
            select_rows = set([ix[0] for ix in special_vehicle_control_wells])

            hist_df = hist_df.loc[[ix for ix in hist_df.index if ix[0] in select_rows]]
            # startswith('G') or \
            #     ix.startswith('H') or ix.startswith('I') or ix.startswith('J')]]
            vehicle_control_wells = special_vehicle_control_wells
        else:
            vehicle_control_wells = vehicleCntrlWells

        print(
            "Find all vehicle control wells and sum the histograms into a vehicle control vector",
            file=sys.stderr,
        )
        # vehicle_control_wells = platemap[PLATE_MAP_WELL_NAME][platemap[PLATE_MAP_SAMPLE_TYPE] == VEHICLE_CONTROL]

        available_vehicle_control_wells = list(
            set(vehicle_control_wells).intersection(hist_df.index)
        )
        # Sum all histograms from wells belonging to the vehicle controls
        vehicle_control_row = (
            hist_df.loc[available_vehicle_control_wells, :].to_numpy().sum(axis=0)
        )  # should not enter if criteria is met
        vehicle_control_row = pd.DataFrame(
            vehicle_control_row, index=hist_df.columns, columns=["VEHICLE_CONTROL"]
        ).T

        # Add vehicle control
        print("Add vehicle control to histogram table", file=sys.stderr)
        hist_df = pd.concat([hist_df, vehicle_control_row])

        # print(hist_df.shape,hist_df.head(5), hist_df.applymap(lambda x: type(x)).describe(),file=sys.stderr)
        print("Smooth histograms", file=sys.stderr)
        smoothed_histograms = hist_df.map(lambda x: exponentialSmoothing(x, alpha=0.25))

        print("Normalize histograms", file=sys.stderr)
        normalized_smoothed_histograms = smoothed_histograms.map(normalize)

        hds = []
        for n, feature in enumerate(featureNames, start=1):
            print(
                f"Calculate HistDiff scores for feature {feature} ({n}/{len(featureNames)} features)",
                file=sys.stderr,
            )

            control = np.array(
                normalized_smoothed_histograms.loc["VEHICLE_CONTROL", feature]
            )
            experimental = np.transpose(
                np.array(normalized_smoothed_histograms[feature].to_list())
            )
            hd = HistSquareDiff(exp=experimental, ctrl=control)

            hds.append(hd)

        histdiff_df = pd.DataFrame(hds, index=featureNames, columns=hist_df.index).T

        # Remove vector control
        print("Drop vehicle control from HistDiff score table", file=sys.stderr)
        histdiff_df = histdiff_df.drop("VEHICLE_CONTROL")
        histdiff_df.rename(
            columns={col: cleanColNames(col) for col in histdiff_df.columns},
            inplace=True,
        )

        return histdiff_df
    else:
        aggDf = []
        consumedControlWells = set()
        for i, controlGroup in enumerate(
            vehicleCntrlWells
        ):  # TODO: on input, give in all the well names dont just look at a row or column
            if i == 0:  # These are your selected blocks:
                select_wells = set(
                    ["".join([i[0], str(int(i[1:]))]) for i in controlGroup]
                )
                [consumedControlWells.add(well) for well in controlGroup]
            else:
                select_wells = set(hist_df.index).difference(select_wells)

            hd_group = hist_df.loc[[ix for ix in select_wells]]

            print(select_wells, controlGroup, i, file=sys.stderr)
            print(hd_group.shape, file=sys.stderr)

            available_vehicle_control_wells = list(
                set(vehicleCntrlWells[1]).intersection(hd_group.index)
            )
            # Sum all histograms from wells belonging to the vehicle controls
            vehicle_control_row = (
                hd_group.loc[available_vehicle_control_wells, :].to_numpy().sum(axis=0)
            )  # should not enter if criteria is met
            vehicle_control_row = pd.DataFrame(
                vehicle_control_row, index=hd_group.columns, columns=["VEHICLE_CONTROL"]
            ).T

            # Add vehicle control
            print("Add vehicle control to histogram table", file=sys.stderr)
            hd_group = pd.concat([hd_group, vehicle_control_row])

            # print(hist_df.shape,hist_df.head(5), hist_df.applymap(lambda x: type(x)).describe(),file=sys.stderr)
            print("Smooth histograms", file=sys.stderr)
            smoothed_histograms = hd_group.map(
                lambda x: exponentialSmoothing(x, alpha=0.25)
            )

            print("Normalize histograms", file=sys.stderr)
            normalized_smoothed_histograms = smoothed_histograms.map(normalize)

            hds = []
            for n, feature in enumerate(featureNames, start=1):
                print(
                    f"Calculate HistDiff scores for feature {feature} ({n}/{len(featureNames)} features)",
                    file=sys.stderr,
                )

                control = np.array(
                    normalized_smoothed_histograms.loc["VEHICLE_CONTROL", feature]
                )
                experimental = np.transpose(
                    np.array(normalized_smoothed_histograms[feature].to_list())
                )
                hd = HistSquareDiff(exp=experimental, ctrl=control)

                hds.append(hd)

            histdiff_df = pd.DataFrame(
                hds, index=featureNames, columns=hd_group.index
            ).T

            # Remove vector control
            print("Drop vehicle control from HistDiff score table", file=sys.stderr)
            histdiff_df = histdiff_df.drop("VEHICLE_CONTROL")
            histdiff_df.rename(
                columns={col: cleanColNames(col) for col in histdiff_df.columns},
                inplace=True,
            )
            aggDf.append(histdiff_df)

        return pd.concat(aggDf, axis=0)


def getMinMaxPlate(chunks: pd.DataFrame, idFeats, badFeats, verbose=True, probOut=None):
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

    xhigh[xhigh == xlow] = xlow[xhigh == xlow] + xlow[xhigh == xlow] * 0.5
    xhigh[xhigh == xlow] = xlow[xhigh == xlow] + 1

    min_max = pd.DataFrame(
        {"xlow": xlow.to_list(), "xhigh": xhigh.to_list()}, index=feats
    )

    bad_features = {
        feature: "noValues"
        for feature in min_max[
            min_max.apply(lambda x: all(np.isnan(x)), axis=1)
        ].index.values.tolist()
    }
    problematic_features_df = None
    if bad_features and verbose:
        print(
            f"MinMax: No values have been found in the following features: "
            f'{" | ".join(bad_features.keys())}',
            file=sys.stderr,
        )
        problematic_features_df = pd.Series(bad_features, name="histdiff_issue")
        if probOut is not None:
            problematic_features_df.to_csv(f"{probOut}_problematicFeats.csv")

    # Get good features and min_max table
    min_max = min_max[~min_max.apply(lambda x: all(np.isnan(x)), axis=1)]
    good_features = min_max.index.values.tolist()
    print(f"length of good features is: {len(good_features)}", file=sys.stderr)

    return (min_max, good_features, problematic_features_df, ids)


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

    goodFeatVerification = [feat for feat in df.columns if feat in badFeats]
    if len(goodFeatVerification) > 0:
        print(
            f"Bad feats still in good features:\n {goodFeatVerification}",
            file=sys.stderr,
        )
        raise ValueError

    return df, df.index.to_list()


def getFeatures(df: pd.DataFrame):
    """Grab Features from tsv file"""
    nrowDf = pd.read_table(df, nrows=0)
    return nrowDf.columns.to_list()


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


def cleanColNames(colName):
    return (
        colName.strip()
        .replace("\t", ",")
        .replace("%", "Pct")
        .replace(" - ", "-")
        .replace(" ", "_")
        .replace("µ", "u")
        .replace("²", "^2")
    )


def findCommonFeats(trueFeats: list, badFeats: list):
    commonFeats = list(set(trueFeats) & set(badFeats))
    return commonFeats


class CommandLine:
    def __init__(self, inOpts=None):
        import argparse

        self.parser = argparse.ArgumentParser(
            description="Calculates HD scores from a cell by cell tsv file from Signals",
            prog="histdiff_pipeline.py",
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
            help="Cell by Cell data input as .tsv file",
        )
        self.parser.add_argument(
            "-o",
            "--output",
            action="store",
            nargs="?",
            required=True,
            type=str,
            help="output name for final HD csv results",
        )
        self.parser.add_argument(
            "-c",
            "--controls",
            action="store",
            nargs="?",
            required=True,
            type=str,
            help="input of control wells as a csv (NOTE: the first column should be wells, the second column should be control type (i.e. DMSO/DMSO+PMA))",
        )

        self.parser.add_argument(
            "-cs",
            "--controlSpecified",
            action="store_true",
            default=False,
            required=False,
            help="Enables specific platemap parsing",
        )

        self.subparser = self.parser.add_subparsers(
            title="Block Re-calculation",
            description="enables block recalculation",
            dest="subcommand",
        )

        self.blockRecalc = self.subparser.add_parser("blockRecalc")
        self.blockRecalc.add_argument(
            "-s",
            "--specials",
            nargs="+",
            required=True,
            help="specifies special wells to individually calculate histdiff on",
            type=str,
        )

        if inOpts is None:
            self.args = self.parser.parse_args()
        else:
            self.args = self.parser.parse_args(inOpts)


def main(inOpts=None):
    # testDf = "/Users/dterciano/Desktop/GitRepos/HistDiffPipeline/peek.tsv"
    # testDf = "/Users/dterciano/Desktop/LokeyLabFiles/TargetMol/XMLexamples/cellbycellTSV/89531a3c-79c7-11ee-a3cc-02420a000169_cellbycell.tsv"
    # df = pd.read_table(testDf, chunksize=10)
    # df = pd.read_table(testDf)

    cl = CommandLine(inOpts=inOpts)

    cellDf = cl.args.input

    controls = pd.read_csv(cl.args.controls, index_col=0)
    if cl.args.controlSpecified:
        controls.reset_index(inplace=True)
        controls.rename(columns=lambda x: str(x).upper(), inplace=True)
        controls.set_index("384_WELL", inplace=True)
        controls = controls[["Sample_type".upper()]]
        controls = controls[controls["Sample_type".upper()] == "REFERENCE"]

    controls = ["".join([i[0], str(int(i[1:]))]) for i in controls.index.to_list()]
    output = cl.args.output

    blockCalc = False
    if cl.args.subcommand == "blockRecalc":
        specialWells = cl.args.specials
        controls = (specialWells, controls)
        blockCalc = True

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
    ]
    idFeats = ["WellName"]

    feats = getFeatures(cellDf)
    badFeats = findCommonFeats(
        trueFeats=feats, badFeats=badFeats
    )  # we need to find the common badfeats
    dtypes = createDTypes(headers=feats, uselessFeats=badFeats)
    hd = calcHistDiffScores(
        cellData=cellDf,
        idFeats=idFeats,
        featuresIgnore=badFeats,
        featureDtypes=dtypes,
        vehicleCntrlWells=controls,
        probOut=output,
        blockCalc=blockCalc,
    )
    hd.to_csv(f"{output}.csv")
    return


if __name__ == "__main__":
    main()
