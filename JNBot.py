from __future__ import division
from JiaBot import JiaBot
from Player import Player
import argparse
from Brisk import Brisk
from BriskMap import BriskMap
import time
import random
import math
from collections import deque
from collections import Counter

class JNBot(JiaBot):
    team_name = "Compute+Data"
    
    def calc_attack_path(self):
        all_paths = []
        for border in self.player.borderTerritories:
            start = time.time()
            all_paths += self.calc_optimal_paths(border, self.player.armyReserves)
            end = time.time()
            # print "calculating optimal paths : {}".format(end-start)
        print "ALL PATHS: {}".format(all_paths)
        sorted_all_paths = sorted(all_paths, key= lambda p: self.calculate_path_value(p, self.player.armyReserves), reverse=True)
        print "Sorted path: {}".format(sorted_all_paths)
        sorted_all_paths = [path for path in sorted_all_paths if len(path) > 1]
        filtered_all_paths = []
        visited_start = set()
        for path in sorted_all_paths:
            start_territory = path[0]
            if start_territory not in visited_start:
                visited_start.add(start_territory)
                filtered_all_paths.append(path)
        sorted_all_path_objects = []
        for path in filtered_all_paths:
            required_armies = reduce(lambda cumulative, t: cumulative + self.other.territories[t]+2, path[1:], 2)
            sorted_all_path_objects.append(Path(path, required_armies))
        return sorted_all_path_objects

    # TODO: include enemy losing territory as part of heuristic
    def calculate_path_value(self, path, num_armies_to_supply):
        armies_left = num_armies_to_supply + self.player.territories[path[0]]
        value = 0
        curr_player = self.player
        curr_other = self.other
        i = 0
        while i < len(path) - 1:
            attacker_territory = path[i]
            defender_territory = path[i+1]
            defender_armies = self.other.territories[defender_territory]

            win_prob = self.get_attack_probability(armies_left-1,defender_armies-1)

            armies_left -= (defender_armies + 1)
            fakeResult = {"attacker_territory": attacker_territory.id, "defender_territory": defender_territory.id, "defender_territory_captured": True, "attacker_territory_armies_left": 1, "defender_territory_armies_left": armies_left}

            temp_player = curr_player.attackResult(fakeResult)
            temp_other = Player(curr_other.id, curr_other.layout, temp_player.state)
            value += win_prob * (temp_player.armyReserves - curr_player.armyReserves + (curr_other.armyReserves - temp_other.armyReserves))
            curr_player = temp_player
            curr_other = temp_other
            i += 1
        return value

    def calc_optimal_paths(self, border, num_armies_to_supply):
        all_paths = []
        q = deque([])
        q.append([border])
        
        while len(q) > 0:
            tmp_path = q.popleft()
            last_node = tmp_path[len(tmp_path)-1]
            # print tmp_path

            keepRecursing = False
            for link_node in last_node.adjacentTerritories:
                if link_node not in tmp_path and link_node not in self.player.territories:
                    new_path = []
                    new_path = tmp_path + [link_node]
                    needed_armies = reduce(lambda cumulative, territory: cumulative + self.other.territories[territory], new_path[1:],0)
                    if needed_armies + len(new_path)-1 < self.player.territories[border] + num_armies_to_supply:
                        q.append(new_path)
                        keepRecursing = True
            if not keepRecursing:
                if len(tmp_path) > 1:
                    all_paths.append(tmp_path)

        return all_paths

    def supplyTroops(self, optimal_path_objects):
        armies_left_to_supply = self.player.armyReserves
        for optimal_path_object in optimal_path_objects:
            if armies_left_to_supply <= 0:
                return
            needed_armies = int(math.ceil(optimal_path_object.get_required_armies() * 1.2))
            if needed_armies <= 0:
                print "Path Object: {} needs 0 armies!!!!".format(optimal_path_object)
                continue
            supplied_armies = min(armies_left_to_supply, needed_armies)
            armies_left_to_supply -= supplied_armies
            print "Supply troops to: {} with {} armies".format(optimal_path_object.path[0], supplied_armies)
            self.game.place_armies(optimal_path_object.path[0].id, supplied_armies)
    
    def attackTroops(self, optimal_path_objects):
        for optimal_path_object in optimal_path_objects:
            optimal_path = optimal_path_object.get_path()
            i = 0
            while i < len(optimal_path) - 1:
                attacking_territory_obj = optimal_path[i]
                curr_territory_num_armies = self.player.territories[attacking_territory_obj]
                next_territory_in_path = optimal_path[i+1]
                if next_territory_in_path in self.player.territories:
                    i += 1
                    continue
                capturedTerritory = self.command_attack(attacking_territory_obj, next_territory_in_path)
                if capturedTerritory:
                    i += 1
                else:
                    break

    def executeStrategy(self, status):
        print "Starting turn"
        turn_start = time.time()
        self.updatePlayerStates()
        optimal_paths = self.calc_attack_path()
        start = time.time()
        print "optimal_paths to supply troops is {}".format(len(optimal_paths))
        self.supplyTroops(optimal_paths)
        end = time.time()
        # print "Supply troops: {}".format(end-start)
        self.updatePlayerStates()
        start = time.time()

        self.attackTroops(optimal_paths)
        end = time.time()
        status = self.game.get_player_status()
        if status['eliminated']:
            print "We lost"
            return
        if status['winner']:
            if status['winner'] == self.game.player_id:
                print "We won"
                # TODO: Reward?
            else:
                print "Hit the limit of turns and lost"
            return
        # print "Attack troops: {}".format(end-start)
        start = time.time()
        try:
            self.game.end_turn()
        except Exception as e:
            print e
            end =  time.time()
            print "Broken End turn: {}".format(end-start)
            return
        end =  time.time()
        # print "End turn: {}".format(end-start)
        turn_end = time.time()
        print "Overall turn took: {}".format(turn_end-turn_start)
        # self.transferArmies()

class Path(object):
    def __init__(self, path, required_armies):
        self.path = path
        self.required_armies = required_armies

    def get_path(self):
        return self.path

    def get_required_armies(self):
        return self.required_armies

    def __repr__(self):
        return "Path: {}. Required armies: {}".format(self.path, self.required_armies)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', default=None, type=int, help="Optional. The game id to join, 0 if we're first")
    args = parser.parse_args()
    game = Brisk(args.g, JNBot.team_name)
    player = JNBot(game)
    player.run()

if __name__ == '__main__':
    main()