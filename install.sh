#!/bin/bash
# ipcop advanced proxy log addon binary installer Ver 1.0.0 for IPCop 2.0.x
#
# created 01 January 2014 by Umberto 'joeyramone76' Miceli <joeyramone76@altervista.org>
#
#
# $Id: install.sh v 1.0 2014-02-08 17:56:23Z joeyramone76 $
#

SCRIPTPATH=`dirname $0`
CMD="$1"

STEP=1
UPDATE=0

ADVPLVER=1.0.0
ADVPLURL=http://joeyramone76.altervista.org/advproxylog/latest
LOGDIR="/var/log/advproxylog"


#error handling
err()
{
    echo " "
    echo "Error : $1 "
    echo " "
    echo "Choose your option:"
    echo " "
    echo "./install -i   ---> to install"
    echo "./install -u   ---> to uninstall"
    echo " "
    exit
}


# installation
ai()
{
    echo ""
    echo "===================================================="
    echo "  IPCop 2.0 Advanced proxy Log add-on installation"
    echo "===================================================="
    echo ""

    ## verify already installed and uninstall
    if [ -e /var/ipcop/addons/advproxylog/version ]; then
        UPDATE=1
    fi

    echo "Step $STEP: Creating directories"
    echo "--------------------------------------------"

    for DIR in /var/ipcop/addons/advproxylog /var/ipcop/addons/advproxylog/reports 
    do
        echo "$DIR"
        if [ ! -d $DIR ]; then
            mkdir $DIR
        fi
    done

    echo " "
    let STEP++



    echo "Step $STEP: Patching system files"
    echo "--------------------------------------------"

    echo "Patching language files"
    addtolanguage AdvProxyLog bz,de,en,es,fr,it,nl,pl,pt,ru $SCRIPTPATH/langs

    echo " "
    let STEP++



    echo "Step $STEP: Copying Advanced Proxy Log files"
    echo "--------------------------------------------"

    echo "/home/httpd/cgi-bin/advproxylog.cgi"
    addcgi $SCRIPTPATH/cgi/advproxylog.cgi
	
    echo "/var/ipcop/addons/advproxylog/advpoxylog-lib.pl"
    cp $SCRIPTPATH/cgi/advproxylog-lib.pl /var/ipcop/addons/advproxylog/advproxylog-lib.pl

	echo "/var/ipcop/proxy/advproxylog/viewersettings"
    cp $SCRIPTPATH/setup/viewersettings /var/ipcop/addons/advproxylog/viewersettings
    
    echo "/var/ipcop/addons/advproxylog/version"
    echo "$ADVPLVER" > /var/ipcop/addons/advproxylog/version
    # echo "URL=$ADVPLURL" >> /var/ipcop/addons/advproxylog/version

    rm -rf /var/ipcop/addons/advproxylog/latestVersion
	
	touch -t 201402100000 /var/ipcop/addons/advproxylog/.up2date

    echo " "
    let STEP++


    echo "Step $STEP: Setting ownerships and permissions"
    echo "--------------------------------------------"

    echo "Setting ownership and permissions (advproxylog)"
    chown -R nobody:nobody /var/ipcop/addons/advproxylog

    
    echo " "
    let STEP++


    if [ "$UPDATE" == 1 ]; then

        echo " "
    fi

    echo " "
}

# deinstallation
au()
{

    echo "===================================================="
    echo "  IPCop 2.0 Advanced Proxy Log add-on uninstall"
    echo "===================================================="
    echo ""

    if [ ! -e "/home/httpd/cgi-bin/advproxylog.cgi" ] && [ ! -d "/var/ipcop/addons/advproxylog" ]; then
        echo "ERROR: Advanced Proxy Log add-on is not installed."
        exit
    fi


    echo "Step $STEP: Removing directories"
    echo "--------------------------------------------"

    for DIR in /var/ipcop/addons/advproxylog /var/ipcop/addons/advproxylog/reports /var/ipcop/proxy/advproxylog
    do
        echo "$DIR"
        if [ -d "$DIR" ]; then
            rm -rf $DIR
        fi
    done

    echo ""
    let STEP++


    echo "Step $STEP: Deleting AdvProxyLog files"
    echo "--------------------------------------------"

    echo "/home/httpd/cgi-bin/advproxylog.cgi"
    removecgi advproxylog.cgi

	echo "/home/httpd/cgi-bin/advproxylog-lib.pl"
	rm -f /home/httpd/cgi-bin/advproxylog-lib.pl
	
    echo ""
    let STEP++


    echo "Step $STEP: Restoring system files"
    echo "--------------------------------------------"

   
    echo "Removing language texts"
    removefromlanguage AdvProxyLog

    echo ""
    let STEP++

}


if [ ! -e /usr/lib/ipcop/library.sh ]; then
    echo "Upgrade your IPCop, library.sh is missing"
    exit 1
fi

. /usr/lib/ipcop/library.sh

# check IPCop version
VERSIONOK=1
if [ 0$LIBVERSION -ge 2 ]; then
    isversion 2.0.3 newer
    VERSIONOK=$?
fi
#DEBUG:
#echo "VERSIONOK: $VERSIONOK"
if [ $VERSIONOK -ne 0 ]; then
    echo "Upgrade your IPCop, this Addon requires at least IPCop 2.0.3"
    exit 1
fi


case $CMD in
    -i|i|install)
        echo " "
        ai
        echo " "
        ;;

    -u|u|uninstall)
        echo " "
        au
        echo " "
        ;;

    *)
        err "Invalid Option"
        ;;
esac
sync

#end of file
