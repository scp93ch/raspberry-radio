#!/bin/sh

cp scripts/radio /usr/local/bin
cp scripts/bbc_radio_update /usr/local/bin
mkdir /var/local/bbc_radio
chmod 777 /var/local/bbc_radio/
cp webserver/radio_server.py /usr/local/bin
cp -r webserver/pages/ /var/local
cp webserver/init.d/radio_server /etc/init.d
update-rc.d radio_server defaults
service radio_server start
