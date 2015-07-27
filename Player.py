class Player(object):
    def __init__(self, id, layout, state):
        self.id = id
        self.layout = layout
        self.state = state
        # Mapping of territory ID to numArmy
        self.territories = {}
        self.armyReserves = 3
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
            for territory in continent.territories:
                if territory not in self.territories:
                    unconqueredTerritories.append(territory)
            self.unconqueredContinents[continent] = unconqueredTerritories
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

