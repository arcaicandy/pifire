#!/usr/bin/env python3

from omxplayer.player import OMXPlayer
from pathlib import Path
from time import sleep

VIDEO_PATH = Path("../shared/fireplace1.mp4")

player = OMXPlayer(VIDEO_PATH)

sleep(10)

player.quit()

