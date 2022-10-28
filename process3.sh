#!/bin/bash 

./mountBackup.pl

export TMPDIR=/data1/tmp

# Shellscript version of the pipeline... 
# process rawFile PlateMap histogramBins stattype
# 
# For example: 
# ./scripts/process.sh IXM490 PlateMaps/SP40002.csv 20 histdiff

function usage {
	echo "$0 $*"
	exit
}
timestamp=$(date +%Y%m%d-%H%M)

# convert windows crlf to just lf
echo "gunzip -c /home/halo384/cyto/$1.zip | tr '\r' '\n' > /data1/tmp/$1.lf.tab"
      gunzip -c /home/halo384/cyto/$1.zip | tr '\r' '\n' > /data1/tmp/$1.lf.tab


# convert tab file to csv file. Also, fix headers to have no special characters. 
echo "./scripts/tab2CSVAndFixHeader /data1/tmp/$1.lf.tab > /data1/tmp/$1.lf.csv"
      ./scripts/tab2CSVAndFixHeader /data1/tmp/$1.lf.tab > /data1/tmp/$1.lf.csv

# marcos: eliminate wells with only a few number of cells
#echo "./countCells.pl $1.lf.csv >$1.lf.tmp"
#./countCells.pl $1.lf.csv >$1.lf.tmp
#mv $1.lf.tmp $1.lf.csv

# marcos: eliminate columns that only appear once per well (actually 4 times per well)
#echo "./countRows.pl $1.lf.csv >$1.lf.tmp"
#./countRows.pl $1.lf.csv >$1.lf.tmp
#mv $1.lf.tmp $1.lf.csv

# Sort the file by CellID so we can do an inline merge of cell rows...
echo "./scripts/sortNamed  /data1/tmp/$1.lf.csv Cell_ID > /data1/tmp/$1.sorted.csv "
      ./scripts/sortNamed  /data1/tmp/$1.lf.csv Cell_ID > /data1/tmp/$1.sorted.csv 

# marcos: remove the "1--", "12-", etc. entries which confuse the mergeSortedCellRows scripts
echo "./filter.pl /data1/tmp/$1.sorted.csv > /data1/tmp/$1.filtered.csv "
      ./filter.pl /data1/tmp/$1.sorted.csv > /data1/tmp/$1.filtered.csv

# todo: cellID should be the first row -- permute it...

# Merge cell rows.  merged.csv is the file that should probably be saved
# from this preprocessing.  
echo "./scripts/mergeSortedCellRows /data1/tmp/$1.filtered.csv  > /data1/tmp/$1.merged.csv"
      ./scripts/mergeSortedCellRows /data1/tmp/$1.filtered.csv  > /data1/tmp/$1.merged.csv

# Compute a features by compound_molarity table, where each cell in the 
# table is a measure of the distance between the control (blank) and experimental
# distributions of values. 
#echo "./scripts/computeFeatureByCompoundTable /data1/tmp/$1.merged.csv $2 $3 $4 > /data1/tmp/$1.$4.dirty.csv"
#      ./scripts/computeFeatureByCompoundTable /data1/tmp/$1.merged.csv $2 $3 $4 > /data1/tmp/$1.$4.dirty.csv

echo "python3 ./scripts/histdiff_elementsVector.py /data1/tmp/$1.merged.csv $2 $3 $4 > /data1/tmp/$1.$4.dirtypy.csv"
      python3 ./scripts/histdiff_elementsVector.py /data1/tmp/$1.merged.csv $2 $3 $4 > /data1/tmp/$1.$4.dirtypy.csv

# rename the wavelengths to the stain names
echo "./renameWavelengths.pl /data1/tmp/$1.$4.dirtypy.csv \"$5\" >/data1/tmp/$1.$4.renamedpy.csv"
      ./renameWavelengths.pl /data1/tmp/$1.$4.dirtypy.csv "$5" >/data1/tmp/$1.$4.renamedpy.csv
#cp /data1/tmp/$1.$4.dirty.csv /data1/tmp/$1.$4.renamed.csv


# Remove uninformative rows from table...
#echo "./scripts/cleanupCompoundByFeatureTable /data1/tmp/$1.$4.renamed.csv > /data1/tmp/$1.$4.temp.csv"
#      ./scripts/cleanupCompoundByFeatureTable /data1/tmp/$1.$4.renamed.csv > /data1/tmp/$1.$4.temp.csv
cp /data1/tmp/$1.$4.renamedpy.csv /data1/tmp/$1.$4.temppy.csv

./transpose.pl -d , /data1/tmp/$1.$4.temppy.csv >"$1.$4_py.csv"

#cp -p "$1.$4_py.csv" ~/cyto_output/.
#cp -p "$1.$4_py.csv" /var/www/html/cyto/.

#echo "./scripts/featureByCompoundHeatmap $1.$4_py.csv $1 heatmap_pdf/$1.pdf heatmap_cdt/$1.cdt"
#      ./scripts/featureByCompoundHeatmap $1.$4_py.csv $1 heatmap_pdf/$1.pdf heatmap_cdt/$1.cdt

echo "removing temporary files..."

# Clean up the temporary files.  Merged is kept as the 
# new "primary" input file for future runs.  
rm -f /data1/tmp/$1.lf.tab
rm -f /data1/tmp/$1.lf.csv 
rm -f /data1/tmp/$1.sorted.csv 
rm -f /data1/tmp/$1.filtered.csv 
rm -f /data1/tmp/$1.$4.dirtypy.csv
touch /data1/tmp/$1.lf.tmp ; rm -f /data1/tmp/$1.lf.tmp
#rm -f /data1/tmp/$1.merged.csv
gzip -f /data1/tmp/$1.merged.csv
mv /data1/tmp/$1.merged.csv.gz merged/.
rm -f /data1/tmp/$1.$4.renamedpy.csv
rm -f /data1/tmp/$1.$4.temppy.csv

timestamp2=$(date +%Y%m%d-%H%M)
echo "started at $timestamp and finished at $timestamp2"
echo "done." 
