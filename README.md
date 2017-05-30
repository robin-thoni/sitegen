sitegen
=======

CLI tool to build web site configuration and obtain SSL certificates from letsencrypt using certbot.

Also provide a simpler way to request SSL certificate over certbot.

Installation
------------

```
#Install from pip
pip2 install sitegencli
#Install from sources
python2 setup.py install
```

Configuration
-------------

Configuration must be copied from `/usr/local/etc/sitegen` to `/etc/sitegen`:

sitegen.json looks like:
```
{
  "siteConfDir": "/etc/apache2/sites-available/",
  "siteDir": "/var/",
  "confDir": "/etc/sitegen/",
  "certRenewTime": 5356800,
  "letsencryptCommands": [
    {
      "patterns": [
        "example.com",
        "*.example.com"
      ],
      "command": {
        "letsencryptCommand": "certbot",
        "letsencryptArgs": [
          "--agree-tos",
          "--text",
          "--renew-by-default",
          "--webroot",
          "--webroot-path",
          "/tmp/acme-challenge/",
          "certonly"
        ]
      }
    },
    {
      "patterns": "*",
      "command": {
        "letsencryptCommand": "certbot",
        "letsencryptArgs": [
          "--agree-tos",
          "--text",
          "--renew-by-default",
          "--authenticator",
          "certbot-pdns:auth",
          "certonly"
        ]
      }
    }
  ],
  "letsencryptDir": "/etc/letsencrypt/live/",
  "certDir": "/etc/ssl/private/"
}

```

Configuration keys:

 - siteConfDir: Apache available sites folder.
 - siteDir: Where to put new site document root folder.
 - confDir: Sitegen configuration folder
 - certRenewTime: Number of seconds before SSL certificate expiration
 - letsencryptCommands: Commands to be used to generate SSL certificates
    - patterns: Fnmatch patterns to select command from domain name
    - command: The command to be executed to generate the certificate
        - letsencryptCommand: Command name
        - letsencryptArgs: Command arguments
 - letsencryptDir: The root directory used by letsencrypt (certbot)
 - certDir: Where to put symlink to certificate files

Usage
-----

Generate a site with SSL:
```
sitegen --site-create example.com:default.https
```

Request a SSL certificate:
```
sitegen --cert-request example.com
```

See `sitegen --help` for more.