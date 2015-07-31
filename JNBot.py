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
        return_paths = []
        for continent,territoryDict in unconqueredContinents:
            unconqueredTerritories = territoryDict["unconqueredTerritories"]
            conqueredTerritories = territoryDict["conqueredTerritories"]
            return_paths += self.calc_optimal_paths(conqueredTerritories, conqueredTerritories, continent.borderTerritories, False)
            return_paths += self.calc_optimal_paths(conqueredTerritories, unconqueredTerritories, continent.borderTerritories, True)
        optimal_paths= sorted(return_paths, key=lambda p: (-p.goodness,p.close_to_border, p.armies_needed[0]))
        ends_seen=set()
        # return optimal_paths
        print "pre-filter paths are {}".format(len(optimal_paths))
        filtered_paths=[]
        for each_path in optimal_paths:
            last_node_index = len(each_path.path)-1
            last_node = each_path.path[last_node_index]
            if not last_node in ends_seen:
                filtered_paths.append(each_path)
                ends_seen.add(last_node)
        print "FILTERED OUT paths are {}".format(len(optimal_paths)-len(filtered_paths))
        return filtered_paths


    def calc_optimal_paths(self, start_points, end_points, borders, is_transfer):
        # TODO: optimize by number of bordering enemy territories on end point
        paths_through = []
        start_end_pairs = set()        
        for start_point in start_points:
            for end_point in end_points:
                if (start_point.id,end_point.id) in start_end_pairs:
                    continue
                else:
                    start_end_pairs.add((start_point.id,end_point.id))
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
                    if not is_transfer:
                        path.pop() # Remove last one
                    start_army = self.calc_start_armies(path)
                    end_army = start_army - (len(path)-1)*2 
                    start_armies = range(start_army, end_army, -2)
                    for step in xrange(1, len(path)-1):
                        enemy = self.other.territories[path[step]]
                        start_armies[step] = start_armies[step]- enemy
                    goodness = self.calc_heuristic(closeness_to_border, start_armies, start_point)
                    path = Path(path, is_transfer, start_armies, closeness_to_border, goodness)
                    paths_through.append(path)
                    
        return paths_through

    def calc_start_armies(self,path):
        steps = len(path)
        enemies = 0
        for i in xrange(1, len(path)):
            enemies += self.other.territories[path[i]]
        return enemies + int(math.ceil(steps*1.5))

    def calc_heuristic(self, close_to_border, start_armies, start_point):
        # close_to_border = minimize
        # start_army  = minimize
        # close_to_conquer_continent = maximize
        current_continent = start_point.continent
        enemies_left_in_continent = reduce(lambda cumulative, territory: cumulative + self.other.territories[territory], self.player.unconqueredContinents[current_continent]["unconqueredTerritories"],0)
        continent_heur = current_continent.continentBonus/enemies_left_in_continent
        bonus_per_terr = current_continent.continentBonus/len(current_continent.territories)
        return continent_heur + bonus_per_terr*(len(start_armies)-1)

    def supplyTroops(self, optimal_paths):
        armyReserves = self.player.armyReserves
        for path_obj in optimal_paths:
            if armyReserves < 0:
                return
            territory = path_obj.path[0]
            num_armies_in_start = self.player.territories[territory]
            num_armies_to_supply = min(path_obj.armies_needed[0] - num_armies_in_start, armyReserves)
            if num_armies_to_supply > 0 and num_armies_to_supply + num_armies_in_start >= path_obj.armies_needed[0]:
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
        for path_obj in optimal_paths:
            i = 0
            # print "path_obj: {}".format(path_obj)
            while i < len(path_obj.path)-1:
                # start = time.time()
                attacking_territory_obj = path_obj.path[i]
                curr_territory_num_armies = self.player.territories[attacking_territory_obj]
                if curr_territory_num_armies >= path_obj.armies_needed[i]:
                    next_territory_in_path = path_obj.path[i+1]
                    if next_territory_in_path in self.player.territories:
                        i += 1
                        # end = time.time()
                        # print "Attack iteration 1 took: {}".format(end-start)
                        continue
                    start = time.time()
                    print "most optimal path is {}".format(path_obj)
                    capturedTerritory = self.command_attack(attacking_territory_obj, next_territory_in_path)
                    end = time.time()
                    print "Attack took: {}".format(end-start)
                    if capturedTerritory:
                        i += 1
                        end = time.time()
                        print "capturedTerritory is {}".format(capturedTerritory)
                    else:
                        end = time.time()
                        # print "Attack iteration 3 took: {}".format(end-start)
                        break
                else:
                    end = time.time()
                    # print "Attack iteration 4 took: {}".format(end-start)
                    break

    def executeStrategy(self, status):
        print "Starting turn"
        self.updatePlayerStates()
        optimal_paths = self.calc_attack_path()
        start = time.time()
        print "optimal_paths to supply troops is {}".format(len(optimal_paths))
        self.supplyTroops(optimal_paths)
        end = time.time()
        print "Supply troops: {}".format(end-start)
        self.updatePlayerStates()
        start = time.time()

        self.attackTroops(optimal_paths)
        end = time.time()
        print "Attack troops: {}".format(end-start)
        start = time.time()
        self.game.end_turn()
        end =  time.time()
        print "End turn: {}".format(end-start)
        # self.transferArmies()

class Path(object):
    def __init__(self, path, need_transfer, armies_needed, close_to_border, goodness):
        self.path = path
        self.armies_needed = armies_needed
        self.transfer = need_transfer
        self.close_to_border = close_to_border
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