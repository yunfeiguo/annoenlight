#!/home/yunfeiguo/localperl/bin/perl

use strict;
use warnings;
use CGI qw/:standard/;
use CGI::Carp qw/fatalsToBrowser/;
use DBI;
use FindBin qw/$RealBin/;
use File::Spec;
use lib "$RealBin/../lib";
use Utils;
use Control;

BEGIN
{
    $ENV{PERL5LIB}=($ENV{PERL5LIB} ? $ENV{PERL5LIB}:"")."/home/yunfeiguo/localperl/lib/5.18.1:/home/yunfeiguo/localperl/lib/site_perl/5.18.1";
}

chdir File::Spec->catdir($RealBin,"..") or &Utils::error ("Cannot enter installation directory\n"); #go to installation dir for safety

my %server_conf=&Utils::readServConf(File::Spec->catfile($RealBin,"../conf/enlight_server.conf"))
    or &Utils::error ("Reading server configuration file failed!\n");

my $EXAMPLE_LOC="example/exampleinput.txt";
my $EXAMPLE_NAME="exampleinput.txt";
$CGI::POST_MAX = 1024 * 1024 * ($server_conf{'maxupload'}||200);
#all paths should be FULL path
my $log=$server_conf{'serverlog'} || File::Spec->catfile($RealBin,"..","serverlog");
my $admin_email=$server_conf{'admin'} || &Utils::error("No administrator email\n",$log);
my $upload_dir=$server_conf{'tmp'} || "/tmp";
my $dbname=$server_conf{'dbname'} || &Utils::error("No MySQL database name\n",$log,$admin_email);
my $dbuser=$server_conf{'dbuser'} || &Utils::error("No MySQL database user\n",$log,$admin_email);
my $dbpassword=$server_conf{'dbpassword'} || &Utils::error("No MySQL database password\n",$log,$admin_email);
my $generic_table_max=$server_conf{'generic_table_max'} || 20;
#my $private_key=$server_conf{'private_key'} || &Utils::error("No RECAPTCHA private key\n",$log,$admin_email);
my $lz_exe=$server_conf{'locuszoom_exe'} || &Utils::error("No locuszoom executable path\n",$log,$admin_email);
my $anno_dir=$server_conf{'annovar_dir'} || &Utils::error("No ANNOVAR database directory\n",$log,$admin_email);
my $anno_exedir=$server_conf{'annovar_bin'} || &Utils::error("No ANNOVAR executable directory\n",$log,$admin_email);
my $interchr_resolution=$server_conf{'interchr_resolution'} || &Utils::error("no interchr_resolution\n",$log,$admin_email);
my $intrachr_resolution=$server_conf{'intrachr_resolution'} || &Utils::error("no intrachr_resolution\n",$log,$admin_email);
my $interchr_template=$server_conf{'interchr_template'} || &Utils::error("no interchr_template\n",$log,$admin_email);
my $intrachr_template=$server_conf{'intrachr_template'} || &Utils::error("no intrachr_template\n",$log,$admin_email);
my $python_dir=$server_conf{'python_bin'};
my $anno_exe=File::Spec->catfile($RealBin,"..","bin","table_annovar.pl"); #customized version of table_annovar.pl

#use this value with 'region_methodINT' (INT is the index from 0 to 8) to get all region_methods (snp, gene, ...)
#also when single region is specified, 'region_method' is used
my $num_manual_select=$server_conf{'num_manual_region_select'} || &Utils::error("No predefined number of manually specified regions\n",$log,$admin_email);

#read database file settings
my $hg19db=$server_conf{'hg19db'} || &Utils::error("No hg19 database\n",$log,$admin_email);
my $hg18db=$server_conf{'hg18db'} || &Utils::error("No hg18 database\n",$log,$admin_email);
my $hg19mindb=$server_conf{'hg19mindb'} || &Utils::error("No hg19 min database\n",$log,$admin_email);
my $hg18mindb=$server_conf{'hg18mindb'} || &Utils::error("No hg18 min database\n",$log,$admin_email);
my $hg19rs=$server_conf{'hg19rs'} || &Utils::error("No hg19 rsID database\n",$log,$admin_email);
my $hg18rs=$server_conf{'hg18rs'} || &Utils::error("No hg18 rsID database\n",$log,$admin_email);
my $hmmLegend=$server_conf{'hmmLegend'} || &Utils::error("No chromHMM legend\n",$log,$admin_email);

$ENV{PATH}="$anno_exedir:$ENV{PATH}";
$ENV{PATH}="$python_dir:$ENV{PATH}" if $python_dir;

my $time=`date +%H:%M:%S`;
chomp $time;
my $date=`date +%m/%d/%Y`;
chomp $date;

my $hitspec="/home/yunfeiguo/enlight/2015Feb_grant/128_GWAS_loci_schizophrenia_allrsID.histspec.txt";
my $cgi_template = "/home/yunfeiguo/enlight/2015Feb_grant/cgidata";
#my $output_dir_file = "/home/yunfeiguo/enlight/2015Feb_grant/output_dir.txt";
my $processed_var_count = 0;
open VAR,'<',$hitspec or die;
while(<VAR>)
{
    next if $.==1; #skip header
    next unless /^(rs\d+)/;
    next if $.<=52;
#read rsID list
    my $rsID = $1;
#modify CGI template
    my $private_cgi_copy = "/tmp/$rsID.cgidata";
    !system("perl -pe 's/index_variant\$/$rsID/;' $cgi_template > $private_cgi_copy &") or die "$!\n";

    sleep 600 if $. % 8 == 0;

#run analysis
    !system("/home/yunfeiguo/enlight/cgi-bin/base_process.cgi $private_cgi_copy") or die "$!";
    $processed_var_count++;
}
#warn "NOTICE: output dir list written to $output_dir_file\n";
warn "NOTICE: processed $processed_var_count variants\n";