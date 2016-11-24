#! /usr/bin/env python3

import json
import argparse
import os

from os import path


class SiteGenException(Exception):
    error = None
    code = None

    def __init__(self, error, code):
        self.error = error
        self.code = code


class SiteGen:
    siteConfDir = ""
    siteDir = ""
    confDir = ""
    hooksEnabledDir = ""
    hooksAvailableDir = ""
    templatesDir = ""
    certRenewTime = ""
    letsencryptCommand = ""
    certDir = ""

    def __init__(self, config):
        self.siteConfDir = config["siteConfDir"]
        self.siteDir = config["siteDir"]
        self.confDir = config["confDir"]
        self.hooksEnabledDir = path.join(self.confDir, "hooks-enabled")
        self.hooksAvailableDir = path.join(self.confDir, "hooks-available")
        self.templatesDir = path.join(self.confDir, "templates")
        self.certRenewTime = config["certRenewTime"]
        self.letsencryptCommand = config["letsencryptCommand"]
        self.certDir = config["certDir"]

    def get_hook_dir(self, hook_type, is_enabled):
        return path.join(self.hooksEnabledDir if is_enabled else self.hooksAvailableDir, hook_type)

    def get_hook_file(self, hook_type, hook_name, is_enabled):
        return path.join(self.get_hook_dir(hook_type, is_enabled), hook_name)

    def get_hook_files(self, hook_type, is_enabled):
        hook_dir = self.get_hook_dir(hook_type, is_enabled)
        files = os.listdir(hook_dir)
        files.sort()
        return files

    def is_hook_present(self, hook_type, hook_name, is_enabled):
        return path.isfile(self.get_hook_file(hook_type, hook_name, is_enabled))

    def is_hook_enabled(self, hook_type, hook_name):
        return self.is_hook_present(hook_type, hook_name, True)

    def cert_request(self, domain):
        pass

    def cert_check(self, domain):
        pass

    def cert_renew(self, domain):
        pass

    def site_create(self, domain):
        pass

    def site_remove(self, domain):
        pass

    def hook_enable(self, hook_type, hook_name):
        if not self.is_hook_present(hook_type, hook_name, False):
            raise SiteGenException("Hook is not present", 1)
        if self.is_hook_enabled(hook_type, hook_name):
            raise SiteGenException("Hook is already enabled", 0)
        hook_dir = self.get_hook_dir(hook_type, hook_name)
        if not path.isdir(hook_dir):
            os.makedirs(hook_dir)
        hook_file_available = self.get_hook_file(hook_type, hook_name, False)
        hook_file_enabled = self.get_hook_file(hook_type, hook_name, True)
        hook_relative_file = path.relpath(hook_file_available, self.get_hook_dir(hook_type, True))

        os.symlink(hook_relative_file, hook_file_enabled)

    def hook_disable(self, hook_type, hook_name):
        if not self.is_hook_present(hook_type, hook_name, False):
            raise SiteGenException("Hook is not present", 1)
        if not self.is_hook_enabled(hook_type, hook_name):
            raise SiteGenException("Hook is not enabled", 0)
        os.remove(self.get_hook_file(hook_type, hook_name, True))


def main():
    parser = argparse.ArgumentParser(description='Manage apache websites and SSL certificates')
    parser.add_argument('--config', dest='config', default='/etc/sitegen/sitegen.json', help='Configuration file path')

    parser.add_argument('--cert-request', metavar='cert_request', const='', nargs='?',
                        help='Request/renew a certificate. Request/renew all certificates if no domain is specified')
    parser.add_argument('--cert-check', metavar='cert_check', const='', nargs='?',
                        help='Check if certificate needs to be renewed. Check all if no domain is specified')
    parser.add_argument('--cert-renew', metavar='cert_renew', const='', nargs='?',
                        help='Renew certificate if it needs to be. Renew all that needs to be if no domain is specified')

    parser.add_argument('--site-create', help='Create a site configuration', metavar='site_create')
    parser.add_argument('--site-remove', help='Remove a site configuration', metavar='site_remove')

    parser.add_argument('--hook-site-enable', help='Enable a site hook', dest='site_hook_enable', metavar='hook')
    parser.add_argument('--hook-site-disable', help='Disable a site hook', dest='site_hook_disable', metavar='hook')

    parser.add_argument('--hook-cert-enable', help='Enable a certificate hook', dest='hook_cert_enable', metavar='hook')
    parser.add_argument('--hook-cert-disable', help='Disable a certificate hook', dest='hook_cert_disable', metavar='hook')

    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    site_gen = SiteGen(config)
    print(site_gen.get_hook_files("site", True))

    try:
        if args.cert_request is not None:
            site_gen.cert_request(args.cert_request)

        elif args.cert_check is not None:
            site_gen.cert_check(args.cert_check)

        elif args.cert_renew is not None:
            site_gen.cert_renew(args.cert_renew)

        elif args.site_create is not None:
            site_gen.site_create(args.site_create)

        elif args.site_remove is not None:
            site_gen.site_remove(args.site_remove)

        elif args.site_hook_enable is not None:
            site_gen.hook_enable("site", args.site_hook_enable)

        elif args.site_hook_disable is not None:
            site_gen.hook_disable("site", args.site_hook_disable)

        elif args.hook_cert_enable is not None:
            site_gen.hook_enable("cert", args.hook_cert_enable)

        elif args.hook_cert_disable is not None:
            site_gen.hook_disable("cert", args.hook_cert_disable)

        else:
            parser.print_help()
    except SiteGenException as e:
        print(e.error)
        exit(e.code)

if __name__ == "__main__":
    main()
