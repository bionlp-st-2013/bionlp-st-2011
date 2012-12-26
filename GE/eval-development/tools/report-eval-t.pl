#!/usr/bin/perl -w
require 5.000;
use strict;
use warnings;
use HTML::Template;

my $evaluator   = '/data/home/genia/public_html/SharedTask/eval/tools/a2-evaluate.pl';
my $evaluator2  = '/data/home/genia/public_html/SharedTask/eval/tools/a2-evaluate-d.pl';
my $name        = 'Anonymous Team';
my $gdir        = './gold';
my $tfile       = '/data/home/genia/public_html/SharedTask/eval/tools/results-team.tmpl';

use Getopt::Std;
my  $opt_string = 'hg:n:t:';
our %opt;


getopts("$opt_string", \%opt) or &usage();
&usage() if $opt{h};
&usage() if $#ARGV < 0;
if ($opt{g}) {$gdir = $opt{g}; $gdir =~ s/\/$//}
if (!-d $gdir) {print STDERR "Cannot find gold directory: $gdir.\n"; exit}

if ($opt{n}) {$name = $opt{n}}

if ($opt{t}) {$tfile = $opt{t}}
unless (-f $tfile && -r $tfile) {print STDERR "Cannot open the template file: $tfile.\n"; exit}

if ($#ARGV <0) {&usage()}

my $sdir = $ARGV[0]; $sdir =~ s/\/$//;

my $task = '';
if (!opendir(SDIR, $sdir)) {print STDERR "Cannot open the source directory: $sdir.\n"; exit}
while (my $fname = readdir(SDIR)) {
    if (($fname =~ /^[1-9][0-9]+.a2.(t12?3?)$/) && ((length $task) < (length $1))) {$task = $1}
} # while
closedir(SDIR);
if (!$task) {print STDERR "Cannot find predicted a2 files."}


##evaluate

# for task 1
my $result1    = `$evaluator   -g $gdir $sdir/*.a2.t1`;
my $result1s   = `$evaluator  -sg $gdir $sdir/*.a2.t1`;
my $result1sp  = `$evaluator -psg $gdir $sdir/*.a2.t1`;
my $result1dp  = `$evaluator   -g $gdir $sdir/*.a2.t1d`;
my $result1dsp = `$evaluator  -sg $gdir $sdir/*.a2.t1d`;


#for task 2
my ($result2, $result2s, $result2sp, $result2dp, $result2dsp, $result2dsp2) = ('N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A');
if (($task eq 't12') || ($task eq 't123')) {
    $result2     = `$evaluator    -g $gdir $sdir/*.a2.t12`;
    $result2s    = `$evaluator   -sg $gdir $sdir/*.a2.t12`;
    $result2sp   = `$evaluator  -psg $gdir $sdir/*.a2.t12`;
    $result2dp   = `$evaluator    -g $gdir $sdir/*.a2.t12d`;
    $result2dsp  = `$evaluator   -sg $gdir $sdir/*.a2.t12d`;
    $result2dsp2 = `$evaluator2  -sg $gdir $sdir/*.a2.t12d`;
} # if


# for task 3
my ($result3, $result3s, $result3sp, $result3dp, $result3dsp) = ('N/A', 'N/A', 'N/A', 'N/A', 'N/A');
if (($task eq 't13') || ($task eq 't123')) {
    $result3    = `$evaluator   -g $gdir $sdir/*.a2.t13`;
    $result3s   = `$evaluator  -sg $gdir $sdir/*.a2.t13`;
    $result3sp  = `$evaluator -psg $gdir $sdir/*.a2.t13`;
    $result3dp  = `$evaluator   -g $gdir $sdir/*.a2.t13d`;
    $result3dsp = `$evaluator  -sg $gdir $sdir/*.a2.t13d`;
} # if


&PrintResult($result1, $result1s, $result1sp, $result1dp, $result1dsp,
	     $result2, $result2s, $result2sp, $result2dp, $result2dsp, $result2dsp2,
	     $result3, $result3s, $result3sp, $result3dp, $result3dsp);

exit;


sub PrintResult {
    my ($result1, $result1s, $result1sp, $result1ap, $result1asp,
	$result2, $result2s, $result2sp, $result2ap, $result2asp, $result2asp2,
	$result3, $result3s, $result3sp, $result3ap, $result3asp) = @_;

    print STDOUT << "EOF";
BioNLP'09 Shared Task Evaluation Results


[TASK 1]

Strict Matching

$result1


Approximate Span Matching

$result1s


Approximate Span Matching/Approximate Recursive Matching

$result1sp


Event Decomposition/Approximate Recursive Matching

$result1ap


Event Decomposition/Approximate Span Matching/Approximate Recursive Matching

$result1asp



[TASK 2]

Strict Matching

$result2


Approximate Span Matching

$result2s


Approximate Span Matching/Approximate Recursive Matching

$result2sp


Event Decomposition/Approximate Recursive Matching

$result2ap


Event Decomposition/Approximate Span Matching/Approximate Recursive Matching

$result2asp


Event Decomposition/Approximate Span Matching/Approximate Recursive Matching (detail)

$result2asp2


[TASK 3]

Strict Matching

$result3


Approximate Span Matching

$result3s


Approximate Span Matching/Approximate Recursive Matching

$result3sp


Event Decomposition/Approximate Recursive Matching

$result3ap


Event Decomposition/Approximate Span Matching/Approximate Recursive Matching

$result3asp

EOF

    exit;
} # PrintResult


sub usage {
    print STDERR << "EOF";

[report-eval] last updated by jdkim\@is.s.u-tokyo.ac.jp on 8 July 2009.


<DESCRIPTION>
It is a part of the BioNLP'09 Shared Task evaluation software.
It uses a2-evaluate.pl to evaluate the predicted a2 files in various evaluation modes.
The evaluation report is output to standard output as a html file.


<USAGE>
$0 [-$opt_string] source_dir

* source_dir has to be a directory containing files produced by 'prepare-eval.pl'.


<OPTIONS>
-h           this (help) message.
-g gold_dir  specifies the gold directory. (default = $gdir)
-n name      specifies the name of the team. (default = $name)
-t tmpl_file specifies the html template file. (default = $tfile)


EOF
      exit;
} # usage
