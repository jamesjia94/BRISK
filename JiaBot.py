from Brisk import Brisk
from BriskMap import BriskMap
import argparse
import time
import random
import pprint
from Player import Player
globald = {}

class JiaBot(object):
    team_name = "Test Bot Please Ignore"

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
        if self.game.player_id == 1:
            self.state = Player(1)
            self.otherState = Player(2)
        else:
            self.state = Player(2)
            self.otherState = Player(1)

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
        self.updatePlayerStates()
        print self.state
        print self.otherState
        lucky_territory = random.randint(0, len(status['territories']) - 1)
        self.game.place_armies(status['territories'][lucky_territory]['territory'], status['num_reserves'])

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

    def clearPlayerStates(self):
        self.state.clearTerritories()
        self.otherState.clearTerritories()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', default=None, type=int, help="Optional. The game id to join, 0 if we're first")
    args = parser.parse_args()
    player = JiaBot()
    globald["player"] = player
    player.run(args.g)

if __name__ == '__main__':
    main()