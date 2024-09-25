from os import getenv
from dotenv import load_dotenv
import telebot
from telebot import types
import re
import requests
from log_lib import *
from db_lib import *
from game_lib import *

ENV_BOTTOKEN = 'BOTTOKEN'
ENV_BOTTOKENTEST = 'BOTTOKENTEST'

ENV_TESTDB = 'TESTDB'
ENV_TESTBOT = 'TESTBOT'

VERSION = '1.0'

TITLETEXT_SEPARATOR = '@@@'

CMD_START = '/start'
CMD_HELP = '/help'
CMD_SETTINGS = '/settings'

CALLBACK_COMPLEXITY_TAG = 'complexity:'
CALLBACK_TYPE1_TAG = 'type1answer:'
CALLBACK_TYPE2_TAG = 'type2answer:'
CALLBACK_GAMETYPE_TAG = 'gametype:'

DEFAULT_ERROR_MESSAGE = 'Произошла ошибка. Попробуйте позже.'

PERSONS_IN_TYPE2_ANSWER = 5

#============================
# Common functions
#----------------------------
def isTestBot() -> bool:
    load_dotenv()
    ret = True
    testbot = getenv(key=ENV_TESTBOT)
    if (testbot):
        if (testbot == "False"):
            ret = False
    return ret

def isTestDB() -> bool:
    load_dotenv()
    ret = True
    testdb = getenv(key=ENV_TESTDB)
    if (testdb):
        if (testdb == "False"):
            ret = False
    return ret    

def getBotToken(test):
    load_dotenv()
    token = getenv(key=ENV_BOTTOKEN)
    if (test):
        token = getenv(key=ENV_BOTTOKENTEST)
    return token

#=====================
# Bot class
#---------------------
class GuessPersonBot:
    __bot = None

    def registerHandlers(self) -> None:
        GuessPersonBot.__bot.register_message_handler(callback=self.messageHandler)
        GuessPersonBot.__bot.register_callback_query_handler(
            callback=self.complexityHandler,
            func=lambda message: re.match(pattern=fr'^{CALLBACK_COMPLEXITY_TAG}\d+$', string=message.data)
        )
        GuessPersonBot.__bot.register_callback_query_handler(
            callback=self.gameTypeHandler,
            func=lambda message: re.match(pattern=fr'^{CALLBACK_GAMETYPE_TAG}\d+$', string=message.data)
        )
        GuessPersonBot.__bot.register_callback_query_handler(
            callback=self.cmdStartHandler,
            func=lambda message: re.match(pattern=fr'^{CMD_START}$', string=message.data)
        )
        GuessPersonBot.__bot.register_callback_query_handler(
            callback=self.settingsCallbackHandler,
            func=lambda message: re.match(pattern=fr'^{CMD_SETTINGS}$', string=message.data)
        )
        GuessPersonBot.__bot.register_callback_query_handler(
            callback=self.answerHandlerType1,
            func=lambda message: re.match(pattern=fr'^{CALLBACK_TYPE1_TAG}\d+$', string=message.data)
        )
        GuessPersonBot.__bot.register_callback_query_handler(
            callback=self.answerHandlerType2,
            func=lambda message: re.match(pattern=fr'^{CALLBACK_TYPE2_TAG}\d+$', string=message.data)
        )

    def initBot(self) -> bool:
        # Check if bot is already initialized
        if (GuessPersonBot.isInitialized()):
            log(str=f'Bot is already initialized', logLevel=LOG_WARNING)
            return False
        # Initialize bot first time
        isTest = isTestBot()
        botToken = getBotToken(test=isTest)
        if (not botToken):
            log(str=f'Cannot read ENV vars: botToken={botToken}', logLevel=LOG_ERROR)
            return False
        log(f'Bot initialized successfully (test={isTest})')
        GuessPersonBot.__bot = telebot.TeleBot(token=botToken)
        self.registerHandlers()
        return True

    def isInitialized() -> bool:
        return (GuessPersonBot.__bot != None)

    def getBot(self):
        return self.__bot

    # Init bot
    def __init__(self) -> None:
        # Check if bot is initialized
        if (not GuessPersonBot.isInitialized()):
            GuessPersonBot.initBot(self=self)
        self.bot = GuessPersonBot.__bot

    def startBot(self):
        if (not GuessPersonBot.isInitialized()):
            log(str=f'Bot is not initialized - cannot start', logLevel=LOG_ERROR)
            return False
        log(str=f'Starting bot...')
        while(True):
            try:
                self.bot.infinity_polling()
            except KeyboardInterrupt:
                log(str='Exiting by user request')
                break
            except requests.exceptions.ReadTimeout as error:
                log(str=f'startBot: exception: {error}', logLevel=LOG_ERROR)

    # Message handler
    def messageHandler(self, message:types.Message) -> None:
        fName = self.messageHandler.__name__
        username = message.from_user.username
        telegramid = message.from_user.id
        if (not GuessPersonBot.isInitialized()):
            log(str=f'{fName}: Bot is not initialized - cannot start', logLevel=LOG_ERROR)
            return
        # Check if photo recieved
        if (message.text != None):
            # Check if there is a CMD
            if (message.text[0] == '/'):
                return self.cmdHandler(message=message)
                # Check if this is an answer to the game type 3
            elif (self.checkGameTypeNInProgress(telegramid=telegramid, gameType=3)):
                return self.answerHandlerType3(message=message)
        help = self.getHelpMessage(username=username)
        self.sendMessage(telegramid=telegramid, text=f"Я вас не понимаю:(/n{help}")

    # Check is user registered
    def checkUser(self, telegramid) -> bool:
        if (not dbLibCheckTelegramid(telegramid=telegramid)):
            return False
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (dbFound(result=userId)):
            return True
        return False

    def cmdHandler(self, message:types.Message) -> None:
        fName = self.cmdHandler.__name__
        telegramid = message.from_user.id
        username = message.from_user.username
        log(str=f'{fName}: Got message cmd "{message.text}"',logLevel=LOG_DEBUG)
        if (not self.checkUser(telegramid=telegramid)):
            # Register new user if not registered yet
            userId = Connection.insertUser(telegramid=telegramid)
            if (not userId):
                log(str=f'{fName}: Cannot register user {username}', logLevel=LOG_ERROR)
                self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
                return
        text = message.text.lower()
        if text == CMD_HELP:
            self.cmdHelpHandler(message=message)
        elif text == CMD_START:
            self.cmdStartHandler(message=message)
        elif text == CMD_SETTINGS:
            self.cmdSettingsHandler(message=message)
        else:
            self.sendMessage(telegramid=telegramid, text="Неизвестная команда.")
            self.sendMessage(telegramid=telegramid, text=self.getHelpMessage(username=message.from_user.username))

    # Send message to user
    # Returns: Message ID or None in case of error
    def sendMessage(self, telegramid, text):
        if (GuessPersonBot.isInitialized()):
            ret = GuessPersonBot.__bot.send_message(chat_id=telegramid, text=text)
            return ret.message_id
        return None

    def cmdStartHandler(self, message:types.Message) -> None:
        telegramid = message.from_user.id
        self.startNewGame(telegramid=telegramid)

    # /settings cmd handler
    def cmdSettingsHandler(self, message: types.Message) -> None:
        self.requestComplexity(telegramid=message.from_user.id)

    # /help cmd handler
    def cmdHelpHandler(self, message:types.Message) -> None:
        help = self.getHelpMessage(username=message.from_user.username)
        self.sendMessage(telegramid=message.from_user.id, text=help)

    # Returns help message
    def getHelpMessage(self, username) -> str:
        if (not GuessPersonBot.isInitialized()):
            log(str=f'Bot is not initialized - cannot start', logLevel=LOG_ERROR)
            return ''
        ret = self.getWelcomeMessage(username=username)
        return ret + f'''
    Команды GuessPerson_Bot:
        {CMD_HELP} - вывести помощь по командам (это сообщение)
        {CMD_START} - регистрация нового пользователя
        {CMD_SETTINGS} - выбрать уровень сложности и тип игры
        '''
    # Get welcome message
    def getWelcomeMessage(self, username) -> str:
        if (username == None):
            username = ''
        ret = f'''
        Добро пожаловать, {username}!
        Это игра "Guess Person". Версия: {VERSION}
        '''
        return ret

    # Settings callback handler
    def settingsCallbackHandler(self, message: types.CallbackQuery) -> None:
        self.bot.answer_callback_query(callback_query_id=message.id)
        self.requestComplexity(telegramid=message.from_user.id)

    def requestComplexity(self, telegramid) -> None:
        complexities = Connection.getComplexities()
        # Request game complexity
        keys = []
        for c in complexities:
            key = types.InlineKeyboardButton(text=c[1], callback_data=f'{CALLBACK_COMPLEXITY_TAG}{c[0]}')
            keys.append(key)
        keyboard = types.InlineKeyboardMarkup(keyboard=[keys])
        question = 'Выберите уровень сложности:'
        self.bot.send_message(chat_id=telegramid, text=question, reply_markup=keyboard)

    def complexityHandler(self, message: types.CallbackQuery) -> None:
        fName = self.complexityHandler.__name__
        telegramid = message.from_user.id
        log(str=f'{fName}: Complexity handler invoked for user {telegramid}: "{message.data}"',logLevel=LOG_DEBUG)
        self.bot.answer_callback_query(callback_query_id=message.id)
        if (not self.checkUser(telegramid=telegramid)):
            log(str=f'{fName}: Unknown user {telegramid} provided',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        complexity = int(message.data.split(sep=':')[1])
        if (not Connection.dbLibCheckGameComplexity(game_complexity=complexity)):
            self.sendMessage(telegramid=telegramid, text='Нет такой сложности. Попробуйте еще раз.')
            self.requestComplexity(telegramid=telegramid)
            return
        # Set complexity for the user
        ret = Connection.updateUserComplexity(telegramid=telegramid, complexity=complexity)
        if (not ret):
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        # Request Game Type setting
        self.requestGameType(telegramid=telegramid)

    # Request new GameType
    def requestGameType(self, telegramid) -> None:
        fName = self.requestGameType.__name__
        if (not self.checkUser(telegramid=telegramid)):
            log(f'{fName}: Unknown user {telegramid} provided',LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        # Get game type
        game_types = Connection.getGameTypes()
        # Request game type
        keyboard = types.InlineKeyboardMarkup(); # keyboard
        for gameType in game_types:
            key = types.InlineKeyboardButton(text=gameType[1], callback_data=f'{CALLBACK_GAMETYPE_TAG}{gameType[0]}')
            keyboard.add(key)
        question = 'Выберите тип игры:'
        self.bot.send_message(chat_id=telegramid, text=question, reply_markup=keyboard)

    def gameTypeHandler(self, message: types.CallbackQuery) -> None:
        fName = self.gameTypeHandler.__name__
        telegramid = message.from_user.id
        self.bot.answer_callback_query(callback_query_id=message.id)
        log(str=f'{fName}: Game type handler invoked for user {telegramid}: "{message.data}"',logLevel=LOG_DEBUG)
        if (not self.checkUser(telegramid=telegramid)):
            log(f'{fName}: Unknown user {telegramid} provided',LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        gameType = int(message.data.split(sep=':')[1])
        if (not Connection.dbLibCheckGameType(game_type=gameType)):
            self.sendMessage(telegramid=telegramid, text='Нет такого типа. Попробуйте еще раз.')
            self.requestGameType(message=message)
            return
        # Set game type for the user
        ret = Connection.updateUserGameType(telergamid=telegramid, gameType=gameType)
        if (not ret):
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        # Success message
        self.sendMessage(telegramid=telegramid, text='Настройки изменены успешно!')
        key1 = types.InlineKeyboardButton(text='Начать новую игру', callback_data=CMD_START)
        key2= types.InlineKeyboardButton(text='Выбрать другой тип игры/сложность', callback_data=CMD_SETTINGS)
        keyboard = types.InlineKeyboardMarkup(); # keyboard
        keyboard.add(key1)
        keyboard.add(key2)
        question = 'Что дальше?'
        self.bot.send_message(chat_id=telegramid, text=question, reply_markup=keyboard)

    def startNewGame(self, telegramid) -> None:
        fName = self.startNewGame.__name__
        # Check user name format first
        if (not self.checkUser(telegramid=telegramid)):
            log(str=f'{fName}: Unknown user {telegramid} provided',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        # Get game type and complexity
        gameType = Connection.getUserGameType(telegramid=telegramid)
        complexity = Connection.getUserComplexity(telegramid=telegramid)
        # Generate new game for the complexity
        params={
            'telegramid':telegramid,
            'type':gameType,
            'complexity':complexity
        }
        gameId = guess_game.generateNewGame(queryParams=params)
        self.showQuestion(telegramid=telegramid, type=gameType, gameId=gameId)

    def showQuestion(self,telegramid,type,gameId) -> None:
        fName = self.showQuestion.__name__
        if (not self.checkUser(telegramid=telegramid)):
            log(str=f'{fName}: Unknown user {telegramid} provided',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        if (type == 1):
            self.showQuestionType1(telegramid=telegramid, gameId=gameId)
        elif (type == 2):
            self.showQuestionType2(telegramid=telegramid, gameId=gameId)
        elif (type == 3): # type = 3
            self.showQuestionType3(telegramid=telegramid, gameId=gameId)
        else:
            self.sendMessage(telegramid=telegramid, text="Неизваестный тип игры. Пожалуйста, начните новую игру.")

    def showQuestionType1(self,telegramid, gameId) -> None:
        fName = self.showQuestionType1.__name__
        if (not self.checkUser(telegramid=telegramid)):
            log(str=f'{fName}: Unknown user {telegramid} provided',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        # Get gameInfo
        gameInfo = Connection.getGameInfoById(gameId=gameId)
        finished = (gameInfo['result'] != None)
        if (finished):
            self.sendMessage(telegramid=telegramid, text=f'Извините, но игра уже завершена. Введите "{CMD_START}" чтобы начать новую.')
            return
        imageIds = guess_game.getQuestionType1Options(gameInfo=gameInfo)
        if (not imageIds):
            log(str=f'{fName}: Wrong format of imageIds = {imageIds}', logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        data = []
        # Get image URLs
        for id in imageIds:
            url = Connection.getImageUrlById(imageId=id)
            data.append({'url':url,'iId':id})
        # Get text question
        textQuestion = guess_game.getTextQuestion(gameInfo=gameInfo)
        self.sendMessage(telegramid=telegramid, text=textQuestion)
        media_group = []
        for d in data:
            log(str=f'{fName}: image url = {d["url"]}',logLevel=LOG_DEBUG)
            media_group.append(types.InputMediaPhoto(show_caption_above_media=True, media=d['url']))
        ret = self.bot.send_media_group(chat_id=telegramid, media=media_group)
        mIds = []
        for m in ret:
            mIds.append(m.id)
        mIdsTxt = " ".join(str(i) for i in mIds)
        # Save options in current game data
        ret = Connection.setCurrentGameData(telegramid=telegramid, gameData=mIdsTxt)
        # Show buttons for answer
        keys = []
        for i in range(len(data)):
            responseData = f'{CALLBACK_TYPE1_TAG}{data[i]["iId"]}'
            keys.append(types.InlineKeyboardButton(text=str(i+1), callback_data=responseData))
        keyboard = types.InlineKeyboardMarkup(keyboard=[keys])
        self.bot.send_message(chat_id=telegramid, text='Выберите вариант:', reply_markup=keyboard)

    def showQuestionType2(self, telegramid, gameId, gameType = 2) -> None:
        fName = self.showQuestionType2.__name__
        if (not self.checkUser(telegramid=telegramid)):
            log(str=f'{fName}: Unknown user {telegramid} provided',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        # Get gameInfo
        gameInfo = Connection.getGameInfoById(gameId=gameId)
        complexity = gameInfo['complexity']
        imageId = gameInfo['question']
        # Get image URL
        url = Connection.getImageUrlById(imageId=imageId)
        # Get answer options
        imageInfo = Connection.getImageInfoById(imageId=imageId)
        finished = (gameInfo['result'] != None)
        if (finished):
            self.sendMessage(telegramid=telegramid, text='Игра уже сыграна. Пожалуйста, начните новую.')
            return
        # Show image
        log(str=f'URL={url}',logLevel=LOG_DEBUG)
        message = self.bot.send_photo(chat_id=telegramid, photo=url)
        # Save options in current game data
        gameData = f'{message.id} {imageId}'
        ret = Connection.setCurrentGameData(telegramid=telegramid, gameData=gameData)
        if (not ret):
            log(str=f'{fName}: Cannot save game data', logLevel=LOG_WARNING)

        textQuestion = guess_game.getTextQuestion(gameInfo=gameInfo)
        if (gameType == 2): # Show answer options
            personId = imageInfo['personId']
            personName = imageInfo['personName']
            gender = imageInfo['gender']
            # Get year range for creators
            yearRange = guess_game.getPersonByImageYearRange(intYear=imageInfo['year'])
            persons = Connection.getNPersons(
                n=PERSONS_IN_TYPE2_ANSWER,
                exclude=personId,
                complexity=complexity,
                range=yearRange,
                gender=gender)
            persons.append({'personId':personId,'personName':personName})
            shuffle(persons)
            # Show buttons with answer options
            keyboard = types.InlineKeyboardMarkup()
            for i in range(0, len(persons)): # 2 because we start with 1 + correct creator
                personId = persons[i].get('personId')
                if (not personId):
                    log(str=f'{fName}: Cannot get personId: {persons[i]}',logLevel=LOG_WARNING)
                    continue
                personName = persons[i].get('personName')
                if (not personName):
                    log(str=f'{fName}: Cannot get personName: {persons[i]}',logLevel=LOG_WARNING)
                    continue
                data = f'{CALLBACK_TYPE2_TAG}{personId}'
                key = types.InlineKeyboardButton(text=personName, callback_data=data)
                keyboard.add(key)
            self.bot.send_message(chat_id=telegramid, text=textQuestion, reply_markup=keyboard)
        else: # game type == 3
            self.sendMessage(telegramid=telegramid, text=textQuestion)

    def showQuestionType3(self,telegramid, gameId) -> None:
        fName = self.showQuestionType3.__name__
        if (not self.checkUser(telegramid=telegramid)):
            log(str=f'{fName}: Unknown user {telegramid} provided',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        return self.showQuestionType2(telegramid=telegramid, gameId=gameId, gameType=3)

    # Send buttons after answer
    def sendAfterAnswer(self, telegramid) -> None:
        fName = self.sendAfterAnswer.__name__
        if (not self.checkUser(telegramid=telegramid)):
            log(str=f'{fName}: Unknown user {telegramid} provided',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        key1 = types.InlineKeyboardButton(text='Сыграть еще раз', callback_data=CMD_START)
        key2= types.InlineKeyboardButton(text='Выбрать другой тип игры/сложность', callback_data=CMD_SETTINGS)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(key1)
        keyboard.add(key2)
        question = 'Выберите дальнейшее действие:'
        self.bot.send_message(chat_id=telegramid, text=question, reply_markup=keyboard)

    # Modify captures of images with person, name, year
    def modifyImageCaptures(self, telegramid, mIds, imageIds) -> None:
        fName = self.modifyImageCaptures.__name__
        if (not self.checkUser(telegramid=telegramid)):
            log(str=f'{fName}: Unknown user {telegramid} provided',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        if (len(mIds) != len(imageIds)):
            log(str=f'{fName}: len of mIds and imageIds doesnt match', logLevel=LOG_ERROR)
            return
        for i in range(0, len(mIds)):
            self.modifyImageCapture(telegramid=telegramid, messageId=mIds[i], imageId=imageIds[i])

    def modifyImageCapture(self, telegramid, messageId, imageId) -> None:
        fName = self.modifyImageCapture.__name__
        if (not self.checkUser(telegramid=telegramid)):
            log(str=f'{fName}: Unknown user {telegramid} provided',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        # Get image info
        imageInfo = Connection.getImageInfoById(imageId=imageId)
        if (dbFound(result=imageInfo)):
            # If image name is just a number - do not show
            imageNameToShow = self.getImageNameToShow(imageName=imageInfo['name'])
            # Do not show year if missing
            yearToShow = self.getYearToShow(year=imageInfo['year_str'])
            caption = f"{imageInfo['personName']}{imageNameToShow}{yearToShow}"
            # Edit image capture
            self.bot.edit_message_caption(chat_id=telegramid, message_id=messageId, caption=caption)
        else:
            log(str=f'{fName}: Cannot get image info for {imageId}', logLevel=LOG_ERROR)

    def getImageNameToShow(self, imageName) -> str:
        imageNameReturn = ''
        try:
            int(imageName)
        except:
            imageNameReturn = f' - {imageName}'
        return imageNameReturn
    
    def getYearToShow(self, year) -> str:
        yearReturn = ''
        try:
            if (int(year) != 0):
                # Should not be here
                log(str=f'Year is number for unkown reason')
        except:
            yearReturn = f' - {year}'
        return yearReturn
    
    def answerHandlerType1(self, message: types.CallbackQuery) -> None:
        fName = self.answerHandlerType1.__name__
        telegramid = message.from_user.id
        self.bot.answer_callback_query(callback_query_id=message.id)
        if (not self.checkUser(telegramid=telegramid)):
            log(str=f'{fName}: Unknown user {telegramid} provided',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        imageId = int(message.data.split(sep=':')[1])
        # Get current game
        gameId = Connection.getCurrentGame(telegramid=telegramid)
        if (not gameId):
            self.sendMessage(telegramid=telegramid, text='Нет запущенных игр. Введите "/start" чтобы начать новую.')
            return
        # Get question info
        gameInfo = Connection.getGameInfoById(gameId=gameId)
        answerOptions = guess_game.getQuestionType1Options(gameInfo=gameInfo)
        correctAnswerNum = None
        if (answerOptions):
            correctAnswerNum = self.findNumOfType1Answer(imageIds=answerOptions, correctId=gameInfo['correct_answer'])
        imageIds = guess_game.getQuestionType1Options(gameInfo=gameInfo)
        if (not imageIds):
            log(str=f'{fName}: Wrong format of imageIds = {imageIds}', logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return

        # Get image messages ids
        mIdsTxt = Connection.getCurrentGameData(telegramid=telegramid)
        mIds = guess_game.getMessageIds(mIdsTxt=mIdsTxt)
        self.modifyImageCaptures(telegramid=telegramid, mIds=mIds, imageIds=imageIds)

        # Finish game and return result
        guess_game.finishGame(telegramid=telegramid, gameId=gameId, answer=imageId)
        # Get game info
        gameInfo = Connection.getGameInfoById(gameId=gameId)
        # Check result
        result = gameInfo['result']
        correctAnswerId = gameInfo.get('correct_answer')
        correctAnswer = Connection.getImageInfoById(imageId=correctAnswerId).get('personName')
        if (dbFound(result=correctAnswer)):
            correctMessage = f'"{correctAnswer}"'
            self.showGameResult(telegramid=telegramid, result=result, correctAnswer=correctAnswer,
                            correctMessage=correctMessage, correctAnswerNum=correctAnswerNum)
        else:
            log(str=f'{fName}: Cannot get person data from DB: {correctAnswerId}',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)

    def answerHandlerType2(self, message: types.CallbackQuery) -> None:
        fName = self.answerHandlerType2.__name__
        telegramid = message.from_user.id
        self.bot.answer_callback_query(callback_query_id=message.id)
        if (not self.checkUser(telegramid=telegramid)):
            log(str=f'{fName}: Unknown user {telegramid} provided',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        personId = int(message.data.split(sep=':')[1])
        # Get current game
        gameId = Connection.getCurrentGame(telegramid=telegramid)
        if (not gameId):
            self.sendMessage(telegramid=telegramid, text=f'Нет запущенных игр. Введите "{CMD_START}" чтобы начать новую.')
            return
        # Modify photo capture
        self.modifyPhotoCapture(telegramid=telegramid)
        # Finish game and return result
        guess_game.finishGame(telegramid=telegramid, gameId=gameId, answer=personId)
        # Get game info
        gameInfo = Connection.getGameInfoById(gameId=gameId)
        # Check result
        result = gameInfo['result']
        # Get correct answer
        correctAnswerId = gameInfo.get('correct_answer')
        personInfo = Connection.getPersonInfoById(personId=correctAnswerId)
        if (dbFound(result=personInfo)):
            correctAnswer = personInfo['name']
            correctMessage = f'Это - "{correctAnswer}".'
            self.showGameResult(telegramid=telegramid, result=result,
                                correctAnswer=correctAnswer, correctMessage=correctMessage)
        else:
            log(str=f'{fName}: Cannot get person data from DB: {correctAnswerId}',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)

    def answerHandlerType3(self, message: types.Message) -> None:
        fName = self.answerHandlerType3.__name__
        telegramid = message.from_user.id
        if (not self.checkUser(telegramid=telegramid)):
            log(str=f'{fName}: Unknown user {telegramid} provided',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        # Get current game
        gameId = Connection.getCurrentGame(telegramid=telegramid)
        if (not gameId):
            log(str=f'{fName}: Answer where no game in progress: user telegramid = {telegramid}',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=f'Нет запущенных игр. Введите "{CMD_START}" чтобы начать новую.')
            return
        # User answer
        personName = message.text
        # Get game info
        gameInfo = Connection.getGameInfoById(gameId=gameId)
        # Get correct answer - personId from DB
        correctAnswerId = gameInfo.get('correct_answer')
        personInfo = Connection.getPersonInfoById(personId=correctAnswerId)
        if (dbFound(result=personInfo)):
            correctAnswer = personInfo['name']
            answer = 0
            if (self.checkAnswerGameType3(userPersonName=personName, correctPersonName=correctAnswer)):
                answer = correctAnswerId # User is correct
            # Modify photo capture
            self.modifyPhotoCapture(telegramid=telegramid)
            # Finish game and return result
            guess_game.finishGame(telegramid=telegramid, gameId=gameId, answer=answer)
            # Get game info again to update result
            gameInfo = Connection.getGameInfoById(gameId=gameId)
            result = gameInfo['result']
            correctMessage = f'Это - {correctAnswer}.'
            self.showGameResult(telegramid=telegramid, result=result,
                                correctAnswer=correctAnswer, correctMessage=correctMessage)
        else:
            log(str=f'{fName}: Cannot get person data from DB: {correctAnswerId}',logLevel=LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)

    # Modify previous photo capture
    def modifyPhotoCapture(self, telegramid) -> None:
        fName = self.modifyPhotoCapture.__name__
        gameData = Connection.getCurrentGameData(telegramid=telegramid)
        if (dbFound(result=gameData)):
            retVal = guess_game.getMessageIdAndMessagePhotoId(gameData=gameData)
            if (retVal):
                mPhotoId = retVal[0]
                imageId = retVal[1]
                self.modifyImageCapture(telegramid=telegramid, messageId=mPhotoId, imageId=imageId)
            else:
                log(str=f'{fName}: Cannot get message id and photo id for user {telegramid}',logLevel=LOG_WARNING)
        else:
            log(str=f'{fName}: Cannot get game data for user {telegramid}',logLevel=LOG_WARNING)

    # Find number of correct answer in type 1 question
    # Returns:
    #   i - num of correct answer starting from 1
    #   None - if any issues
    def findNumOfType1Answer(self, imageIds, correctId):
        ret = None
        for i in range(0, len(imageIds)):
            if (imageIds[i] == correctId):
                ret = i + 1
                break
        return ret
    
    # Show game result
    def showGameResult(self, telegramid, result, correctAnswer, correctMessage='', correctAnswerNum=None) -> None:
        # Check result
        correctAnswerTxt = ''
        if (correctAnswerNum):
            correctAnswerTxt = f' под номером {correctAnswerNum}'
        if (result):
            # Answer is correct
            self.sendMessage(telegramid=telegramid, text=f'Поздравляю! Вы ответили верно. {correctMessage}{correctAnswerTxt}')
        else:
            correctAnswerTxt = ''
            if (correctAnswerNum):
                correctAnswerTxt = f' под номером {correctAnswerNum}'
            self.sendMessage(telegramid=telegramid, text=f'А вот и не верно. Верный ответ{correctAnswerTxt}: "{correctAnswer}"')
        self.sendAfterAnswer(telegramid=telegramid)

    # Check answer for game type 3
    def checkAnswerGameType3(self, userPersonName, correctPersonName) -> bool:
        # 1. Convern both strings to the same format
        userPersonName = userPersonName.lower() # Convert to lower
        correctPersonName = correctPersonName.lower()
        userPersonName = userPersonName.replace('ё','е') # Replace 'ё'
        correctPersonName = correctPersonName.replace('ё','е') # Replace 'ё'
        correctPersonName = correctPersonName.replace('й','й') # Replace 'й'

        # 0. Full match
        if (userPersonName == correctPersonName):
            log(f'Full match: {userPersonName} == {correctPersonName}',LOG_DEBUG)
            return True

        lU = len(userPersonName)
        lC = len(correctPersonName)
        # 2. Check length of userAnswer
        if (lU > lC):
            log(f'User len > correct len: {lU} > {lC}',LOG_DEBUG)
            return False
        
        # 3. Check if only one word in answer (probably last name)
        userAnswerWords = userPersonName.split(' ')
        if (len(userAnswerWords) == 1):
            # Get last work of correctAnswer
            correctAnswerWords = correctPersonName.split(' ')
            userAnswerLastWord = userAnswerWords[0]
            correctAnswerLastWord = correctAnswerWords[-1]
            # If correct last word len < 3 - only exact answer
            if (len(correctAnswerLastWord) <= 3):
                if (userAnswerLastWord == correctAnswerLastWord):
                    log(f'Full last word match (len <=3): {userAnswerLastWord} == {correctAnswerLastWord}',LOG_DEBUG)
                    return True
            else:
                # Check len difference
                lAlw = len(userAnswerLastWord)
                lClw = len(correctAnswerLastWord)
                if (abs(lAlw-lClw) <= 2):
                    # Check similarity for last name
                    ret = isStrSimilar(userAnswerLastWord, correctAnswerLastWord)
                    if (ret):
                        log(f'Last word similarity match (similarity={ret}): {userAnswerLastWord} | {correctAnswerLastWord}',LOG_DEBUG)
                        return True

        if (lU > 5):
            correctAnswer = correctPersonName[-lU:]
            ret = isStrSimilar(userPersonName, correctAnswer)
            if (ret):
                log(f'Last part of answer similarity (similarity={ret}): {userPersonName} | {correctAnswer}',LOG_DEBUG)
                return True

        # 4. Check Levenstein similarity for full answer
        ret = isStrSimilar(userPersonName, correctPersonName)
        if (ret):
            log(f'Full answer similarity (similarity={ret}: {userPersonName} | {correctPersonName}',LOG_DEBUG)
            return True

        return ret

    # Check that game N is in progress
    # Returns: True/False
    def checkGameTypeNInProgress(self, telegramid, gameType) -> bool:
        fName = self.checkGameTypeNInProgress.__name__
        userName = telegramid
        if (not self.checkUser(telegramid=telegramid)):
            log(f'{fName}: Unknown user {telegramid} provided',LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text=DEFAULT_ERROR_MESSAGE)
            return
        ret = Connection.getCurrentGame(telegramid=userName)
        if (dbFound(result=ret)):
            gameInfo = Connection.getGameInfoById(gameId=ret)
            if (dbFound(result=gameInfo)): # Game info is valid
                if (gameInfo['game_type'] == gameType):
                    return True
            else:
                log(str=f'{fName}: Cannot get gameInfo from DB: {ret}', logLevel=LOG_ERROR)
        return False