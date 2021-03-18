#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = [
    "pdfreader==0.1.7",
    "python-dateutil==2.8.1",
]

extras = {"gui": ["PyQt5"]}

setup(
    name="insurrector",
    version="0.0.1",
    description=(
        "Tool to process income from stock trading to prepare Czech tax return."
    ),
    long_description=readme,
    author="Pavol Babinčák",
    author_email="scroolik@gmail.com",
    url="https://github.com/scrool/insurrector",
    packages=[
        "insurrector",
        "insurrector.calculators",
        "insurrector.parsers",
        "insurrector.gui",
    ],
    entry_points={
        "console_scripts": [
            "insurrector-cli=insurrector.cli:main",
            "insurrector-gui=insurrector.gui.main:main [gui]",
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    extras_require=extras,
    license="MIT license",
    zip_safe=False,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
    ],
)
