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
import traceback

class JiaBot(AbstractBot):
    team_name = "Ign"
    supply_threshold = 0.1

    def supplyTroops(self, status):
        print "Supply Phase"
        # Place our troops to conqueredContinents a continent.
        armyReserves = self.player.armyReserves
        unconqueredContinents = sorted(self.player.unconqueredContinents.items(), key=lambda x: (len(x[1]["unconqueredTerritories"]),-x[0].continentBonus/len(x[0].borderTerritories)))
        for continent,territoryDict in unconqueredContinents:
            unconqueredTerritories = territoryDict["unconqueredTerritories"]
            if len(unconqueredTerritories) > 0.75 * len(continent.territories):
                print "Continent {} has too many territories to conquer".format(continent.name)
                break
            for territory in unconqueredTerritories:
                for adjacentTerritory in territory.adjacentTerritories:
                    if adjacentTerritory in self.player.territories:
                        print "Placing on territory {} with armies {} to conquer territory {}".format(adjacentTerritory.id, int(self.player.armyReserves), territory.id)
                        self.game.place_armies(adjacentTerritory.id, int(self.player.armyReserves))
                        return

        # Place our troops that border an enemy continent.
        enemyContinents = sorted(self.other.conqueredContinents, key=lambda x: x.continentBonus, reverse=True)
        for continent in enemyContinents:
            for territory in continent.territories:
                for adjacentTerritory in territory.adjacentTerritories:
                    if adjacentTerritory in self.player.territories:
                        print "Placing on territory {} with armies: {}".format(adjacentTerritory.id, int(self.player.armyReserves))
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
        print "Attack Phase"
        start = time.time()
        flag = True
        while flag:
            flag = False
            unconqueredContinents = sorted(self.player.unconqueredContinents.items(), key=lambda x: (len(x[1]["unconqueredTerritories"]),-x[0].continentBonus/len(x[0].borderTerritories)))
            for continent,territoryDict in unconqueredContinents:
                unconqueredTerritories = territoryDict["unconqueredTerritories"]
                conqueredTerritories = territoryDict["conqueredTerritories"]
                if len(unconqueredTerritories) > 0.75 * len(continent.territories):
                    break
                continueFlag = True
                for attackingTerritory in conqueredTerritories:
                    attackingArmies = self.player.territories[attackingTerritory]
                    if attackingArmies > 2:
                        for adjacentTerritory in attackingTerritory.adjacentTerritories:
                            if adjacentTerritory in self.other.territories:
                                if self.command_attack(attackingTerritory, adjacentTerritory):
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
        end = time.time()
        print "Attack phase took: {}".format(end-start)

    def command_attack(self, attackingTerritory, defendingTerritory):
        capturedTerritory = None
        attackingArmies = self.player.territories[attackingTerritory]
        defendingArmies = self.other.territories[defendingTerritory]
        while attackingArmies > defendingArmies and attackingArmies > 2:
            print "attacking: {} from {} with {} armies".format(attackingTerritory.id, defendingTerritory.id, min(3, attackingArmies-1))
            result = self.game.attack(attackingTerritory.id, defendingTerritory.id, min(3, attackingArmies-1))
            attackingArmies = result["attacker_territory_armies_left"]
            defendingArmies = result["defender_territory_armies_left"]
            self.player = self.player.attackResult(result)
            self.other = Player(self.other.id, self.other.layout, self.player.state)
            if result["defender_territory_captured"]:
                capturedTerritory = defendingTerritory
                if attackingArmies > 2:
                    print "Captured territory: Transfering army from territory {} to territory {} using armies {}".format(attackingTerritory.id, defendingTerritory.id, attackingArmies - 2)
                    self.game.transfer_armies(attackingTerritory.id, defendingTerritory.id, attackingArmies - 2)
                    self.player = self.player.transferArmy(attackingTerritory.id, defendingTerritory.id, attackingArmies - 2)
                    self.other = Player(self.other.id, self.other.layout, self.player.state)
                break
        
        return capturedTerritory

    def transferArmies(self):
        state = self.game.get_game_state()
        if state["winner"]:
            return
        print "Transfer phase"
        territoriesByArmies = sorted(self.player.territories.items(), key=lambda x: x[1], reverse=True)
        for continent in self.player.conqueredContinents:
            nonborderTerritories = [nonborder for nonborder in continent.territories if nonborder not in continent.borderTerritories]
            sortedNonBorderTerritories = sorted(nonborderTerritories, key=lambda x: self.player.territories[x],reverse=True)
            for territory in sortedNonBorderTerritories:
                for border in continent.borderTerritories:
                    for adjacentTerritory in border.adjacentTerritories:
                        if adjacentTerritory.continent not in self.player.conqueredContinents:
                            armiesToMove = self.player.territories[territory]-1
                            if armiesToMove > 1:
                                p = self.layout.getPath(territory,border)
                                print "transferring {} to {} using {}".format(territory.id,p[1].id,armiesToMove)
                                self.game.transfer_armies(territory.id,p[1].id, armiesToMove)
                                return
                for othercontinent in self.player.conqueredContinents:
                    for border in othercontinent.borderTerritories:
                        for adjacentTerritory in border.adjacentTerritories:
                            if adjacentTerritory.continent not in self.player.conqueredContinents:
                                armiesToMove = self.player.territories[territory]-1
                                if armiesToMove > 1:
                                    p = self.layout.getPath(territory,border)
                                    print "transferring {} to {} using {}".format(territory.id,p[1].id,armiesToMove)
                                    self.game.transfer_armies(territory.id,p[1].id, armiesToMove)
                                    return
        print "Ending turn"
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