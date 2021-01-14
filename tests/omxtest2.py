#!/usr/bin/env python3

from omxplayer.player import OMXPlayer
from pathlib import Path
from time import sleep
import logging
import sys, os
import curses

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

        self.player1 = self.initPlayer(self.videos[0], 'org.mpris.MediaPlayer2.omxplayer1', log)

        # Show player 1
        self.player1.play()
        self.player1.show_video()
        self.player1.active = True

        self.activePlayer = self.player1

        self.player2 = self.initPlayer(self.videos[1], 'org.mpris.MediaPlayer2.omxplayer2', log)

    def initPlayer(self, video, dbusName, log):

        player = OMXPlayer(video.path, dbus_name=dbusName, args=['--loop'])

        player.hide_video()
        player.pause()
        player.set_position(video.start)
        player.set_volume(video.volume)
        player.set_aspect_mode(video.aspect)

        player.active = False

        return player

    def playNext(self):

        self.currentVideo = self.currentVideo + 1

        if self.currentVideo == len(self.videos):

            self.currentVideo = 0

        if self.player1.active:
            activePlayer = self.player1
            pausedPlayer = self.player2
        else:
            activePlayer = self.player2
            pausedPlayer = self.player1

        # Show the paused player
        self.pausedPlayer.play()
        self.pausedPlayer.show_video()
        self.pausedPlayer.active = True

        sleep(.15)

        # Hide and quit the active player 
        self.activePlayer.hide_video()
        self.activePlayer.quit()
        self.activePlayer.active = False

        # Switch the players
        self.activePlayer = self.pausedPlayer

        # Create a new player for the one we just quit using the next video
        self.pausedPlayer = self.initPlayer(self.videos[self.getNextVideoIndex()], 'org.mpris.MediaPlayer2.omxplayer1', log)


        # self.activePlayer = self.pausedPlayer

        # # If player 1 playing
        # if self.player1.active:

        #     # Show player 2
        #     self.player2.play()
        #     self.player2.show_video()
        #     sleep(.15)
        #     self.player1.hide_video()
        #     self.player1.quit()

        #     self.player1 = self.initPlayer(self.videos[self.getNextVideoIndex()], 'org.mpris.MediaPlayer2.omxplayer1', log)

        #     self.player1.active = False
        #     self.player2.active = True

        #     self.activePlayer = self.player2

        # # If player 2 playing
        # elif self.player2.active:

        #     # Show player 1
        #     self.player1.play()
        #     self.player1.show_video()
        #     sleep(.15)
        #     self.player2.hide_video()
        #     self.player2.quit()

        #     self.player2 = self.initPlayer(self.videos[self.getNextVideoIndex()], 'org.mpris.MediaPlayer2.omxplayer2', log)

        #     self.player1.active = True
        #     self.player2.active = False

        #     self.activePlayer = self.player1

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

        self.player1.quit()
        self.player2.quit()

videos = []

videos.append(Video('../shared/fireplace.mp4', [160, 0, 1760, 1200], 'fill', 0, 1.5))
videos.append(Video('../shared/aquarium.mp4', None, 'fill', 0, 5.5))
videos.append(Video('../shared/beach.mp4', None, 'fill', 5, 0.5))
videos.append(Video('../shared/river.mp4', None, 'fill', 2, 0.5))
videos.append(Video('../shared/testcard.mp4', None, 'fill', 0, 0.25))
#videos.append(Video('../shared/matrix.mp4', None, 'fill', 0, 1.0))
#videos.append(Video('../shared/timer.mp4', None, 'fill', 10, 0.25))

stdscr = curses.initscr()

curses.noecho()
curses.cbreak()
stdscr.nodelay(1)

logging.basicConfig(level=logging.INFO)

log = logging.getLogger("Player 1")

player = Player(videos, log)

quit = False

while quit == False:

  key = stdscr.getch()

  pos = player.position()
  dur = player.duration()

  stdscr.addstr(1, 1, str(pos) + ', ' + str(dur) + '         ')

  if pos > (dur - 1): 
    player.restart()

  if key == 27:

    quit = True

  elif key == 45:

    vol = player.volume(-0.1)
    log.info("Volume = " + str(vol))

  elif key == 61:

    vol = player.volume(0.1)
    log.info("Volume = " + str(vol))

  elif key == 115:

      player.playNext()

  sleep(0.1)

player.quit()

curses.nocbreak()
curses.echo()
curses.endwin()
