from __future__ import division
from Brisk import Brisk
from BriskMap import BriskMap
import argparse
import time
import random
import math
from Player import Player
from collections import Counter

class AbstractBot(object):
    team_name = "Test Bot Please Ignore"
    supply_threshold = 0.1

    def __init__(self, game):
        self.layout = None
        self.game = game
        self.playerID = self.game.player_id
        self.otherID = 2 if self.playerID == 1 else 1
        self.player = None
        self.other = None
        self.iterations = 0

    def getMapLayout(self):
        self.layout = BriskMap(self.game.get_map_layout())

    """" Waits for turn, returning the updated reponse"""
    def wait_for_turn(self):
        while True:
            status = self.game.get_player_status()
            if status['current_turn'] or status['eliminated'] or status['winner']:
                print "Player status is : {}".format(status)
                return status
            else:
                time.sleep(1)

    def run(self):
        print "starting game {} we are player {}".format(self.game.game_id, self.game.player_id)
        self.getMapLayout()
        # print self.layout

        while True:
            status = self.wait_for_turn()
            if status['eliminated']:
                print "We lost"
                break
            if status['winner']:
                if status['winner'] == self.game.player_id:
                    print "We won"
                    # TODO: Reward?
                else:
                    print "Hit the limit of turns and lost"
                break
            self.executeStrategy(status)
            self.iterations += 1

    def executeStrategy(self, status):
        state = self.updatePlayerStates()
        self.supplyTroops(status, self.iterations)
        self.updatePlayerStates()
        self.attack()
        self.transferArmies()
    
    def updatePlayerStates(self):
        start = time.time()
        state = self.game.get_game_state()
        end = time.time()
        print "Getting player state took: {}".format(end-start)

        start = time.time()
        self.player = Player(self.playerID, self.layout, state)
        self.other = Player(self.otherID, self.layout, state)
        end = time.time()
        print "Updating players took: {}".format(end-start)
        return state

    def supplyTroops(self, status):
        pass

    def attack(self):
        pass

    def transferArmies(self):
        state = self.game.get_game_state()
        if state["winner"]:
            return
        self.game.end_turn()
