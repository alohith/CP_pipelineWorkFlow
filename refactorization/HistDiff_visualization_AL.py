import numpy as np


class Hist1D(object):
    """ taken from https://stackoverflow.com/a/45092548"""

    def __init__(self, nbins, xlow, xhigh):
        self.nbins = nbins
        self.xlow = xlow
        self.xhigh = xhigh
        self.hist, edges = np.histogram([], bins=nbins, range=(xlow, xhigh))
        self.bins = (edges[:-1] + edges[1:]) / 2.

    def fill(self, arr):
        hist, edges = np.histogram(arr, bins=self.nbins, range=(self.xlow, self.xhigh))
        self.hist += hist

    @property
    def data(self):
        return self.bins, self.hist


def HistSquareDiff(exp, ctrl, factor=1):
    """ The actual workhorse HistDiff scoring function """

    # we transpose twice to ensure the final result is a 1 x m feature score vector
    ctrl_meanProxy = (np.arange(1, ctrl.shape[0] + 1) * ctrl.T).T.sum(axis=0)
    exp_meanProxy = (np.arange(1, exp.shape[0] + 1) * exp.T).T.sum(axis=0)
    # evaluate where and when to adjust the score to be negative
    negScore = np.where(ctrl_meanProxy > exp_meanProxy, -1, 1)
    diff = ctrl - (exp.T * factor)
    diff **= 2

    return diff.sum() * negScore


def normalize(x):
    """  generic normalize histogram by sum of all bins function """
    return np.divide(x, x.sum(), out=np.zeros_like(x, dtype='longdouble'), where=x.sum() != 0)


if __name__ == '__main__':

    import matplotlib.pyplot as plt

    CENTER_EXP = 14
    CENTER_CTRL = 2
    #BINS = 20

    # Get random samples
    experimental = np.random.normal(CENTER_EXP, 1, 1000)
    control = np.random.normal(CENTER_CTRL, 1, 1000)

    # Get min max values of the whole dataset
    min_val = min(np.concatenate([experimental, control]))
    max_val = max(np.concatenate([experimental, control]))
    
    for BINS in range(5,50,5):
        # Create the histograms using the min/max values
        experimental_hist = Hist1D(nbins=BINS, xlow=min_val, xhigh=max_val)
        experimental_hist.fill(experimental)

        control_hist = Hist1D(nbins=BINS, xlow=min_val, xhigh=max_val)
        control_hist.fill(control)

        # Normalize the values
        experimental_hist_norm = normalize(experimental_hist.hist)
        control_hist_norm = normalize(control_hist.hist)

        # Calculate the HistDiff score
        histdiff_val = HistSquareDiff(experimental_hist_norm, control_hist_norm, factor=1)

        # Plot the normalized experimental and control histograms side by side
        x_axis = np.arange(1, experimental_hist_norm.shape[0] + 1)
        y_max = max(np.concatenate([experimental_hist_norm.flatten(), control_hist_norm]))

        plt.bar(x_axis - 0.2, experimental_hist_norm.flatten(), 0.4, label='exp')
        plt.bar(x_axis + 0.2, control_hist_norm, 0.4, label='ctrl')
        plt.xticks([])
        #plt.text(x=x_axis[0], y=y_max * 7/8, s=f'HistDiff value: \n{round(histdiff_val[0], 4)}')
        print(f"Bins: {BINS}\t{round(histdiff_val,4)}")
        plt.legend()
        plt.savefig(f'HistDiff_visualize_random_numBins{BINS}.png',dpi=300)
        plt.close()
