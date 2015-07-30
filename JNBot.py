from __future__ import division
from JiaBot import JiaBot
from Player import Player
import argparse
from Brisk import Brisk
from BriskMap import BriskMap
import time
import random
import math
from collections import Counter

class JNBot(JiaBot):
    team_name = "NJ"
    def calc_attack_path(self):
        unconqueredContinents = sorted(self.player.unconqueredContinents.items(), key=lambda x: (len(x[1]["unconqueredTerritories"]),-x[0].continentBonus/len(x[0].borderTerritories)))
        # Loop over each continent
        return_paths =[]
        for continent,territoryDict in unconqueredContinents:
            unconqueredTerritories = territoryDict["unconqueredTerritories"]
            conqueredTerritories = territoryDict["conqueredTerritories"]
            #set(conqueredTerritories) & set(continent.borderTerritories)
            return_paths += self.calc_optimal_paths(conqueredTerritories, conqueredTerritories, continent.borderTerritories, False)
            return_paths += self.calc_optimal_paths(conqueredTerritories, unconqueredTerritories, continent.borderTerritories, True)
        return sorted(return_paths, key=lambda p: (p.goodness,p.armies_needed[0]))

    def calc_optimal_paths(self, start_points, end_points, borders, is_transfer):
        # TODO: optimize by number of bordering enemy territories on end point
        paths_through = []
        for start_point in start_points:
            for end_point in end_points:
                if start_point.id == end_point.id:
                    continue
                for border_territory in borders:
                    start_to_border = self.layout.shortestPathMatrix[start_point.id-1][border_territory.id-1]
                    end_to_border = self.layout.shortestPathMatrix[end_point.id-1][border_territory.id-1]
                # Need to minimize this
                closeness_to_border = start_to_border + end_to_border
                all_paths = self.player.get_paths(start_point, end_point)
                # Calc needed armies for each path
                for path in all_paths:
                    start_army = self.calc_start_armies(path)
                    end_army = start_army - (len(path)-1)*2
                    
                    # if len(range(start_army, end_army, -2)) == 0:
                    #     print "Path: {}".format(path)
                    #     print "Start_army {}: end_army {}".format(start_army, end_army) 
                    path = Path(path, range(start_army, end_army, -2), is_transfer, closeness_to_border)
                    paths_through.append(path)
        return paths_through

    def calc_start_armies(self,path):
        steps = len(path)-1
        enemies = 0
        for i in xrange(1, len(path)):
            enemies += self.other.territories[path[i]]
        return enemies + steps*2


    def supplyTroops(self, optimal_paths):
        print "Supply troop phase"
        armyReserves = self.player.armyReserves
        for path_obj in optimal_paths:
            if armyReserves < 0:
                return
            territory = path_obj.path[0]
            num_armies_in_start = self.player.territories[territory]
            num_armies_to_supply = min(path_obj.armies_needed[0] - num_armies_in_start, armyReserves)
            if num_armies_to_supply > 0:
                print "optimal path is: {}".format(path_obj)
                print "Supplying troops to territory {} with {} armies".format(territory.id, num_armies_to_supply)
                self.game.place_armies(territory.id, num_armies_to_supply)
                self.player = self.player.placeArmy(territory.id,num_armies_to_supply)
                self.other = Player(self.other, self.player.layout, self.player.state)
                armyReserves -= num_armies_to_supply
        # If we have any reserves left, just dump in the starting point of most optimal path.
        if armyReserves > 0:
            firstPath = optimal_paths[0]
            startTerritory = firstPath.path[0]
            self.player = self.player.placeArmy(startTerritory.id, armyReserves)
            self.other =  Player(self.other, self.player.layout, self.player.state)

    def attackTroops(self, optimal_paths):
        print "Attack phase"
        for path_obj in optimal_paths:
            i = 0
            while i < len(path_obj.path)-1:
                attacking_territory_obj = path_obj.path[i]
                curr_territory_num_armies = self.player.territories[attacking_territory_obj]
                if curr_territory_num_armies >= path_obj.armies_needed[i]:
                    next_territory_in_path = path_obj.path[i+1]
                    if next_territory_in_path in self.player.territories:
                        continue
                    capturedTerritory = self.command_attack(attacking_territory_obj, next_territory_in_path)
                    if capturedTerritory:
                        i += 1
                    else:
                        break
                else:
                    break

    def executeStrategy(self, status):
        self.updatePlayerStates()
        optimal_paths = self.calc_attack_path()
        self.supplyTroops(optimal_paths)
        self.updatePlayerStates()
        self.attackTroops(optimal_paths)
        self.game.end_turn()
        # self.transferArmies()

class Path(object):
    def __init__(self, path, armies_needed, need_transfer, goodness):
        self.path = path
        self.armies_needed = armies_needed
        self.transfer = need_transfer
        self.goodness = goodness

    def __repr__(self):
        return "Path: {} \n Armies needed: {}.\nTransfer: {}.\nGoodness: {}\n".format(self.path,self.armies_needed, self.transfer, self.goodness)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', default=None, type=int, help="Optional. The game id to join, 0 if we're first")
    args = parser.parse_args()
    game = Brisk(args.g, JNBot.team_name)
    player = JNBot(game)
    player.run()

if __name__ == '__main__':
    main()