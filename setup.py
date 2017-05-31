#! /usr/bin/env python
from os import path
import os
from setuptools import setup, find_packages

install_requires = [
    'argcomplete'
]

here = path.abspath(path.dirname(__file__))


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join(path, filename))
    return paths

setup(
    name='sitegencli',
    version="1.0.0",

    description="CLI tool to build web site configuration",
    long_description="""\
CLI tool to build web site configuration and obtain SSL certificates from letsencrypt using certbot.
Also provide a simpler way to request SSL certificate over certbot""",

    url='https://git.rthoni.com/robin.thoni/sitegen',
    author="Robin Thoni",
    author_email='robin@rthoni.com',

    license='MIT',

    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 5 - Production/Stable',

        # Indicate who your project is intended for
        'Intended Audience :: System Administrators',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    keywords="certbot apache ssl",

    packages=find_packages(),
    install_requires=install_requires,

    extras_require={
        'dev': [],
        'test': [],
    },

    package_data={
    },

    data_files=[
        ('/etc/bash_completion.d/', ['extra/bash/sitegen']),
        ('share/sitegen/', ['extra/apache/sitegen.conf']),
        ('etc/sitegen/', ['extra/sitegen/sitegen.json']),
        ('etc/sitegen/hooks-available/cert/', package_files('extra/sitegen/hooks-available/cert/')),
        ('etc/sitegen/hooks-available/site/', package_files('extra/sitegen/hooks-available/site/')),
        ('etc/sitegen/templates/', package_files('extra/sitegen/templates/'))
    ],

    entry_points={
        'console_scripts': [
            'sitegen=sitegencli.sitegen:main',
        ],
    },

    cmdclass={
        # 'install': PostInstallCommand,
    }
)
