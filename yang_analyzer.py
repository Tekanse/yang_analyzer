import random
import bisect
import json

import plotly.express as px
import pandas as pd
import scipy.spatial as spatial

pd.options.plotting.backend = "plotly"

USE_SQL = True

# Constants
PROTO_COLUMNS_TITLE = ["GOLD_MIN", "GOLD_MAX", "RANK", "LEVEL"]
RANKS = ["PAWN", "S_PAWN", "KNIGHT", "S_KNIGHT", "BOSS", "KING"]
MOB_RANK_DROP_CHANCE = [20, 20, 25, 30, 50, 100]
PLAYER_LEVEL = 60
DROP_CHANCE_LEVEL_DELTA = [
	1, 3, 5, 7, 15, 30, 60, 90, 91, 92, 93, 94,
	1, 3, 5, 7, 15, 30, 60, 90, 91, 92, 93, 94,
	95, 97, 99, 100, 105, 110, 115, 120, 125, 130,
	135, 140, 145, 150, 155, 160, 165, 170, 180,
]

all_group_group = {}
all_groups = {}
mob_yangs = {}
graph_data = []
map_mob_data = {}
pts_x = []
pts_y = []


class GroupGroup:
	def __init__(self, groups):
		self.vec_probs = []
		self.vec_members = []
		self.create(groups)
		self.groups = None

	def create(self, groups):
		self.groups = groups
		for group in self.groups:
			self.add_member(group["vnum"], group["chance"])

	def get_group(self):
		n = random.randint(1, self.vec_probs[-1])
		it = bisect.bisect_left(self.vec_probs, n)
		return self.vec_members[it]

	def add_member(self, vnum, chance):
		if len(self.vec_probs) > 0:
			chance = chance + self.vec_probs[-1]
		self.vec_probs.append(chance)
		self.vec_members.append(vnum)


def load_data():
	f = open("settings.json")
	data = json.load(f)
	for m in data:
		map_details = data[m][0]
		for i in range(map_details['level_min'], map_details['level_max']):
			GetYangFromMap(map_details['folder_name'], i)


def get_mob_yang():
	if USE_SQL:
		import mysql
		mydb = mysql.connector.connect(
			host="localhost",
			user="user",
			password="password",
			charset="utf8"
		)
		my_cursor = mydb.cursor(dictionary=True)

		my_cursor.execute("SELECT * FROM player.mob_proto")
		records = my_cursor.fetchall()
		for row in records:
			mob_yangs[int(row["vnum"])] = [
				int(row["gold_min"]), int(row["gold_max"]), int(row["rank"]), int(row["level"])
			]
	else:
		with open("mob_proto.txt", "r+", encoding="utf-8", errors="ignore") as proto:
			lines = proto.readlines()
			first_line = lines[0].split("\t")
			i_min = first_line.index(PROTO_COLUMNS_TITLE[0])
			i_max = first_line.index(PROTO_COLUMNS_TITLE[1])
			i_rank = first_line.index(PROTO_COLUMNS_TITLE[2])
			i_level = first_line.index(PROTO_COLUMNS_TITLE[3])
			for line in lines[1:]:
				line = line.split("\t")
				mob_yangs[int(line[0])] = [
					int(line[i_min]), int(line[i_max]), RANKS.index(line[i_rank]), int(line[i_level])
				]


def load_groups():
	group_file = open('data/group.txt', 'r', encoding="cp1250")
	lines = group_file.readlines()
	group_vnum = 0
	group_mobs = []
	is_loading_mobs = False
	for line in lines:
		vec = [i.replace('\n', '') for i in line.split("\t")]
		if len(vec) > 1 and vec[1] == "Vnum":
			group_vnum = int(vec[2])
			is_loading_mobs = True
			continue
		if len(vec[0]) > 0 and vec[0][0] == "}":
			is_loading_mobs = False
			all_groups[group_vnum] = group_mobs
			group_mobs = []
		if is_loading_mobs:
			group_mobs.append(int(vec[3]))


def load_group_group():
	group_group_file = open('data/group_group.txt', 'r')
	lines = group_group_file.readlines()
	group_vnum = 0
	group_groups = []
	is_loading_mobs = False
	for line in lines:
		vec = line.split("\t")
		vec = [i.replace('\n', '') for i in vec]
		if len(vec) > 1 and vec[1] == "Vnum":
			group_vnum = int(vec[2])
			is_loading_mobs = True
			continue
		if len(vec[0]) > 0 and vec[0][0] == "}":
			is_loading_mobs = False
			all_group_group[group_vnum] = GroupGroup(group_groups)
			group_groups = []
		if is_loading_mobs and len(vec) > 3 and vec[2] != "":
			group_groups.append({"vnum": int(vec[2]), "chance": int(vec[3])})


def GetYangFromMap(map_name, player_level):
	map_mob_data[map_name] = []
	mob_file = open('data/map/' + map_name + '/regen.txt', 'r', encoding="cp1250")
	lines = mob_file.readlines()

	for line in lines:
		if line[0] == "r":
			group_group_vnum = line.split("\t")[10]
			group_group_vnum = group_group_vnum.replace("\n", "")
			group_vnum = all_group_group[int(group_group_vnum)].get_group()
			coord_x = line.split("\t")[1]
			coord_y = line.split("\t")[2]
			time = line.split("\t")[7]
			time_val = int(time[:-1])
			if time[-1:] == 'm':
				time_val *= 60
			elif time[-1:] == 'h':
				time_val *= 3600

			if int(group_vnum) in all_groups:
				mobs_vnum = all_groups[int(group_vnum)]
				coord_arr = [coord_x, coord_y, mobs_vnum, time_val]
				map_mob_data[map_name].append(coord_arr)
		elif line[0] == "g":
			group_vnum = line.split("\t")[10]
			group_vnum = group_vnum.replace("\n", "")
			mobs_vnum = all_groups[int(group_vnum)]
			coord_x, coord_y = line.split("\t")[1:3]
			time = line.split("\t")[7]
			time_val = int(time[:-1])
			if time[-1:] == 'm':
				time_val *= 60
			elif time[-1:] == 'h':
				time_val *= 3600
			coord_arr = [coord_x, coord_y, mobs_vnum, time_val]
			map_mob_data[map_name].append(coord_arr)
		else:
			continue
	get_max_density_point(map_name, player_level)


def get_max_density_point(map_name, player_level):
	whole_yang = 0
	mob_count = 0
	temp_arr = []
	for point in map_mob_data[map_name]:
		temp_arr.append(point[:2])
	point_tree = spatial.cKDTree(temp_arr)
	max_count = 0
	points_array = []
	for point in temp_arr:
		arr = point_tree.query_ball_point(point, 70, 2.)
		if len(arr) > max_count:
			max_count = len(arr)
			points_array = arr

	for index in points_array:
		for mob in map_mob_data[map_name][index][2]:
			if mob not in mob_yangs:
				continue
			yang_min = mob_yangs[mob][0]
			yang_max = mob_yangs[mob][1]
			mob_rank = mob_yangs[mob][2]
			avr_yang = random.randint(yang_min, yang_max)
			gold_percent = MOB_RANK_DROP_CHANCE[mob_rank]
			mob_level = mob_yangs[mob][3]

			level_delta = max((mob_level + 15) - player_level, 0)
			level_delta = min(level_delta, 30)

			total_percent = (gold_percent * DROP_CHANCE_LEVEL_DELTA[level_delta]) / 100
			mob_count += 1
			if random.randint(0, 100) > total_percent:
				continue

			time = map_mob_data[map_name][index][3]
			resp_per_hour = 3600 / time
			avr_yang *= resp_per_hour

			whole_yang += avr_yang
	data_point = {'level': player_level, 'yang': whole_yang, 'mapName': map_name}
	graph_data.append(data_point)


load_group_group()
load_groups()
get_mob_yang()
load_data()

df = pd.DataFrame(graph_data)
fig = px.bar(df, x='level', y='yang', color='mapName')
fig.show()
