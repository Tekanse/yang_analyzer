import mysql.connector
import random
import bisect
import json

import plotly.express as px
import pandas as pd
pd.options.plotting.backend = "plotly"
import scipy.spatial as spatial

allGroupGroup = {}
allGroups = {}
mobYangs = {}
graphData = []
mapMobData = {}
pts_x = []
pts_y = []
class GroupGroup:
	def __init__(self, groups):
		self.vecProbs = []
		self.vecMembers = []
		self.Create(groups)

	def Create(self, groups):
		self.groups = groups
		for group in self.groups:
			self.AddMember(group["vnum"], group["chance"])

	def GetGroup(self):
		n = random.randint(1, self.vecProbs[-1])
		it = bisect.bisect_left(self.vecProbs, n)
		return self.vecMembers[it]

	def AddMember(self, vnum, chance):
		if len(self.vecProbs) > 0:
			chance = chance + self.vecProbs[-1]
		self.vecProbs.append(chance)
		self.vecMembers.append(vnum)

MOB_RANK_DROP_CHANCE = [20, 20, 25, 30, 50, 100]

PLAYER_LEVEL = 60

DROP_CHANCE_LEVEL_DELTA = [
	1,  
	3,  
	5,  
	7,  
	15, 
	30, 
	60, 
	90, 
	91, 
	92, 
	93, 
	94, 
	95, 
	97, 
	99, 
	100,
	105,
	110,
	115,
	120,
	125,
	130,
	135,
	140,
	145,
	150,
	155,
	160,
	165,
	170,
	180,
]

def LoadData(densManager):
	f = open("settings.json")
	data = json.load(f)
	for map in data:
		mapDetails = data[map][0]
		for i in range(mapDetails['level_min'], mapDetails['level_max']):
			GetYangFromMap(mapDetails['folder_name'], i, densManager)


def GetMobYang():
	mydb = mysql.connector.connect(
	host="localhost",
		user="user",
		password="password",
		charset = "utf8"
	)
	mycursor = mydb.cursor(dictionary=True)

	mycursor.execute("SELECT * FROM player.mob_proto")
	records = mycursor.fetchall()
	for row in records:
		mobYangs[int(row["vnum"])] = [int(row["gold_min"]), int(row["gold_max"]), int(row["rank"]), int(row["level"])]


def LoadGroups():
	groupFile = open('data/group.txt', 'r')
	Lines = groupFile.readlines()
	groupVnum = 0
	groupMobs = []
	isLoadingMobs = False
	for line in Lines:
		vec = line.split("\t")
		vec = [i.replace('\n','') for i in vec]
		if len(vec) > 1 and vec[1] == "Vnum":
			groupVnum = int(vec[2])
			isLoadingMobs = True
			continue
		if len(vec[0]) > 0 and vec[0][0] == "}":
			isLoadingMobs = False
			allGroups[groupVnum] = groupMobs
			groupMobs = []
		if isLoadingMobs == True:
			groupMobs.append(int(vec[3]))

def LoadGroupGroup():
	groupGroupFile = open('data/group_group.txt', 'r')
	Lines = groupGroupFile.readlines()
	groupVnum = 0
	groupGroups = []
	isLoadingMobs = False
	for line in Lines:
		vec = line.split("\t")
		vec = [i.replace('\n','') for i in vec]
		if len(vec) > 1 and vec[1] == "Vnum":
			groupVnum = int(vec[2])
			isLoadingMobs = True
			continue
		if len(vec[0]) > 0 and vec[0][0] == "}":
			isLoadingMobs = False
			allGroupGroup[groupVnum] = GroupGroup(groupGroups)
			groupGroups = []
		if isLoadingMobs == True and len(vec) > 3 and vec[2] != "":
			groupGroups.append( {"vnum": int(vec[2]), "chance": int(vec[3]) })

def GetYangFromMap(mapName, playerLevel, densManager):
	mapMobData[mapName] = []
	mobFile = open('data/map/' + mapName + '/regen.txt', 'r')
	Lines = mobFile.readlines()

	mobsVnum = []
	for line in Lines:
		mobsVnum = []
		if line[0] == "r":
			groupGroupVnum = line.split("\t")[10]
			groupGroupVnum = groupGroupVnum.replace("\n", "")
			groupVnum = allGroupGroup[int(groupGroupVnum)].GetGroup()
			coordX = line.split("\t")[1]
			coordY = line.split("\t")[2]
			time = line.split("\t")[7]
			timeVal = int(time[:-1])
			if time[-1:] == 'm':
				timeVal *= 60
			elif time[-1:] == 'h':
				timeVal *= 3600

			if int(groupVnum) in allGroups:
				mobsVnum = allGroups[int(groupVnum)]
				coordArr = [coordX, coordY, mobsVnum, timeVal]
				mapMobData[mapName].append(coordArr)
		elif line[0] == "g":
			groupVnum = line.split("\t")[10]
			groupVnum = groupVnum.replace("\n", "")
			mobsVnum = allGroups[int(groupVnum)]
			coordX = line.split("\t")[1]
			coordY = line.split("\t")[2]
			time = line.split("\t")[7]
			timeVal = int(time[:-1])
			if time[-1:] == 'm':
				timeVal *= 60
			elif time[-1:] == 'h':
				timeVal *= 3600
			coordArr = [coordX, coordY, mobsVnum, timeVal]
			mapMobData[mapName].append(coordArr)
		else:
			continue
	densManager.GetDensiestPoint(mapName, playerLevel)

class DensityGraph:
	def GetDensiestPoint(self, mapName, playerLevel):
		wholeYang = 0
		mobCount = 0
		tempArr = []
		for point in mapMobData[mapName]:
			tempArr.append(point[:2])
		point_tree = spatial.cKDTree(tempArr)
		maxCount = 0
		densiest = 0
		pointsArray = []
		for point in tempArr:
			arr = point_tree.query_ball_point(point, 70)
			if len(arr) > maxCount:
				maxCount = len(arr)
				densiest = point
				pointsArray = arr

		for index in pointsArray:
			for mob in mapMobData[mapName][index][2]:
				if mob not in mobYangs:
					continue
				yangMin = mobYangs[mob][0]
				yangMax = mobYangs[mob][1]
				mobRank = mobYangs[mob][2]
				avrYang = random.randint(yangMin, yangMax)
				goldPercent = MOB_RANK_DROP_CHANCE[mobRank]
				mobLevel = mobYangs[mob][3]

				levelDelta = max((mobLevel + 15) - playerLevel, 0)
				levelDelta = min(levelDelta, 30)

				totalPercent = (goldPercent * DROP_CHANCE_LEVEL_DELTA[levelDelta]) / 100
				mobCount += 1 
				if (random.randint(0, 100) > totalPercent):
					continue

				time = mapMobData[mapName][index][3]
				respPerHour = 3600 / time
				avrYang *= respPerHour

				wholeYang += avrYang
		dataPoint = { 'level': playerLevel, 'yang': wholeYang, 'mapName': mapName}
		graphData.append(dataPoint)


densGraphInstance = DensityGraph()

LoadGroupGroup()
LoadGroups()
GetMobYang()
LoadData(densGraphInstance)

df = pd.DataFrame(graphData)
fig = px.bar(df, x = 'level', y = 'yang', color='mapName')
fig.show()
