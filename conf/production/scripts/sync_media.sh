#!/bin/bash

dosync() {
    if [ $debug == true ]; then
        echo "       -> ${toserv}"
    fi
    rsync -q -av --bwlimit=4200  /var/www/uploads/${SERV}/ ${toserv}:/var/www/uploads/${SERV}/
}

debug=true

SERV="s9.favim.com";
if [ $debug == true ]; then
        echo "Sync from ${SERV}"
fi
toserv="s1.favim.com"; dosync
toserv="s3.favim.com"; dosync

#SERV="zero.favim.com";
#echo "Sync from ${SERV}"
#toserv="s1.favim.com"; dosync
#toserv="s3.favim.com"; dosync
#toserv="s4.favim.com"; dosync
#toserv="s5.favim.com"; dosync
#toserv="s6.favim.com"; dosync
#toserv="s8.favim.com"; dosync

echo "All done."
