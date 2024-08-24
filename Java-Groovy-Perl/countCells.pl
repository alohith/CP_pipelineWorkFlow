#!/usr/bin/perl

use strict;
use warnings;

use Data::Dumper;

my $cutoff=20;
my %badWells;

my $file=shift || die "usage: countCells.pl <filename>";

my $cellCount1=-1;
my $cellCount2=-1;
my $wellName=-1;

open(F,"<$file") || die "file $file not found";
my $header=<F>;
chomp $header;
my @a=split ',',$header;
for (my $i=0;  $i<scalar(@a);  $i++) {
  $cellCount1=$i if ($a[$i] eq "Total_Cells_Micronuclei");
  $cellCount2=$i if ($a[$i] eq "Total_Cells_MultiWaveScoring");
  $wellName=$i if ($a[$i] eq "WellName");
}
die "WellName, Total_Cells_Micronuclei, or Total_Cells_MultiWaveScoring not found in header" if ($wellName==-1 || $cellCount1==-1 || $cellCount2==-1);
while(<F>) {
  chomp;
  if (length($_)>1) {
  my @a=split ',';
  if (length($a[$cellCount1]) || length($a[$cellCount2])) {
#   print "".$a[$wellName]." ".$a[$cellCount1]." ".$a[$cellCount2]."\n";
    if ($a[$cellCount1]<$cutoff || $a[$cellCount2]<$cutoff) {
      $badWells{$a[$wellName]}='1';
    }
  }
  }
}
close(F);

#print Dumper(\%badWells);

open(F,"<$file") || die "file $file not found";
while(<F>) {
  my $input=$_;
  chomp;
  if (length($_)>1) {
  my @a=split ',';
  if (!exists $badWells{$a[$wellName]}) {
    print "$input";
  }
  }
}
close(F);


