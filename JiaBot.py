from __future__ import division
from Brisk import Brisk
from BriskMap import BriskMap
import argparse
import time
import random
import math
from Player import Player
from collections import Counter
# globald = {}

class JiaBot(object):
    team_name = "Test Bot Please Ignore"
    supply_threshold = 0.1

    def __init__(self):
        self.layout = None
        self.game = None
        self.state = None
        self.otherState = None

    def getMapLayout(self):
        self.layout = BriskMap(self.game.get_map_layout())

    """" Waits for turn, returning the updated reponse"""
    def wait_for_turn(self):
        while True:
            status = self.game.get_player_status()
            if status['current_turn'] or status['eliminated'] or status['winner']:
                return status

    def run(self, game_num=None):
        self.game = Brisk(game_num, self.team_name)
        print "starting game {} we are player {}".format(self.game.game_id, self.game.player_id)
        self.getMapLayout()
        # print self.layout

        if self.game.player_id == 1:
            self.state = Player(1, self.layout)
            self.otherState = Player(2, self.layout)
        else:
            self.state = Player(2, self.layout)
            self.otherState = Player(1, self.layout)

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
            self.game.end_turn()

    def executeStrategy(self, status):
        self.updatePlayerStates()
        # print self.state
        # print self.otherState
        self.supplyTroops(status)
    
    def updatePlayerStates(self):
        state = self.game.get_game_state()
        print "Total turns: {}".format(state["num_turns_taken"] + 1)
        self.clearPlayerStates()

        for territory in state["territories"]:
            # print "territory {} is held by player {}".format(territory["territory"], territory["player"])
            if territory["player"] == self.state.id:
                self.state.updateTerritories(self.layout.getTerritoryByID(territory["territory"]), territory["num_armies"])
            else:
                self.otherState.updateTerritories(self.layout.getTerritoryByID(territory["territory"]), territory["num_armies"])

        self.state.updateCountries()
        self.state.updateArmyReserves()
        self.otherState.updateCountries()
        self.otherState.updateArmyReserves()

    def supplyTroops(self, status):
        # Find all of our territories that border an enemy territory
        borderTerritories = Counter()
        for territory in self.state.territories:
            for adjacentTerritory in territory.adjacentTerritories:
                if adjacentTerritory in self.otherState.territories:
                    borderTerritories[territory] += self.otherState.territories[adjacentTerritory]
            borderTerritories[territory] /= self.state.territories[territory]

        # print "Prenorm borderTerritories: {}".format(borderTerritories)

        # Ignore small values
        for border,value in borderTerritories.items():
            if value < self.supply_threshold:
                del borderTerritories[border]

        # Normalize
        totalValues = sum(borderTerritories.values(), 0.0)
        if totalValues:
            for border in borderTerritories:
                borderTerritories[border] /= totalValues
        
        # Can use either.
        reserves = status["num_reserves"]
        # reserves = self.state.armyReserves
        assert self.state.armyReserves == reserves

        placements = {}
        spilloverBorder = None
        spilloverBorderValue = 0
        totalReservesAdded = 0
        # print "border values: {}".format(borderTerritories)
        for border,value in borderTerritories.items():
            if spilloverBorderValue < value:
                spilloverBorder = border
                spilloverBorderValue = value
            reservesToAdd = math.floor(reserves * value)
            placements[border] = reservesToAdd
            totalReservesAdded += reservesToAdd

        # BorderTerritories was empty.
        if spilloverBorder == None:
            spilloverBorder = random.randint(0, len(status['territories']) - 1)

        if spilloverBorder in placements:
            placements[spilloverBorder] += max(0, reserves - totalReservesAdded)
        else:
            placements[spilloverBorder] = max(0, reserves - totalReservesAdded)

        # print placements
        # print "reserves: {}".format(self.state.armyReserves)
        for border, army in placements.items():
            if army:
                print "Placing on country {} with armies: {}".format(border.id, int(army))
                self.game.place_armies(border.id, int(army))

    def clearPlayerStates(self):
        self.state.clearState()
        self.otherState.clearState()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', default=None, type=int, help="Optional. The game id to join, 0 if we're first")
    args = parser.parse_args()
    player = JiaBot()
    # globald["player"] = player
    player.run(args.g)

if __name__ == '__main__':
    main()