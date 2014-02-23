#!/usr/bin/perl
#
# This code is distributed under the terms of the GPL
#
# (c) 2013,2014 umberto.miceli http://joeyramone76.altervista.org
#
# $Id: advproxylog.cgi,v 1.0.1 2014/02/23 00:00:00 umberto.miceli Exp $
#

# Add entry in menu
# MENUENTRY logs 032 "Advanced Proxy Logs" "advproxylog proxy log"  haveProxy
#
# Make sure translation exists $Lang::tr{'advproxylog proxy log'}

use strict;

# enable only the following on debugging purpose
# use warnings;
# use CGI::Carp 'fatalsToBrowser';
use IO::Socket;

require '/usr/lib/ipcop/general-functions.pl';
require '/usr/lib/ipcop/lang.pl';
require '/usr/lib/ipcop/header.pl';

require '/var/ipcop/addons/advproxylog/advproxylog-lib.pl';

use POSIX();

my $version = `cat ${General::swroot}/addons/advproxylog/version`;
my $updflagfile = "${General::swroot}/addons/advproxylog/.up2date";
my $logdir = "${General::swroot}/addons/advproxylog/reports";


my %cgiparams    = ();
my %logsettings  = ();
my %ips          = ();
my %responsecodes = ();
my %selected     = ();
my %checked      = ();
my @log          = ();
my $errormessage = '';
my $hintcolour='#FFFFCC';

my $unique=time;

my @now  = localtime();
my $dow  = $now[6];          # day of week
my $doy  = $now[7];          # day of year (0..364)
my $tdoy = $now[7];
my $year = $now[5] + 1900;

my %columnsortedclass = ();

my %debug = ();
my $check4updatesresponse = &check4updates;
my $latest=substr($check4updatesresponse,0,length($version));

$cgiparams{'DAY'}           = $now[3];
$cgiparams{'MONTH'}         = $now[4];
$cgiparams{'SOURCE_IP'}     = 'ALL';
$cgiparams{'RESPONSE_CODE'}     = 'ALL';
$cgiparams{'FILTER'}        = "[.](gif|jpeg|jpg|png|css|js)\$";
$cgiparams{'ENABLE_FILTER'} = 'off';
$cgiparams{'INCLUDE_FILTER'}        = "";
$cgiparams{'ENABLE_INCLUDE_FILTER'} = 'off';
$cgiparams{'SORT_BY'}     = 'DATE';
$cgiparams{'ORDER'}     = 'ASC';
$cgiparams{'ACTION'}        = '';
$cgiparams{'FULL_URL'} = 'off';
$cgiparams{'MEASURES_RAW'} = 'off';

&General::getcgihash(\%cgiparams);
$logsettings{'LOGVIEW_REVERSE'}  = 'off';
$logsettings{'LOGVIEW_VIEWSIZE'} = 150;
&General::readhash('/var/ipcop/logging/settings', \%logsettings);

	

if ($cgiparams{'ACTION'} eq '') {
    my %save = ();
    &General::readhash('/var/ipcop/addons/advproxylog/viewersettings', \%save)  if (-e '/var/ipcop/addons/advproxylog/viewersettings');
    $cgiparams{'FILTER'}        = $save{'FILTER'}        if (exists($save{'FILTER'}));
    $cgiparams{'ENABLE_FILTER'} = $save{'ENABLE_FILTER'} if (exists($save{'ENABLE_FILTER'}));
	
	$cgiparams{'INCLUDE_FILTER'}        = $save{'INCLUDE_FILTER'}        if (exists($save{'INCLUDE_FILTER'}));
    $cgiparams{'ENABLE_INCLUDE_FILTER'} = $save{'ENABLE_INCLUDE_FILTER'} if (exists($save{'ENABLE_INCLUDE_FILTER'}));
	
	$cgiparams{'SORT_BY'} = $save{'SORT_BY'} if (exists($save{'SORT_BY'}));
	$cgiparams{'ORDER'} = $save{'ORDER'} if (exists($save{'ORDER'}));
	
	$cgiparams{'FULL_URL'} = $save{'FULL_URL'} if (exists($save{'FULL_URL'}));
	$cgiparams{'MEASURES_RAW'} = $save{'MEASURES_RAW'} if (exists($save{'MEASURES_RAW'}));
}

if ($cgiparams{'ACTION'} eq $Lang::tr{'restore defaults'}) {
    $cgiparams{'SOURCE_IP'}     = 'ALL';
	$cgiparams{'RESPONSE_CODE'}     = 'ALL';
    $cgiparams{'FILTER'}        = "[.](gif|jpeg|jpg|png|css|js)\$";
    $cgiparams{'ENABLE_FILTER'} = 'on';
	$cgiparams{'INCLUDE_FILTER'}        = "";
    $cgiparams{'ENABLE_INCLUDE_FILTER'} = 'off';
	$cgiparams{'SORT_BY'}     = 'DATE';
	$cgiparams{'ORDER'}     = 'ASC';
	$cgiparams{'FULL_URL'}     = 'off';
	$cgiparams{'MEASURES_RAW'}     = 'off';
	
	
}

if ($cgiparams{'ACTION'} eq $Lang::tr{'save'}) {
    my %save = ();
    $save{'FILTER'}        = $cgiparams{'FILTER'};
    $save{'ENABLE_FILTER'} = $cgiparams{'ENABLE_FILTER'};
	$save{'INCLUDE_FILTER'}        = $cgiparams{'INCLUDE_FILTER'};
    $save{'ENABLE_INCLUDE_FILTER'} = $cgiparams{'ENABLE_INCLUDE_FILTER'};
	$save{'SORT_BY'} = $cgiparams{'SORT_BY'};
	$save{'ORDER'} = $cgiparams{'ORDER'};
	$save{'FULL_URL'} = $cgiparams{'FULL_URL'};
	$save{'MEASURES_RAW'} = $cgiparams{'MEASURES_RAW'};;
	
    &General::writehash('/var/ipcop/addons/advproxylog/viewersettings', \%save);
}

#my $start = ($cgiparams{'ORDER'} eq 'DESC') ? 0x7FFFF000 : 0;    #index of first line number to display
my $start = 0;


my @temp_then = ();
if ($ENV{'QUERY_STRING'} && $cgiparams{'ACTION'} ne $Lang::tr{'update'}) {
    @temp_then = split(',', $ENV{'QUERY_STRING'});
    $start                  = $temp_then[0];
    $cgiparams{'MONTH'}     = $temp_then[1];
    $cgiparams{'DAY'}       = $temp_then[2];
    $cgiparams{'SOURCE_IP'} = $temp_then[3];
	$cgiparams{'RESPONSE_CODE'} = $temp_then[4];
	$cgiparams{'SORT_BY'} = $temp_then[5];
	$cgiparams{'ORDER'} = $temp_then[6];
	$cgiparams{'FULL_URL'} = $temp_then[7];
	$cgiparams{'ENABLE_FILTER'} = $temp_then[8];
	$cgiparams{'FILTER'} = $temp_then[9];
	$cgiparams{'ENABLE_INCLUDE_FILTER'} = $temp_then[10];
	$cgiparams{'INCLUDE_FILTER'} = $temp_then[11];
	

	
}

if (!($cgiparams{'MONTH'} =~ /^(0|1|2|3|4|5|6|7|8|9|10|11)$/)
    || !($cgiparams{'DAY'} =~
        /^(0|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31)$/))
{
    $cgiparams{'DAY'}   = $now[3];
    $cgiparams{'MONTH'} = $now[4];
}
elsif ($cgiparams{'ACTION'} eq '>>') {
    @temp_then = &General::calculatedate($year, $cgiparams{'MONTH'}, $cgiparams{'DAY'}, 1);
    $year               = $temp_then[5]+1900;
    $cgiparams{'MONTH'} = $temp_then[4];
    $cgiparams{'DAY'}   = $temp_then[3];
}
elsif ($cgiparams{'ACTION'} eq '<<') {
    @temp_then = &General::calculatedate($year, $cgiparams{'MONTH'}, $cgiparams{'DAY'}, -1);
    $year               = $temp_then[5]+1900;
    $cgiparams{'MONTH'} = $temp_then[4];
    $cgiparams{'DAY'}   = $temp_then[3];
}
else {
    @temp_then = &General::validatedate(0, $cgiparams{'MONTH'}, $cgiparams{'DAY'});
    $year               = $temp_then[5]+1900;
    $cgiparams{'MONTH'} = $temp_then[4];
    $cgiparams{'DAY'}   = $temp_then[3];
}

# Date to display 
my $date;
$date = sprintf("%d-%02d-%02d", $year, $cgiparams{'MONTH'}+1, $cgiparams{'DAY'});

my $filter    = $cgiparams{'ENABLE_FILTER'} eq 'on' ? $cgiparams{'FILTER'} : '';
my $enablefilter  = $cgiparams{'ENABLE_FILTER'} eq 'on' ? 1 : 0;
my $includefilter = $cgiparams{'ENABLE_INCLUDE_FILTER'} eq 'on' ? $cgiparams{'INCLUDE_FILTER'} : '';
my $enableincludefilter  = $cgiparams{'ENABLE_INCLUDE_FILTER'} eq 'on' ? 1 : 0;
my $fullurl = $cgiparams{'FULL_URL'} eq 'on' ? 1 : 0;
my $measuresraw = $cgiparams{'MEASURES_RAW'} eq 'on' ? 1 : 0;

my $sourceip  = $cgiparams{'SOURCE_IP'};
my $responsecode  = $cgiparams{'RESPONSE_CODE'};
my $sourceall = $cgiparams{'SOURCE_IP'} eq 'ALL' ? 1 : 0;
my $responseall = $cgiparams{'RESPONSE_CODE'} eq 'ALL' ? 1 : 0;
my $sortby = $cgiparams{'SORT_BY'};
my $order = $cgiparams{'ORDER'};
my $lastdatetime;    # for debug
my $lines    = 0;
my $temp     = ();
my $thiscode = '$temp =~ /$filter/;';
eval($thiscode);
if ($@ ne '') {
    $errormessage = "$Lang::tr{'bad ignore filter'}:.$@<P>";
    $filter       = '';
}
else {
    my $loop    = 1;
    my $filestr = 0;

    my $day_extension = ($cgiparams{'DAY'} == 0 ? 1: $cgiparams{'DAY'});

    while ($loop) {

        my $gzindex;
        if (($cgiparams{'MONTH'} eq $now[4]) && ($day_extension eq $now[3])) {
            $filestr = "/var/log/squid/access.log";
            $loop = 0;
        }
        else {
            $filestr = sprintf("/var/log/squid/access.log-%d%02d%02d", $year, $cgiparams{'MONTH'}+1, $day_extension);
            $filestr = "${filestr}.gz" if -f "${filestr}.gz";
        }
		
        # now read file if existing
        if (open(FILE, ($filestr =~ /.gz$/ ? "gzip -dc $filestr |" : $filestr))) {
			
			#open (TMPLOG,">>$logdir/advproxylog-$unique.log") or die "ERROR: Cannot write to $logdir/advproxylog-$unique.log\n";
            
			#&General::log("reading $filestr");
            my @temp_now = localtime(time);
            $temp_now[4] = $cgiparams{'MONTH'};
            $temp_now[3] = $cgiparams{'DAY'};
            if (   ($cgiparams{'MONTH'} eq $now[4]) && ($cgiparams{'DAY'} > $now[3])
                || ($cgiparams{'MONTH'} > $now[4]))
            {
                $temp_now[5]--;    # past year
            }

            $temp_now[2] = $temp_now[1] = $temp_now[0] = 0;    # start at 00:00:00
            $temp_now[3] = 1 if ($cgiparams{'DAY'} == 0);      # All days selected, start at '1'
            my $mintime = POSIX::mktime(@temp_now);
            my $maxtime;
            if ($cgiparams{'DAY'} == 0) {                      # full month
                if ($temp_now[4]++ == 12) {
                    $temp_now[4] = 0;
                    $temp_now[5]++;
                }
                $maxtime = POSIX::mktime(@temp_now);
            }
            else {
                $maxtime = $mintime + 86400;                   # full day
            }
        READ: while (<FILE>) {
                my ($datetime, $duration, $ip, $result, $size, $reqm, $url, $so) = split;
                $ips{$ip}++;
				$responsecodes{$result}++;
				
                # for debug
                $lastdatetime = $datetime;
				my $testpassed = 0;
                # collect lines between date && filter
                if (   (($datetime > $mintime) && ($datetime < $maxtime))
                    && ((!$enablefilter) || (($enablefilter) && !($url =~ /$filter/)))
                    && ((($ip eq $sourceip) || $sourceall))
					&& ((($url =~ /$includefilter/) || ($includefilter eq "")))
					)
					
                {
					$testpassed = 1;
					if ($responseall) {
						$testpassed = 1;
					
					} elsif (($responsecode eq "HIT" || $responsecode eq "MISS") 
						&& (($responsecode eq "HIT" && ($result =~  /(HIT|UNMODIFIED)/)) 
						|| ($responsecode eq "MISS" && ($result =~  /(MISS|_MODIFIED)/)))) {
						$testpassed = 1;
					} elsif (!($responsecode eq "HIT") && !($responsecode eq "MISS") && !($responseall) && ($result eq $responsecode)) {
						$testpassed = 1; 
					} else {
						$testpassed = 0;
					}
					
					if ($testpassed) {
						# when standart viewing, just keep in memory the correct slices
						# it starts a '$start' and size is $viewport
						# If export, then keep all lines...
						if ($cgiparams{'ACTION'} eq $Lang::tr{'export'}) {
							$log[ $lines++ ] = "$datetime $duration $ip $result $size $reqm $url $so";
						}
						else {
						    # print TMPLOG "$datetime $duration $ip $result $size $reqm $url $so\n";
							# if ($lines++ < ($start + $logsettings{'LOGVIEW_VIEWSIZE'})) {
							    $lines++;
								push(@log, "$datetime $duration $ip $result $size $reqm $url $so");
								# if (@log > $logsettings{'LOGVIEW_VIEWSIZE'}) {
								#	shift(@log);
								# }

								
							# }
						}
					}	
                }

                # finish loop when date of lines are past maxtime
                $loop = ($datetime < $maxtime);
            }
            close(FILE);
			#close (TMPLOG);
        }
        $day_extension++;
        if ($day_extension > 31) {
            $loop = 0;
        }
    }

}

if ($cgiparams{'ACTION'} eq $Lang::tr{'export'}) {
    print "Content-type: text/plain\n";
    print "Content-Disposition: attachment; filename=\"ipcop-advproxylog-$date.log\";\n";
    print "\n";
    print "IPCop Advanced Proxy log\r\n";
    print "$Lang::tr{'date'}: $date\r\n";
    print "Source IP: $cgiparams{'SOURCE_IP'}\r\n";
    if ($cgiparams{'ENABLE_FILTER'} eq 'on') {
        print "Ignore filter: $cgiparams{'FILTER'}\r\n";
    }
	if ($cgiparams{'ENABLE_INCLUDE_FILTER'} eq 'on') {
        print "Include filter: $cgiparams{'INCLUDE_FILTER'}\r\n";
    }
	print "Response Code Filter: $cgiparams{'RESPONSE_CODE'}\r\n";
	print "Sorted By: $cgiparams{'SORT_BY'}\r\n";
    print "\r\n";

    # Do not reverse log when exporting
    #if ($logsettings{'LOGVIEW_REVERSE'} eq 'on') { @log = reverse @log; }

    foreach $_ (@log) {
        my ($datetime, $ip, $duration, $result, $size, $reqm, $url, $so) = split;
        my ($SECdt, $MINdt, $HOURdt, $DAYdt, $MONTHdt, $YEARdt) = localtime($datetime);
        $SECdt  = sprintf("%.02d", $SECdt);
        $MINdt  = sprintf("%.02d", $MINdt);
        $HOURdt = sprintf("%.02d", $HOURdt);
        if ($cgiparams{'DAY'} == 0) {    # full month
            $DAYdt = sprintf("%.02d", $DAYdt);
            print "$DAYdt/$HOURdt:$MINdt:$SECdt $duration $ip $result $size $reqm $url $so\n";
        }
        else {
            print "$HOURdt:$MINdt:$SECdt $duration $ip $result $size $reqm $url $so\n";
        }
    }
    exit;
}

$selected{'SOURCE_IP'}{$cgiparams{'SOURCE_IP'}} = "selected='selected'";
$selected{'RESPONSE_CODE'}{$cgiparams{'RESPONSE_CODE'}} = "selected='selected'";
$checked{'ENABLE_FILTER'}{'off'}                       = '';
$checked{'ENABLE_FILTER'}{'on'}                        = '';
$checked{'ENABLE_FILTER'}{$cgiparams{'ENABLE_FILTER'}} = "checked='checked'";

$checked{'ENABLE_INCLUDE_FILTER'}{'off'}                       = '';
$checked{'ENABLE_INCLUDE_FILTER'}{'on'}                        = '';
$checked{'ENABLE_INCLUDE_FILTER'}{$cgiparams{'ENABLE_INCLUDE_FILTER'}} = "checked='checked'";

$selected{'SORT_BY'}{$cgiparams{'SORT_BY'}} = "selected='selected'";
$selected{'ORDER'}{$cgiparams{'ORDER'}} = "selected='selected'";

$checked{'FULL_URL'}{'off'}                       = '';
$checked{'FULL_URL'}{'on'}                        = '';
$checked{'FULL_URL'}{$cgiparams{'FULL_URL'}} = "checked='checked'";

$checked{'MEASURES_RAW'}{'off'}                       = '';
$checked{'MEASURES_RAW'}{'on'}                        = '';
$checked{'MEASURES_RAW'}{$cgiparams{'MEASURES_RAW'}} = "checked='checked'";


&Header::showhttpheaders();

&Header::openpage($Lang::tr{'proxy log viewer'}, 1, '');

&Header::openbigbox('100%', 'left', '');

if ($errormessage) {
    &Header::openbox('100%', 'left', "$Lang::tr{'error messages'}:", 'error');
    print "<font class='base'>$errormessage&nbsp;</font>\n";
    &Header::closebox();
}

# -----------------------------------------------------------------
# check version for updates
# -----------------------------------------------------------------
if (($version lt $latest) && (-e $updflagfile)) { unlink($updflagfile); }

if (!-e $updflagfile) {
	&Header::openbox('100%', 'left', $Lang::tr{'advproxylog update notification'});
	print "<table width='100%' cellpadding='5'>\n";
	print "<tr>\n";
	print "<td bgcolor='$hintcolour' class='base'>$Lang::tr{'advproxylog update information'}<br/>$Lang::tr{'advproxylog current installed version'}: $version </td>";
	print "</tr>\n";
	print "</table>\n";
	&Header::closebox();
}

# ------------------------------------------------------------------

&Header::openbox('100%', 'left', "$Lang::tr{'settings'}:");

print <<END
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<table width='100%'>
<tr>
	<td width='50%' class='base' nowrap='nowrap'>$Lang::tr{'month'}:&nbsp;
	<select name='MONTH'>
END
    ;
for (my $month = 0; $month < 12; $month++) {
    print "\t<option ";
    if ($month == $cgiparams{'MONTH'}) {
        print "selected='selected' ";
    }
    print "value='$month'>$Lang::tr{$General::longMonths[$month]}</option>\n";
}
print <<END
	</select>
	&nbsp;&nbsp;$Lang::tr{'day'}:&nbsp;
	<select name='DAY'>
END
    ;
print "<option value='0'>$Lang::tr{'all'}</option>";
for (my $day = 1; $day <= 31; $day++) {
    print "\t<option ";
    if ($day == $cgiparams{'DAY'}) {
        print "selected='selected' ";
    }
    print "value='$day'>$day</option>\n";
}
print <<END
	</select>
	</td>
	<td width='45%'  align='center'>
		
	</td>
    <td class='onlinehelp'>
        <!-- <a href='${General::adminmanualurl}/logs-proxy.html' target='_blank'><img src='/images/web-support.png' alt='$Lang::tr{'online help en'}' title='$Lang::tr{'online help en'}' /></a> -->
    </td>
</tr>
</table>
<hr />
<table width='100%' border='0'>
<tr>
	<td colspan='4' class='base'><b>$Lang::tr{'advproxylog options'}:</b></td>
</tr>
<tr>
	<td  style='width:30%;' class='base'>$Lang::tr{'source ip'}:</td>
	<td  style='width:15%;'>
	<select name='SOURCE_IP'>
	<option value='ALL' $selected{'SOURCE_IP'}{'ALL'}>$Lang::tr{'caps all'}</option>
END
    ;
foreach my $ip (keys %ips) {
    print "<option value='$ip' $selected{'SOURCE_IP'}{$ip}>$ip</option>\n";
}
print <<END
	</select>
	</td>
	<td style='width:30%;' class='base'>Response Code:</td>
	<td style='width:25%;'>
	<select name='RESPONSE_CODE'>
	<option value='ALL' $selected{'RESPONSE_CODE'}{'ALL'}>$Lang::tr{'caps all'}</option>
	<option value='HIT' $selected{'RESPONSE_CODE'}{'HIT'}>ALL HIT</option>
	<option value='MISS' $selected{'RESPONSE_CODE'}{'MISS'}>ALL MISS</option>
END
    ;
foreach my $responsecode (keys %responsecodes) {
    print "<option value='$responsecode' $selected{'RESPONSE_CODE'}{$responsecode}>$responsecode</option>\n";
}
print <<END
	</select>
	</td>
</tr>
<tr>
	<td class='base'>$Lang::tr{'enable ignore filter'}:</td>
	<td><input type='checkbox' name='ENABLE_FILTER' value='on' $checked{'ENABLE_FILTER'}{'on'} /></td>
	<td class='base'>$Lang::tr{'ignore filter'}:</td>
	<td><input type='text' name='FILTER' value='$cgiparams{'FILTER'}' size='40' /></td>
</tr>
<tr>
	<td class='base'>$Lang::tr{'advproxylog enable match criteria'}:</td>
	<td><input type='checkbox' name='ENABLE_INCLUDE_FILTER' value='on' $checked{'ENABLE_INCLUDE_FILTER'}{'on'} /></td>
	<td class='base'>$Lang::tr{'advproxylog match criteria'}:</td>
	<td><input type='text' name='INCLUDE_FILTER' value='$cgiparams{'INCLUDE_FILTER'}' size='40' /></td>
</tr>

<tr>
	<td class='base'>$Lang::tr{'advproxylog full url'}:</td>
	<td><input type='checkbox' name='FULL_URL' value='on' $checked{'FULL_URL'}{'on'} /></td>
	<td class='base'>$Lang::tr{'advproxylog measures raw'}:</td>
	<td><input type='checkbox' name='MEASURES_RAW' value='on' $checked{'MEASURES_RAW'}{'on'} /></td>
</tr>

</table>

<hr />
<table width='100%' border='0'>
<tr>
	<td colspan='4' class='base'><b>$Lang::tr{'advproxylog sorting options'}</b></td>
</tr>
<tr>
	<td  style='width:30%;' class='base'>$Lang::tr{'advproxylog sort by'}:</td>
	<td  style='width:15%;'>
	 <select name='SORT_BY'>
		<option value='DATE' $selected{'SORT_BY'}{'DATE'}>$Lang::tr{'advproxylog sort by date'}</option>
		<option value='RESULT' $selected{'SORT_BY'}{'RESULT'}>$Lang::tr{'advproxylog sort by result code'}</option>
		<option value='DURATION' $selected{'SORT_BY'}{'DURATION'}>$Lang::tr{'advproxylog sort by duration'}</option>
		<!-- <option value='DURATION_SIZE' $selected{'SORT_BY'}{'DURATION_SIZE'}>$Lang::tr{'advproxylog sort by duration and size'}</option> -->
		<option value='SIZE' $selected{'SORT_BY'}{'SIZE'}>$Lang::tr{'advproxylog sort by size'}</option>
		<option value='URL' $selected{'SORT_BY'}{'URL'}>$Lang::tr{'advproxylog sort by url'}</option>
	 </select>	
	<td>	
	<td style='width:30%;' class='base'>$Lang::tr{'advproxylog order'}:</td>
	<td style='width:25%;'>
		<select name='ORDER'>
		<option value='ASC' $selected{'ORDER'}{'ASC'}>$Lang::tr{'advproxylog order asc'}</option>
		<option value='DESC' $selected{'ORDER'}{'DESC'}>$Lang::tr{'advproxylog order desc'}</option>
	 </select>	
	</td>
</tr>
</table>

<hr />
<table width='100%' border='0'>
<tr>
	<td width='45%'  align='center'>
		<input type='submit' name='ACTION' title='$Lang::tr{'day before'}' value='&lt;&lt;' />
		<input type='submit' name='ACTION' title='$Lang::tr{'day after'}' value='&gt;&gt;' />
		<input type='submit' name='ACTION' value='$Lang::tr{'update'}' />
		<input type='submit' name='ACTION' value='$Lang::tr{'export'}' />
	</td>
	<td width='55%' align='right'>
		<input type='submit' name='ACTION' value='$Lang::tr{'restore defaults'}' />&nbsp;
		<input type='submit' name='ACTION' value='$Lang::tr{'save'}' />
	</td>
	<td width='5%' align='right'>&nbsp;</td>
</tr>
<tr>
 <td colspan="2" align='right'><sup><small><a href='http://joeyramone76.altervista.org/advproxylog' target='_blank'>AdvproxyLog $version for IPCop</a></small></sup></td>
 <td width='5%' align='right'>&nbsp;</td>
</tr>
</table>
</form>
END
    ;

%columnsortedclass = ("DATE"   => "boldbase",
					 "RESULT" => "boldbase",
					 "DURATION" => "boldbase",
					 "DURATION_SIZE" => "boldbase",
					 "SIZE" => "boldbase",
					 "URL" => "boldbase"
);

$columnsortedclass{$sortby} = "ipcop_StatusBigRed";

# sort the @log based on user choices - select the column text color for ordered item

# sort by date?	Do nothing!

# sort by duration?	
if ($sortby eq 'DURATION')
{
	@log = sort { (split ' ', $a)[1] <=> (split ' ', $b)[1] } @log ;	
}
# sort by duration and size?	
elsif ($sortby eq 'DURATION_SIZE') 
{
	@log = sort { (split ' ', $a)[1] <=> (split ' ', $b)[1] || (split ' ', $a)[4] <=> (split ' ', $b)[4] } @log  ;	
	$columnsortedclass{"DURATION"}="ipcop_StatusBigRed";	
	$columnsortedclass{"SIZE"}="ipcop_StatusBigRed";	
}	
# sort by size?	
elsif ($sortby eq 'SIZE') {
	@log = sort { (split ' ', $a)[4] <=> (split ' ', $b)[4] } @log ;
}
# sort by result?
elsif ($sortby eq 'RESULT')	
{
	@log = sort { (split ' ', $a)[3] cmp (split ' ', $b)[3] } @log;
}

# sort by url?
elsif ($sortby eq 'URL') {
	@log = sort { (split ' ', $a)[6] cmp (split ' ', $b)[6] } @log ;
} else {
	$columnsortedclass{'DATE'} = "ipcop_StatusBigRed";
}

if ($order eq 'DESC') { @log = reverse @log; }



    #$errormessage="$errormessage$Lang::tr{'date not in logs'}: $filestr $Lang::tr{'could not be opened'}";
    if (0) {           # print last date record read
        my ($SECdt, $MINdt, $HOURdt, $DAYdt, $MONTHdt, $YEARdt) = localtime($lastdatetime);
        $SECdt   = sprintf("%.02d", $SECdt);
        $MINdt   = sprintf("%.02d", $MINdt);
        $HOURdt  = sprintf("%.02d", $HOURdt);
        $DAYdt   = sprintf("%.02d", $DAYdt);
        $MONTHdt = sprintf("%.02d", $MONTHdt + 1);
        $YEARdt  = sprintf("%.04d", $YEARdt + 1900);
        &General::log("$HOURdt:$MINdt:$SECdt, $DAYdt/$MONTHdt/$YEARdt--");
    }

my $durationcoldes = $Lang::tr{'advproxylog duration'};
$durationcoldes = $Lang::tr{'advproxylog duration in ms'} if ( $measuresraw );

my $sizecoldes = $Lang::tr{'advproxylog size in hr'};
$sizecoldes = $Lang::tr{'advproxylog size in bytes'} if ( $measuresraw );

my $end = $start + $logsettings{'LOGVIEW_VIEWSIZE'};
$end = $#log if ($#log < $start + $logsettings{'LOGVIEW_VIEWSIZE'});
@log =  @log [$start .. $end];

&Header::closebox();
&Header::openbox('100%', 'left', "$Lang::tr{'log'}: start->$start end->$end step->$logsettings{'LOGVIEW_VIEWSIZE'}  total lines-> $lines");

$start = $lines - $logsettings{'LOGVIEW_VIEWSIZE'} if ($start >= $lines - $logsettings{'LOGVIEW_VIEWSIZE'});
$start = 0 if ($start < 0);
my $prev;
if ($start == 0) {
    $prev = -1;
}
else {
    $prev = $start - $logsettings{'LOGVIEW_VIEWSIZE'};
    $prev = 0 if ($prev < 0);
}

my $next;
if ($start == $lines - $logsettings{'LOGVIEW_VIEWSIZE'}) {
    $next = -1;
}
else {
    $next = $start + $logsettings{'LOGVIEW_VIEWSIZE'};
    $next = $lines - $logsettings{'LOGVIEW_VIEWSIZE'} if ($next >= $lines - $logsettings{'LOGVIEW_VIEWSIZE'});
}

# if ($logsettings{'LOGVIEW_REVERSE'} eq 'on') { @log = reverse @log; }

print "<p><b>$Lang::tr{'web hits'} $date: $lines - $Lang::tr{'advproxylog sort by'} $sortby</b></p>";
if ($lines != 0) { &oldernewer(); }

	
	

 
print <<END
<table width='100%'>
<tr>
<td width='10%' align='center' class='$columnsortedclass{"DATE"}'><b>$Lang::tr{'time'}</b></td>
<td width='10%' align='center' class='boldbase'><b>$Lang::tr{'source ip'}</b></td>
<td width='5%' align='center' class='$columnsortedclass{"RESULT"}'><b>$Lang::tr{'advproxylog sort by result code'}</b></td>
<td width='5%' align='center' class='$columnsortedclass{"REQUEST_METHOD"}'><b>$Lang::tr{'advproxylog request method'}</b></td>
<td width='10%' align='center' class='$columnsortedclass{"SIZE"}'><b>$sizecoldes</b></td>
<td width='10%' align='center' class='$columnsortedclass{"DURATION"}'><b>$durationcoldes</b></td>
<td width='10%' align='center' class='boldbase'><b>$Lang::tr{'advproxylog transfer rate speed'}</b></td>
<td width='40%' align='center' class='$columnsortedclass{"URL"}'><b>$Lang::tr{'website'}</b></td>
</tr>
END
    ;
	

my $ll = 0;
foreach $_ (@log) {
   
    my ($datetime, $duration, $ip, $result, $size, $reqm, $url, $so) = split;
    my ($SECdt, $MINdt, $HOURdt, $DAYdt, $MONTHdt, $YEARdt) = localtime($datetime);
    $SECdt  = sprintf("%.02d", $SECdt);
    $MINdt  = sprintf("%.02d", $MINdt);
    $HOURdt = sprintf("%.02d", $HOURdt);
    #my $fullurl = $url;
	
	my $rate = 0;
	
	if ($duration > 0) 
	{
	  $rate = $size / ($duration * 0.001);
	} else {
	 $rate = $size * 2;
	}
	$rate = &ADVPXL::get_rate_str($rate) if (! $measuresraw);
	$rate = &ADVPXL::get_rate_str_bytes($rate) if ($measuresraw);
	
	$size = &ADVPXL::get_filesize_str($size) if (! $measuresraw);
	$duration = &ADVPXL::truncate_ms_to_sec($duration) if (! $measuresraw);
	# sprintf("%.01d", ($me + 1023)/1024);
	
	my $urlsize = 50;
	$urlsize = 190 if ($fullurl);
	
    $url =~ /(^.{0,$urlsize})/;
    my $part = $1;
    unless (length($part) < $urlsize) { $part = "${part}..."; }
    $url  = &Header::cleanhtml($url,  "y");
    $part = &Header::cleanhtml($part, "y");
    if ($cgiparams{'DAY'} == 0) {    # full month
        $DAYdt = sprintf("%.02d/", $DAYdt);
    }
    else {
        $DAYdt = '';
    }
	
	#TODO: move inline style in stylesheet
	my $resultstyle='';
	if ($result =~ /(HIT|UNMODIFIED)/) {
		$resultstyle='style="color:#558107; font-weight: bold;" ';
	}
	 print "<tr $resultstyle class='table".int(($ll % 2) + 1)."colour'>";
    print <<END
	<td align='center'>$DAYdt$HOURdt:$MINdt:$SECdt</td>
	<td align='center'>$ip</td>
	<td align='left'>$result</td>
	<td align='left'>$reqm</td>
	<td align='right'>$size</td>
	<td align='right'>$duration</td>
	<td align='right'>$rate</td>
	<td align='left'><a href='$url' title='$url' target='_new'>$part</a></td>
</tr>
END
        ;
    $ll++;
}

print "</table>";

&oldernewer();

&Header::closebox();

 #enable following only for debug
 # &Header::openbox('100%', 'left', 'DEBUG');
 #   my $debugCount = 0;
 #   foreach my $line (sort keys %debug) {
 #       print "$line = $debug{$line}<br />\n";
 #       $debugCount++;
 #   }
 #   print "&nbsp;Count: $debugCount\n";
 #   &Header::closebox();

&Header::closebigbox();

&Header::closepage();


# -------------------------------------------------------------------

sub check4updates
{
	if ((-e "${General::swroot}/red/active") && (-e $updflagfile) && (int(-M $updflagfile) > 3))
	{
		my @response=();;

		my $remote = IO::Socket::INET->new(
			PeerHost => 'joeyramone76.altervista.org',
			PeerPort => 'http(80)',
			Timeout  => 1
		);

		if ($remote)
		{
			print $remote "GET http://joeyramone76.altervista.org/advproxylog/latest HTTP/1.0\n";
			print $remote "User-Agent: Mozilla/4.0 (compatible; IPCop $General::version; $Lang::language; advproxylog)\n\n";
			while (<$remote>) { push(@response,$_); }
			close $remote;
			if ($response[0] =~ /^HTTP\/\d+\.\d+\s200\sOK\s*$/)
			{
				unlink($updflagfile);
				system("touch $updflagfile");
				return "$response[$#response]";
			}
		}
	} 
}

# -------------------------------------------------------------------


sub oldernewer {
    print <<END
<table width='100%'>
<tr>
END
        ;

    print "<td align='center' width='50%'>";
    if ($prev != -1) {
        print
"<a href='/cgi-bin/advproxylog.cgi?$prev,$cgiparams{'MONTH'},$cgiparams{'DAY'},$cgiparams{'SOURCE_IP'},$cgiparams{'RESPONSE_CODE'},$cgiparams{'SORT_BY'},$cgiparams{'ORDER'},$cgiparams{'FULL_URL'},$cgiparams{'ENABLE_FILTER'},$cgiparams{'FILTER'},$cgiparams{'ENABLE_INCLUDE_FILTER'},$cgiparams{'INCLUDE_FILTER'}'>$Lang::tr{'advproxylog prev'}</a>";
    }
    else {
        print "$Lang::tr{'advproxylog prev'}";
    }
    print "</td>\n";

    print "<td align='center' width='50%'>";
    if ($next >= 0) {
        print
"<a href='/cgi-bin/advproxylog.cgi?$next,$cgiparams{'MONTH'},$cgiparams{'DAY'},$cgiparams{'SOURCE_IP'},$cgiparams{'RESPONSE_CODE'},$cgiparams{'SORT_BY'},$cgiparams{'ORDER'},$cgiparams{'FULL_URL'},$cgiparams{'ENABLE_FILTER'},$cgiparams{'FILTER'},$cgiparams{'ENABLE_INCLUDE_FILTER'},$cgiparams{'INCLUDE_FILTER'}'>$Lang::tr{'advproxylog next'}</a>";
    }
    else {
        print "$Lang::tr{'advproxylog next'}";
    }
    print "</td>\n";

    print <<END
</tr>
</table>
END
        ;
}

