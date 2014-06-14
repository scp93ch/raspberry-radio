Installation
============

You can install the two commands and the web server and start the webserver running by just doing:
```shell
$ sudo ./install.sh
```

However, it is not a great idea to run any old script as root so please just check the `install.sh` file and make sure you understand what it is doing first. Otherwise, the commands required are detailed below.

Radio Command
-------------

The "radio" script plays BBC radio streams using mpd and relies upon the "bbc_radio_update" script to get hold of the correct URLs for the streams. The radio command runs bbc_radio_update when necessary but you can also run the update by hand.

To install these two scripts, follow these steps.

Copy scripts/radio to /usr/local/bin:
```shell
$ sudo cp scripts/radio /usr/local/bin
```

Copy scripts/bbc_radio_update to /usr/local/bin:
```shell
$ sudo cp scripts/bbc_radio_update /usr/local/bin
```

Make the directory to cache the radio stream URLs in:
```shell
$ sudo mkdir /var/local/bbc_radio
```

Make the cache directory writable by all users:
```shell
$ sudo chmod 777 /var/local/bbc_radio/
```

At this point the "radio" command should work.
you can try e.g. `radio 4`, `radio stations`, `radio bbc1`, `radio stop`.

Webserver
---------

You can also install the tiny webserver to let you control the radio from a web browser (such as on your smartphone). To do that, follow these steps.

Copy the webserver into /usr/local/bin:
```shell
$ sudo cp webserver/radio_server.py /usr/local/bin
```

Copy the web pages into /var/local:
```shell
$ sudo cp -r webserver/pages/ /var/local
```

Copy the init script into /etc/init.d:
```shell
$ sudo cp webserver/init.d/radio_server /etc/init.d
```

Update start-up and shut-down links for the radio:
```shell
$ sudo update-rc.d radio_server defaults
```

Start the radio webserver process:
```shell
$ sudo service radio_server start
```

The web page is then available on port 8080, so visit [http://localhost:8080](http://localhost:8080) from the computer running the server or http://your-hostname-or-IP-address:8080 from your smartphone.