#! /usr/bin/env python3
import fnmatch
import json
import argparse
import os
import subprocess
import argcomplete

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
    letsencryptCommands = ""
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
        self.letsencryptCommands = config["letsencryptCommands"]
        self.letsencryptDir = config["letsencryptDir"]
        self.certDir = config["certDir"]

    def make_dirs_p(self, folder):
        if not path.isdir(folder):
            os.makedirs(folder)

    def make_dirs(self):
        self.make_dirs_p(self.certDir)
        self.make_dirs_p(self.siteConfDir)
        self.make_dirs_p(self.siteDir)

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

    def get_letsencrypt_command(self, domain):
        for d in self.letsencryptCommands:
            patterns = d['patterns'] if isinstance(d['patterns'], list) else [d['patterns']]
            for pattern in patterns:
                if fnmatch.fnmatch(domain, pattern):
                    return d['command']
        return None

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
        args = args[:]
        args.insert(0, exe)
        proc = subprocess.Popen(args, stdout=(subprocess.PIPE if get_output else None))
        out = proc.communicate()
        return proc.returncode, out[0]

    def execute_hooks(self, hook_type, hook_event, args):
        args = args[:]
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

    def get_all_certs(self):
        files = os.listdir(self.certDir)
        files.sort()
        domains = []
        for file in files:
            if file.endswith(".crt") and self.is_cert_present(file[:-4]):
                domains.append(file[:-4])
        return domains

    def get_all_site_confs(self):
        files = os.listdir(self.get_site_template_dir())
        files.sort()
        templates = []
        for file in files:
            if file.endswith(".conf"):
                templates.append(file[:-5])
        return templates

    def get_all_site_incs(self):
        files = os.listdir(self.get_site_template_dir())
        files.sort()
        templates = []
        for file in files:
            if file.endswith(".include"):
                templates.append(file[:-8])
        return templates

    def get_all_sites(self):
        files = os.listdir(self.siteConfDir)
        files.sort()
        templates = []
        for file in files:
            if file.endswith(".conf"):
                templates.append(file[:-5])
        return templates

    def get_all_domains(self):
        domains = list(set(self.get_all_sites() + self.get_all_certs()))
        domains.sort()
        return domains

    def get_site_template_dir(self):
        return path.join(self.confDir, "templates")

    def get_site_conf_files(self, domain):
        return [
            path.join(self.siteConfDir, domain + ".conf"),
            path.join(self.siteConfDir, domain + ".include")
        ]

    def get_site_template_conf_files(self, inc, conf):
        return [
            path.join(self.get_site_template_dir(), conf + ".conf"),
            path.join(self.get_site_template_dir(), inc + ".include")
        ]

    def get_site_dir(self, domain):
        return path.abspath(path.join(self.siteDir, domain))

    def is_site_present(self, domain):
        for file in self.get_site_conf_files(domain):
            if path.isfile(file):
                return True
        return False

    def is_site_template_present(self, inc, conf):
        for file in self.get_site_template_conf_files(inc, conf):
            if path.isfile(file):
                return True
        return False

    def generate_site_conf_file(self, domain, template, outfile):
        with open(template) as f:
            content = f.read()
        content = content.replace("%%HOST%%", domain).replace("%%ROOT%%", self.get_site_dir(domain))
        with open(outfile, "w") as f:
            f.write(content)

    def cert_request(self, domain):

        cert_files = self.get_cert_files(domain)
        cert_files.insert(0, domain)
        self.execute_hooks("cert", "pre", cert_files)

        command = self.get_letsencrypt_command(domain)

        args = command['letsencryptArgs'][:]
        args.append("-d")
        args.append(domain)

        res, out = self.execute(command['letsencryptCommand'], args, False)
        if res != 0:
            raise SiteGenException("Certificate request failed with code %i" % res, res)

        self.symlink_letsencrypt_file(domain, "cert.pem", domain + ".crt")
        self.symlink_letsencrypt_file(domain, "privkey.pem", domain + ".key")
        self.symlink_letsencrypt_file(domain, "chain.pem", domain + "-chain.crt")
        self.symlink_letsencrypt_file(domain, "fullchain.pem", domain + "-fullchain.crt")

        self.execute_hooks("cert", "post", cert_files)

    def certs_request(self, domains):
        for domain in domains:
            self.cert_request(domain)

    def cert_check(self, domain):
        if not self.is_cert_present(domain):
            raise SiteGenException("Certificate not present: %s" % domain, 1)
        if self.is_cert_gonna_expire(domain, self.certRenewTime):
            print("%s: %s" % (domain, self.get_cert_end_date(domain)))
            return True
        return False

    def certs_check(self, domains):
        for domain in domains:
            self.cert_check(domain)

    def cert_enddate(self, domain):
        if not self.is_cert_present(domain):
            raise SiteGenException("Certificate not present: %s" % domain, 1)
        print("%s: %s" % (domain, self.get_cert_end_date(domain)))

    def certs_enddate(self, domains):
        for domain in domains:
            self.cert_enddate(domain)

    def cert_renew(self, domain):
        if self.cert_check(domain):
            self.cert_request(domain)

    def certs_renew(self, domains):
        for domain in domains:
            self.cert_renew(domain)

    def site_create(self, domain, inc, conf):
        if self.is_site_present(domain):
            raise SiteGenException("Site is present", 1)
        if not self.is_site_template_present(inc, conf):
            raise SiteGenException("Template is not present", 1)

        args = [domain, self.get_site_dir(domain)]
        conf_files = self.get_site_template_conf_files(inc, conf)
        site_files = self.get_site_conf_files(domain)
        for f in conf_files:
            args.append(f)
        for f in site_files:
            args.append(f)

        self.execute_hooks("site", "pre", args)

        self.make_dirs_p(self.get_site_dir(domain))
        i = 0
        while i < len(conf_files):
            self.generate_site_conf_file(domain, conf_files[i], site_files[i])
            i += 1

        self.execute_hooks("site", "post", args)

    def hook_enable(self, hook_type, hook_name):
        if hook_type is None or not self.is_hook_present(hook_type, hook_name, False):
            raise SiteGenException("Hook is not present", 1)
        if self.is_hook_enabled(hook_type, hook_name):
            raise SiteGenException("Hook is already enabled", 0)
        print("Enabling %s %s" % (hook_type, hook_name))
        hook_dir = self.get_hook_dir(hook_type, hook_name)
        self.make_dirs_p(hook_dir)
        hook_file_available = self.get_hook_file(hook_type, hook_name, False)
        hook_file_enabled = self.get_hook_file(hook_type, hook_name, True)
        hook_relative_file = path.relpath(hook_file_available, self.get_hook_dir(hook_type, True))

        os.symlink(hook_relative_file, hook_file_enabled)

    def hook_disable(self, hook_type, hook_name):
        if hook_type is None or not self.is_hook_present(hook_type, hook_name, False):
            raise SiteGenException("Hook is not present", 1)
        if not self.is_hook_enabled(hook_type, hook_name):
            raise SiteGenException("Hook is not enabled", 0)
        print("Disabling %s %s" % (hook_type, hook_name))
        os.remove(self.get_hook_file(hook_type, hook_name, True))


def parse_domain(domain, default_inc="default", default_conf="https"):
    inc = default_inc
    conf = default_conf
    if ":" in domain:
        split = domain.split(":")
        domain = split[0]
        inc = split[1]
        if "." in inc:
            split = inc.split(".")
            inc = split[0]
            conf = split[1]
    return domain, inc, conf


def parse_hook(hook):
    if "." in hook:
        split = hook.split(".")
        return split[0], split[1]
    return None, None


def get_site_gen(prefix, **kwargs):
    with open(kwargs.get("parsed_args").config, "r") as f:
        config = json.load(f)
    return SiteGen(config)


def cert_completer(prefix, **kwargs):
    site_gen = get_site_gen(prefix, **kwargs)
    return site_gen.get_all_certs()


def domain_completer(prefix, **kwargs):
    site_gen = get_site_gen(prefix, **kwargs)
    return site_gen.get_all_domains()


def site_conf_completer(prefix, **kwargs):
    site_gen = get_site_gen(prefix, **kwargs)
    return site_gen.get_all_site_confs()


def site_inc_completer(prefix, **kwargs):
    site_gen = get_site_gen(prefix, **kwargs)
    return site_gen.get_all_site_incs()


def site_create_completer(prefix, **kwargs):
    domain, inc, conf = parse_domain(prefix, None, None)
    if inc is not None:
        if conf is not None:
            templates = site_conf_completer(prefix, **kwargs)
            return [domain + ":" + inc + "." + elt for elt in templates]
        else:
            templates = site_inc_completer(prefix, **kwargs)
            return [domain + ":" + elt for elt in templates]

    return domain_completer(prefix, **kwargs)


def hook_completer(prefix, **kwargs):
    site_gen = get_site_gen(prefix, **kwargs)
    return site_gen.get_all_certs()


def main():
    parser = argparse.ArgumentParser(description='Manage apache websites and SSL certificates')
    parser.add_argument('--config', dest='config', default='/etc/sitegen/sitegen.json', help='Configuration file path')

    parser.add_argument('--cert-request', metavar='domain', const='', nargs='?',
                        help='Request/renew a certificate. Request/renew all certificates if no domain is specified').completer = domain_completer
    parser.add_argument('--cert-check', metavar='domain', const='', nargs='?',
                        help='Check if certificate needs to be renewed. Check all if no domain is specified').completer = cert_completer
    parser.add_argument('--cert-renew', metavar='domain', const='', nargs='?',
                        help='Renew certificate if it needs to be. Renew all that needs to be if no domain is specified').completer = cert_completer
    parser.add_argument('--cert-enddate', metavar='enddate', const='', nargs='?',
                        help='Print certificate enddate. Print all certificates enddate if no domain is specified').completer = cert_completer

    parser.add_argument('--site-create', help='Create a site configuration in the form domain[:template]',
                        metavar='domain').completer = site_create_completer

    parser.add_argument('--hook-enable', help='Enable a site hook in the form (site|cert):hook_name',
                        dest='hook_enable', metavar='hook').completer = hook_completer
    parser.add_argument('--hook-disable', help='Disable a site hook in the form (site|cert):hook_name',
                        dest='hook_disable', metavar='hook').completer = hook_completer

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    site_gen = SiteGen(config)

    site_gen.make_dirs()

    try:
        if args.cert_request is not None:
            if args.cert_request == "":
                site_gen.certs_request(site_gen.get_all_certs())
            else:
                site_gen.cert_request(args.cert_request)

        elif args.cert_check is not None:
            if args.cert_check == "":
                site_gen.certs_check(site_gen.get_all_certs())
            else:
                site_gen.cert_check(args.cert_check)

        elif args.cert_renew is not None:
            if args.cert_renew == "":
                site_gen.certs_renew(site_gen.get_all_certs())
            else:
                site_gen.cert_renew(args.cert_renew)

        elif args.cert_enddate is not None:
            if args.cert_enddate == "":
                site_gen.certs_enddate(site_gen.get_all_certs())
            else:
                site_gen.cert_enddate(args.cert_enddate)

        elif args.site_create is not None:
            domain, inc, conf = parse_domain(args.site_create)
            site_gen.site_create(domain, inc, conf)

        elif args.hook_enable is not None:
            hook_type, hook_name = parse_hook(args.hook_enable)
            site_gen.hook_enable(hook_type, hook_name)

        elif args.hook_disable is not None:
            hook_type, hook_name = parse_hook(args.hook_disable)
            site_gen.hook_disable(hook_type, hook_name)

        else:
            parser.print_help()
    except SiteGenException as e:
        print(e.error)
        exit(e.code)

if __name__ == "__main__":
    main()
