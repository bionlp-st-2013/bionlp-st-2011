#!/usr/bin/perl -w
use strict;
use warnings;
use CGI;
use HTML::Template;

my $password = 'calmodulin';
my $ufile    = "../../registration/list-members.lst";
my $logfile  = 'submit.log';
my $errfile  = 'error.log';
my $timefile = 'time.log';
my $access_limit = 24;
my $listfile = 'files.lst';
my $sfile    = 'submission.tar.gz';
my $gdir     = 'gold';
my $wdir     = 'work';
my $cdir     = 'collect';

my $checker     = "../tools/a2-normalize.pl -u -g $gdir";
my $decomposer  = "../tools/a2-decompose.pl";
my $evaluator   = "../tools/a2-evaluate.pl -g $gdir";
my $devaluator  = "../tools/a2d-evaluate.pl -g $gdir";

my %userlist = ();
open (FILE, $ufile) or die "cannot open $ufile";
while (<FILE>){
    chomp;
    my $email = (split /\t/)[2];
    $userlist{$email} = 1;
}
close (FILE);


my $query   = new CGI;
my $email   = $query->param('email');
my $pass    = $query->param('password');
my $fname   = $query->param('file');

## check input fields
if (!$userlist{$email})    {&PrintMessage("Your E-mail address is not registered.")}
if ($pass ne $password)    {&PrintMessage("Please enter the correct password.")}
if ($fname !~ /\.tar.gz$/) {&PrintMessage("We only accept submission of a *.tar.gz file containing *.a2 files.")}


&logging($email, "access."); 

#if ($verbose eq 'on') {$evaluator .= ' -v'}

## prepare working directory
$wdir .= '/' . $email;

umask 0000;
mkdir($wdir, 0777) || &PrintMessage("Your previous submission is still being processed. Please retry after a moment.");

## prepare files to be tested
my ($buf, $file) = ('', '');
my $fh = $query->upload('file');
while (read($fh, $buf, 1024)) {$file .= $buf}

if (!open (FILE, '>' . $wdir . '/'. $sfile)) {
    system ("rm -r $wdir");
    &logging($email, "failed to open the working file.");
    &PrintMessage("Failed to open the working file. Please try again.")
} # if
print FILE $file;
close (FILE);

my $cmd = "/bin/tar -xzf $wdir/$sfile -C $wdir";
my $errmsg = `$cmd 2>&1`;
if ($errmsg) {
    sleep 2;
    $errmsg = `$cmd 2>&1`;
} # if

if ($errmsg) {
    system ("rm -r $wdir");
    &logging ($email, "failed to unpack:\n$errmsg\n" . `which tar`);
    &PrintMessage("Failed to unpack. Please check your tar.gz file and try again.");
} # if


my %target = ();
open (FILE, '<' . $listfile) ;
while (<FILE>) {chomp; $target{"$_.a2"} = 1}
close (FILE);

my @missingfile = ();
foreach (keys %target) {
    if (! -e "$wdir/$_") {push @missingfile, $_}
} # foreach

if (@missingfile) {
    system ("rm -r $wdir");
    @missingfile = sort @missingfile;
    &logging ($email, $#missingfile+1 . " missing files.");
    &PrintMessage("Your submission is missing the following file(s):<ul><li>" . join ("</li><li>", @missingfile) . "</li></ul>");
} # if

my @wrongfile = ();
opendir(WDIR, $wdir);
while (my $fname = readdir(WDIR)) {
    if (($fname eq '.') || ($fname eq '..') || ($fname eq $sfile)) {next}
    if (!$target{$fname}) {push @wrongfile, $fname}
} # while
closedir(WDIR);
 
#if (@wrongfile) {
#    system ("rm -r $wdir");
#    &logging ($email, $#wrongfile+1 . " unexpected files.");
#    &PrintMessage("Your submission includes the following unexpected file(s):<ul><li>" . join ("</li><li>", @wrongfile) . "</li></ul>");
#} # if


system ("/usr/bin/chmod -R 777 $wdir");

## check format of the files
$cmd = "$checker $wdir/*.a2 2>&1";
$errmsg = `$cmd`;

if ($errmsg) {
    system ("rm -r $wdir");
    $errmsg =~ s/$wdir\///g;
    &logging ($email, "format error detected.\n");
    &errlog  ($email, "format error detected:\n$errmsg\n");
    &PrintMessage("The following problem(s) were detected in your submission:<br/><pre>$errmsg</pre>");
} # if


## check last submission
my %last_sub = ();
open (SFILE, $timefile) or &PrintMessage ("cannot open time file.");
while (<SFILE>) {chomp; my ($user, $last) = split "\t"; $last_sub{$user} = $last}
close (SFILE);

my $now = time;
if ($last_sub{$email}) {
    my $r_seconds = ($access_limit * 3600) - ($now - $last_sub{$email});
    if ($r_seconds > 0) {
	system ("rm -r $wdir");
        &PrintMessage ("Your submission has passed format checking without problem.<br>The test set online evaluation is available only once per $access_limit hours for each.<br/>It will next be available for you in " . (int ($r_seconds / 3600) + 1) . " hours.");
    } # if
} # if


# decompose events

$cmd = "$decomposer $wdir/*.a2 2>&1";
$errmsg = `$cmd`;
# skip error checking

## case collection
#my ($sec, $min, $hour, $day, $mon) = (localtime)[0 .. 4]; $mon++;
#my $ctime = "$mon-$day-$hour-$min-$sec";
#$cmd = "cp $wdir/$sfile $cdir/$email-$ctime.tar.gz";
#$errmsg = `$cmd`;



## update the last submission log file
$last_sub{$email} = $now;
open (SFILE, ">", $timefile) or &PrintMessage ("cannot open $timefile for update.");
flock(LOGFILE, 2);
foreach (keys %last_sub) {print SFILE "$_\t$last_sub{$_}\n"}
flock(LOGFILE, 8);
close (SFILE);


## evaluate (whole)

# for task 1
my $result1     = `$evaluator  -t1     $wdir/*.a2`;
my $result1sp   = `$evaluator  -t1 -ps $wdir/*.a2`;
my $result1Sp   = `$evaluator  -t1 -pS $wdir/*.a2`;
my $result1spd  = `$devaluator -t1 -ps $wdir/*.a2d`;
my $result1Spd  = `$devaluator -t1 -pS $wdir/*.a2d`;

# for task 2
my $result2d    = `$devaluator -t2     $wdir/*.a2d`;
my $result2spd  = `$devaluator -t2 -ps $wdir/*.a2d`;
my $result2Spd  = `$devaluator -t2 -pS $wdir/*.a2d`;


# for task 3
my $result3    = `$evaluator -t3      $wdir/*.a2`;
my $result3sp  = `$evaluator -t3  -ps $wdir/*.a2`;
my $result3Sp  = `$evaluator -t3  -pS $wdir/*.a2`;


## evaluate (abstracts)

# for task 1
my $aresult1     = `$evaluator  -t1     $wdir/PMID-*.a2`;
my $aresult1sp   = `$evaluator  -t1 -ps $wdir/PMID-*.a2`;
my $aresult1Sp   = `$evaluator  -t1 -pS $wdir/PMID-*.a2`;
my $aresult1spd  = `$devaluator -t1 -ps $wdir/PMID-*.a2d`;
my $aresult1Spd  = `$devaluator -t1 -pS $wdir/PMID-*.a2d`;

# for task 2
my $aresult2d    = `$devaluator -t2     $wdir/PMID-*.a2d`;
my $aresult2spd  = `$devaluator -t2 -ps $wdir/PMID-*.a2d`;
my $aresult2Spd  = `$devaluator -t2 -pS $wdir/PMID-*.a2d`;


# for task 3
my $aresult3    = `$evaluator -t3      $wdir/PMID-*.a2`;
my $aresult3sp  = `$evaluator -t3  -ps $wdir/PMID-*.a2`;
my $aresult3Sp  = `$evaluator -t3  -pS $wdir/PMID-*.a2`;


## evaluate (full papers)

# for task 1
my $fresult1     = `$evaluator  -t1     $wdir/PMC-*.a2`;
my $fresult1sp   = `$evaluator  -t1 -ps $wdir/PMC-*.a2`;
my $fresult1Sp   = `$evaluator  -t1 -pS $wdir/PMC-*.a2`;
my $fresult1spd  = `$devaluator -t1 -ps $wdir/PMC-*.a2d`;
my $fresult1Spd  = `$devaluator -t1 -pS $wdir/PMC-*.a2d`;

# for task 2
my $fresult2d    = `$devaluator -t2     $wdir/PMC-*.a2d`;
my $fresult2spd  = `$devaluator -t2 -ps $wdir/PMC-*.a2d`;
my $fresult2Spd  = `$devaluator -t2 -pS $wdir/PMC-*.a2d`;


# for task 3
my $fresult3    = `$evaluator -t3      $wdir/PMC-*.a2`;
my $fresult3sp  = `$evaluator -t3  -ps $wdir/PMC-*.a2`;
my $fresult3Sp  = `$evaluator -t3  -pS $wdir/PMC-*.a2`;



system ("rm -r $wdir");

my $logmsg = "got evaluation results\n##### TASK 1\n[approx span/recursive]\n$result1sp\n##### TASK 2\n[approx span/recursive/decompose]\n$result2spd\
\n##### TASK 3\n[approx span/recursive]\n$result3sp\n\n";

my @logmsg = split /\n/, $logmsg;
$logmsg = join "\n", grep {!/^\[F[PN]]  /} @logmsg;


&logging ($email, $logmsg . "\n");

&PrintResult(
    $result1,  $result1sp,  $result1Sp, $result1spd, $result1Spd,
    $result2d, $result2spd, $result2Spd,
    $result3,  $result3sp,  $result3Sp,
    $aresult1,  $aresult1sp,  $aresult1Sp, $aresult1spd, $aresult1Spd,
    $aresult2d, $aresult2spd, $aresult2Spd,
    $aresult3,  $aresult3sp,  $aresult3Sp,
    $fresult1,  $fresult1sp,  $fresult1Sp, $fresult1spd, $fresult1Spd,
    $fresult2d, $fresult2spd, $fresult2Spd,
    $fresult3,  $fresult3sp,  $fresult3Sp,
    );



sub logging {
    my ($email, $event) = @_;
    open (LOGFILE, ">> $logfile") ;
    flock(LOGFILE, 2);
    seek(LOGFILE, 0, 2);
    my $datetime = localtime;
    print LOGFILE "[$datetime / $email] $event\n" ;
    flock(LOGFILE, 8);
    close (LOGFILE);
} # logging


sub errlog {
    my ($email, $event) = @_;
    open (LOGFILE, ">> $errfile") ;
    flock(LOGFILE, 2);
    seek(LOGFILE, 0, 2);
    my $datetime = localtime;
    print LOGFILE "[$datetime / $email] $event\n" ;
    flock(LOGFILE, 8);
    close (LOGFILE);
} # errlog


sub PrintMessage {
    my ($msg) = shift;
    my $template = HTML::Template->new(filename => 'message.tmpl');

    $template->param(MSG => $msg);
    print "Content-Type: text/html\n\n", $template->output;
    exit;
} # PrintMessage


sub PrintResult {
    my (
	$result1,  $result1sp,  $result1Sp, $result1spd, $result1Spd,
	$result2d, $result2spd, $result2Spd,
	$result3,  $result3sp,  $result3Sp,
	$aresult1,  $aresult1sp,  $aresult1Sp, $aresult1spd, $aresult1Spd,
	$aresult2d, $aresult2spd, $aresult2Spd,
	$aresult3,  $aresult3sp,  $aresult3Sp,
	$fresult1,  $fresult1sp,  $fresult1Sp, $fresult1spd, $fresult1Spd,
	$fresult2d, $fresult2spd, $fresult2Spd,
	$fresult3,  $fresult3sp,  $fresult3Sp,
	) = @_;

    my $template = HTML::Template->new(filename => 'result.tmpl');

    $template->param(
                     RESULT1  => $result1,  RESULT1SP   => $result1sp,  RESULT1ZP  => $result1Sp,  RESULT1SPD => $result1spd, RESULT1ZPD => $result1Spd,
                     RESULT2D => $result2d, RESULT2SPD  => $result2spd, RESULT2ZPD => $result2Spd,
                     RESULT3  => $result3,  RESULT3SP   => $result3sp,  RESULT3ZP  => $result3Sp,
                     ARESULT1  => $aresult1,  ARESULT1SP   => $aresult1sp,  ARESULT1ZP  => $aresult1Sp,  ARESULT1SPD => $aresult1spd, ARESULT1ZPD => $aresult1Spd,
                     ARESULT2D => $aresult2d, ARESULT2SPD  => $aresult2spd, ARESULT2ZPD => $aresult2Spd,
                     ARESULT3  => $aresult3,  ARESULT3SP   => $aresult3sp,  ARESULT3ZP  => $aresult3Sp,
                     FRESULT1  => $fresult1,  FRESULT1SP   => $fresult1sp,  FRESULT1ZP  => $fresult1Sp,  FRESULT1SPD => $fresult1spd, FRESULT1ZPD => $fresult1Spd,
                     FRESULT2D => $fresult2d, FRESULT2SPD  => $fresult2spd, FRESULT2ZPD => $fresult2Spd,
                     FRESULT3  => $fresult3,  FRESULT3SP   => $fresult3sp,  FRESULT3ZP  => $fresult3Sp,
		     );
    print "Content-Type: text/html\n\n", $template->output;
    exit;
} # PrintResult 
