#!/usr/bin/perl

use strict;
use warnings;

use Data::Dumper;

my $filename=shift || die "usage: runCommand.pl runContents.csv [measurementFilename]\n";
my $measurementName=shift;


open(F,"<$filename") || die "file $filename not found";
my @b;
my $header=<F>;
chomp $header;
my @a=split ',',$header;
for (my $i=0;  $i<scalar(@a);  $i++) {
  if ($a[$i] =~ m/(.+?) \((.+?)\)/) {
#   print "$1 $2\n";
    $b[$i]="$2 $1";
  }
}

#print Dumper(\@b);
while(<F>) {
  chomp;
  my @a=split ',';
  my $file=$a[1];
  my $plateMap=$a[2];
  my $map="";
  for (my $i=3;  $i<scalar(@a);  $i++) {
    $map.=$b[$i].' ' if ($a[$i] eq '1');
  }
  $map =~ s/ $//g;
  if (!$measurementName || $file eq $measurementName) {
    print STDERR "time ./process2.sh $file PlateMaps/$plateMap.csv 20 histdiff \"$map\" >& $file.log\n";
    `time ./process2.sh $file PlateMaps/$plateMap.csv 20 histdiff "$map" >& $file.log`;
    `echo >> $file.log`;
    `echo "time ./process2.sh $file PlateMaps/$plateMap.csv 20 histdiff \"$map\"" >> $file.log`;
#   `echo "$filename ($file $measurementName $map) processed using $plateMap.csv" | ~/bin/cytomail.pl`;
  }
}

close(F);
