#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from setuptools import setup, find_packages


setup(
    name="RapidSMS",
    version="0.9.1a",
    license="BSD",

    install_requires = [
        "django",
        "django-nose",
        "djtables",
        "djappsettings"
    ],

    scripts = ["bin/rapidsms-admin.py"],

    author="RapidSMS development community",
    author_email="rapidsms@googlegroups.com",

    maintainer="RapidSMS development community",
    maintainer_email="rapidsms@googlegroups.com",

    description="Build SMS applications with Python and Django",
    url="http://github.com/rapidsms/rapidsms-core-dev",

    package_dir = {"": "lib"},
    packages = find_packages("lib"))
