class BriskMap(object):
    def __init__(self, jsonMap):
        self.territoriesByID = {jsonTerritory["territory"]:Territory(jsonTerritory) for jsonTerritory in jsonMap["territories"]}
        self.initializeTerritories(jsonMap["territories"])
        self.continentsByID = {jsonContinent["continent"]:Continent(jsonContinent) for jsonContinent in jsonMap["continents"]}
        self.initializeContinents(jsonMap["continents"])

    def getTerritoryByID(self, id):
        return self.territoriesByID[id]

    def getContinentByID(self, id):
        return self.continentsByID[id]

    def initializeTerritories(self, jsonTerritories):
        for jsonTerritory in jsonTerritories:
            territory = self.getTerritoryByID(jsonTerritory["territory"])
            adjacentTerritories = [self.getTerritoryByID(adjacentTerritory) for adjacentTerritory in jsonTerritory["adjacent_territories"]]
            territory.setAdjacentTerritories(adjacentTerritories)

    def initializeContinents(self, jsonContinents):
        for jsonContinent in jsonContinents:
            continent = self.getContinentByID(jsonContinent["continent"])
            territories = [self.getTerritoryByID(territory) for territory in jsonContinent["territories"]]
            continent.setTerritories(territories)

    def __str__(self):
        territories = [str(territory) for territory in self.territoriesByID.values()]
        continents = [str(continent) for continent in self.continentsByID.values()]
        return "Territories: {}. \n Continents: {}".format(territories, continents)
                
class Continent(object):
    def __init__(self, jsonContinent):
        self.id = jsonContinent["continent"]
        self.name = jsonContinent["continent_name"]
        self.continentBonus = jsonContinent["continent_bonus"]
        self.territories = None

    def setTerritories(self, territories):
        self.territories = territories

    def __str__(self):
        territories = [territory.id for territory in self.territories]
        return "Continent {} is named {} with bonus {} and territories {}.".format(self.id, self.name, self.continentBonus, territories)

class Territory(object):
    def __init__(self, jsonTerritory):
        self.id = jsonTerritory["territory"]
        self.name = jsonTerritory["territory_name"]
        self.adjacentTerritories = None

    def setAdjacentTerritories(self, adjacentTerritories):
        self.adjacentTerritories = adjacentTerritories

    def __str__(self):
        adjacentTerritories = [territory.id for territory in self.adjacentTerritories]
        return "Territory {} is named {} with adjacentTerritories: {}".format(self.id, self.name, adjacentTerritories)
