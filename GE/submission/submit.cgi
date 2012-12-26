#!/usr/bin/perl -w
use strict;
use warnings;
use CGI;
use HTML::Template;

my $password = 'calmodulin';
my $ufile    = "../../registration/list-members.lst";
my $logfile  = 'submit.log';
my $errfile  = 'error.log';
my $listfile = 'files.lst';
my $sfile    = 'submission.tar.gz';
my $qfile    = 'questionnaire.txt';
my $gdir     = 'gold';
my $wdir     = 'work';
my $cdir     = 'collect';

my $checker   = "../eval/tools/a2-normalize.pl -u -g $gdir";

my $query       = new CGI;
my $name        = $query->param('name');
my $affiliation = $query->param('affiliation');
my $email       = $query->param('email');
my $pass        = $query->param('password');
my $task        = $query->param('task');
my $rfile       = $query->param('rfile');

my %userlist;
open (FILE, $ufile) or die "cannot open $ufile";
while (<FILE>){
    chomp;
    my $email = (split /\t/)[2];
    $userlist{$email} = 1;
}
close (FILE);

## check input fields
if (!$name)                {&PrintMessage("Please enter your name.")}
if (!$affiliation)         {&PrintMessage("Please enter your affiliation.")}
if (!$userlist{$email})    {&PrintMessage("Your E-mail address is not registered.")}
if ($pass ne $password)    {&PrintMessage("Please enter the correct password.")}
if ($rfile !~ /\.tar.gz$/) {&PrintMessage("We accept submission of a *.tar.gz file containing the all *.a2 files.")}

&logging($email, "access with task: GE."); 

## prepare working directory
$wdir .= '/' . $email;

umask 0000;
mkdir($wdir, 0777) || &PrintMessage("Your previous submission is still being processed. Please wait and retry.");

## prepare files to be tested
my ($buf, $file) = ('', '');
my $fh = $query->upload('rfile');
while (read($fh, $buf, 1024)) {$file .= $buf}

if (!open (FILE, '>' . $wdir . '/'. $sfile)) {
    system ("rm -r $wdir");
    &logging($email, "failed to open the working file.\n");
    &PrintMessage("Failed to open a working file. Please try again.")
} # if
print FILE $file;
close (FILE);

my $cmd = "/bin/tar -C $wdir -xzf $wdir/$sfile";
my $errmsg = `$cmd 2>&1`;
if ($errmsg) {
    sleep 2;
    $errmsg = `$cmd 2>&1`;
} # if

if ($errmsg) {
    system ("rm -r $wdir");
    &logging ($email, "failed to unpack:\n$errmsg\n");
    &PrintMessage("Failed to unpack. Please check your tar.gz file and try again.");
} # if

open (FILE, '<' . $listfile) ;
my @pmid = <FILE>; chomp (@pmid);
close (FILE);

my @missingfile = ();
if (! -e "$wdir/$qfile") {push @missingfile, $qfile}

foreach (@pmid) {
    my $rfile = "$_.a2";
    if (! -e "$wdir/$rfile") {push @missingfile, $rfile}
} # foreach


if (@missingfile) {
    system ("rm -r $wdir");
    &logging ($email, $#missingfile+1 . " missing files.\n");
    &PrintMessage("Your submission is missing the following file(s):<ul><li>" . join ("</li><li>", @missingfile) . "</li></ul>");
} # if

system ("/usr/bin/chmod -R 777 $wdir");
system ("/usr/bin/dos2unix $wdir/*.a2");

# check format of the files
$cmd = "$checker $wdir/*.a2 2>&1";
$errmsg = `$cmd`;
if ($errmsg) {
    system ("rm -r $wdir");
    $errmsg =~ s/$wdir\///g;
    &logging ($email, "format error detected.\n");
    &errlog  ($email, "format error detected.\n$errmsg\n");
    &PrintMessage("Following formatting problem(s) detected in your submission:<br/><pre>$errmsg</pre>");
} # if


# case collection
my ($sec, $min, $hour, $day, $mon) = (localtime)[0 .. 4]; $mon++;
my $ctime = "$mon-$day-$hour-$min-$sec";
$cmd = "cp $wdir/$sfile $cdir/$email-$task-$ctime.tar.gz";
$errmsg = `$cmd`;
system ("rm -r $wdir");


&logging ($email, "submission accepted.\n");
&PrintMessage("<h3>Your submission is accepted without problem.<br/>Thank you for your participation!</h3>");


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
