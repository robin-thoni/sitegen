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

Hooks
-----

There's two types of hooks:
 - Certificate: Cert hooks are triggered when creating a site using the --site-create flag. Hooks are executed once per site, before and after creation.
 - Site: Site hooks are triggered when requesting/renewing a certificate using the flags --cert-request and --cert-renew. Hooks are executed once per certificate, before and after request/renew.

Hooks must be enabled/disabled using `--hook-enable` and `--hook-disable` arguments.

Some hooks are provided:
 - Certificates
    - 000-print: Print request/renewal details, before request/renewal.
    - 100-mkwebroot: make directory for the letsencrypt challenge, to be used with `extra/apache/sitegen.conf`, before request/renewal.
    - 200-reload: Reload apache daemon, after request/renewal.
 - Sites
    - 000-print: Print site details, before site creation.
    - 100-sitegen-cert-request: Request a letsencrypt certificate if SSL is detected in site configuration files, after site creation.
    - 200-chown: Change owner of the document root to the user running the command, after site creation.
    - 300-a2ensite: Enable site in apache, after site creation.
    - 400-reload: Reload apache daemon, after site creation.


Templates
---------

Templates are used to generate apache site configuration. They are split in two files:
 - Transport configuration (*.conf): These files setup the http and/or https configuration to be used.
 - Site configuration (*.include): These files setup the site configuration, as document root, server name, aliases, location, etc. They are included ine the .conf files using Include directive.

Default templates are default.include and https.conf. Templates can be specified when creating site by using the following syntax:
```
sitegen --site-create www.example.com:docker.rhttps
```
Where `www.example.com` is the site to create, `docker` is the `docker.include` template and `rhttps` is the `rhttps.conf` template.

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