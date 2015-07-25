from Brisk import Brisk
from BriskMap import BriskMap
import argparse
import time
import random
import pprint
globald = {}

class JiaBot(object):
    team_name = "Test Bot Please Ignore"

    def __init__(self):
        self.layout = None
        self.game = None

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

            print "Turn {}".format(status['turns_taken'])
            self.executeStrategy(status)
            self.game.end_turn()

    def executeStrategy(self, status):
        lucky_territory = random.randint(0, len(status['territories']) - 1)
        self.game.place_armies(status['territories'][lucky_territory]['territory'], status['num_reserves'])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', default=None, type=int, help="Optional. The game id to join, 0 if we're first")
    args = parser.parse_args()
    player = JiaBot()
    globald["player"] = player
    player.run(args.g)

if __name__ == '__main__':
    main()