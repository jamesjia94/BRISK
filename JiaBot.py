from __future__ import division
from Brisk import Brisk
from BriskMap import BriskMap
import argparse
import time
import random
import math
from AbstractBot import AbstractBot
from Player import Player
from collections import Counter

class JiaBot(AbstractBot):
    team_name = "Test Bot Please Ignore"
    supply_threshold = 0.1

    def supplyTroops(self, status):
        # Place our troops to conquer a continent.
        unconqueredContinents = sorted(self.player.unconqueredContinents.items(), key=lambda x: x[1], reverse=True)
        for continent,territories in unconqueredContinents:
            if len(territories) > 2:
                break
            for adjacentTerritory in territories[0].adjacentTerritories:
                if adjacentTerritory in self.player.territories:
                    print "Placing on country {} with armies: {}".format(adjacentTerritory.id, int(self.player.armyReserves))
                    self.game.place_armies(adjacentTerritory.id, int(self.player.armyReserves))
                    return

        # Place our troops that border an enemy continent.
        enemyContinents = sorted(self.other.conqueredContinents, key=lambda x: x.continentBonus, reverse=True)
        for continent in enemyContinents:
            for territory in continent.territories:
                for adjacentTerritory in territory.adjacentTerritories:
                    if adjacentTerritory in self.player.territories:
                        print "Placing on country {} with armies: {}".format(adjacentTerritory.id, int(self.player.armyReserves))
                        self.game.place_armies(adjacentTerritory.id, int(self.player.armyReserves))
                        return

        # Find all of our territories that border an enemy territory
        borderTerritories = Counter()
        for territory in self.player.territories:
            for adjacentTerritory in territory.adjacentTerritories:
                if adjacentTerritory in self.other.territories:
                    borderTerritories[territory] += self.other.territories[adjacentTerritory]
            borderTerritories[territory] /= self.player.territories[territory]

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
        # reserves = self.player.armyReserves
        assert self.player.armyReserves == reserves

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

        for border, army in placements.items():
            if army:
                print "Placing on country {} with armies: {}".format(border.id, int(army))
                self.game.place_armies(border.id, int(army))

    def attack(self):
        borderTerritories = []
        for territory in self.player.territories:
            for adjacentTerritory in territory.adjacentTerritories:
                if adjacentTerritory in self.other.territories:
                    borderTerritories.append(territory)
        newPlayer = self.player
        while borderTerritories:
            curr_territory = borderTerritories.pop(0)
            adjacentTerritories = curr_territory.adjacentTerritories
            for adjacentTerritory in adjacentTerritories:
                if adjacentTerritory in self.other.territories:
                    attackingArmies = self.player.territories[curr_territory]
                    defendingArmies = self.other.territories[adjacentTerritory]
                    while attackingArmies > defendingArmies and attackingArmies > 2:
                        result = self.game.attack(curr_territory.id, adjacentTerritory.id, min(3, attackingArmies-1))
                        attackingArmies = result["attacker_territory_armies_left"]
                        defendingArmies = result["defender_territory_armies_left"]
                        newPlayer = newPlayer.attackResult(result)
                        currState = self.game.get_game_state()
                        try:
                            assert cmp(newPlayer.state["territories"], currState["territories"]) == 0
                        except Exception:
                            print "Attacking armies left: {}".format(attackingArmies)
                            print "Defending armies left: {}".format(defendingArmies)
                            print "newPlayer: {}".format(newPlayer.state["territories"])
                            print "currState: {}".format(currState["territories"])
                            print "\n\n\n"
                            raise Exception()
                        if result["defender_territory_captured"]:
                            if attackingArmies > 1:
                                newPlayer = newPlayer.transferArmy(curr_territory.id, adjacentTerritory.id, attackingArmies - 1)
                                self.game.transfer_armies(curr_territory.id, adjacentTerritory.id, attackingArmies - 1)
                                currState = self.game.get_game_state()
                                try:
                                    assert cmp(newPlayer.state["territories"], currState["territories"]) == 0
                                except Exception:
                                    print "newPlayer: {}".format(newPlayer.state["territories"])
                                    print "currState: {}".format(currState["territories"])
                                    print "\n\n\n"
                                    raise Exception()
                                borderTerritories.append(adjacentTerritory)
                            break
                    self.updatePlayerStates()
                    newPlayer = self.player

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', default=None, type=int, help="Optional. The game id to join, 0 if we're first")
    args = parser.parse_args()
    game = Brisk(args.g, JiaBot.team_name)
    player = JiaBot(game)
    player.run()

if __name__ == '__main__':
    main()