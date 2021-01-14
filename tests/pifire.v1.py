#!/usr/bin/env python3

from omxplayer.player import OMXPlayer
from pathlib import Path
from time import sleep
import logging
import sys, os
import curses

class video:  

    def __init__(self, path, crop, aspect, start, volume):  

        self.path = path  
        self.crop = crop
        self.aspect = aspect
        self.start = start
        self.volume = volume
   
videos = []
videos.append(video('../shared/fireplace.mp4', [160, 0, 1760, 1200], 'fill', 0, 1.5))
videos.append(video('../shared/aquarium.mp4', None, 'fill', 0, 5.6))
videos.append(video('../shared/beach.mp4', None, 'fill', 5, 0.5))
videos.append(video('../shared/matrix.mp4', None, 'fill', 0, 1.0))
videos.append(video('../shared/river.mp4', None, 'fill', 0, 0.5))
videos.append(video('../shared/testcard.mp4', None, 'fill', 0, 0.35))
videos.append(video('../shared/timer.mp4', None, 'fill', 10, 0.35))

def playVideo(video, player_log):

    if Path(video.path).is_file():

        player = OMXPlayer(video.path, dbus_name='org.mpris.MediaPlayer2.omxplayer1', args=['--loop'])

        player.playEvent += lambda _: player_log.info("Play")
        player.pauseEvent += lambda _: player_log.info("Pause")
        player.stopEvent += lambda _: player_log.info("Stop")

        player.hide_video()

        player.set_position(video.start)
        player.set_volume(video.volume)

        if video.crop != None:
            player.set_video_crop(video.crop[0], video.crop[1], video.crop[2], video.crop[3])

        player.set_aspect_mode(video.aspect)

        player.show_video()
        player.play()

        return player

    else:

        return None

stdscr = curses.initscr()

curses.noecho()
curses.cbreak()
stdscr.nodelay(1)

logging.basicConfig(level=logging.INFO)

player_log = logging.getLogger("Player 1")

currentVideo = 0
player = playVideo(videos[0], player_log)

quit = False

while quit == False:

  key = stdscr.getch()

  pos = player.position()
  dur = player.duration()

  stdscr.addstr(1, 1, str(pos) + ', ' + str(dur) + '         ')

  if pos > (dur - 1): 
    player.set_position(videos[currentVideo].start)

  if key == 27:

    quit = True

  elif key == 45:

    player.action(17)
    player_log.info("Volume = ", player.volume())

  elif key == 61:

    player.action(18)
    player_log.info("Volume = ", player.volume())

  elif key == 115:

    player.quit()

    player = None

    while player is None:

      currentVideo = currentVideo + 1

      if currentVideo == len(videos):
        currentVideo = 0

      player = playVideo(videos[currentVideo], player_log)

  sleep(0.1)

player.quit()

curses.nocbreak()
curses.echo()
curses.endwin()
