class Player(object):
    def __init__(self, id, layout):
        self.id = id
        self.layout = layout
        # Mapping of territory ID to numArmy
        self.territories = {}
        self.armyReserves = 3
        self.continents = set()

    def updateTerritories(self, territory, numArmy):
        self.territories[territory] = numArmy

    def clearState(self):
        self.territories.clear()
        self.continents.clear()
        self.armyReserves = 3

    def __repr__(self):
        territories = [(territory.id,self.territories[territory]) for territory in self.territories]
        return "Player {} has territories: {}".format(self.id, territories)

    # To be called after territories are up to date.
    def updateCountries(self):
        for continent in self.layout.continentsByID.values():
            hasContinent = True
            for territory in continent.territories:
                if territory not in self.territories:
                    hasContinent = False
                    break
            if hasContinent:
                self.continents.add(continent)

    # To be called after countries are up to date.
    def updateArmyReserves(self):
        totalContinentBonus = reduce(lambda x,y: x + y.continentBonus, self.continents, 0)
        self.armyReserves = max(self.armyReserves, len(self.territories)//3) + totalContinentBonus