def attackTroops(self, optimal_paths):
	for path_obj in optimal_paths:
		i = 0
		while i < len(path_obj.path):
			attacking_territory_obj = path_obj.path[i]
			curr_territory_num_armies = self.player.territories[attacking_territory_obj]
			if curr_territory_num_armies >= path_obj.num_armies_required:
				capturedTerritory = self.command_attack(curr_territory, path_obj.path[i+1])
				if capturedTerritory:
					i += 1
				else:
					break
			else:
				break


