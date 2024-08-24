#!/usr/bin/perl

use strict;
use warnings;

use Data::Dumper;

my %synonyms=(
  "UCSC CSC Plate ID" => "Plate Map",
  "UCSC CSC PlateID" => "Plate Map",
  "Plate Name" => "Plate Map",
  "PlateName" => "Plate Map",
  "384 well" => "Well",
  "384 well position" => "Well",
  "Well Name" => "Well",
  "Molecule Name" => "MoleculeID",
  "Molecule ID" => "MoleculeID",
  "ID Number" => "MoleculeID",
  "Molarity" => "Concentration",
  "Molarity (mM)" => "Concentration",
  "Stock Concentration" => "Concentration",
  "Stock_Concentration" => "Concentration",
  "Stock concentration" => "Concentration",
  "Stock_concentration" => "Concentration",
  "UCSC_CSC_Plate_ID" => "Plate Map",
  "UCSC_CSC_PlateID" => "Plate Map",
  "Plate_Name" => "Plate Map",
  "PlateName" => "Plate Map",
  "384_well" => "Well",
  "384_well_position" => "Well",
  "Well_Name" => "Well",
  "Molecule_Name" => "MoleculeID",
  "Molecule_ID" => "MoleculeID",
  "ID_Number" => "MoleculeID",
  #"Molarity" => "Concentration",
  "Molarity_(mM)" => "Concentration"
);


my $header=<>;
chomp $header;
#print "$header\n";
$header=~s/\(.+?\)//g;
$header=~s/, /,/g;
$header=~s/ ,/,/g;
$header=~s/ $//g;
$header=~s/^ //g;
foreach my $i (reverse sort keys %synonyms) {
  $header=~s/$i/$synonyms{$i}/ig;
}
$header=~s/,+$//;
print "$header\n";

my %header;
my @a=split ',', $header;
for (my $i=0;  $i<scalar(@a);  $i++) {
  $header{$a[$i]}=$i;
}
#print Dumper(\%header);

foreach my $i (sort keys %synonyms) {
  (exists $header{$synonyms{$i}}) || die "\n\n$synonyms{$i} column not found: $header";
}

my $nameColumn=$header{"MoleculeID"};

while(<>) {
  chomp;
  my @a=split ',';
#print Dumper(\@a);
  if ($a[$nameColumn] && length($a[$nameColumn])>0) {
    s/,+$//;
    print "$_\n";
  }
}



