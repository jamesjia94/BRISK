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
        armyReserves = self.player.armyReserves
        unconqueredContinents = sorted(self.player.unconqueredContinents.items(), key=lambda x: len(x[1]))
        for continent,territories in unconqueredContinents:
            if len(territories) > 2:
                break
            for territory in territories:
                for adjacentTerritory in territory.adjacentTerritories:
                    if adjacentTerritory in self.player.territories:
                        print "Placing on country {} with armies {} to conquer country {}".format(adjacentTerritory.id, int(self.player.armyReserves), territory.id)
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
        flag = True
        while flag:
            flag = False
            unconqueredContinents = sorted(self.player.unconqueredContinents.items(), key=lambda x: len(x[1]))
            for continent,territories in unconqueredContinents:
                if len(territories) > 2:
                    break

                continueFlag = True
                for territory in territories:
                    for adjacentTerritory in territory.adjacentTerritories:
                        if adjacentTerritory in self.player.territories:
                            if self.command_attack(adjacentTerritory, territory):
                                flag = True
                                continueFlag = False
                                break
                    if not continueFlag:
                        break
                if not continueFlag:
                    break

        borderTerritories = []
        for territory in self.player.territories:
            for adjacentTerritory in territory.adjacentTerritories:
                if adjacentTerritory not in self.player.territories:
                    borderTerritories.append(territory)
        
        while borderTerritories:
            curr_territory = borderTerritories.pop(0)
            adjacentTerritories = curr_territory.adjacentTerritories
            for adjacentTerritory in adjacentTerritories:
                if adjacentTerritory in self.other.territories:
                    capturedTerritory = self.command_attack(curr_territory, adjacentTerritory)
                    if capturedTerritory:
                        borderTerritories.append(capturedTerritory)

    def command_attack(self, attackingTerritory, defendingTerritory):
        capturedTerritory = None
        attackingArmies = self.player.territories[attackingTerritory]
        defendingArmies = self.other.territories[defendingTerritory]
        while attackingArmies > defendingArmies and attackingArmies > 2:
            result = self.game.attack(attackingTerritory.id, defendingTerritory.id, min(3, attackingArmies-1))
            attackingArmies = result["attacker_territory_armies_left"]
            defendingArmies = result["defender_territory_armies_left"]
            
            if result["defender_territory_captured"]:
                capturedTerritory = defendingTerritory
                if attackingArmies > 1:
                    self.game.transfer_armies(attackingTerritory.id, defendingTerritory.id, attackingArmies - 1)
                break
        self.updatePlayerStates()
        return capturedTerritory

    def transferArmies(self):
        state = self.game.get_game_state()
        if state["winner"]:
            return
        src = None
        dst = None
        pathLength = -1
        for continent in self.player.conqueredContinents:
            for territory in [nonborder for nonborder in continent.territories if nonborder not in continent.borderTerritories]:
                for border in continent.borderTerritories:
                    armiesToMove = self.player.territories[territory]-1
                    if armiesToMove > 1:
                        p = self.layout.getPath(territory,border)
                        if not src:
                            src = p[0]
                            dst = p[1]
                            pathLength = len(p)
                        elif pathLength > len(p):
                            src = p[0]
                            dst = p[1]
                            pathLength = len(p)
        if src:
            armiesToMove = self.player.territories[src]-1
            print "Transferring {} armies from {} to {} during army transfer phase.".format(armiesToMove, src.id,dst.id)
            self.game.transfer_armies(src.id,dst.id, armiesToMove)
        else:
            self.game.end_turn()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', default=None, type=int, help="Optional. The game id to join, 0 if we're first")
    args = parser.parse_args()
    game = Brisk(args.g, JiaBot.team_name)
    player = JiaBot(game)
    player.run()

if __name__ == '__main__':
    main()