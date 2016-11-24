#! /usr/bin/env python3

import json
import argparse
import os
import subprocess

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
    letsencryptDir = ""
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
        self.letsencryptDir = config["letsencryptDir"]
        self.certDir = config["certDir"]

    def make_dirs(self):
        if not path.isdir(self.certDir):
            os.makedirs(self.certDir)

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

    def get_letsencrypt_dir(self, domain):
        return path.join(self.letsencryptDir, domain)

    def symlink_letsencrypt_file(self, domain, file, outfile):
        letsencrypt_cert_file = path.abspath(self.get_letsencrypt_dir(domain))
        my_cert_file = path.join(self.certDir, outfile)
        if path.lexists(my_cert_file):
            os.remove(my_cert_file)
        os.symlink(path.join(letsencrypt_cert_file, file), my_cert_file)

    def get_cert_files(self, domain):
        return [path.abspath(path.join(self.certDir, domain + ".crt")),
                path.abspath(path.join(self.certDir, domain + ".key")),
                path.abspath(path.join(self.certDir, domain + "-chain.crt"))]

    def execute(self, exe, args, get_output):
        args.insert(0, exe)
        proc = subprocess.Popen(args, stdout=(subprocess.PIPE if get_output else None))
        out = proc.communicate()
        return proc.returncode, out[0]

    def execute_hooks(self, hook_type, hook_event, args):
        args.insert(0, hook_event)
        for hook_name in self.get_hook_files(hook_type, True):
            self.execute(self.get_hook_file(hook_type, hook_name, True), args, False)

    def is_cert_present(self, domain):
        cert_files = self.get_cert_files(domain)
        for cert_file in cert_files:
            if not path.isfile(cert_file):
                return False
        return True

    def get_cert_end_date(self, domain):
        cert_files = self.get_cert_files(domain)
        res, out = self.execute("openssl", ["x509", "-noout", "-in", cert_files[0], "-enddate"], True)
        if res == 0:
            return out.decode("UTF-8").split("=")[1][:-1]
        return None

    def is_cert_gonna_expire(self, domain, checkend):
        cert_files = self.get_cert_files(domain)
        res, out = self.execute("openssl", ["x509", "-noout", "-in", cert_files[0], "-checkend", str(checkend)], True)
        return res == 1

    def get_all_domains(self):
        files = os.listdir(self.certDir)
        files.sort()
        domains = []
        for file in files:
            if file.endswith(".crt") and self.is_cert_present(file[:-4]):
                domains.append(file[:-4])
        return domains

    def cert_request(self, domain, logger):

        cert_files = self.get_cert_files(domain)
        cert_files.insert(0, domain)
        self.execute_hooks("cert", "pre", cert_files)

        res, out = self.execute(self.letsencryptCommand, [domain], False)
        if res != 0:
            raise SiteGenException("Certificate request failed with code %i" % res, res)

        self.symlink_letsencrypt_file(domain, "cert.pem", domain + ".crt")
        self.symlink_letsencrypt_file(domain, "privkey.pem", domain + ".key")
        self.symlink_letsencrypt_file(domain, "chain.pem", domain + "-chain.crt")

        self.execute_hooks("cert", "post", cert_files)

    def certs_request(self, domains, logger):
        for domain in domains:
            self.cert_request(domain, logger)

    def cert_check(self, domain, logger):
        if not self.is_cert_present(domain):
            raise SiteGenException("Certificate not present: %s" % domain, 1)
        if self.is_cert_gonna_expire(domain, self.certRenewTime):
            logger("%s: %s" % (domain, self.get_cert_end_date(domain)))
            return True
        return False

    def certs_check(self, domains, logger):
        for domain in domains:
            self.cert_check(domain, logger)

    def cert_enddate(self, domain, logger):
        if not self.is_cert_present(domain):
            raise SiteGenException("Certificate not present: %s" % domain, 1)
        logger("%s: %s" % (domain, self.get_cert_end_date(domain)))

    def certs_enddate(self, domains, logger):
        for domain in domains:
            self.cert_enddate(domain, logger)

    def cert_renew(self, domain, logger):
        if self.cert_check(domain, logger):
            self.cert_request(domain, logger)

    def certs_renew(self, domains, logger):
        for domain in domains:
            self.cert_renew(domain, logger)

    def site_create(self, domain, logger):
        pass

    def site_remove(self, domain, logger):
        pass

    def hook_enable(self, hook_type, hook_name, logger):
        if not self.is_hook_present(hook_type, hook_name, False):
            raise SiteGenException("Hook is not present", 1)
        if self.is_hook_enabled(hook_type, hook_name):
            raise SiteGenException("Hook is already enabled", 0)
        logger("Enabling %s %s" % (hook_type, hook_name))
        hook_dir = self.get_hook_dir(hook_type, hook_name)
        if not path.isdir(hook_dir):
            os.makedirs(hook_dir)
        hook_file_available = self.get_hook_file(hook_type, hook_name, False)
        hook_file_enabled = self.get_hook_file(hook_type, hook_name, True)
        hook_relative_file = path.relpath(hook_file_available, self.get_hook_dir(hook_type, True))

        os.symlink(hook_relative_file, hook_file_enabled)

    def hook_disable(self, hook_type, hook_name, logger):
        if not self.is_hook_present(hook_type, hook_name, False):
            raise SiteGenException("Hook is not present", 1)
        if not self.is_hook_enabled(hook_type, hook_name):
            raise SiteGenException("Hook is not enabled", 0)
        logger("Disabling %s %s" % (hook_type, hook_name))
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
    parser.add_argument('--cert-enddate', metavar='cert_enddate', const='', nargs='?',
                        help='Print certificate enddate. Print all certificates enddate if no domain is specified')

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

    site_gen.make_dirs()

    logger = print

    try:
        if args.cert_request is not None:
            if args.cert_request == "":
                site_gen.certs_request(site_gen.get_all_domains(), logger)
            else:
                site_gen.cert_request(args.cert_request, logger)

        elif args.cert_check is not None:
            if args.cert_check == "":
                site_gen.certs_check(site_gen.get_all_domains(), logger)
            else:
                site_gen.cert_check(args.cert_check, logger)

        elif args.cert_renew is not None:
            if args.cert_renew == "":
                site_gen.certs_renew(site_gen.get_all_domains(), logger)
            else:
                site_gen.cert_renew(args.cert_renew, logger)

        elif args.cert_enddate is not None:
            if args.cert_enddate == "":
                site_gen.certs_enddate(site_gen.get_all_domains(), logger)
            else:
                site_gen.cert_enddate(args.cert_enddate, logger)

        elif args.site_create is not None:
            site_gen.site_create(args.site_create, logger)

        elif args.site_remove is not None:
            site_gen.site_remove(args.site_remove, logger)

        elif args.site_hook_enable is not None:
            site_gen.hook_enable("site", args.site_hook_enable, logger)

        elif args.site_hook_disable is not None:
            site_gen.hook_disable("site", args.site_hook_disable, logger)

        elif args.hook_cert_enable is not None:
            site_gen.hook_enable("cert", args.hook_cert_enable, logger)

        elif args.hook_cert_disable is not None:
            site_gen.hook_disable("cert", args.hook_cert_disable, logger)

        else:
            parser.print_help()
    except SiteGenException as e:
        print(e.error)
        exit(e.code)

if __name__ == "__main__":
    main()
