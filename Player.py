from collections import deque
class Player(object):
    def __init__(self, id, layout, state):
        self.id = id
        self.layout = layout
        self.state = state
        # Mapping of territory obj to numArmy
        self.territories = {}
        self.armyReserves = 3
        # Mapping of continent obj to territories that aren't conquered.
        self.unconqueredContinents = {}
        self.conqueredContinents = set()
        self.borderTerritories = set()

        # Update self.territories
        for territory in self.state["territories"]:
            if territory["player"] == self.id:
                territoryObj = self.layout.getTerritoryByID(territory["territory"])
                self.territories[territoryObj] = territory["num_armies"]
                
        # Update border territories
        for territory in self.state["territories"]:
            if territory["player"] == self.id:
                territoryObj = self.layout.getTerritoryByID(territory["territory"])
                for adjTerritory in territoryObj.adjacentTerritories:
                    if adjTerritory not in self.territories:
                        self.borderTerritories.add(territoryObj)

        self.updateCountries()
        self.updateArmyReserves()

    def __repr__(self):
        borderTerritories = [str(territory) for territory in self.borderTerritories]
        return "Player {} has border territories: {}".format(self.id, borderTerritories)

    # To be called after territories are up to date.
    def updateCountries(self):
        for continent in self.layout.continents:
            unconqueredTerritories = []
            conqueredTerritories = []
            for territory in continent.territories:
                if territory not in self.territories:
                    unconqueredTerritories.append(territory)
                else:
                    conqueredTerritories.append(territory)
            self.unconqueredContinents[continent] = {"unconqueredTerritories": unconqueredTerritories, "conqueredTerritories": conqueredTerritories}
            if not unconqueredTerritories:
                self.conqueredContinents.add(continent)

    # To be called after countries are up to date.
    def updateArmyReserves(self):
        totalContinentBonus = reduce(lambda x,y: x + y.continentBonus, self.conqueredContinents, 0)
        self.armyReserves = max(self.armyReserves, len(self.territories)//3) + totalContinentBonus

    def attackResult(self, result):
        attackerTerritory = int(result["attacker_territory"])
        defenderTerritory = int(result["defender_territory"])
        capturedDefenderTerritory = int(result["defender_territory_captured"])
        attackerArmyLeft = int(result["attacker_territory_armies_left"])
        defenderArmyLeft = int(result["defender_territory_armies_left"])
        newState = self.state
        newTerritories = []
        for territory in self.state["territories"]:
            newTerritory = territory.copy()
            if territory["territory"] == attackerTerritory:
                newTerritory["num_armies"] = attackerArmyLeft
            if territory["territory"] == defenderTerritory:
                newTerritory["num_armies"] = defenderArmyLeft
                if capturedDefenderTerritory:
                    newTerritory["player"] = self.id
            newTerritories.append(newTerritory)
        newState["territories"] = newTerritories
        return Player(self.id, self.layout, newState)

    def transferArmy(self, src, dst, numTransfer):
        newState = self.state
        newTerritories = []
        for territory in self.state["territories"]:
            newTerritory = territory.copy()
            if territory["territory"] == src:
                newTerritory["num_armies"] = territory["num_armies"] - numTransfer
            elif territory["territory"] == dst:
                newTerritory["num_armies"] = territory["num_armies"] + numTransfer
            newTerritories.append(newTerritory)
        newState["territories"] = newTerritories
        return Player(self.id, self.layout, newState)

    def placeArmy(self, src, armies_to_supply):
        newState = self.state
        newTerritories = []
        for territory in self.state["territories"]:
            newTerritory = territory.copy()
            if territory["territory"] == src:
                newTerritory["num_armies"] = territory["num_armies"] + armies_to_supply
            newTerritories.append(newTerritory)
        newState["territories"] = newTerritories
        return Player(self.id, self.layout, newState)

    # returns a list of valid paths that go from start to end.
    def get_paths(self,start,end):
        all_paths = []
        q = deque([])
        q.append([start])
        
        while len(q) > 0:
            tmp_path = q.popleft()
            last_node = tmp_path[len(tmp_path)-1]
            # print tmp_path
            if last_node.id == end.id:
                all_paths.append(tmp_path)
            for link_node in last_node.adjacentTerritories:
                if link_node not in tmp_path and link_node not in self.territories and link_node in start.continent.territories:
                    new_path = []
                    new_path = tmp_path + [link_node]
                    q.append(new_path)
        return all_paths
