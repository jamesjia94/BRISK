from Path import path
from JiaBot import JiaBot
from Player import Player
from sets import Set

class JNBot(JiaBot):

	def calc_attack_path(self, status):
		unconqueredContinents = sorted(self.player.unconqueredContinents.items(), key=lambda x: (len(x[1]["unconqueredTerritories"]),-x[0].continentBonus/len(x[0].borderTerritories)))
		# Loop over each continent
        for continent,territoryDict in unconqueredContinents:
            unconqueredTerritories = territoryDict["unconqueredTerritories"]
            conqueredTerritories = territoryDict["conqueredTerritories"]
            #set(conqueredTerritories) & set(continent.borderTerritories)
        	paths_no_transfer += calc_optimal_paths(conqueredTerritories, conqueredTerritories, continent.borderTerritories, False)
        	paths_need_transfer += calc_optimal_paths(conqueredTerritories, unconqueredTerritories, continent.borderTerritories, True)

    def calc_optimal_paths(self, start_points, end_points, borders, is_transfer):
    	# TODO: optimize by number of bordering enemy territories on end point
    	paths_through = []
    	for start_point in start_points:
    		for end_point in end_points:
    			for border_territory in border_terrs:
    				start_to_border = self.layout.shortestPathMatrix[start_point.id][border_territory.id]
    				end_to_border = self.layout.shortestPathMatrix[end_point.id][border_territory.id]
    			# Need to minimize this
    			closeness_to_border = start_to_border + end_to_border
    			all_paths = get_paths(start_point, end_point)
    			# Calc needed armies for each path
    			for path in all_paths:
    				start_army = calc_start_armies(path)
    				end_army = start_army - (len(path)-1)*2
    				path = Path(path, range(start_army, end_army, 2), is_transfer)
    				paths_through+=path
    	return paths_through

    def calc_start_armies(path):
    	steps = len(path)-1
    	enemies = 0
    	for i in xrange(1, len(path)):
    		enemies += self.other.territories[path[i]]
    	return enemies + steps*2


class Path(object):
	def __init__(self, path, armies_needed, need_transfer):
		self.path = path
		self.armies_needed = armies_needed
		self.transfer = transfer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', default=None, type=int, help="Optional. The game id to join, 0 if we're first")
    args = parser.parse_args()
    game = Brisk(args.g, JiaBot.team_name)
    player = JNBot(game)
    player.run()

if __name__ == '__main__':
    main()