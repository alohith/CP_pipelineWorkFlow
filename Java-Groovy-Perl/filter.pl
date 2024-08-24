#!/usr/bin/perl

use strict;
use warnings;

my $header=<>;
chomp $header;
print "$header\n";

#Cell_ID,Series_ID,Site_ID,WellName
#"1158_1261924_1262155_116",1262155,1261924,"A01"
#"1158_1.26192e+006_1.26215e+006_0",1262154,1261923,"A01"

my $cell_ID_column=-1;
my $series_ID_column=-1;
my $site_ID_column=-1;

my @a=split ',',$header;
for (my $i=0;  $i<scalar(@a);  $i++) {
  $cell_ID_column=$i if ($a[$i] eq "Cell_ID");
  $series_ID_column=$i if ($a[$i] eq "Series_ID");
  $site_ID_column=$i if ($a[$i] eq "Site_ID");
}

#print STDERR "$cell_ID_column $series_ID_column $site_ID_column\n";

while(<>) {
  chomp;
  my $l=$_;
  if (length($l)>1) {
    $l=~s/"\d.."//g;
    $l=~s/""//g;
    my @a=split ',',$l;
    my $a=$a[$cell_ID_column];
    if ($a =~ m/e/) {
      $a =~ s/"//g;
      $a =~ s/\+/\\\+/g;
      my @b=split '_',$a;
      my $c=$b[0]."_".$a[$site_ID_column]."_".$a[$series_ID_column]."_".$b[3];
#     print STDERR "$a[$cell_ID_column] $c\n";
#print STDERR "$l\n";
#print STDERR "$a $c\n";
      $l =~ s/$a/$c/;
#print STDERR "$l\n";
#exit;
    }
    print "$l\n";
  }
}


