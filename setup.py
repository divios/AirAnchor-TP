import os
import subprocess

from setuptools import setup, find_packages


data_files = []

if os.path.exists("/etc/default"):
    data_files.append(
        ('/etc/default', ['packaging/systemd/sawtooth-location-tp-python']))

if os.path.exists("/lib/systemd/system"):
    data_files.append(
        ('/lib/systemd/system',
         ['packaging/systemd/location-tp-python.service']))

setup(
    name='sawtooth_location_key',
    version='1.0',
    description='Sawtooth Location Python',
    author='Hyperledger Sawtooth',
    url='https://github.com/hyperledger/sawtooth-sdk-python',
    packages=find_packages('app'),
    install_requires=[
        "cbor",
        "colorlog",
        "sawtooth-sdk",
    ],
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'location-tp-python = app.main:main'
        ]
    })