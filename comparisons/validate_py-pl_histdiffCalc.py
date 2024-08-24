import pandas as pd, glob, os,sys, numpy as np,subprocess
import pickle
import umap
import Bio.Cluster as pycluster
from collections import Counter

mxid = Counter([mx.split('.')[0] for mx in glob.glob('MX*histdiff*.csv')])

mx_matchCount = dict()

likely_empty = list()

for mx, count in mxid.items():
    if count >1:
        print(mx)
        try:
            mx_1 = pd.read_csv(f'{mx}.histdiff.csv',index_col=0)
            mx_2 = pd.read_csv(f'{mx}.histdiff_py.csv',index_col=0)
            print(mx_1.shape,
                mx_2.shape,
                (mx_1.index.isin(mx_2.index.to_list())).sum(),
                (mx_1.index.isin([ix[:-2] if ix.endswith('.0') else ix for ix in mx_2.index.to_list()])).sum(),
                (mx_1.index.isin([ix[:-1] if ix.endswith('m') else ix for ix in mx_2.index.to_list()])).sum(),
                (mx_1.index.isin([ix[:-3] if ix.endswith('nan') else ix for ix in mx_2.index.to_list()])).sum())
            mx_matchCount[mx] = ((mx_1.index.isin(mx_2.index.to_list())).sum(),
                mx_1.index.isin([ix[:-2]  if ix.endswith('.0') else ix for ix in mx_2.index.to_list()]).sum(),
                (mx_1.index.isin([ix[:-1] if ix.endswith('m') else ix for ix in mx_2.index.to_list()])).sum(),
                (mx_1.index.isin([ix[:-3] if ix.endswith('nan') else ix for ix in mx_2.index.to_list()])).sum())
            if mx_matchCount[mx][0] == mx_1.shape[0]:
                subprocess.run(f'mv {mx}.histdiff.csv matched_out/.',shell=True)
                subprocess.run(f'mv {mx}.histdiff_py.csv matched_out/.',shell=True)
                mx_matchCount.pop(mx)
            elif mx_matchCount[mx][1] == mx_1.shape[0]:
                subprocess.run(f'mv {mx}.histdiff.csv matched_out/.',shell=True)
                mx_2.rename(index={ix:ix[:-2] for ix in mx_2.index if ix.endswith('.0')},inplace=True)
                mx_2.to_csv(f'{mx}.histdiff_py.csv')
                subprocess.run(f'mv {mx}.histdiff_py.csv matched_out/.',shell=True)
                mx_matchCount.pop(mx)
            elif mx_matchCount[mx][2] == mx_1.shape[0]:
                subprocess.run(f'mv {mx}.histdiff.csv matched_out/.',shell=True)
                mx_2.rename(index={ix:ix[:-1] for ix in mx_2.index if ix.endswith('m')},inplace=True)
                mx_2.to_csv(f'{mx}.histdiff_py.csv')
                subprocess.run(f'mv {mx}.histdiff_py.csv matched_out/.',shell=True)
                mx_matchCount.pop(mx)
            elif mx_matchCount[mx][3] == mx_1.shape[0]:
                subprocess.run(f'mv {mx}.histdiff.csv matched_out/.',shell=True)
                mx_2.rename(index={ix:ix[:-3] for ix in mx_2.index if ix.endswith('nan')},inplace=True)
                mx_2.to_csv(f'{mx}.histdiff_py.csv')
                subprocess.run(f'mv {mx}.histdiff_py.csv matched_out/.',shell=True)
                mx_matchCount.pop(mx)
        except:
            print(f" mx {mx} is empty,probably  move to ignore")
            likely_empty.append(mx)
        try:
            del mx_1
            del mx_2
        except NameError:
            pass


for mx, count in mx_matchCount.items():
    if mx not in likely_empty:
        mx_1 = pd.read_csv(f'{mx}.histdiff.csv',index_col=0)
        mx_2 = pd.read_csv(f'{mx}.histdiff_py.csv',index_col=0)
        index_df = pd.DataFrame({
        'pl':mx_1.index.to_list()+[np.nan]*(385-mx_1.shape[0]),
        'py':mx_2.index.to_list()+[np.nan]*(385-mx_2.shape[0]),
        'py-.0':[ix[:-2] if ix.endswith('.0') else ix for ix in mx_2.index.to_list()]+[np.nan]*(385-mx_2.shape[0]),
        'py-m':[ix[:-1] if ix.endswith('m') else ix for ix in mx_2.index.to_list()]+[np.nan]*(385-mx_2.shape[0]),
        'py-nan':[ix[:-3] if ix.endswith('nan') else ix for ix in mx_2.index.to_list()]+[np.nan]*(385-mx_2.shape[0])})
        #print(index_df)
        index_df.to_csv(f'{mx}_{mx_1.shape[0]}-{count}_indexCompare.csv')
        try:
            del mx_1
            del mx_2
        except NameError:
            pass

        
matched_enough = list()
mutated = list()

for mx,count in mx_matchCount.copy().items():
    if mx not in likely_empty:
        if count[0] >1:
            matched_enough.append((mx,['py','py-.0','py-m','py-nan'][np.argmax(count)]))
            subprocess.run(f'mv {mx}.histdiff.csv matched_out/.',shell=True)
            subprocess.run(f'mv {mx}.histdiff_py.csv matched_out/.',shell=True)
            mx_matchCount.pop(mx)
        else:
            mx_2 = pd.read_csv(f'{mx}.histdiff_py.csv',index_col=0)
            ending = ['','.0','m','nan'][np.argmax(count)]
            mutated.append((mx,ending))
            subprocess.run(f'mv {mx}.histdiff.csv matched_out/.',shell=True)
            mx_2.rename(index={ix:ix[:-len(ending)] for ix in mx_2.index if ix.endswith(ending)},inplace=True)
            mx_2.to_csv(f'{mx}.histdiff_py.csv')
            subprocess.run(f'mv {mx}.histdiff_py.csv matched_out/.',shell=True)
            mx_matchCount.pop(mx)
            del mx_2
            
            
pd.DataFrame({'mxid':[x for x in mxid.items()],
              'likely_empty':likely_empty+[np.nan]*(len(mxid)-len(likely_empty)),
              'matched_enough':matched_enough+[np.nan]*(len(mxid)-len(matched_enough)),
              'mutated':mutated +[np.nan]*(len(mxid)-len(mutated)),
              'ignore':ignore +[np.nan]*(len(mxid)-len(ignore))}).to_excel('validation_pl-py_construction.xlsx')

os.chdir('matched_out')

matched_mxid = Counter([mx.split('.')[0] for mx in glob.glob('MX*histdiff*.csv')])

matched_mx_1 =pd.DataFrame()
matched_mx_2 =pd.DataFrame()

matched_cor_corDist = dict().fromkeys(matched_mxid.keys())

from scipy.spatial import distance as sp_distance
from scipy import stats as sp_stats

for mx, count in matched_mxid.items():
    if count >1:
        mx_1 = pd.read_csv(f'{mx}.histdiff.csv',index_col=0)
        mx_2 = pd.read_csv(f'{mx}.histdiff_py.csv',index_col=0)
        mx_1_pert = mx_1.loc[mx_1.index.isin(mx_2.index.to_list())]
        mx_2_pert = mx_2.loc[mx_1_pert.index.to_list()][mx_1.columns.to_list()]
        print(mx_1_pert.shape,mx_2_pert.shape)
        assert mx_1_pert.index.to_list() == mx_2_pert.index.to_list()
        matched_corrDist = mx_2_pert.apply(lambda compSig: sp_distance.correlation(compSig.to_numpy(), mx_1_pert.loc[compSig.name].to_numpy()),axis=1)
        matched_cor = mx_2_pert.apply(lambda compSig: sp_stats.pearsonr(compSig.to_numpy(), mx_1_pert.loc[compSig.name].to_numpy())[0],axis=1)
        matched_cor_corDist[mx] = {'CorDist':matched_corrDist,'PearsonCor':matched_cor}
        # matched_mx_1 = pd.concat([matched_mx_1,mx_1_pert])
        # matched_mx_2 = pd.concat([matched_mx_2,mx_2_pert])

pd.DataFrame(matched_cor_corDist)

assert matched_mx_1.index.to_list() == matched_mx_2.index.to_list()
assert matched_mx_1.columns.to_list() == matched_mx_2.columns.to_list()

print(matched_mx_1.index == matched_mx_2.index,
      matched_mx_1.columns == matched_mx_2.columns,
      (matched_mx_1.index == matched_mx_2.index).sum(),
      (matched_mx_1.columns == matched_mx_2.columns).sum(),
      matched_mx_1.shape,
      matched_mx_2.shape)


matched_mx_1.to_csv('Matched_MX_histdiff.csv')
matched_mx_2.to_csv('Matched_MX_histdiffpy.csv')

#unfortunately the formatting of the stored corr values is a little hard to access
#so unpack more simply

temp_corrDist = list()
temp_cor = list()

for x,y in matched_cor_corDist.items():
    temp_cor.extend(y['PearsonCor'].to_list())

for x,y in matched_cor_corDist.items():
    temp_corrDist.extend(y['CorDist'].to_list())

pd.DataFrame({'PearsonCor':temp_cor,'CorrDist':temp_corrDist}).to_excel('Matched_MX_histdiff_pl-py_cor-corrDist.xlsx')

import seaborn as sns, matplotlib.pyplot as plt

for i, corrSet in enumerate([pd.Series(temp_corrDist),pd.Series(temp_cor)]):
    plt.figure(figsize=(10,8))
    sns.set()
    g = sns.distplot(corrSet.dropna(),bins=40,
                     hist=True,
                     kde=True,
                     norm_hist=True,
                     rug=True,
                     rug_kws={ "alpha": 0.05, "linewidth": 2, "height":0.03})
    #need to include the actual correlations as points or numbers on the histogram
    # print(corrSet.median,corrSet.median())
    g.vlines(corrSet.median(),ymin=0,ymax=12,linestyles='dashed',color='black',label="Median")
    g.set_ylabel("Density")
    plt.legend()
    if i ==0:
        plt.title(f"Density Plot of Correlation Distances\n{len(corrSet.dropna())}/{len(corrSet)} Perl vs Python calculated signatures compared")
        plt.savefig("{}.png".format("Matched_MX_histdiff_pl-py_corrDist"),dpi=300)
    elif i==1:
        plt.title(f"Density Plot of Pearson Correlations\n{len(corrSet.dropna())}/{len(corrSet)} Perl vs Python calculated signatures compared")
        plt.savefig("{}.png".format("Matched_MX_histdiff_pl-py_PearCorr"),dpi=300)
    plt.show()
    plt.close()