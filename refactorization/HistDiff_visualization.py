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
    """  generic normalize histogram by sum of all bins function """
    return np.divide(x, x.sum(), out=np.zeros_like(x, dtype='longdouble'), where=x.sum() != 0)


def mean_sd(x: list):
    print(f'mean +- sd: {round(np.mean(x), 3)} +- {round(np.std(x, ddof=1), 3)}, n = {len(x)}')
    return


if __name__ == '__main__':

    import matplotlib.pyplot as plt

    CENTER_EXP = 1000
    CENTER_CTRL = 1
    # BINS = 50

    for BINS in range(5,60,5):

        print(f'Number of bins tested: {BINS}')
        hd_vals = []

        for i in range(100):

            # Artificially define the histograms with weight in completely opposite bins
            max_diff = False
            if max_diff:
                experimental_hist_norm = np.concatenate([[1], np.zeros(BINS-1)]).reshape(BINS, 1)
                control_hist_norm = np.concatenate([np.zeros(BINS-1), [1]])
            else:
                # Get random samples
                experimental = np.random.normal(CENTER_EXP, 1, 1000)
                control = np.random.normal(CENTER_CTRL, 1, 1000)

                # Get min max values of the whole dataset
                min_val = min(np.concatenate([experimental, control]))
                max_val = max(np.concatenate([experimental, control]))

                # Create the histograms using the min/max values
                experimental_hist = Hist1D(nbins=BINS, xlow=min_val, xhigh=max_val)
                experimental_hist.fill(experimental)

                control_hist = Hist1D(nbins=BINS, xlow=min_val, xhigh=max_val)
                control_hist.fill(control)

            # Smooth histograms
            smoothing = True
            if smoothing:
                exp_hist_smoothed = exponentialSmoothing(experimental_hist.hist)
                ctrl_hist_smoothed = exponentialSmoothing(control_hist.hist)
            else:
                exp_hist_smoothed = experimental_hist.hist
                ctrl_hist_smoothed = control_hist.hist

            # Normalize the values
            experimental_hist_norm = normalize(exp_hist_smoothed).reshape(exp_hist_smoothed.size, 1)
            control_hist_norm = normalize(ctrl_hist_smoothed)

            # Calculate the HistDiff score
            histdiff_val = HistSquareDiff(experimental_hist_norm, control_hist_norm, factor=1)

            hd_vals.append(histdiff_val)

        mean_sd(hd_vals)
    # # Plot the normalized experimental and control histograms side by side
    # x_axis = np.arange(1, experimental_hist_norm.shape[0] + 1)
    # y_max = max(np.concatenate([experimental_hist_norm.flatten(), control_hist_norm]))
    #
    # plt.bar(x_axis - 0.2, experimental_hist_norm.flatten(), 0.4, label='exp')
    # plt.bar(x_axis + 0.2, control_hist_norm, 0.4, label='ctrl')
    # plt.xticks([])
    # plt.text(x=x_axis[0], y=y_max * 7/8, s=f'HistDiff value: \n{round(histdiff_val[0], 4)}')
    # plt.legend()
    # plt.show()
    #
    # for i in np.arange(1, (BINS / 2)):
    #     exp = np.zeros(BINS)
    #     exp[int(i + 1)] = 1
    #     print(f'exp: {exp}')
    #     exp = exp.reshape(BINS, 1)
    #
    #     ctrl = np.zeros(BINS)
    #     ctrl[-int(i)] = 1
    #     print(f'con: {ctrl}')
    #
    #     hd_val = HistSquareDiff(exp, ctrl, factor=1)
    #     print(f'HistDiff value: {hd_val}\n')



