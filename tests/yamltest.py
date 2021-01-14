#!/usr/bin/env python3

from pathlib import Path

import signal, sys, os, getopt

import yaml

with open('pifire.yaml') as file:

    piFireData = yaml.full_load(file)

    for video in piFireData['videos']:

        print(video['id'], ":")

        crop = video['crop']

        if crop == None:
            print(None)            
        else:
            print(crop[0])