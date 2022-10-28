#!/usr/bin/perl

use strict;
use warnings;

use Data::Dumper;

my $file=shift || die "usage: countRows.pl <filename>";

open(F,"<$file") || die "file $file not found";

my @count;
while(<F>) {
  chomp;
  my @a=split ',';
  for (my $i=0;  $i<scalar(@a);  $i++) {
    $count[$i]++ if (length ($a[$i])>0);
  }
}
close(F);

#print Dumper(\@count);

open(F,"<$file") || die "file $file not found";
while(<F>) {
  chomp;
  my @a=split ',';
  if (scalar(@a)>10) {
  for (my $i=0;  $i<scalar(@a);  $i++) {
    print "$a[$i]," if ($count[$i]>1600);   # should be 384*4+1
  }
  print "\n";
  }
}
close(F);


