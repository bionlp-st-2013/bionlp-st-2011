#!/usr/bin/perl -w
use strict;
use warnings;
use CGI;

my $wdir = './test-work';
system ("rm -r $wdir/*");
