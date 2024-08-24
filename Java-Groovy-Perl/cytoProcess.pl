#!/usr/bin/perl

use strict;
use warnings;

use Data::Dumper;

my $semaphore="cytoProcess.lock";

sub mylog($) {
  my $s=shift;
  print STDERR $s;
}


if (open(F,"<$semaphore")) {
  my $pid=<F>;
  close(F);
  chomp $pid;
  my $count=`ps -ef | grep $pid | grep -v grep | wc -l`;
  exit if ($count>0);
}
open F,">$semaphore";
print F "$$\n";
close F;


my @files = </home/halo384/cyto/CytoRunContents*>;
@files=sort @files;
my $newRunContents=$files[-1];

# check to see if any of the platemaps have been updated in the upload folder
# if so removed the processed files so they'll be reprocessed below
@files = </home/halo384/cyto/CytoPlateMaps/*csv>;
for (my $i=0;  $i<scalar(@files);  $i++) {
  my $f1=$files[$i];
  my $f2=$files[$i];
  $f2=~s|.+/||;
  $f2="PlateMaps/".$f2;
  my $t1=(stat $f1)[9];
  my $t2=0;
#print "$f1 $f2\n";
  $t2=(stat $f2)[9] if (-e $f2);
  if ($t1>$t2) {
    my $t=$files[$i];
    $t=~s|.+/||;
    $t=~s|\.csv$||;
#print "$f1 $f2 $t\n";
#print "$t1 $t2\n"; 
    my $s=`grep $t $newRunContents`;
    my @s=split '\n',$s;
#print Dumper(\@s);
    foreach my $t (@s) {
#    print "$t\n";
     my @a=split ',',$t;
     mylog "removing $a[1].histdiff.csv\n";
     unlink("$a[1].histdiff.csv");
    }
  }
}

#print "$newRunContents\n";

# check to see if any new or updated zip files have been uploaded
@files = </home/halo384/cyto/*.zip>;
for (my $i=0;  $i<scalar(@files);  $i++) {
  my $f1=$files[$i];
  $f1=~s/.zip//;
  $f1=~s|.+/||;
  my $f2=$files[$i];
  $f2=~s/.zip/.histdiff.csv/;
  $f2=~s|.+/||;
  my $t1=(stat $files[$i])[9];
  my $t2=0;
  $t2=(stat $f2)[9] if (-e $f2);
  my $s=`grep $f1 $newRunContents`;
  chomp $s;
  my $size=0;
  $size= -s $f2 if (-e $f2);
  if (($t1>$t2 || $size==0) && length($s)) {
    my @b=split ',',$s;
    mylog "./flip -u /home/halo384/cyto/CytoPlateMaps/$b[2].csv\n";
    `./flip -u /home/halo384/cyto/CytoPlateMaps/$b[2].csv`;
    mylog "./fixPlateMap.pl /home/halo384/cyto/CytoPlateMaps/$b[2].csv >PlateMaps/$b[2].csv\n";
    `./fixPlateMap.pl /home/halo384/cyto/CytoPlateMaps/$b[2].csv >PlateMaps/$b[2].csv`;
    mylog "./fixZip.pl $f1\n";
    `./fixZip.pl $f1`;
    mylog "./runCommand.pl $newRunContents $f1\n";
    `./runCommand.pl $newRunContents $f1`;
  }
}

my $lastRunContents="";

if (open(F,"<lastRunContents.txt")) {
  $lastRunContents=<F>;
  chomp $lastRunContents;
  close(F);
} else {
  $lastRunContents='/dev/null';
}

if ($newRunContents eq $lastRunContents) {
# mylog "nothing to do\n";
} else {

`./flip -u $newRunContents`;

`cp -p $newRunContents ./runcontents.csv`;
`cp -p $newRunContents ../cyto_output/runcontents.csv`;
`touch /var/www/html/cyto/runcontents.csv`;
`rm -f /var/www/html/cyto/runcontents.csv`;
`cp -p $newRunContents /var/www/html/cyto/runcontents.csv`;


my $a=`diff $lastRunContents $newRunContents | grep ">"`;

$a=~s/> //g;

my @a=split '\n',$a;
for (my $i=0;  $i<scalar(@a);  $i++) {
  my @b=split ',',$a[$i];
  mylog "$b[1] $b[2]\n";
  mylog "./flip -u /home/halo384/cyto/CytoPlateMaps/$b[2].csv\n";
  `./flip -u /home/halo384/cyto/CytoPlateMaps/$b[2].csv`;
  mylog "./fixPlateMap.pl /home/halo384/cyto/CytoPlateMaps/$b[2].csv >PlateMaps/$b[2].csv\n";
  `./fixPlateMap.pl /home/halo384/cyto/CytoPlateMaps/$b[2].csv >PlateMaps/$b[2].csv`;
  mylog "./fixZip.pl $b[1]\n";
  `./fixZip.pl $b[1]`;
  mylog "./runCommand.pl $newRunContents $b[1]\n";
  `./runCommand.pl $newRunContents $b[1]`;
}


open(F,">lastRunContents.txt");
print F "$newRunContents\n";
close(F);
}

unlink($semaphore);

