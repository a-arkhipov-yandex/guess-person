from random import shuffle
from db_lib import *
from log_lib import *

class guess_game:
    GAME2NUMBEROFOPTIONS = 3

    IMAGERANGEDIFF = 51
    CREATORRANGEDIFF = 40

    # Get range for image search
    # Returns:
    #   (startYear, endYear) - start, end years for image creation
    def getImageCreationRange(intYear):
        return (intYear - guess_game.IMAGERANGEDIFF, intYear + guess_game.IMAGERANGEDIFF)

    # Get range for creator seatch by image year
    # Returns:
    #   (startYear, endYear) - start, end years for image creation
    def getPersonByImageYearRange(intYear):
        return (intYear - 2*guess_game.CREATORRANGEDIFF, intYear + 2*guess_game.IMAGERANGEDIFF)

    # Get range for creator search
    # Returns:
    #   (None,None) - cannot detirmine
    #   (startYear, endYear) - start, end years for creator
    def getCreatorYearRange(creatorBirth, creatorDeath):
        # return nothing if neither birth nor death provided
        if (not creatorBirth and not creatorDeath):
            return (None,None)
        middleYear = 0
        if (creatorBirth and not creatorDeath):
            middleYear = creatorBirth + guess_game.CREATORRANGEDIFF
        elif (creatorDeath and not creatorBirth):
            middleYear = creatorDeath - guess_game.CREATORRANGEDIFF
        else:
            middleYear = int((creatorDeath - creatorBirth)/2)
        return (middleYear-2*guess_game.CREATORRANGEDIFF, middleYear+2*guess_game.CREATORRANGEDIFF)

    # Generate new game
    # Returns:
    #   None - if error
    #   id - new game id
    def generateNewGame(queryParams):
        fName = guess_game.generateNewGame.__name__
        ret = None
        game_type = queryParams.get('type')
        game_complexity = queryParams.get('complexity')
        if (not Connection.dbLibCheckGameType(game_type)):
            print(f'{fName}: game type is incorect ({game_type})',LOG_ERROR)
            return None
        if (not Connection.dbLibCheckGameComplexity(game_complexity)):
            print(f'{fName}: game complexity is incorect ({game_complexity})',LOG_ERROR)
            return None
        game_type = int(game_type)
        if (game_type == 1):
            ret = guess_game.generateNewGame1(queryParams=queryParams)
        elif (game_type == 2):
            ret = guess_game.generateNewGame2(queryParams=queryParams)
        elif (game_type == 3):
            ret = guess_game.generateNewGame3(queryParams=queryParams)
        else:
            print(f'{fName}: Unknown game type {game_type}',LOG_ERROR)
        return ret

    # Extract game type 1 question options
    # Returns:
    #   [id1, ...] - GAME2NUMBEROFOPTIONS image ids
    #   None - if any error
    def getQuestionType1Options(gameInfo):
        imageIds = []
        question = gameInfo['question']
        for item in question.split(' '):
            imageIds.append(int(item))
        if (len(imageIds) != guess_game.GAME2NUMBEROFOPTIONS + 1): # +1 correct answer
            return None
        return imageIds

    # Extract message ids for images
    # Returns:
    #   [id1, ...] - GAME2NUMBEROFOPTIONS message ids
    #   None - if any error
    def getMessageIds(mIdsTxt:str):
        mIds = []
        for item in mIdsTxt.split(' '):
            mIds.append(int(item))
        if (len(mIds) != guess_game.GAME2NUMBEROFOPTIONS + 1): # +1 correct answer
            return None
        return mIds

    # Extract message id and image id for photo
    # Returns:
    #   (message_id, image_id) - message id and image id
    #   None - if any error
    def getMessageIdAndMessagePhotoId(gameData):
        fName = guess_game.getMessageIdAndMessagePhotoId.__name__
        gameData = str(gameData)
        ret = None
        data = gameData.split(sep=' ')
        if (len(data) != 2):
            return ret
        messageId = data[0]
        imageId = data[1]
        try:
            imageId = int(imageId)
        except:
            log(str=f'{fName}: Image id is not int: {imageId}',logLevel=LOG_ERROR)
            None
        return (messageId, imageId)

    # Get random person and ramdom image of this person
    # Returns:
    #   (personId, imageId) - tuple with ids
    #   None - in case of any errors
    def getRandomPersonAndImageId(complexity):
        fName = guess_game.getRandomPersonAndImageId.__name__
       # Get random creator
        ret = Connection.getRandomPersonIds(complexity=complexity)
        if (ret == None):
            print(f'{fName}: Cannoe get random person: DB issue', LOG_ERROR)
            return None
        elif (dbNotFound(ret)):
            print(f'{fName}: Cannot get random person: person not found',LOG_ERROR)
            return None  
        personId = ret[0]
        # Get random image of the creator
        ret = Connection.getRandomImageIdsOfPerson(personId=personId)
        if (ret == None):
            print(f'{fName}: Cannot get random image of person {personId}: DB issue',LOG_ERROR)
            return None
        elif (dbNotFound(result=ret)):
            print(f'{fName}: Cannot get random image of person {personId}: image not found',LOG_ERROR)
            return None
        imageId = ret[0]
        return (personId, imageId)

    # Generate new game with type 1: guess image of the person
    # Returns:
    #   None - is any error
    #   gameId - id of new game
    def generateNewGame1(queryParams):
        fName = guess_game.generateNewGame1.__name__
        complexity = queryParams.get('complexity')
        if (not complexity):
            print(f'{fName}: Cannot get complexity: {queryParams}',LOG_ERROR)
            return None
        if (not complexity):
            complexity = DEFAULT_GAMECOMPLEXITY
        else:
            complexity = int(complexity)
        ret = guess_game.getRandomPersonAndImageId(complexity=complexity)
        if (not ret):
            return None # Error message is printed in getRandom function
        personId = ret[0]
        imageId = ret[1]
        # Get year range for other images
        imageInfo = Connection.getImageInfoById(imageId=imageId)
        yearRange = (None, None)
        if (dbFound(result=imageInfo)):
            yearRange = guess_game.getImageCreationRange(intYear=imageInfo['year'])
        # Get 3 random images where creator is not the same
        otherImageIds = Connection.getRandomImageIdsOfOtherPersons(
            personId=personId,
            complexity=complexity, 
            n=guess_game.GAME2NUMBEROFOPTIONS,
            range=yearRange)
        if (dbNotFound(result=otherImageIds) or len(otherImageIds) != guess_game.GAME2NUMBEROFOPTIONS):
            print(f'{fName}: Cannot get random {guess_game.GAME2NUMBEROFOPTIONS} images of creator other than {personId}',LOG_ERROR)
            return None
        telegramid = queryParams['telegramid']
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (userId == None or dbNotFound(result=userId)):
            print(f'{fName}: Cannot get user id by telegramid {telegramid}',LOG_ERROR)
            return None
        gameType = queryParams['type']
        questionIds = []
        for i in otherImageIds:
            questionIds.append(i[0]) # it is array of arrays
        questionIds.append(imageId)
        # Shuffle it
        shuffle(questionIds)
        question = " ".join(str(i) for i in questionIds)
        # Generate game with user, type(1), correct_answer (correct_image_id), question(image ids)
        ret = Connection.insertGame(
            userId=userId, game_type=gameType, correct_answer=imageId,
            question=question, complexity=complexity
        )
        if (ret == None):
            print(f'{fName}: Cannot insert game u={telegramid},gt={gameType},q={question},ca={imageId}',LOG_ERROR)
            return None
        else:
            # Set current_game
            Connection.setCurrentGame(telegramid=telegramid, gameId=ret)
        return ret

    # Generate new game with type 2 or 3 (if gameType is set): guess creator of the image
    # Returns:
    #   None - is any error
    #   gameId - id of new game
    def generateNewGame2(queryParams, gameType = 2):
        fName = guess_game.generateNewGame2.__name__
        telegramid = queryParams['telegramid']
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (userId == None or dbNotFound(result=userId)):
            print(f'{fName}: Cannot get user id by telegramid {telegramid}', LOG_ERROR)
            return None
        # Check game type
        if (gameType != 2 and gameType != 3):
            print(f'{fName}: Incorrect game type provided: {gameType}',LOG_ERROR)
            return None
        complexity = queryParams['complexity']
        if (not complexity):
            complexity = DEFAULT_GAMECOMPLEXITY
        complexity = int(complexity)
        newGameId = guess_game.getRandomPersonAndImageId(complexity=complexity)
        if (not newGameId):
            return None # Error message is printed in getRandom function
        personId = newGameId[0]
        imageId = newGameId[1]
        # Get image info
        imageInfo = Connection.getImageInfoById(imageId=imageId)
        if (dbNotFound(result=imageInfo)):
            print(f'{fName}: Cannot get random image info (image id = {imageId})',LOG_ERROR)
            return None
        gameType = queryParams['type']
        # Generate game with user, type(2-3), question(image id), correct_answer (creator_id), complexity
        newGameId = Connection.insertGame(
            userId=userId,game_type=gameType,correct_answer=personId,
            question=imageId,complexity=complexity
        )
        if (newGameId == None):
            print(f'{fName}: Cannot insert game u={telegramid},gt={gameType},q={imageId},ca={personId}',LOG_ERROR)
            return None
        else:
            # Set current_game
            Connection.setCurrentGame(telegramid=telegramid, gameId=newGameId)
        return newGameId

    # Generate new game with type 3: guess person of the image - no variants
    # Returns:
    #   None - is any error
    #   gameId - id of new game
    def generateNewGame3(queryParams):
        return guess_game.generateNewGame2(queryParams=queryParams, gameType=3)

    # Get text question
    def getTextQuestion(gameInfo) -> str:
        fName = guess_game.getTextQuestion.__name__
        gameType = int(gameInfo['game_type'])
        textQ = "Default text question"
        if gameType == 1: # Type = 1
            imageInfo = Connection.getImageInfoById(imageId=gameInfo['correct_answer'])
            if (dbFound(result=imageInfo)):
                creatorInfo = Connection.getPersonInfoById(personId=imageInfo['id'])
                writeForm = ""
                if (dbFound(result=creatorInfo)):
                    if (dbIsWoman(gender=creatorInfo['gender'])):
                        writeForm = 'а'
                textQ = f"На какой картинке изображен{writeForm} \"{imageInfo['personName']}\"?"
        elif (gameType == 2 or gameType == 3):
            imageInfo = Connection.getImageInfoById(imageId=gameInfo['question'])
            if (dbFound(result=imageInfo)):
                textQ = f"Чье это изображение?"
        else: # wrong type
            log(f'{fName}: Unkown game type provided: {gameType}',LOG_WARNING)
        return textQ

    # Finish game
    # Returns: True/False
    def finishGame(telegramid, gameId, answer) -> bool:
        ret =  Connection.finishGame(gameId=gameId, answer=answer)
        if (not ret):
            return False
        # Clear current game
        Connection.clearCurrentGame(telegramid=telegramid)
        Connection.clearCurrentGameData(telegramid=telegramid)
        return True
