import os
import subprocess

from setuptools import setup, find_packages


data_files = []

if os.path.exists("/etc/default"):
    data_files.append(
        ('/etc/default', ['packaging/systemd/air-anchor-tp']))

if os.path.exists("/lib/systemd/system"):
    data_files.append(
        ('/lib/systemd/system',
         ['packaging/systemd/air-anchor-tp.service']))

setup(
    name='air_anchor_tp',
    version='1.0',
    description='Air Anchor Transaction Processor',
    author='divios',
    url='',
    packages=find_packages(),
    install_requires=[
        "cbor",
        "colorlog",
        "sawtooth-sdk",
        "requests",
        "pymongo",
        "protobuf==3.20.*"
    ],
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'air-anchor-tp = air_anchor_tp.main:main'
        ]
    })