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
    # off by 1 because attacker is each row and starts with 1, defender is also off by 1
    ATTACK_PROB = [[0.417,0.106,0.027,0.007,0.002,0.000,0.000,0.000,0.000,0.000],[0.754,0.363,0.206,0.091,0.049,0.021,0.011,0.005,0.003,0.001],[0.916,0.656,0.470,0.315,0.206,0.134,0.084,0.054,0.033,0.021],[0.972,0.785,0.642,0.477,0.359,0.253,0.181,0.123,0.086,0.057],[0.990,0.890,0.769,0.638,0.506,0.397,0.297,0.224,0.162,0.118],[0.997,0.934,0.857,0.745,0.638,0.521,0.423,0.329,0.258,0.193],[0.999,0.967,0.910,0.834,0.736,0.640,0.536,0.446,0.357,0.287],[1.000,0.980,0.947,0.888,0.818,0.730,0.643,0.547,0.464,0.380],[1.000,0.990,0.967,0.930,0.873,0.808,0.726,0.646,0.558,0.480],[1.000,0.994,0.981,0.954,0.916,0.861,0.800,0.724,0.650,0.568]]

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
                # print "Player status is : {}".format(status)
                return status
            else:
                time.sleep(1)

    def run(self):
        print "starting game {} we are player {}".format(self.game.game_id, self.game.player_id)
        self.getMapLayout()
        # print self.layout

        while True:
            try:
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
            except:
                pass

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
        # print "Getting player state took: {}".format(end-start)

        start = time.time()
        self.player = Player(self.playerID, self.layout, state)
        self.other = Player(self.otherID, self.layout, state)
        end = time.time()
        # print "Updating players took: {}".format(end-start)
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

    def get_attack_probability(self, attack, defend):
        attacking_num = attack
        defending_num = defend
        while attacking_num > 9 or defending_num > 9:
            attacking_num -= 1
            defending_num -= 1
        return self.ATTACK_PROB[max(0,attacking_num)][max(0,defending_num)]
