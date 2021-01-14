#!/usr/bin/env python3

from omxplayer.player import OMXPlayer
from pathlib import Path
from time import sleep

import logging, logging.handlers
import signal, sys, os, getopt
import curses

import RPi.GPIO as GPIO
import yaml

BUTTON_GPIO_SWITCH_VIDEO = 16
BUTTON_GPIO_VOLUME_UP = 20
BUTTON_GPIO_VOLUME_DOWN = 21

class Video:  

    def __init__(self, path, crop, aspect, start, volume):  

        self.path = path  
        self.crop = crop
        self.aspect = aspect
        self.start = start
        self.volume = volume
   
class Player:

    def __init__(self, videos, log):

        self.videos = videos
        self.log = log
        self.currentVideo = 0
        self.dbusIndex = 0 

        # Create the first/active player
        self.activePlayer = self.initPlayer(self.videos[0], self.log)

        # Show active player
        self.activePlayer.play()
        self.activePlayer.show_video()

        # Create the paused player
        self.pausedPlayer = self.initPlayer(self.videos[1], self.log)

    def initPlayer(self, video, log):

        if self.dbusIndex == 0:
            dbusName = 'org.mpris.MediaPlayer2.omxplayer1'
        else:
            dbusName = 'org.mpris.MediaPlayer2.omxplayer2'

        self.dbusIndex = 0 if self.dbusIndex == 1 else 1

        player = OMXPlayer(video.path, dbus_name=dbusName, args=['--loop'])

        player.hide_video()
        player.pause()
        player.set_position(video.start)
        if video.crop is not None:
            player.set_video_crop(video.crop[0], video.crop[1], video.crop[2], video.crop[3])
        player.set_volume(video.volume)
        player.set_aspect_mode(video.aspect)

        return player

    def playNext(self):

        if debug: self.log.info("Playing next video")

        self.currentVideo = self.currentVideo + 1

        if self.currentVideo == len(self.videos):
            self.currentVideo = 0

        # Show the paused player
        if debug: self.log.info("Showing paused player")
        self.pausedPlayer.play()
        self.pausedPlayer.show_video()

        # Sleep for an appropriate amount of time so we get a seamless transition
        sleep(.15)

        # Hide and quit the active player 
        if debug: self.log.info("Hiding active player")
        self.activePlayer.hide_video()
        self.activePlayer.quit()

        # Switch the players
        self.activePlayer = self.pausedPlayer

        # Create a new player for the one we just quit using the next video
        if debug: self.log.info("Creating new paused player")
        self.pausedPlayer = self.initPlayer(self.videos[self.getNextVideoIndex()], self.log)

    def getNextVideoIndex(self):

        return 0 if self.currentVideo == len(self.videos) - 1 else self.currentVideo + 1

    def position(self):

        return self.activePlayer.position()

    def duration(self):

        return self.activePlayer.duration()

    def restart(self):

        self.activePlayer.set_position(self.videos[self.currentVideo].start)

    def action(self, key):

        self.activePlayer.action(key)

    def volume(self, volChange):

        newVol = self.activePlayer.volume() + volChange

        if newVol < 0:
            newVol = 0
        elif newVol > 10:
            newVol = 10

        return self.activePlayer.set_volume(newVol)

    def quit(self):

        self.activePlayer.quit()
        self.pausedPlayer.quit()

# Signal handler - Cleans up in case of control C
def signal_handler(sig, frame):

    global quit

    if debug: logging.debug("CTRL C detected")

    quit = True

def cleanUp():

    if debug: logging.debug("Performing cleanup")

    player.quit()

    GPIO.cleanup()

    curses.nocbreak()
    curses.echo()
    curses.endwin()

    if debug: logging.debug("About to exit")

    sys.exit(0)

# GPIO Button callbacks
# We just set flags here so the actual changes to the OMXPlayer are done in the main loop
# so as to minimise the time in the GPIO callbacks
def gpio_switch_video(channel):

    global requestSwitchVideo

    if debug: logging.debug("gpio_switch_video")

    requestSwitchVideo = True

def gpio_volume_up(channel):

    global requestVolumeUp

    if debug: logging.debug("gpio_volume_up")

    requestVolumeUp = True

def gpio_volume_down(channel):

    global requestVolumeDown

    if debug: logging.debug("gpio_volume_down")

    requestVolumeDown = True

# Parse command line
loglevel = 'WARNING'
debug = False

try:
    options, remainder = getopt.gnu_getopt(sys.argv[1:], '', ['loglevel=', 'debug='])

except getopt.GetoptError as err:
    print('pifire: Invalid command line:', err)
    sys.exit(1)

for opt, arg in options:
    if opt in ('--loglevel'):
        loglevel = arg
    if opt in ('--debug'):
        debug = True

# Setup logging
logger = None

if debug:

    logger = logging.getLogger('pifire')
    logger.setLevel(getattr(logging, loglevel.upper()))

    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

    fileHandler = logging.handlers.RotatingFileHandler("pifire.log", maxBytes=(1048576 * 1), backupCount=2)
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    logger.info("piFire starting....")

# Use GPIO Numbering
GPIO.setmode(GPIO.BCM)

# Setup GPIO buttons
GPIO.setup(BUTTON_GPIO_SWITCH_VIDEO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_GPIO_VOLUME_UP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_GPIO_VOLUME_DOWN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.add_event_detect(BUTTON_GPIO_SWITCH_VIDEO, GPIO.FALLING, callback=gpio_switch_video, bouncetime=100)
GPIO.add_event_detect(BUTTON_GPIO_VOLUME_UP, GPIO.FALLING, callback=gpio_volume_up, bouncetime=100)
GPIO.add_event_detect(BUTTON_GPIO_VOLUME_DOWN, GPIO.FALLING, callback=gpio_volume_down, bouncetime=100)

# Catch CTRL C
signal.signal(signal.SIGINT, signal_handler)

stdscr = curses.initscr()

curses.noecho()
curses.cbreak()
stdscr.nodelay(1)

# Load the video data from the YAML file
videos = []

with open('pifire.yaml') as file:

    piFireData = yaml.full_load(file)

    for video in piFireData['videos']:

        videos.append(Video(video['path'], video['crop'], video['aspect'], video['start'], video['volume']))

# Get ready for main loop
requestSwitchVideo = False
requestVolumeUp = False
requestVolumeDown = False

# Create the player
player = Player(videos, logger)

quit = False

while quit == False:

    # Work out position and duration and loop to start if at end
    pos = player.position()
    dur = player.duration()

    if pos > (dur - 1): 
        player.restart()

    # Process any key presses
    key = stdscr.getch()

    if key != -1:
        if debug: logging.debug("Keypress - Key value = " + str(key))

    # Esc or Q
    if key == 27 or key == 113:

        if debug: logging.debug("Keypress - Quit")

        quit = True

    # Minus
    elif key == 45:

        if debug: logging.debug("Keypress - Volume down")

        requestVolumeDown = True

    # Equals
    elif key == 61:

        if debug: logging.debug("Keypress - Volume up")

        requestVolumeUp = True

    # S or Space
    elif key == 115 or key == 32:

        if debug: logging.debug("Keypress - Switch video")

        requestSwitchVideo = True

    # Process requests from GPIO or key presses
    if requestSwitchVideo:

        if debug: logging.debug("Switching video")

        player.playNext()

        requestSwitchVideo = False

    if requestVolumeUp:

        if debug: logging.debug("Increasing volume")

        player.volume(0.1)

        requestVolumeUp = False

    if requestVolumeDown:

        if debug: logging.debug("Decreasing volume")

        player.volume(-0.1)

        requestVolumeDown = False

    sleep(0.1)

if debug: logging.debug("Shutting down")

cleanUp()
