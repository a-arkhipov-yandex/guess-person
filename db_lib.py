import psycopg2
from log_lib import *
from guess_common_lib import *

ENV_DBHOST = 'DBHOST'
ENV_DBPORT = 'DBPORT'
ENV_DBNAME = 'DBNAME'
ENV_DBUSER = 'DBUSER'
ENV_DBTOKEN ='DBTOKEN'
ENV_DBTESTHOST = 'DBTESTHOST'
ENV_DBTESTPORT = 'DBTESTPORT'
ENV_DBTESTNAME = 'DBTESTNAME'
ENV_DBTESTUSER = 'DBTESTUSER'
ENV_DBTESTTOKEN ='DBTESTTOKEN'

ENV_TESTDB = 'TESTDB'
ENV_TESTBOT = 'TESTBOT'

NOT_FOUND = "!!!NOT_FOUND!!!"

DEFAULT_GAMETYPE = 1
DEFAULT_GAMECOMPLEXITY = 1

DB_GENDER_MAN = 1
DB_GENDER_WOMAN = 2

#=======================
# Common functions section
#-----------------------
# Check that item not found
# Returns:
#   True - item was not found
#   False - otherwise (found or error)
def dbNotFound(result) -> bool:
    if (result != None):
        if (result == NOT_FOUND): # empty array
            return True
    return False

# Check that item is found
# Returns:
#   True - item has been found
#   False - otherwise (not found or error)
def dbFound(result) -> bool:
    if (result != None):
        if (result != NOT_FOUND): # empty array
            return True
    return False

def getDBbConnectionData():
    load_dotenv()
    data={}
    data['dbhost']=getenv(ENV_DBHOST)
    data['dbport']=getenv(ENV_DBPORT)
    data['dbname']=getenv(ENV_DBNAME)
    data['dbuser']=getenv(ENV_DBUSER)
    data['dbtoken']=getenv(ENV_DBTOKEN)
    for v in data.values():
        if (v == None): # Something wrong
            return None
    return data

def getDBbTestConnectionData():
    load_dotenv()
    data={}
    data['dbhost']=getenv(ENV_DBTESTHOST)
    data['dbport']=getenv(ENV_DBTESTPORT)
    data['dbname']=getenv(ENV_DBTESTNAME)
    data['dbuser']=getenv(ENV_DBTESTUSER)
    data['dbtoken']=getenv(ENV_DBTESTTOKEN)
    for v in data.values():
        if (v == None): # Something wrong
            return None
    return data

# Check if gender of person is woman
def dbIsWoman(gender)-> bool:
    return (gender == DB_GENDER_WOMAN)

def dbLibCheckPerson(personInfo) -> bool:
    if (not personInfo.get('id')):
        return False
    if (not personInfo.get('name')):
        return False
    return True

# Check user name (can be string with '[a-zA-Z][0-9a-zA-Z]')
def dbLibCheckTelegramid(telegramid) -> bool:
    if (telegramid == None):
        return False
    ret = False
    try:
        tInt = int(telegramid) # Check that it is valid int value
        if (tInt > 0):
            ret = True
    except:
        pass
    return ret

# Check user id (can be string or int with positive integer value)
def dbLibCheckUserId(userId) -> bool:
    ret = False
    iId = 0
    try:
        iId = int(userId)
    except:
        pass
    if (iId > 0):
        ret = True
    return ret

# Check if game is finished
# Input:
#   gameInfo - data
# Returns: True/False
def dbLibCheckIfGameFinished(gameInfo:dict) -> bool:
    result = gameInfo.get('result')
    if (result != None):
        return True
    return False

# Check gender
# Input:
#   gameInfo - data
# Returns: True/False
def dbLibCheckGender(gender) -> bool:
    ret = False
    try:
        iGender = int(gender)
        if (gender ==1 or gender == 2):
            ret = True
    except:
        log(str='Incorrect gender provided: {gender}', logLevel=LOG_ERROR)
    return ret

# Make useful map for image
def dbGetImageInfo(queryResult):
    imageInfo = {}
    if (len(queryResult) != 8):
        return imageInfo
    imageInfo['id'] = int(queryResult[0])
    imageInfo['personId'] = int(queryResult[1])
    imageInfo['personName'] = queryResult[2]
    imageInfo['image_type'] = queryResult[3]
    if (imageInfo['image_type']):
        imageInfo['image_type'] = int(imageInfo['image_type'])
    imageInfo['year'] = int(queryResult[4])
    imageInfo['year_str'] = queryResult[5]
    imageInfo['name'] = queryResult[6]
    imageInfo['gender'] = queryResult[7]
    if (imageInfo['gender']):
        imageInfo['gender'] = int(imageInfo['gender'])
    return imageInfo

# Make useful map for person
def dbGetPersonInfo(queryResult):
    person = {}
    if (len(queryResult) != 8):
        return person
    person['id'] = int(queryResult[0])
    person['name'] = queryResult[1]
    person['gender'] = queryResult[2]
    if (person['gender']):
        person['gender'] = int(person['gender'])
    person['country'] = queryResult[3]
    person['birth'] = queryResult[4]
    if (person['birth']):
        person['birth'] = int(person['birth'])
    person['death'] = queryResult[5]
    if (person['death']):
        person['death'] = int(person['death'])
    person['complexity'] = queryResult[6]
    if (person['complexity']):
        person['complexity'] = int(person['complexity'])
    person['speciality'] = queryResult[7]
    if (person['speciality']):
        person['speciality'] = int(person['speciality'])
    return person

# Make useful map for game
def dbGetGameInfo(queryResult) -> dict:
    game = {}
    if (len(queryResult) != 10):
        return game
    game['id'] = int(queryResult[0])
    game['userid'] = int(queryResult[1])
    game['game_type'] = int(queryResult[2])
    game['correct_answer'] = int(queryResult[3])
    game['question'] = queryResult[4]
    game['user_answer']  = queryResult[5]
    if (game['user_answer']):
        game['user_answer'] = int(game['user_answer'])
    game['result'] = queryResult[6]
    game['created'] = queryResult[7]
    game['finished'] = queryResult[8]
    game['complexity'] = int(queryResult[9])
    return game

#==================
# Class definition
class Connection:
    __connection = None
    __isInitialized = False
    __baseImageUrl = None
    __defaultGameType = DEFAULT_GAMETYPE
    __defaultComplexity = DEFAULT_GAMECOMPLEXITY
    __gameTypes = []
    __complexities = []
    __specialities = []
    __imageTypes = []
    BASE_URL_KEY = 'IMAGE_URL'

    # Init connection - returns True/False
    def initConnection(test=False) -> bool:
        ret = False
        if (not Connection.__isInitialized):
            Connection.__connection = Connection.__newConnection(test=test)
            if (Connection.isInitialized()):
                # Cache section
                Connection.__baseImageUrl = Connection.getSettingValue(key=Connection.BASE_URL_KEY)
                Connection.__gameTypes = Connection.getGameTypesFromDb()
                Connection.__complexities = Connection.getComplexitiesFromDb()
                Connection.__imageTypes = Connection.getImageTypesFromDb()
                Connection.__specialities = Connection.getSpecialitiesFromDb()
                log(str=f"DB Connection created (test={test})", logLevel=LOG_DEBUG)
                ret = True
            else:
                log(str=f'Cannot initialize connection to DB',logLevel=LOG_ERROR)
        else:
                log(str=f'Trying to initialize connection that already initialized',logLevel=LOG_WARNING)
        return ret
    
    def getConnection():
        if (not Connection.isInitialized()):
            return None
        return Connection.__connection
    
    def closeConnection():
        if (Connection.__isInitialized):
            Connection.__connection.close()
            Connection.__isInitialized = False
            log(str=f"DB Connection closed")

    def __newConnection(test=False):
        conn = None
        try:
            if (test):
                data = getDBbTestConnectionData()
            else: # Production
                data = getDBbConnectionData()
            if (data == None):
                log(str=f'Cannot get env data. Exiting.',logLevel=LOG_ERROR)
                return

            conn = psycopg2.connect(f"""
                host={data['dbhost']}
                port={data['dbport']}
                sslmode=verify-full
                dbname={data['dbname']}
                user={data['dbuser']}
                password={data['dbtoken']}
                target_session_attrs=read-write
            """)
            conn.autocommit = True
            Connection.__isInitialized = True
            log(str=f'DB Connetion established')
        except (Exception, psycopg2.DatabaseError) as error:
            log(str=f"Cannot connect to database: {error}",logLevel=LOG_ERROR)
            conn = None
        
        return conn

    def isInitialized() -> bool:
        return Connection.__isInitialized

    def getBaseImageUrl():
        return Connection.__baseImageUrl


    # Execute query with params
    # If 'all' == True - execute fetchAll()/ otherwise fetchOne()
    # Returns:
    #   None - issue with execution
    #   NOT_FOUND - if nothing found
    #   [result] - array with one/many found item(s)
    def executeQuery(query, params={}, all=False):
        if (not Connection.isInitialized()):
            log(str=f'Cannot execute query "{query}" with "{params}" (all={all}): connection is not initialized', logLevel=LOG_ERROR)
            return None
        ret = NOT_FOUND
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            try:
                cur.execute(query=query,vars=params)
                if (all):
                    res = cur.fetchall()
                    if (len(res) == 0):
                        ret = NOT_FOUND
                    else:
                        ret = []
                        for i in res:
                            tmp = []
                            for j in i:
                                tmp.append(j)
                            ret.append(tmp)
                else:
                    res = cur.fetchone()
                    if (res):
                        if (len(res) == 0):
                            ret = NOT_FOUND
                        else:
                            ret = []
                            for i in res:
                                ret.append(i)
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'Failed execute query "{query}" with params "{params}" (all={all}): {error}',logLevel=LOG_ERROR)
                return None
        return ret
    
    #==========================
    # Check functions
    #--------------------------
    # Check game type (can be string or int with value 1 or 2)
    def dbLibCheckGameType(game_type) -> bool:
        ret = False
        iType = 0
        try:
            iType = int(game_type)
        except:
            return ret
        gameTypes = Connection.getGameTypes()
        if (iType >= 1 and iType <= len(gameTypes)):
            ret = True
        return ret

    # Check image type (can be string or int with value 1 or 2)
    def dbLibCheckImageType(image_type) -> bool:
        ret = False
        iType = 0
        try:
            iType = int(image_type)
        except:
            return ret
        imageTypes = Connection.getImageTypes()
        if (iType >= 1 and iType <= len(imageTypes)):
            ret = True
        return ret

    # Check game type (can be string or int with value 1 or 2)
    def dbLibCheckGameComplexity(game_complexity) -> bool:
        ret = False
        iComplexity = 0
        try:
            iComplexity = int(game_complexity)
        except:
            return ret
        gameComplexities = Connection.getComplexities()
        if (iComplexity >= 1 and iComplexity <= len(gameComplexities)):
            ret = True
        return ret

    # Check game type (can be string or int with value 1 or 2)
    def dbLibCheckGameSpeciality(game_speciality) -> bool:
        fName = Connection.dbLibCheckGameSpeciality.__name__
        ret = False
        if (game_speciality == None): # Speciality can be cleared
            return True
        iSpeciality = 0
        try:
            iSpeciality = int(game_speciality)
        except:
            log(str=f'{fName}: Speciality is not int: {game_speciality}',logLevel=LOG_ERROR)
            return ret
        gameSpecialities = Connection.getSpecialities()
        if (iSpeciality >= 1 and iSpeciality <= len(gameSpecialities)):
            ret = True
        return ret

    #=======================
    # Common section
    #-----------------------

    # Get URL by image id
    # Returns:
    #   URL - if success
    #   NOT_FOUND - if image not found
    #   None - if failed connection or no such image
    def getImageUrlById(imageId):
        fName = Connection.getImageUrlById.__name__
        if (not Connection.isInitialized()):
            log(f"{fName}: Cannot get image url by id - connection is not initialized",LOG_ERROR)
            return None
        image = Connection.getImageInfoById(imageId=imageId)
        if (image == None):
            log(f'{fName}: Cannot get image URL for image {imageId}: DB issue',LOG_ERROR)
            return None
        elif (dbNotFound(result=image)):
            log(f'{fName}: Cannot get image URL for image {imageId}: no such image in DB',LOG_ERROR)
            return Connection.NOT_FOUND
        baseUrl = Connection.getBaseImageUrl()
        url = None
        if (baseUrl):
            pName = image['personName']
            iName = image['name']
            yearStr = image['year_str']
            url = buildImgUrl(base_url=baseUrl, person=pName, imageName=iName, year=yearStr)
        return url

    #==========================
    # Settings section
    #--------------------------
    # Get setting value. Returns key or None if not found or if connection is not initialized
    def getSettingValue(key):
        query = 'select value from settings where key=%(key)s'
        ret = Connection.executeQuery(query=query,params={'key': key})
        if (dbFound(result=ret)):
            ret = ret[0]
        return ret

    # Get game types from DB
    # Returns:
    #   [[game_type_id, name]]
    #   NOT_FOUND - no game_types in DB
    #   None - issue with connection
    def getGameTypesFromDb():
        query = 'select id,name from game_types order by id asc'
        ret = Connection.executeQuery(query=query,params={},all=True)
        return ret

    # Get game types from cache
    # Returns:
    #   [[game_type_id, name, question]]
    #   None - connection not initialized
    def getGameTypes():
        if (Connection.isInitialized()):
            return Connection.__gameTypes
        return None
    
    # Get image types from DB
    # Returns:
    #   [[image_type_id, image_type]]
    #   NOT_FOUND - no image_types in DB
    #   None - issue with connection
    def getImageTypesFromDb():
        query = 'select id,image_type from image_types order by id asc'
        ret = Connection.executeQuery(query=query,params={},all=True)
        return ret

    # Get image types from cache
    # Returns:
    #   [[type_id, name]]
    #   None - connection not initialized
    def getImageTypes():
        if (Connection.isInitialized()):
            return Connection.__imageTypes
        return None

    # Get person specialities from DB
    # Returns:
    #   [[speciality_id, speciality]]
    #   NOT_FOUND - no image_types in DB
    #   None - issue with connection
    def getSpecialitiesFromDb():
        query = 'select id,speciality,show from specialities order by id asc'
        ret = Connection.executeQuery(query=query,params={},all=True)
        return ret

    # Get image specialities from cache
    # Returns:
    #   [[speciality_id, speciality]]
    #   None - connection not initialized
    def getSpecialities():
        if (Connection.isInitialized()):
            return Connection.__specialities
        return None

    # Get image specialities from cache to show
    # Returns:
    #   [[speciality_id, speciality]]
    #   None - connection not initialized
    def getSpecialitiesToShow():
        ret = None
        if (Connection.isInitialized()):
            ret = []
            for spec in Connection.__specialities:
                if (spec[2]):
                    ret.append(spec)
        return ret

    # Get complexities from DB
    # Returns:
    #   [[complexity_id, name]]
    #   NOT_FOUND - no complexities in DB
    #   None - issue with connection
    def getComplexitiesFromDb():
        query = 'select id,name from game_complexities'
        ret = Connection.executeQuery(query=query,params={},all=True)
        return ret

    # Get game complexities from cache
    # Returns:
    #   [[complexity_id, name]]
    #   None - connection not initialized
    def getComplexities():
        if (Connection.isInitialized()):
            return Connection.__complexities
        return None

    # Get default game type from cache
    # Returns:
    #   game_type_id
    #   None - connection not initialized
    def getDefaultGameType():
        if (Connection.isInitialized()):
            return Connection.__defaultGameType
        return None
    
    # Get default complexity from cache
    # Returns:
    #   game_complexity
    #   None - connection not initialized
    def getDefaultComplexity():
        if (Connection.isInitialized()):
            return Connection.__defaultComplexity
        return None

    #==========================
    # User section
    #--------------------------

    # Get all settings for user
    # Returns:
    #   NOT_FOUND - no such user
    #   None - issue with DB
    #   [game_type,game_complexity]
    def getUserSetting(telegramid):
        # Get user id
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (dbFound)(result=userId):
            query = 'select game_type, game_complexity, game_speciality from users where id=%(id)s'
            ret = Connection.executeQuery(query=query,params={'id':userId})
        else:
            ret = userId
        return ret

    # Get user by name
    # Return:
    #   None - something wrong with connection/query
    #   id - user id
    #   NOT_FOUND - no such user
    def getUserIdByTelegramid(telegramid):
        ret = dbLibCheckTelegramid(telegramid=telegramid)
        if (not ret):
            return Connection.NOT_FOUND
        query = f"SELECT id FROM users WHERE telegramid = %(tid)s"
        ret = Connection.executeQuery(query=query,params={'tid':telegramid})
        if (dbFound(result=ret)):
            ret = ret[0]
        return ret

    # Delete user - returns True/False
    def deleteUser(userId) -> bool:
        ret = False
        if (not Connection.isInitialized()):
            log(str="Cannot delete user - connection is not initialized",logLevel=LOG_ERROR)
            return ret
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from users where id = %(user)s"
            try:
                cur.execute(query=query, vars={'user':userId})
                log(str=f'Deleted user: {userId}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'Failed delete user {userId}: {error}',logLevel=LOG_ERROR)
        return ret
    
    # Insert new user in DB. 
    #   Returns:
    #      user id - if success
    #      None - if any error
    def insertUser(telegramid, gameType=None, complexity=None):
        fName = Connection.insertUser.__name__
        if (not Connection.isInitialized()):
            log(str=f"{fName}: Cannot insert user - connection is not initialized",logLevel=LOG_ERROR)
            return None
        ret = dbLibCheckTelegramid(telegramid=telegramid)
        if (not ret):
            log(str=f"{fName}: Cannot insert user -  invalid telegramid format: {telegramid}",logLevel=LOG_ERROR)
            return None
        if ((complexity == None) or (not Connection.dbLibCheckGameComplexity(game_complexity=complexity))):
            complexity = Connection.getDefaultComplexity()

        if ((gameType == None) or (not Connection.dbLibCheckGameType(game_type=gameType))):
            gameType = Connection.getDefaultGameType()

        ret = None
        conn = Connection.getConnection()
        # Check for duplicates
        retUser = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (retUser == None): # error with DB
            log(str=f'{fName}: Cannot get user from DB: {telegramid}',logLevel=LOG_ERROR)
            return None
        if (dbNotFound(result=retUser)):
            with conn.cursor() as cur:
                query = "INSERT INTO users ( telegramid,game_type,game_complexity ) VALUES ( %(u)s,%(t)s,%(c)s ) returning id"
                try:
                    cur.execute(query=query, vars={'u':telegramid,'t':gameType,'c':complexity})
                    row = cur.fetchone()
                    if (row):
                        ret = row[0]
                        log(str=f'{fName}: Inserted user: {telegramid} - {gameType} - {complexity}')
                    else:
                        log(str=f'{fName}: Cannot get id of new user: {query}',logLevel=LOG_ERROR)
                except (Exception, psycopg2.DatabaseError) as error:
                    log(str=f'{fName}: Failed insert user {telegramid}: {error}',logLevel=LOG_ERROR)
        else:
            log(str=f'{fName}: Trying to insert duplicate user: {telegramid}',logLevel=LOG_WARNING)
            ret = None
        return ret

    # Get current game data for user userName
    # Returns:
    # id - current game id
    # None - no current game
    def getCurrentGameData(telegramid):
        fName = Connection.getCurrentGameData.__name__
        ret = dbLibCheckTelegramid(telegramid=telegramid)
        if (not ret):
            log(str=f'{fName}: Incorrect user {telegramid} provided',logLevel=LOG_ERROR)
            return None
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {telegramid}',logLevel=LOG_ERROR)
            return None
        ret = None
        query = 'select game_data from users where id=%(uId)s'
        currentGameData = Connection.executeQuery(query=query, params={'uId':userId})
        if (dbFound(result=currentGameData)):
            currentGameData = currentGameData[0]
            if (currentGameData):
                ret = currentGameData
        return ret
    
    # Get user game type
    # Returns:
    #   game_type - game type
    #   None - if error
    def getUserGameType(telegramid):
        fName = Connection.getUserGameType.__name__
        ret = None
        if (not Connection.isInitialized()):
            log(str=f"{fName}: connection is not initialized",logLevel=LOG_ERROR)
            return ret
        ret2 = dbLibCheckTelegramid(telegramid=telegramid)
        if (not ret2):
            log(str=f'{fName}: Incorrect user {telegramid} provided',logLevel=LOG_ERROR)
            return ret
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {telegramid}',logLevel=LOG_ERROR)
            return ret
        query = f'select game_type from users where id=%(uId)s'
        ret2 = Connection.executeQuery(query=query,params={'uId':userId})
        if (dbFound(result=ret2)):
            ret = ret2[0]
        return ret

    # Update game type for the userId
    # Returns: True - update successful / False - otherwise
    def updateUserGameType(telegramid, gameType) -> bool:
        fName = Connection.updateUserGameType.__name__
        if (not Connection.isInitialized()):
            log(str=f"{fName}: connection is not initialized",logLevel=LOG_ERROR)
            return False
        ret = dbLibCheckTelegramid(telegramid=telegramid)
        if (not ret):
            log(str=f'{fName}: Incorrect user {telegramid} provided',logLevel=LOG_ERROR)
            return False
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {telegramid}',logLevel=LOG_ERROR)
            return False
        if (not Connection.dbLibCheckGameType(game_type=gameType)):
            log(str=f'{fName}: Wrong game type format: {gameType}',logLevel=LOG_ERROR)
            return False

        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set game_type=%(gt)s where id = %(uId)s'
            try:
                cur.execute(query=query,vars={'gt':gameType,'uId':userId})
                log(str=f'Updated game type: (user={telegramid} | gameType = {gameType})')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'Failed update game type (gameType = {gameType}, user={telegramid}): {error}',logLevel=LOG_ERROR)
        return ret

    # Get user complexity
    # Returns:
    #   complexity - complexity
    #   None - if error
    def getUserComplexity(telegramid):
        fName = Connection.getUserComplexity.__name__
        ret = None
        if (not Connection.isInitialized()):
            log(str=f"{fName}: connection is not initialized",logLevel=LOG_ERROR)
            return ret
        ret2 = dbLibCheckTelegramid(telegramid=telegramid)
        if (not ret2):
            log(str=f'{fName}: Incorrect user {telegramid} provided',logLevel=LOG_ERROR)
            return ret
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {telegramid}',logLevel=LOG_ERROR)
            return ret
        query = 'select game_complexity from users where id=%(uId)s'
        ret2 = Connection.executeQuery(query=query,params={'uId':userId})
        if (dbFound(result=ret2)):
            ret = ret2[0]
        return ret

    # Update users complexity for the userId
    # Returns: True - update successful / False - otherwise
    def updateUserComplexity(telegramid, complexity) -> bool:
        fName = Connection.updateUserComplexity.__name__
        if (not Connection.isInitialized()):
            log(str=f"{fName}: connection is not initialized",logLevel=LOG_ERROR)
            return False
        ret = dbLibCheckTelegramid(telegramid=telegramid)
        if (not ret):
            log(str=f'{fName}: Incorrect user {telegramid} provided',logLevel=LOG_ERROR)
            return False
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {telegramid}',logLevel=LOG_ERROR)
            return False
        if (not Connection.dbLibCheckGameComplexity(game_complexity=complexity)):
            log(str=f'{fName}: Wrong complexity format: {complexity}',logLevel=LOG_ERROR)
            return False

        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set game_complexity=%(c)s where id = %(uId)s'
            try:
                cur.execute(query=query,vars={'c':complexity,'uId':userId})
                log(str=f'Updated complexity: (user={telegramid} | complexity = {complexity})')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed update complexity (complexity = {complexity}, user={telegramid}): {error}',logLevel=LOG_ERROR)
        return ret

    # Get user speciality
    # Returns:
    #   speciality - speciality
    #   None - if error
    def getUserSpeciality(telegramid):
        fName = Connection.getUserSpeciality.__name__
        ret = None
        if (not Connection.isInitialized()):
            log(str=f"{fName}: connection is not initialized",logLevel=LOG_ERROR)
            return ret
        ret2 = dbLibCheckTelegramid(telegramid=telegramid)
        if (not ret2):
            log(str=f'{fName}: Incorrect user {telegramid} provided',logLevel=LOG_ERROR)
            return ret
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {telegramid}',logLevel=LOG_ERROR)
            return ret
        query = 'select game_speciality from users where id=%(uId)s'
        ret2 = Connection.executeQuery(query=query,params={'uId':userId})
        if (dbFound(result=ret2)):
            ret = ret2[0]
        return ret

    # Update users speciality for the userId
    # Returns: True - update successful / False - otherwise
    def updateUserSpeciality(telegramid, speciality) -> bool:
        fName = Connection.updateUserSpeciality.__name__
        if (not Connection.isInitialized()):
            log(str=f"{fName}: connection is not initialized",logLevel=LOG_ERROR)
            return False
        ret = dbLibCheckTelegramid(telegramid=telegramid)
        if (not ret):
            log(str=f'{fName}: Incorrect user {telegramid} provided',logLevel=LOG_ERROR)
            return False
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {telegramid}',logLevel=LOG_ERROR)
            return False
        if (not Connection.dbLibCheckGameSpeciality(game_speciality=speciality)):
            log(str=f'{fName}: Wrong speciality format: {speciality}',logLevel=LOG_ERROR)
            return False

        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set game_speciality=%(s)s where id = %(uId)s'
            try:
                cur.execute(query=query,vars={'s':speciality,'uId':userId})
                log(str=f'Updated speciality: (user={telegramid} | speciality = {speciality})')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed update speciality (speciality = {speciality}, user={telegramid}): {error}',logLevel=LOG_ERROR)
        return ret

    # Clear user speciality for the userId
    # Returns: True - update successful / False - otherwise
    def clearUserSpeciality(telegramid) -> bool:
        return Connection.updateUserSpeciality(telegramid=telegramid, speciality=None)

    # Get current game for user userName
    # Returns:
    # id - current game id
    # None - no current game
    def getCurrentGame(telegramid):
        fName = Connection.getCurrentGame.__name__
        ret = dbLibCheckTelegramid(telegramid=telegramid)
        if (not ret):
            log(str=f'{fName}: Incorrect user {telegramid} provided',logLevel=LOG_ERROR)
            return None
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {telegramid}',logLevel=LOG_ERROR)
            return None
        ret = None
        query = 'select current_game from users where id=%(uId)s'
        currentGame = Connection.executeQuery(query=query, params={'uId':userId})
        if (dbFound(result=currentGame)):
            currentGame = currentGame[0]
            if (currentGame):
                # Check that game is not finished
                ret2 = Connection.checkGameIsFinished(gameId=currentGame)
                if (not ret2): # UnFinished game
                    ret = currentGame
                else:
                    log(str=f'{fName}: Current game {currentGame} is finished for user {userId} - clear current game')
                    Connection.clearCurrentGame(telegramid=telegramid)
        return ret
    
    def setCurrentGameData(telegramid, gameData) -> bool:
        return Connection.updateCurrentGameData(telegramid=telegramid, gameData=gameData)

    def clearCurrentGameData(telegramid) -> bool:
        return Connection.updateCurrentGameData(telegramid=telegramid, gameData=None)

    # Update game_data for the userId
    # Returns: True - update successful / False - otherwise
    def updateCurrentGameData(telegramid, gameData) -> bool:
        fName = Connection.updateCurrentGameData.__name__
        if (not Connection.isInitialized()):
            log(str=f"{fName}: connection is not initialized",logLevel=LOG_ERROR)
            return False
        ret = dbLibCheckTelegramid(telegramid=telegramid)
        if (not ret):
            log(str=f'{fName}: Incorrect user {telegramid} provided',logLevel=LOG_ERROR)
            return False
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {telegramid}',logLevel=LOG_ERROR)
            return False
        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set game_data=%(gd)s where id = %(uId)s'
            try:
                cur.execute(query=query,vars={'gd':gameData,'uId':userId})
                log(str=f'Updated current game data: (user={telegramid} | gameData = {gameData})')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed update current game data (gameData = {gameData}, user={telegramid}): {error}',logLevel=LOG_ERROR)
        return ret

    def setCurrentGame(telegramid, gameId) -> bool:
        return Connection.updateCurrentGame(telegramid=telegramid, gameId=gameId)

    def clearCurrentGame(telegramid) -> bool:
        return Connection.updateCurrentGame(telegramid=telegramid, gameId=None)

    # Update current_game for the userId
    # Returns: True - update successful / False - otherwise
    def updateCurrentGame(telegramid, gameId) -> bool:
        fName = Connection.updateCurrentGame.__name__
        if (not Connection.isInitialized()):
            log(str=f"{fName}: connection is not initialized",logLevel=LOG_ERROR)
            return False
        ret = dbLibCheckTelegramid(telegramid=telegramid)
        if (not ret):
            log(str=f'{fName}: Incorrect user {telegramid} provided',logLevel=LOG_ERROR)
            return False
        userId = Connection.getUserIdByTelegramid(telegramid=telegramid)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {telegramid}',logLevel=LOG_ERROR)
            return False
        if (gameId):
            gameInfo = Connection.getGameInfoById(gameId=gameId)
            if (gameInfo == None or dbNotFound(result=gameInfo)):
                log(str=f'{fName}: cannot find game {gameId} (user={telegramid})',logLevel=LOG_ERROR)
                return False
            # Check userId is correct
            if (gameInfo['userid'] != userId):
                log(str=f'{fName}: game {gameId} doesnt belong to user {telegramid} ({userId})',logLevel=LOG_ERROR)
                return False
            # Check that game is finished
            ret = dbLibCheckIfGameFinished(gameInfo=gameInfo)
            if (ret):
                log(str=f'{fName}: cannot set finished game as current (gameId = {gameId}, user={telegramid})',logLevel=LOG_ERROR)
                return False
        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set current_game=%(gId)s where id = %(uId)s'
            try:
                cur.execute(query=query,vars={'gId':gameId,'uId':userId})
                log(str=f'Updated current game: (user={telegramid} | gameId = {gameId})')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed update current game (gameId = {gameId}, user={telegramid}): {error}',logLevel=LOG_ERROR)
        return ret

    #====================
    # Image section
    #--------------------
    # Delete image - returns True/False
    def deleteImage(imageId) -> bool:
        ret = False
        if (not Connection.isInitialized()):
            log(str="Cannot delete image - connection is not initialized",logLevel=LOG_ERROR)
            return ret
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from images where id = %(id)s"
            try:
                cur.execute(query=query, vars={'id':imageId})
                log(str=f'Deleted image: {imageId}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'Failed delete image {imageId}: {error}',logLevel=LOG_ERROR)
        return ret
    
    # Insert image in DB
    # Returns:
    #   id - id of newly created image
    #   None - if error
    def insertImage(personId, imageName, year, intYear, imageType=None):
        fName = Connection.insertImage.__name__
        if (not Connection.isInitialized()):
            log(str=f"{fName}: Cannot insert image - connection is not initialized",logLevel=LOG_ERROR)
            return None
        # Check input
        try:
            int(intYear)
        except:
            log(str=f"{fName}: Cannot insert image - intYear is not integer: person={personId}, name={imageName}, intYear={intYear}",logLevel=LOG_ERROR)
            return None
        # Check image type
        if (imageType != None and not Connection.dbLibCheckImageType(image_type=imageType)):
            log(str=f"{fName}: Wrong image type provided: {imageType}: person={personId}, name={imageName}, intYear={intYear}",logLevel=LOG_ERROR)
            return None
        # Check that person exist
        if (not Connection.checkPersonExists(personId=personId)):
            log(str=f"{fName}: Cannot insert image - person doesnt exist {personId}, name={imageName}, intYear={intYear}",logLevel=LOG_ERROR)
            return None
        # Check for duplicates
        imageIdDup = Connection.getImageIdByPersonId(personId=personId, imageName=imageName, intYear=intYear)
        if (imageIdDup == None):
            log(str=f'Cannot insert image {personId} - {imageName} - {year}: DB issue',logLevel=LOG_ERROR)
            return None
        ret = None
        if (dbNotFound(result=imageIdDup)):
            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = f'''
                            INSERT INTO images (person, name, year_str, year, image_type) 
                            VALUES (%(pId)s,%(im)s,%(yStr)s,%(iY)s,%(iT)s) returning id
                        '''
                try:
                    cur.execute(query=query, vars={'pId':personId, 'im':imageName,'yStr':year,'iY':intYear,'iT':imageType})
                    row = cur.fetchone()
                    if (row):
                        ret = row[0]
                        log(str=f'Inserted image: {personId} - {imageName} - {year}')
                    else:
                        log(str=f'Cannot get id of new image: {query}',logLevel=LOG_ERROR)
                except (Exception, psycopg2.DatabaseError) as error:
                    log(str=f'Failed insert image {personId} - {imageName} - {year}: {error}',logLevel=LOG_ERROR)
        else:
            log(str=f'Trying to insert duplicate image: {personId} - {imageName} - {year}',logLevel=LOG_WARNING)
            ret = None
        return ret
    
    # Get image id with personId.
    # Returns:
    #    None if connection is not initialized or error during query
    #    [id] - with image id
    #    NOT_FOUND - if not found
    def getImageIdByPersonId(personId, imageName, intYear):
        query = "SELECT id FROM images WHERE person =%(cId)s AND name =%(image)s AND year = %(year)s"
        ret = Connection.executeQuery(query,{'cId':personId,'image':imageName,'year':intYear})
        if (dbFound(result=ret)):
            ret = ret[0]
        return ret

    # Get image info from DB by id
    # Returns:
    #   [{personId, personName, imageName, year, year_str, orientation}]
    #   NOT_FOUND - if no such image
    #   None - if issue with connection
    def getImageInfoById(imageId):
        query = f'''
                    select i.id,i.person,p.name,i.image_type,i.year,i.year_str,i.name,p.gender
                    from images as i 
                    join persons as p on i.person = p.id where i.id = %(id)s
                '''
        ret = Connection.executeQuery(query=query,params={'id':imageId})
        if (dbFound(result=ret)):
            imageInfo = dbGetImageInfo(queryResult=ret)
            ret = imageInfo
        return ret

    # Get all images from DB
    # Returns:
    #   ['imageInfo1',...] - array of image info
    #   None - in case of error
    def getAllImages(personName=False):
        fName = Connection.getAllImages.__name__
        if (not Connection.isInitialized()):
            log(str=f"{fName}: Cannot get all images - connection is not initialized",logLevel=LOG_ERROR)
            return None
        images = []
        query = f"""select i.id, i.person, i.year, i.name
                    from images as i
                """
        if (personName):
            query = f"""select i.id, i.person, i.year, i.name, p.name
                        from images as i join persons as p on i.person=p.id
                    """
        ret = Connection.executeQuery(query=query,params={},all=True)
        if (dbFound(result=ret)):
            for i in ret:
                # Fill out persons info
                image = {}
                image['id'] = i[0]
                image['personId'] = i[1]
                image['year'] = i[2]
                image['name'] = i[3]
                if (personName):
                    image['personName'] = i[4]
                images.append(image)
        else:
            return None
        return images

    # Get all images of the person
    # Returns:
    #   ['imageInfo1',...] - array of image info
    #   None - in case of error
    def getAllImagesOfPerson(personId):
        fName = Connection.getAllImagesOfPerson.__name__
        if (not Connection.isInitialized()):
            log(str=f"{fName}: Cannot get all images of person {personId} - connection is not initialized",logLevel=LOG_ERROR)
            return None
        images = []
        query = f"""select i.id, i.person, p.name, i.image_type, i.year, i.year_str, i.name,p.gender
                    from images as i join persons as p on i.person = p.id where p.id = %(id)s
                """
        ret = Connection.executeQuery(query=query,params={'id':personId},all=True)
        if (dbFound(result=ret)):
            for i in ret:
                # Fill out persons info
                image = dbGetImageInfo(queryResult=i)
                images.append(image)
        else:
            return None
        return images

    #=======================
    # Game serction
    #-----------------------
    # Delete game - returns true/false
    def deleteGame(gameId) -> bool:
        ret = False
        if (not Connection.isInitialized()):
            log(str="Cannot delete game - connection is not initialized",logLevel=LOG_ERROR)
            return ret
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from games where id = %(id)s"
            try:
                cur.execute(query=query, vars={'id':gameId})
                log(str=f'Deleted game: {gameId}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'Failed delete game {gameId}: {error}',logLevel=LOG_ERROR)
        return ret
    
    # Insert new user in DB
    # Returns:
    #   id - id of new game
    #   None - otherwise
    def insertGame(userId, game_type, correct_answer, question, complexity):
        # Checks first
        if (not dbLibCheckUserId(userId=userId)):
            return None
        if (not Connection.dbLibCheckGameType(game_type=game_type)):
            return None
        if (not Connection.dbLibCheckGameComplexity(game_complexity=complexity)):
            return None
        if (not Connection.isInitialized()):
            log(str=f"Cannot insert game for user {userId}- connection is not initialized",logLevel=LOG_ERROR)
            return None
        ret = None
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'INSERT INTO games (userid,game_type,correct_answer,question,created,complexity) VALUES ( %(u)s, %(t)s, %(ca)s, %(q)s, NOW(), %(com)s) returning id'
            try:
                cur.execute(query=query, vars={'u':userId,'t':game_type,'ca':correct_answer,'q':question,'com':complexity})
                row = cur.fetchone()
                if (row):
                    ret = row[0]
                    log(str=f'Inserted game: {ret}')
                else:
                    log(str=f'Cannot get id of new game: {query}',logLevel=LOG_ERROR)
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'Failed insert game for user {userId}: {error}',logLevel=LOG_ERROR)
        return ret

    # Get game by id
    # Returns:
    #   None - issue with DB
    #   NOT_FOUND - no such game
    #   {gameInfo} - game info
    def getGameInfoById(gameId):
        query = 'select id,userid,game_type,correct_answer,question,user_answer,result,created,finished,complexity from games where id = %(id)s'
        ret = Connection.executeQuery(query=query,params={'id':gameId})
        if (dbFound(result=ret)):
            gameInfo = dbGetGameInfo(queryResult=ret)
            ret = gameInfo
        return ret

    # Finish game
    # Input:
    #   gameId - game id
    #   answer - user_answer
    # Result:
    #   False - issue with DB
    #   True - successful finish
    def finishGame(gameId, answer) -> bool:
        fName = Connection.finishGame.__name__
        if (not Connection.isInitialized()):
            log(str=f"{fName}: Cannot finish game - connection is not initialized",logLevel=LOG_ERROR)
            return False
        gameInfo = Connection.getGameInfoById(gameId=gameId)
        if (gameInfo == None):
            log(str=f'{fName}: cannot get game {gameId}: DB issue',logLevel=LOG_ERROR)
            return False
        ret = False
        if (dbFound(result=gameInfo)):
            # Check that game is not finished yet
            isFinished = dbLibCheckIfGameFinished(gameInfo=gameInfo)
            if (isFinished):
                log(str=f'{fName}: Game {gameId} is already finished',logLevel=LOG_WARNING)
                return False
            # Check result by answer
            correct_answer = gameInfo['correct_answer']
            answer = int(answer)
            dbResult = 'false'
            if (answer == correct_answer):
                dbResult = 'true'
            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = 'update games set finished = NOW(), result=%(r)s, user_answer=%(a)s where id = %(id)s'
                try:
                    cur.execute(query=query,vars={'r':dbResult,'id':gameId, 'a':answer})
                    log(str=f'{fName}: Finished game: {gameId} - {dbResult}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    log(str=f'{fName}: Failed finish game {gameId}: {error}',logLevel=LOG_ERROR)
        else:
            log(str=f"{fName}: Cannot find game {gameId}: game not found",logLevel=LOG_ERROR)
        return ret
    
    # Check is game is finished. Returns True/False
    def checkGameIsFinished(gameId) -> bool:
        gameInfo = Connection.getGameInfoById(gameId=gameId)
        if (dbFound(result=gameInfo)):
            return (dbLibCheckIfGameFinished(gameInfo=gameInfo))
        return False

    # Returns 'n' personIDs or None if connection not initialized or issue with DB
    def getRandomPersonIds(complexity, n = 1, speciality = None):
        params = {'c':complexity, 'n':n}
        query2 = ''
        if (speciality):
            query2 = ' and speciality=%(s)s'
            params['s'] = speciality
            pass
        query = f'''
                SELECT id FROM persons
                WHERE (complexity<=%(c)s or complexity is null)
                {query2}
                ORDER BY RANDOM() LIMIT %(n)s
        '''
        ret = Connection.executeQuery(query=query,params=params,all=True)
        if (dbFound(result=ret)):
            if (n == 1):
                ret = ret[0]
            else:
                ids = []
                for i in ret:
                    ids.append(i)
                ret = ids
        return ret

    # Returns 'n' imageIds or None if connection not initialized or issue with DB
    def getRandomImageIdsOfPerson(personId, n = 1):
        query = "SELECT id FROM images where person=%(p)s ORDER BY RANDOM() LIMIT %(n)s"
        ret = Connection.executeQuery(query=query,params={'p':personId, 'n':n},all=True)
        if (dbFound(result=ret)):
            if (n == 1):
                ret = ret[0]
            else:
                ids = []
                for i in ret:
                    ids.append(i)
                ret = ids
        return ret

    # Returns 'n' imageIds or None if connection not initialized or issue with DB
    def getRandomImageIdsOfOtherPersons(personId, complexity, n, range = (None, None), speciality=None):
        fName = Connection.getRandomImageIdsOfOtherPersons.__name__
        if ((len(range) != 2)):
            log(str=f'{fName}: Wrong range format provided: {range}',logLevel=LOG_ERROR)
            range = (None, None)
        # Get person gender
        personInfo = Connection.getPersonInfoById(personId=personId)
        if (personInfo == None or dbNotFound(result=personInfo)):
            log(str=f'{fName}: Cannot get person info: {personId}',logLevel=LOG_ERROR)
            return None
        params = {'p':personId, 'com':complexity, 'n':n}
        query2 = ''
        if ((range[0] != None) and (range[1] != None)):
            query2 = query2 + ' and (i.year > %(start)s and i.year < %(end)s)'
            params['start'] = range[0]
            params['end'] = range[1]
            pass
        gender = personInfo['gender']
        if (gender):
            query2 = query2 + ' and p.gender = %(gen)s'
            params['gen'] = gender
        if (speciality):
            query2 = query2 + ' and p.speciality = %(spec)s'
            params['spec'] = speciality
        query = f'''
            SELECT i.id FROM images as i join persons as p on i.person=p.id
            where i.person!=%(p)s and (p.complexity<=%(com)s or p.complexity is null)
            {query2}
            ORDER BY RANDOM()
            LIMIT %(n)s;
        '''
        ret = Connection.executeQuery(query=query,params=params,all=True)
        if (dbFound(result=ret)):
            if (n == 1):
                ret = ret[0]
            else:
                ids = []
                for i in ret:
                    ids.append(i)
                ret = ids
        return ret

    # Gets 'n' images of person (or any person if None) for complexity
    # Returns:
    #   [id1, id2,...] - 'n' imageIds
    #   None if connection not initialized or issue with DB
    def getRandomImageIdsOfAnyPerson(complexity, personId=None, n = 1):
        params = {'c':complexity, 'n':n}
        query_start = '''
                SELECT i.id FROM images as i join persons as p on i.person = p.id
                where (p.complexity<=%(c)s or p.complexity is null)
        '''
        query_middle =''
        if (personId):
            query_middle = ' and p.id=%(pId)s'
            params['pId'] = personId
        query_end = " ORDER BY RANDOM() LIMIT %(n)s"
        query = query_start + query_middle + query_end
        ret = Connection.executeQuery(query=query, params=params,all=True)  
        if (dbFound(result=ret)):
            if (n == 1):
                ret = ret[0]
            else:
                ids = []
                for i in ret:
                    ids.append(i)
                ret = ids
        return ret
    
    #=====================
    # Person section
    #---------------------

    # Get person ID by name
    # Returns:
    #    personID by name
    #    None if not found or connection not initialized
    #    NOT_FOUND - not found person
    def getPersonIdByName(person):
        fName = Connection.getPersonIdByName.__name__
        if (not Connection.isInitialized()):
            log(str=f"{fName}: Cannot get person id - connection is not initialized",logLevel=LOG_ERROR)
            return None
        query = "SELECT id FROM persons WHERE name =%(p)s"
        ret = Connection.executeQuery(query=query,params={'p':person})
        if (dbFound(result=ret)):
            ret = ret[0]
        return ret

    # Insert new person
    # Returns:
    #   None - if error
    #   personId - id of new person
    def insertPerson(personName:str):
        fName = Connection.insertPerson.__name__
        if (not Connection.isInitialized()):
            log(str=f"{fName}: Cannot insert person - connection is not initialized",logLevel=LOG_ERROR)
            return None
        ret = None
        # Check for duplicates
        retPerson = Connection.getPersonIdByName(person=personName)
        if (retPerson == None): # error with DB
            log(str=f'{fName}: Cannot get person from DB: {personName}',logLevel=LOG_ERROR)
            return None
        if (dbNotFound(result=retPerson)):
            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = "INSERT INTO persons ( name ) VALUES ( %(cr)s ) returning id"
                try:
                    cur.execute(query=query, vars={'cr':personName})
                    row = cur.fetchone()
                    if (row):
                        ret = row[0]
                        log(str=f'{fName}: Inserted person: {personName}')
                    else:
                        log(str=f'{fName}: Cannot get id of new person: {query}',logLevel=LOG_ERROR)
                except (Exception, psycopg2.DatabaseError) as error:
                    log(str=f'Failed insert person {personName}: {error}',logLevel=LOG_ERROR)
        else:
            log(str=f'Trying to insert duplicate person: {personName}',logLevel=LOG_WARNING)
        return ret

    # Returns:
    #    personInfo by id {'id':N,...}
    #    None DB issue or connection not initialized
    #    NOT_FOUND - not found person
    def getPersonInfoById(personId):
        fName = Connection.getPersonInfoById.__name__
        if (not personId):
            log(str=f'{fName}: personID is not passed',logLevel=LOG_ERROR)
            return Connection.NOT_FOUND
        query = "SELECT id,name,gender,country,birth,death,complexity,speciality FROM persons WHERE id =%(id)s"
        ret = Connection.executeQuery(query=query,params={'id':personId})
        if (dbFound(result=ret)):
            personInfo = dbGetPersonInfo(queryResult=ret)
            ret = personInfo
        return ret

    # Get max number of person images (1 if no number images)
    def getLastPersonImageNumber(personId) -> int:
        maxNum = 0
        # Get all person images
        images = Connection.getAllImagesOfPerson(personId=personId)
        if (dbFound(result=images)):
            intImages = []
            for imageInfo in images:
                imageName = imageInfo['name']
                try:
                    intName = int(imageName)
                    intImages.append(intName)
                except:
                    pass # Do nothing here
            # Return max number
            if (intImages):
                maxNum = max(intImages)
        return maxNum

    # Check if person exists in DB
    # Returns:
    #    None if connection is not initialized or error during query
    #    True if exists
    #    False if not exists
    def checkPersonExists(personId) -> bool:
        query = "SELECT id FROM persons WHERE id =%(pId)s"
        ret = Connection.executeQuery(query=query,params={'pId':personId})
        if (dbFound(result=ret)):
            ret = True
        else:
            ret = False
        return ret

    # Get N persons
    # Input:
    #   n - number of persons to returl
    #   exclude - person id to exclude
    #   complexity - game complexity
    # Returns:
    #   None - issue with DB
    #   [{'personId':id,'personName':name}] - persons Info
    def getNPersons(n, exclude, complexity, range=(None,None),gender=None):
        fName = Connection.getNPersons.__name__
        if ((len(range) != 2)):
            log(str=f'{fName}: Wrong range format provided for person: {range}',logLevel=LOG_WARNING)
            range = (None, None)
        params = {'e':exclude, 'c':complexity,'n':n}
        query2 = ''
        if (gender != None and dbLibCheckGender(gender=gender)):
            query2 = query2 + ' and gender = %(gen)s'
            params['gen'] = gender
        if ((range[0] != None) and (range[1] != None)):
            query2 = query2 + ' and ((birth is %(start1)s or birth > %(start2)s) and (death is %(end1)s or death < %(end2)s))'
            params['start1'] = None
            params['start2'] = range[0]
            params['end1'] = None
            params['end2'] = range[1]
        query = f'''
            SELECT id,name FROM persons
            where id != %(e)s and (complexity <= %(c)s or complexity is null)
            {query2}
            ORDER BY RANDOM()
            LIMIT %(n)s;
        '''
        ret = Connection.executeQuery(query=query,params=params,all=True)
        if (dbFound(result=ret)):
            retArr = []
            for person in ret:
                pInfo = {}
                pInfo['personId'] = person[0]
                pInfo['personName'] = person[1]
                retArr.append(pInfo)
            ret = retArr
        return ret

    # Get speciality id by text
    def getSpecialityIdByText(specialityTxt):
        specialities = Connection.getSpecialities()
        for speciality in specialities:
            if (speciality[1] == specialityTxt):
                return speciality[0]
        return None

    # Update persons info from CSV file
    def updatePersonsFromCSV() -> None:
        fName = Connection.updatePersonsFromCSV.__name__
        persons = readPersonsCSV()
        if (not persons):
            log(str=f'{fName}: No persons for update',logLevel=LOG_ERROR)
            return
        for person in persons:
            if (not dbLibCheckPerson(personInfo=person)):
                log(str=f'{fName}: Invalid person: {person}',logLevel=LOG_ERROR)
                continue
            # Get person's info from DB
            dbPerson = Connection.getPersonInfoById(personId=person.get('id'))
            if dbFound(result=dbPerson):
                # Check if there is new info in CSV
                if (not Connection.comparePersonsInfo(person=person, dbPerson=dbPerson)):
                    # Update person in DB
                    Connection.updatePerson(personInfo=person)
                else:
                    # Do nothing they are equal
                    pass
            else:
                log(str=f'{fName}: Cannot find person "{person}" in DB',logLevel=LOG_ERROR)

    # Compare 2 persons info
    # Returns: True if everything is equal / False - if any differences
    def comparePersonsInfo(person, dbPerson) -> bool:
        ret = True
        for k in dbPerson.keys():
            newV = person.get(k)
            if (not newV):
                newV = None
            if (dbPerson[k] != newV):
                log(str=f'person={person}, dbPerson={dbPerson}',logLevel=LOG_DEBUG)
                ret = False
                break
        return ret

    # Update person - returns True/False
    def updatePerson(personInfo) -> bool:
        fName = Connection.updatePerson.__name__
        ret = False
        if (not dbLibCheckPerson(personInfo=personInfo)):
            log(str=f'{fName}: Person check failed for "{personInfo}"',logLevel=LOG_ERROR)
            return False
        pId = personInfo['id']
        name = personInfo['name']
        cmpsty = None
        if (personInfo['complexity']):
            if (Connection.dbLibCheckGameComplexity(game_complexity=personInfo['complexity'])):
                cmpsty = personInfo['complexity']
            else:
                log(str=f'{fName}: Complexity check failed: {personInfo["complexity"]}',logLevel=LOG_WARNING)
        gender = None
        if (personInfo['gender']):
            if (dbLibCheckGender(gender=personInfo['gender'])):
                gender = personInfo['gender']
            else:
                log(str=f'{fName}: Gender check failed: {personInfo["gender"]}',logLevel=LOG_WARNING)
        birth = None
        if (personInfo['birth']):
            birth = int(personInfo['birth'])
        if (not personInfo['death']):
            personInfo['death'] = None
        death = personInfo['death']
        if (not personInfo['country']):
            personInfo['country'] = None
        country = personInfo['country']
        if (not personInfo['speciality']):
            personInfo['speciality'] = None
        spec = personInfo['speciality']
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = '''
                        update persons set
                        name=%(n)s,gender=%(g)s,birth=%(b)s,death=%(d)s,
                        country=%(c)s,complexity=%(com)s,speciality=%(spec)s
                        where id = %(id)s
                    '''
            params = {'id':pId,'g':gender,'b':birth,'d':death,'n':name,'c':country,'com':cmpsty,'spec':spec}
            try:
                cur.execute(query=query,vars=params)
                log(str=f'{fName}: Updated person: {personInfo}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed update person {personInfo}: {error}',logLevel=LOG_ERROR)
        return ret

    #=======================
    # Game section
    #-----------------------
    # Delete person - returns true/false
    def deletePerson(personId) -> bool:
        ret = False
        if (not Connection.isInitialized()):
            log(str="Cannot delete person - connection is not initialized",logLevel=LOG_ERROR)
            return ret
        # Check existance
        if (not Connection.checkPersonExists(personId=personId)):
            log(str=f"Cannot delete person - doesnt exist: {personId}",logLevel=LOG_WARNING)
            return ret
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from persons where id = %(id)s"
            try:
                cur.execute(query=query, vars={'id':personId})
                log(str=f'Deleted person: {personId}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'Failed delete person {personId}: {error}',logLevel=LOG_ERROR)
        return ret

    #=========================
    # Update DB section
    #-------------------------
    # Update DB
    def updateDB(persons, names, years, intYears) -> None:
        if (not Connection.isInitialized()):
            log(str="Cannot updateDB - connection is not initialized", logLevel=LOG_ERROR)
            return
        Connection.bulkPersonsInsert(persons=persons)
        mPersons = Connection.getImagePersonMap(persons=persons, names=names, years=years, intYears=intYears)
        Connection.bulkImageInsersion(mPersons=mPersons)

    # Make map: personName -> [imageName, year, intYear]
    def getImagePersonMap(persons, names, years, intYears):
        mPersons = {}
        for i in range(0, len(persons)):
            if (not mPersons.get(persons[i])):
                mPersons[persons[i]] = []
            imageInfo = {'name':names[i],'year_str':years[i],'year':intYears[i]}
            mPersons[persons[i]].append(imageInfo)
        return mPersons

    # Update DB - remove non existing persons and images
    def updateDB2(persons, names, years, intYears) -> None:
        if (not Connection.isInitialized()):
            log(str="Cannot updateDB2 - connection is not initialized", logLevel=LOG_ERROR)
            return
        Connection.bulkPersonsDelete(persons=persons)
        mPersons = Connection.getImagePersonMap(persons=persons, names=names, years=years, intYears=intYears)
        Connection.bulkImageDeletion(mPersons=mPersons)

    # Bulk persons insertion
    def bulkPersonsInsert(persons) -> None:
        personsSet = set(persons)
        # Get all persons from DB
        persons = Connection.getAllPersonsInfo()
        if (persons != None):
            # Create set of persons in DB - personsSetDB
            personsSetDb = set()
            for p in persons:
                personsSetDb.add(p['name'])
            # For each person in personsrSet check that it is in personsSetDB
            for p in personsSet:
                if (p not in personsSetDb):
                    # Insert new person
                    Connection.insertPerson(personName=p)
        else:
            log(str=f'Cannot get persons from DB',logLevel=LOG_ERROR)

    # Bulk persons deletion
    def bulkPersonsDelete(persons) -> None:
        personsSet = set(persons)
        # Get all persons from DB
        persons = Connection.getAllPersonsInfo()
        if (persons != None):
            # Create set of persons in DB - personsSetDB
            personsSetDb = set()
            for p in persons:
                personsSetDb.add(p['name'])
            # For each person in personsrSet check that it is in personsSetDB
            for p in personsSetDb:
                if (p not in personsSet):
                    # Delete person
                    log(str=f'Delete person {p}',logLevel=LOG_DEBUG)
                    personId = Connection.getPersonIdByName(person=p)
                    Connection.deletePerson(personId=personId)
        else:
            log(str=f'Cannot get persons from DB',logLevel=LOG_ERROR)

    # Bulk image insertion
    def bulkImageInsersion(mPersons) -> None:
        if (not Connection.isInitialized()):
            log(str="Cannot bulk image insert - connection is not initialized",logLevel=LOG_ERROR)
            return
        # Pass through all the persons
        for person in mPersons:
            # Check that person is in DB
            personId = Connection.getPersonIdByName(person=person)
            if (personId == None):
                log(str=f'Error getting person from DB: {person}',logLevel=LOG_ERROR)
                continue
            if (dbNotFound(result=personId)):
                log(str=f'Cannot insert image. No such person in DB: {person}',logLevel=LOG_ERROR)
                continue

            # Get all imsages for person
            imagesDB = Connection.getAllImagesOfPerson(personId=personId)

            images = mPersons[person]
            # Pass through all the images of the person
            for imageInfo in images:
                name = imageInfo['name']
                year = imageInfo['year_str']
                intYear = imageInfo['year']

                if (not Connection.findImageByTitleAndYear(imagesDB=imagesDB, name=name, year=year)):
                    # Insert personId, name, year, intYear
                    Connection.insertImage(personId=personId, imageName=name, year=year, intYear=intYear)

    # Bulk image deletion
    def bulkImageDeletion(mPersons) -> None:
        if (not Connection.isInitialized()):
            log(str="Cannot bulk image delete - connection is not initialized",logLevel=LOG_ERROR)
            return
        # Get all images from DB
        images = Connection.getAllImages()
        if (dbFound(result=images)):
            for imageInfo in images:
                pId = imageInfo['personId']
                iYear = imageInfo['year']
                iName = imageInfo['name']
                # Check if person exists
                ret = Connection.checkPersonExists(personId=pId)
                if (not ret):
                    # Delete image
                    log(str=f'Delete image (no person) {pId} - {iName} - {iYear}',logLevel=LOG_DEBUG)
                    Connection.deleteImage(imageId=imageInfo['id'])
                    continue
        else:
            log(str=f'No images found in DB',logLevel=LOG_WARNING)
        # Get all images from DB again
        images = Connection.getAllImages(personName=True)
        if (dbFound(result=images)):
            for imageInfo in images:
                pId = imageInfo['personId']
                iYear = imageInfo['year']
                iName = imageInfo['name']
                pName = imageInfo['personName']
                # Person exists - check if image exists locally
                # Get all images for the person
                pImages = mPersons.get(pName)
                if (not pImages):
                    log(str=f'Cannot find images for person {pName}', logLevel=LOG_ERROR)
                    continue
                # Go through all images of person
                found = False
                for image in pImages:
                    if ((image['name'] == iName) and (image['year'] == iYear)):
                        found = True
                        break
                if (not found):
                    # Delete image
                    log(str=f'Delete image (no image) {pName} - {iName} - {iYear}',logLevel=LOG_DEBUG)
                    Connection.deleteImage(imageId=imageInfo['id'])
                    continue
        else:
            log(str=f'No images found in DB 2',logLevel=LOG_WARNING)

    def findImageByTitleAndYear(imagesDB, name, year) -> bool:
        if (imagesDB == None): # No images for person - this is the first one
            return False
        for imageInfo in imagesDB:
            if (imageInfo['name'] == name and imageInfo['year_str'] == year):
                return True
        return False

    # Get all persons from DB
    # Returns:
    #   [[personInfo],...] - array of person info
    #   None - issue with DB
    def getAllPersonsInfo():
        fName = Connection.getAllPersonsInfo.__name__
        if (not Connection.isInitialized()):
            log(str=f"{fName}: Cannot get all persons - connection is not initialized",logLevel=LOG_ERROR)
            return None
        persons = []
        query = "select id,name,gender,country,birth,death,complexity,speciality from persons"
        ret = Connection.executeQuery(query=query,params={},all=True)
        if (dbFound(result=ret)):
            for p in ret:
                # Fill out person info
                person = dbGetPersonInfo(queryResult=p)
                persons.append(person)
        return persons
