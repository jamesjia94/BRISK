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
        attackerTerritory = result["attacker_territory"]
        defenderTerritory = result["defender_territory"]
        capturedDefenderTerritory = result["defender_territory_captured"]
        attackerArmyLeft = result["attacker_territory_armies_left"]
        defenderArmyLeft = result["defender_territory_armies_left"]
        newState = self.state
        newTerritories = []
        for territory in self.state["territories"]:
            if territory["territory"] == attackerTerritory:
                newTerritories.append({"territory": attackerTerritory, "player": self.id, "num_armies": attackerArmyLeft})
            elif territory["territory"] == defenderTerritory:
                newTerritoryState = {"territory": attackerTerritory, "num_armies": defenderArmyLeft}
                if capturedDefenderTerritory:
                    newTerritoryState["player"] = self.id
                else:
                    newTerritoryState["player"] = territory["player"]
                newTerritories.append(newTerritoryState)
            else:
                newTerritories.append(territory)
        newState["territories"] = newTerritories
        return Player(self.id, self.layout, newState)

    def transferArmy(self, numTransfer, src, dst):
        newState = self.state
        for territory in self.state["territories"]:
            if territory["territory"] == src:
                newTerritories.append({"territory": attackerTerritory, "player": self.id, "num_armies": territory["territory"] - numTransfer})
            elif territory["territory"] == dst:
                newTerritories.append({"territory": attackerTerritory, "player": self.id, "num_armies": territory["territory"] + numTransfer})
            else:
                newTerritories.append(territory)
        newState["territories"] = newTerritories
        return Player(self.id, self.layout, newState)

