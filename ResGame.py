import random
class ResGame:
    fiveP = [2, 3, 2, 3, 3]
    sixP = [2, 3, 4, 3, 4]
    sevenP = [2, 3, 3, 4, 4]
    eightP = [3, 4, 4, 5, 5]
    nineP = [3, 4, 4, 5, 5]
    tenP = [3, 4, 4, 5, 5]
    missions = [fiveP, sixP, sevenP, eightP, nineP, tenP]

    def __init__(self):
        self.players = []
        self.playerNames = {}
        self.spies = {}
        self.missionP = 0
        self.missionF = 0
        self.teamF = 0
        self.spyNames = ' '
        self.gameStarted = False
        self.leaderId = 0
        self.teamCache = []
        self.teamLimit = 0
        self.leaderClock = 0
        self.yesCache = []
        self.noCache = []
        self.passCache = 0
        self.failCache = 0
        self.failsNeeded = 1

    def setup(self):
        if len(self.players) == 10:
            self.splitTeams(4)
        elif len(self.players) >= 7:
            self.splitTeams(3)
        elif len(self.players) >= 5:
            self.splitTeams(2)
        #else:
            #delete this after
            #self.splitTeams(1)

    def splitTeams(self, spiesNum):
        #move the required number of spies from resistance to spies
        for i in range(spiesNum):
            #first pop the chosen user id from players so it wont get used again
            spy_id = self.players.pop(random.randrange(len(self.players)))
            self.spies[spy_id] = self.playerNames[spy_id]
        #add all the spies' ids back to players
        for i in list(self.spies.keys()):
            self.players.append(i)
        self.spyNames = ', '.join(list(self.spies.values()))
        #shuffle the list of players for deciding on leader of each round
        random.shuffle(self.players)

    def generateMission(self):
        round = self.missionP + self.missionF
        missionSet = ResGame.missions[len(self.players) - 5]
        #delete this after
        #missionSet=ResGame.missions[0]
        self.teamLimit = missionSet[round]
        failsReq = '1 sabotage and this mission fails\.'
        if round == 3 and len(self.players) >= 7:
            failsReq = '2 sabotages and this mission fails\.'
            self.failsNeeded = 2
        else:
            self.failsNeeded = 1
        leader = self.leaderName()
        leaderStatement = 'The leader for this round is ' + leader + '\. Mission ' + str(round + 1) + ':\n'
        missionStatement = str(missionSet[round]) + ' players must be sent on the mission this round\. ' + failsReq
        mission = leaderStatement + missionStatement
        return mission

    def leaderName(self):
        if self.leaderClock == len(self.players):
            self.leaderClock = 0
        self.leaderId = self.players[self.leaderClock]
        self.leaderClock += 1
        if self.leaderId in self.playerNames:
            return self.playerNames[self.leaderId]
        else:
            return 'Error occurred while generating leader name.'

    def teamNames(self):
        teamList = []
        for i in self.teamCache:
            teamList.append(self.playerNames[i])
        names = ', '.join(teamList)
        return names

    def voteNames(self):
        yesList = []
        noList = []
        for i in self.yesCache:
            yesList.append(self.playerNames[i])
        for i in self.noCache:
            noList.append(self.playerNames[i])
        yesVote = ', '.join(yesList)
        noVote = ', '.join(noList)
        vote = 'Voted yes:\n' + yesVote + '\nVoted no:\n' + noVote
        return vote

    def clearCache(self):
        self.teamCache = []
        self.yesCache = []
        self.noCache = []
        self.passCache = 0
        self.failCache = 0

#resistanceBot was coded in April 2020 by nijiakT as a personal project to get familiar with python
#and learn more about telegram bots. Many thanks to btwj for providing bot advice and friends for
#testing and feedback about bot functionality :)
