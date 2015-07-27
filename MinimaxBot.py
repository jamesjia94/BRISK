from __future__ import division
from Brisk import Brisk
from BriskMap import BriskMap
import argparse
import time
import sys
import random
import math
from Player import Player
from collections import Counter
from Heuristic import Heuristic
# globald = {}

class MiniMaxBot(object):
    team_name = "Test Bot Please Ignore"
    supply_threshold = 0.1
    depth = 3
    heuristic = Heuristic()

    def __init__(self, game):
        self.layout = None
        self.game = game
        self.playerID = self.game.player_id
        self.otherID = 2 if self.playerID == 1 else 1
        self.player = None
        self.other = None

    def getMapLayout(self):
        self.layout = BriskMap(self.game.get_map_layout())

    """" Waits for turn, returning the updated reponse"""
    def wait_for_turn(self):
        while True:
            status = self.game.get_player_status()
            if status['current_turn'] or status['eliminated'] or status['winner']:
                return status

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
            self.game.end_turn()

    def executeStrategy(self, status):
        state = self.updatePlayerStates()
        print "Num turns taken: {}".format(state["num_turns_taken"]+1,)
        print "Player: {}".format(self.player)
        print "Other: {}".format(self.other)
        print ""
        self.supplyTroops(status)
        self.updatePlayerStates()
        self.attack()
    
    def updatePlayerStates(self):
        state = self.game.get_game_state()
        self.player = Player(self.playerID, self.layout, state)
        self.other = Player(self.otherID, self.layout, state)
        return state

    def supplyTroops(self, status):
        # Find all of our territories that border an enemy territory
        borderTerritories = Counter()
        for territory in self.player.territories:
            for adjacentTerritory in territory.adjacentTerritories:
                if adjacentTerritory in self.other.territories:
                    borderTerritories[territory] += self.other.territories[adjacentTerritory]
            borderTerritories[territory] /= self.player.territories[territory]

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

    def alphabeta(self, depth, alpha, beta, isMax, player, other):
        if depth == 0:
            return self.heuristic.evaluate(player)
        if isMax:
            v = -sys.maxint - 1
            moves = self.getMoves(player,other)
            for move,p,o in moves:
                v = max(v,self.alphabeta(depth-1, alpha, beta, False, p, o))
                alpha = max(alpha, v)
                if beta <= alpha:
                    break
            return v
        else:
            v = sys.maxint
            moves = self.getMoves(other,player)
            for move,o,p in moves:
                v = min(v,self.alphabeta(depth-1, alpha, beta, True, p, o))
                beta = min(beta, v)
                if beta <= alpha:
                    break
            return v

    def getMoves(self, player, other):
        moves = []
        for curr_territory in player.borderTerritories:
            adjacentTerritories = curr_territory.adjacentTerritories
            for adjacentTerritory in adjacentTerritories:
                if adjacentTerritory in other.territories:
                    attackingArmies = player.territories[curr_territory]
                    defendingArmies = other.territories[adjacentTerritory]
                    if attackingArmies > 1:
                        attackingArmy = attackingArmies-1
                        attackingArmies -= attackingArmy
                        defendingArmies -= attackingArmy

                        capturedDefenderTerritory = False
                        if defendingArmies <= 0:
                            capturedDefenderTerritory = True
                            defendingArmies = attackingArmies - defendingArmies - 1
                            attackingArmies = 1
                        result = {"attacker_territory_armies_left": attackingArmies, "defender_territory_armies_left": defendingArmies, "defender_territory": adjacentTerritory.id, "attacker_territory": curr_territory.id, "defender_territory_captured": capturedDefenderTerritory}
                        newPlayer = player.attackResult(result)
                        newOther = Player(other.id, other.layout, newPlayer.state.copy())
                        moves.append(((curr_territory.id, adjacentTerritory.id),newPlayer,newOther))
        return moves
  

    def attack(self):
        moves = self.getMoves(self.player,self.other)
        v = -sys.maxint - 1
        bestMove = None
        alpha = -sys.maxint - 1
        beta = sys.maxint
        for move,p,o in moves:
            temp = self.alphabeta(self.depth, alpha , beta, False, p, o)
            if v < temp:
                bestMove = move
                v = temp
            alpha = max(alpha, v)
            if beta <= alpha:
                break

        curr_territory = self.layout.territoriesByID[move[0]]
        adjacentTerritory = self.layout.territoriesByID[move[1]]
        attackingArmies = self.player.territories[curr_territory]
        defendingArmies = self.other.territories[adjacentTerritory]
        while attackingArmies > 1:
            result = self.game.attack(curr_territory.id, adjacentTerritory.id, min(3, attackingArmies-1))
            attackingArmies = result["attacker_territory_armies_left"]
            defendingArmies = result["defender_territory_armies_left"]
            currState = self.game.get_game_state()
 
            if result["defender_territory_captured"]:
                if attackingArmies > 1:
                    self.game.transfer_armies(curr_territory.id, adjacentTerritory.id, attackingArmies - 1)
                break
        self.updatePlayerStates()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', default=None, type=int, help="Optional. The game id to join, 0 if we're first")
    args = parser.parse_args()
    game = Brisk(args.g, MiniMaxBot.team_name)
    player = MiniMaxBot(game)
    # globald["player"] = player
    player.run()

if __name__ == '__main__':
    main()