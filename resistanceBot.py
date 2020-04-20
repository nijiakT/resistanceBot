from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, Filters
from ResGame import ResGame
import telegram
import logging
import time
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

bot_token = 'redacted'
bot = telegram.Bot(token=bot_token)
my_persistence = PicklePersistence(filename='resistanceBot.py')
updater = Updater(token=bot_token, persistence=my_persistence, use_context=True)
j = updater.job_queue
dispatcher = updater.dispatcher


games = {}

#internal functions - keyboard markup stuff
def button(update, context):
    global games
    query = update.callback_query
    try:
        query.answer()
        tempList = list(query.data.split(' '))
        func = int(tempList[0])
        chatId = int(tempList[1])
        game = games[chatId]
        if func == 1:
            #func 1 is leader choosing team members
            chosenId = int(tempList[2])
            if chosenId in game.teamCache:
                query.edit_message_text(text='You already chose {}!'.format(game.playerNames[chosenId]))
                teamChoosing(query.from_user.id, chatId)
                return
            else:
                game.teamCache.append(chosenId)
                query.edit_message_text(text='You chose: {}'.format(game.playerNames[chosenId]))
                if len(game.teamCache) == game.teamLimit:
                    teamVoting(chatId)
                    return
                else:
                    teamChoosing(query.from_user.id, chatId)
                    return
        elif func == 2:
            #func 2 is voting on the team
            if int(tempList[3]) == 1:
                game.yesCache.append(int(tempList[2]))
                query.edit_message_text(text='You chose: >Yes 👍')
            else:
                game.noCache.append(int(tempList[2]))
                query.edit_message_text(text='You chose: >No 👎')
            responses = len(game.yesCache) + len(game.noCache)
            if responses == len(game.players):
                voteOutcome(chatId)
        else:
            #func 3 is voting on the mission
            if int(tempList[3]) == 1:
                game.passCache += 1
                query.edit_message_text(text='You chose: >Pass 👍')
            else:
                game.failCache += 1
                query.edit_message_text(text='You chose: >Fail 👎')
            responses = game.passCache + game.failCache
            if responses == len(game.teamCache):
                missionOutcome(chatId)
    except:
        query.edit_message_text(text='Sorry, there was an error. Please try again from the team choosing phase. (Leader, send /chooseteam!)')
        tempList = list(query.data.split(' '))
        func = int(tempList[0])
        chatId = int(tempList[1])
        game = games[chatId]
        if func == 1:
            teamChoosing(query.from_user.id, chatId)
            return
        elif func == 2:
            team = games[chatId].teamNames()
            button_list = [[InlineKeyboardButton('Yes', callback_data='2 '+ str(chatId) + ' ' + str(query.from_user.id) + ' ' + '1'), InlineKeyboardButton('No', callback_data='2 ' + str(chatId) + ' ' + str(query.from_user.id) + ' ' + '2')]]
            reply_markup = InlineKeyboardMarkup(button_list)
            bot.send_message(chat_id=query.from_user.id, text='Your leader has chosen to send: ' + team + '\. Do you want to support them?', parse_mode=telegram.ParseMode.MARKDOWN_V2, reply_markup=reply_markup)
        elif func == 3:
            button_list = [[InlineKeyboardButton('Pass', callback_data='3 '+ str(chatId) + ' ' + str(query.from_user.id) + ' ' + '1'), InlineKeyboardButton('Fail', callback_data='3 ' + str(chatId) + ' ' + str(query.from_user.id) + ' ' + '2')]]
            reply_markup = InlineKeyboardMarkup(button_list)
            bot.send_message(chat_id=query.from_user.id, text='You are on the mission team. Do you want to pass or fail the mission?', reply_markup=reply_markup)
        else:
            bot.send_message(chat_id=query.from_user.id, text="We're sorry, there was an unforeseen error. Please report this to the person who introduced you to this bot. Thank you!")

def teamChoosing(userId, chatId):
    button_list = []
    for id in list(games[chatId].playerNames.keys()):
        boldName = games[chatId].playerNames[id]
        name = boldName[1:len(boldName) - 1]
        button_list = button_list + [[InlineKeyboardButton(name, callback_data='1 ' + str(chatId) + ' ' + str(id))]]
    reply_markup = InlineKeyboardMarkup(button_list)
    bot.send_message(chat_id=userId, text='Choose the team for this round:', parse_mode=telegram.ParseMode.MARKDOWN_V2, reply_markup=reply_markup)

def teamVoting(chatId):
    team = games[chatId].teamNames()
    #maybe move the for block out, shift to teamChooseButton where this func is called
    for id in games[chatId].players:
        button_list = [[InlineKeyboardButton('Yes', callback_data='2 '+ str(chatId) + ' ' + str(id) + ' ' + '1'), InlineKeyboardButton('No', callback_data='2 ' + str(chatId) + ' ' + str(id) + ' ' + '2')]]
        reply_markup = InlineKeyboardMarkup(button_list)
        bot.send_message(chat_id=id, text='Your leader has chosen to send: ' + team + '\. Do you want to support them?', parse_mode=telegram.ParseMode.MARKDOWN_V2, reply_markup=reply_markup)

def voteOutcome(chatId):
    team = games[chatId].teamNames()
    votes = games[chatId].voteNames()
    bot.send_message(chat_id=chatId, text='The voting outcome to send ' + team + ' is:\n' + votes, parse_mode=telegram.ParseMode.MARKDOWN_V2)
    if len(games[chatId].yesCache) <= len(games[chatId].noCache):
        if games[chatId].teamF == 4:
            bot.send_message(chat_id=chatId, text='❎ Failed to send a team 5 times in a row!')
            spiesWin(chatId)
        else:
            bot.send_message(chat_id=chatId, text='❎ Insufficient votes to send the team! Moving to the next leader.')
            games[chatId].teamF += 1
            sendMissionState(chatId)
    else:
        bot.send_message(chat_id=chatId, text="🚩 Sent the team out! Let's see how the mission goes...")
        missionVoting(chatId)

def missionVoting(chatId):
    for id in games[chatId].teamCache:
        button_list = [[InlineKeyboardButton('Pass', callback_data='3 '+ str(chatId) + ' ' + str(id) + ' ' + '1'), InlineKeyboardButton('Fail', callback_data='3 ' + str(chatId) + ' ' + str(id) + ' ' + '2')]]
        reply_markup = InlineKeyboardMarkup(button_list)
        bot.send_message(chat_id=id, text='You are on the mission team. Do you want to pass or fail the mission?', reply_markup=reply_markup)

def missionOutcome(chatId):
    votes = 'The voting outcome is:\nPass --> ' + str(games[chatId].passCache) + '\nFail --> ' + str(games[chatId].failCache)
    bot.send_message(chat_id=chatId, text=votes)
    if games[chatId].failCache >= games[chatId].failsNeeded:
        if games[chatId].missionF < 2:
            bot.send_message(chat_id=chatId, text='❌ The mission failed! Was there a spy in the team?')
            games[chatId].missionF += 1
            games[chatId].teamF = 0
            sendMissionState(chatId)
        else:
            bot.send_message(chat_id=chatId, text='❌ The mission failed, and that was the third one...')
            spiesWin(chatId)
    else:
        if games[chatId].missionP < 2:
            bot.send_message(chat_id=chatId, text='⭕ We succeeded! On to the next mission, team!')
            games[chatId].missionP += 1
            games[chatId].teamF = 0
            sendMissionState(chatId)
        else:
            bot.send_message(chat_id=chatId, text="⭕ Success! We've completed all our missions!")
            resistanceWins(chatId)


#internal functions - setup and cleanup
def gameStart(chatId, context):
    global games
    #change to 5!
    if len(games[chatId].players) < 5:
        context.bot.send_message(chat_id=chatId, text='Not enough players to start the game.')
        return
    games[chatId].gameStarted = True
    context.bot.send_message(chat_id=chatId, text='Starting game!')
    games[chatId].setup()
    revealRoles(chatId)
    return

def resistanceWins(chatId):
    spies = games[chatId].spyNames
    bot.send_message(chat_id=chatId, text='🔵 The resistance has won\! The spies were: ' + spies, parse_mode=telegram.ParseMode.MARKDOWN_V2)
    gameEnd(chatId)

def spiesWin(chatId):
    spies = games[chatId].spyNames
    bot.send_message(chat_id=chatId, text='🔴 The spies have won\! They were: ' + spies, parse_mode=telegram.ParseMode.MARKDOWN_V2)
    gameEnd(chatId)

def gameEnd(chatId):
    global games
    del games[chatId]
    return

def first_call(context):
    chatId = context.job.context['chat_id']
    if chatId not in games:
        return
    elif games[chatId].gameStarted:
        return
    context.bot.send_message(chat_id=chatId, text='30 seconds left to join la Resistencia!')
    j.run_once(last_call, 15, context=context.job.context)

def last_call(context):
    chatId = context.job.context['chat_id']
    if chatId not in games:
        return
    elif games[chatId].gameStarted:
        return
    context.bot.send_message(chat_id=chatId, text='15 seconds left to join la Resistencia! (Or to betray us, you traitor scum.)')
    j.run_once(delayedStart, 15, context=context.job.context)

def delayedStart(context):
    chatId = context.job.context['chat_id']
    if chatId not in games:
        return
    elif games[chatId].gameStarted:
        return
    else:
        if len(games[chatId].players) < 5:
            context.bot.send_message(chat_id=chatId, text='Not enough players to play, cancelling game!')
            gameEnd(chatId)
            return
        games[chatId].gameStarted = True
        context.bot.send_message(chat_id=chatId, text='Starting game!')
        games[chatId].setup()
        revealRoles(chatId)
        return

def revealRoles(chatId):
    global games
    game = games[chatId]
    for i in list(game.playerNames.keys()):
        if i not in list(game.spies.keys()):
            bot.send_message(chat_id=i, text='🔵 You are a member of the resistance. There are ' + str(len(game.spies)) + ' spies this game.')
    for i in list(game.spies.keys()):
        bot.send_message(chat_id=i, text='🔴 You are a spy\! The spies this game are: ' + game.spyNames + '\.', parse_mode=telegram.ParseMode.MARKDOWN_V2)
    sendMissionState(chatId)

def sendMissionState(chatId):
    games[chatId].clearCache()
    missionState = games[chatId].generateMission()
    bot.send_message(chat_id=chatId, text=missionState, parse_mode=telegram.ParseMode.MARKDOWN_V2)
    bot.send_message(chat_id=chatId, text='Leader: send /chooseteam when you are ready to choose your team for the round!')

#Commands
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Viva la Resistencia! To start a game, add me into a group chat and send /hostgame.')
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def startgame(update, context):
    global games
    if update.effective_chat.type == "group":
        chatId = update.effective_chat.id
        if chatId not in games:
            games[chatId] = ResGame()
            context.bot.send_message(chat_id=chatId, text='A game is starting! Send /join to join the game. (Please make sure that all players have sent me a PM with /start!)')
            j.run_once(first_call, 30, context={'chat_id':chatId})
        else:
            context.bot.send_message(chat_id=chatId, text='A game is already being hosted.')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Sorry, a game can only be started in a group chat.')
startgame_handler = CommandHandler('startgame', startgame)
dispatcher.add_handler(startgame_handler)

def forcestart(update, context):
    chatId = update.effective_chat.id
    if chatId not in games:
        context.bot.send_message(chat_id=chatId, text='There is no game being hosted. Send /startgame to start a game!')
        return
    elif games[chatId].gameStarted:
        context.bot.send_message(chat_id=chatId, text='What do you mean? The game has already started!')
        return
    gameStart(chatId, context)
forcestart_handler = CommandHandler('forcestart', forcestart)
dispatcher.add_handler(forcestart_handler)

def join(update, context):
    global games
    chatId = update.effective_chat.id
    if chatId not in games:
        context.bot.send_message(chat_id=chatId, text='There is no game being hosted. Send /startgame to start a game!')
        return
    elif games[chatId].gameStarted:
        context.bot.send_message(chat_id=chatId, text='The game has already started! Wait for the next revolution of the people.')
        return
    #get userId and name of the player who sent the command and store for the game
    userId = update.effective_user.id
    name = '*' + update.message.from_user.full_name + '*'
    if userId in games[chatId].players:
        context.bot.send_message(chat_id=chatId, text=name + ' has already joined\!', parse_mode=telegram.ParseMode.MARKDOWN_V2)
    else:
        games[chatId].players.append(userId)
        games[chatId].playerNames[userId] = name
        context.bot.send_message(chat_id=chatId, text=name + ' has joined the game\!', parse_mode=telegram.ParseMode.MARKDOWN_V2)
        #change this value to 10!
        if len(games[chatId].players) == 10:
            context.bot.send_message(chat_id=chatId, text='Maximum number of players reached.')
            gameStart(chatId, context)
join_handler = CommandHandler('join', join)
dispatcher.add_handler(join_handler)

def chooseteam(update, context):
    chatId = update.effective_chat.id
    userId = update.effective_user.id
    if chatId not in games:
        context.bot.send_message(chat_id=chatId, text='There is no game being hosted. Send /startgame to start a game!')
        return
    else:
        if userId == games[chatId].leaderId:
            games[chatId].clearCache()
            #function to send keyboard markup for team selection
            teamChoosing(userId, chatId)
        else:
            context.bot.send_message(chat_id=chatId, text="You aren't the leader this round! We're trying to take down tyranny, not each other.")
chooseteam_handler = CommandHandler('chooseteam', chooseteam)
dispatcher.add_handler(chooseteam_handler)

def endgame(update, context):
    if update.effective_chat.id not in games:
        context.bot.send_message(chat_id=update.effective_chat.id, text='There is no game being hosted. Send /startgame to start a game!')
        return
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Ending game!')
        gameEnd(update.effective_chat.id)
        return
endgame_handler = CommandHandler('endgame', endgame)
dispatcher.add_handler(endgame_handler)

def playerlist(update, context):
    chatId = update.effective_chat.id
    if chatId not in games:
        context.bot.send_message(chat_id=chatId, text='There is no game being hosted. Send /startgame to start a game!')
        return
    else:
        players = ', '.join(list(games[chatId].playerNames.values()))
        context.bot.send_message(chat_id=update.effective_chat.id, text='Players currently in the game:\n' + players, parse_mode=telegram.ParseMode.MARKDOWN_V2)
        return
playerlist_handler = CommandHandler('playerlist', playerlist)
dispatcher.add_handler(playerlist_handler)

def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='''Bienvenido, Resistencia! We have missions to complete, but there are traitors in our midst, and we are running low on time.\n\nEach round, the leader will have 3 minutes to choose the mission team. We'll put it to a vote, and if the majority agrees, we'll send them out. If not, we'll change the leader and decide on a new team. If we fail to send a team five times for the same mission, then the traitors have sown discord amongst us and we have lost.\n\nThe success of the mission depends on each member, and if three missions fail, then these traitors have won. But if we succeed in three of our missions, then there is hope yet for our land. Let's begin!''')
help_handler = CommandHandler('help', help)
dispatcher.add_handler(help_handler)

def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Lo siento, I didn't understand that command.")
unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

#CallbackQueryHandler to handle button responses
updater.dispatcher.add_handler(CallbackQueryHandler(button))

while True:
    try:
        updater.start_polling()
    except Exception:
        time.sleep(15)

#resistanceBot was coded in April 2020 by nijiakT as a personal project to get familiar with python
#and learn more about telegram bots. Many thanks to btwj for providing bot advice and friends for
#testing and feedback about bot functionality :)
