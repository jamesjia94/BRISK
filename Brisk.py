import json
import urllib2
import time

class Brisk(object):
    HOST = 'http://www.briskchallenge.com'

    def __init__(self, game_id=None, name=None, token=None):
        token = "468c2a5e7f390e846cd62587a45951b1689ca345"
        res = self.join_game(game_id, name, token)
        self.game_id = res['game']
        self.player_id = res['player']
        self.token = res['token']

    @classmethod
    def url_root(cls):
        return cls.HOST + "/v1/brisk/game"

    def join_game(self, game_id, name, token):
        data = {'join': True, 'team_name': name, 'b': 2}
        if game_id is not None:
            if game_id: #game_id is not 0
                data['game'] = game_id
            data['no_bot'] = True
        data['token'] = token
        res = self.post(self.url_root(), data)
        return res

    def url_game(self):
        return self.url_root() + "/" + str(self.game_id)

    def url_player(self):
        return self.url_game() + "/player/" + str(self.player_id)

    def url_territory(self, territory_id):
        return self.url_player() + "/territory/" + str(territory_id)

    def post(self, url, data):
        req = urllib2.Request(url, json.dumps(data))
        try:
            start = time.time()
            response = urllib2.urlopen(req)
        except Exception as ex:
            print ex
            raise
        res = response.read()
        end = time.time()
        # print "Post time: {}".format(end-start)
        try:
            return json.loads(res)
        except ValueError:
            # probably empty response so no JSON to decode
            return res

    def get(self, url):
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        return json.loads(response.read())

    def get_game_state(self):
        start = time.time()
        end = time.time()
        # print "Get Game state time: {}".format(end-start)
        return self.get(self.url_game())

    def get_map_layout(self):
        start = time.time()
        map_layout = self.get(self.url_game() + "?map=true")
        end = time.time()
        # print "Get map layout time: {}".format(end-start)
        return map_layout

    def get_player_status(self, lite=False):
        return self.get(self.url_player() + {False: "", True: "?check_turn=true"}[lite])

    def end_turn(self):
        return self.post(self.url_player(), {'token': self.token, 'end_turn': True})

    def get_history(self):
        return self.get(self.url_game() + "/history")

    def attack(self, attacker_territory_id, defender_territory_id, num_attacker_armies):
        url = self.url_territory(defender_territory_id)
        data = {'token': self.token, 'num_armies': num_attacker_armies, 'attacker': attacker_territory_id}
        return self.post(url, data)

    def place_armies(self, territory_id, num_armies):
        url = self.url_territory(territory_id)
        data = {'token': self.token, 'num_armies': num_armies}
        return self.post(url, data)

    def transfer_armies(self, from_territory_id, to_territory_id, num_armies):
        url = self.url_territory(from_territory_id)
        data = {'token': self.token, 'num_armies': num_armies, 'destination': to_territory_id}
        return self.post(url, data)

    def get_map_svg(self):
        url = self.url_game() + "?map=svg"
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        return response.read()  # "<svg>\n ... </svg>"

    def reward(self):
        url = self.HOST + "/v1/brisk/reward.php"
        data = {'game':self.game_id, 'player':self.player_id, 'token':self.token}
        req = urllib2.Request(url, json.dumps(data))
        response = urllib2.urlopen(req)
        return response.read() # ???
