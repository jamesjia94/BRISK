# optimalPaths is a sorted list of Path objects to a path (list of territories) and a list of number of armies at each position
def supplyTroops(self, optimal_paths):
	armyReserves = self.player.armyReserves
	for path_obj in optimal_paths:
		if armyReserves < 0:
			return
		territory = path_obj.path[0]
		num_armies_in_start = self.player.territories[territory]
		num_armies_to_supply = path_obj.num_armies_required - num_armies_in_start
		if num_armies_to_supply > 0:
			self.game.place_armies(territory.id, armies_to_supply)
			self.player = self.player.placeArmy(territory.id,armies_to_supply)
			self.other = Player(self.other, self.player.layout, self.player.state)
			armyReserves -= armies_to_supply
	# If we have any reserves left, just dump in the starting point of most optimal path.
	if armyReserves > 0:
		firstPath = optimal_paths[0]
		startTerritory = firstPath.path[0]
		self.player = self.player.placeArmy(startTerritory.id, armyReserves)
		self.other =  Player(self.other, self.player.layout, self.player.state)