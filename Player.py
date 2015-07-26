class Player(object):
    def __init__(self, id):
        # Mapping of territory ID to numArmy
        self.id = id
        self.territories = {}

    def updateTerritories(self, territory, numArmy):
        self.territories[territory] = numArmy

    def clearTerritories(self):
        self.territories = {}

    def __str__(self):
        territories = [territory.id for territory in self.territories]
        return "Player {} has territories: {}".format(self.id, territories)