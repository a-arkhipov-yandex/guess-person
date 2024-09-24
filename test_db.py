from __future__ import annotations

import pytest

from datetime import datetime as dt, timedelta
from db_lib import *

class TestDB:
    testUserTelegramId1 = '123456789'
    testUserTelegramId2 = "987654321"
    testUserId1 = None
    testUserId2 = None
    testPersonId1 = None
    testPersonId2 = None
    testPersonId3 = None
    testImageId1 = None
    testImageId2 = None
    testImageId3 = None
    testImageId4 = None
    testImageId5 = None
    testImageId21 = None

    def testDBConnectoin(self) -> None: # Test both test and production connection
        initLog(printToo=True)
        Connection.initConnection(test=False) # prod connection
        isInit1 = Connection.isInitialized()
        Connection.closeConnection()
        Connection.initConnection(test=True) # test connections
        isInit2 = Connection.isInitialized()
        # Create test user
        TestDB.testUserId1 = Connection.insertUser(telegramid=TestDB.testUserTelegramId1) # fake telegramid
        (game_type, game_complexity) = Connection.getUserSetting(telegramid=TestDB.testUserTelegramId1)
        assert(game_type == DEFAULT_GAMETYPE)
        assert(game_complexity == DEFAULT_GAMECOMPLEXITY)
        assert(len(Connection.getComplexities()) > 0)
        assert(len(Connection.getGameTypes()) > 0)
        assert(len(Connection.getImageTypes()) > 0)
        assert(len(Connection.getSpecialities()) > 0)
        userId = Connection.getUserIdByTelegramid(telegramid=TestDB.testUserTelegramId1)
        assert(userId == TestDB.testUserId1)
        TestDB.testUserId2 = Connection.insertUser(telegramid=TestDB.testUserTelegramId2) # fake telegramid
        id_tmp = Connection.insertUser(telegramid=TestDB.testUserTelegramId2) # fake telegramid
        assert(id_tmp == None)
        assert(isInit1 and isInit2)
        assert(TestDB.testUserId1 and TestDB.testUserId2)

    @pytest.mark.parametrize(
        "query, params, expected_result",
        [
            # Correct
            ('select id from users where id = 1000000', {}, NOT_FOUND), # Correct query wihtout params returning nothing
            ('select id from users where id = %(c)s', {'c':1000000}, NOT_FOUND), # Correct query with 1 param returning nothing
            ('select id from users where id=%(c)s and telegramid=%(n)s', {'c':1000000, 'n':'12'}, NOT_FOUND), # Correct query with >1 params returning nothing
            # Incorrect
            ('select id from users where people = 10', {}, None), # InCorrect query syntax
            ('select id from users where id = %(c)s', {}, None), # InCorrect query need params but not provided
            ('select id from users where id=%(c)s and name=%(n)s', {'c':1000000}, None), # InCorrect number of params in query
        ],
    )
    def testExecuteQueryFetchOne(self, query, params, expected_result):
        assert(Connection.executeQuery(query, params) == expected_result)

    @pytest.mark.parametrize(
        "query, params, expected_result",
        [
            # Correct
            ('select id from users where id = 1000000', {}, NOT_FOUND), # Correct query wihtout params returning nothing
            ('select id from users where id = %(c)s', {'c':1000000}, NOT_FOUND), # Correct query with 1 param returning nothing
            ('select id from users where id=%(c)s and telegramid=%(n)s', {'c':1000000, 'n':'123'}, NOT_FOUND), # Correct query with >1 params returning nothing
            # Incorrect
            ('select id from users where people = 10', {}, None), # InCorrect query syntax
            ('select id from users where id = %(c)s', {}, None), # InCorrect query need params but not provided
            ('select id from users where id=%(c)s and name=%(n)s', {'c':1000000}, None), # InCorrect number of params in query
        ],
    )
    def testExecuteQueryFetchAll(self, query, params, expected_result):
        assert(Connection.executeQuery(query, params, True) == expected_result)

    # Test user name format
    @pytest.mark.parametrize(
        "p, expected_result",
        [
            ('123dfdf', False),
            ('dfввв12', False),
            ('s232', False),
            ('232', True),
            ('s23#2', False),
            ('s/232', False),
            ('s#232', False),
            ('s$232', False),
            ('s%232', False),
            ('s2.32', False),
            ('-123', False),
            ('alex_arkhipov', False),
        ],
    )
    def testCheckUserTelegramFormat(self, p, expected_result):
        ret = dbLibCheckTelegramid(telegramid=p)
        assert(ret == expected_result)

    # Test dbLibCheckUserId
    @pytest.mark.parametrize(
        "u, expected_result",
        [
            (128, True),
            ('12', True),
            ('s232', False),
            ('s23#2', False),
            ('s/232', False),
            ('-123', False),
            ('0', False),
        ],
    )
    def testdbLibCheckUserId(self, u, expected_result):
        ret = dbLibCheckUserId(userId=u)
        assert(ret == expected_result)

    # Test dbLibCheckGameType()
    def testdbLibCheckGameType(self) -> None:
        gameTypes = Connection.getGameTypes()
        ret = Connection.dbLibCheckGameType(game_type=0)
        assert(ret == False)
        ret = Connection.dbLibCheckGameType(game_type=len(gameTypes))
        assert(ret == True)
        ret = Connection.dbLibCheckGameType(game_type=len(gameTypes)+1)
        assert(ret == False)
        ret = Connection.dbLibCheckGameType(game_type="dfdf")
        assert(ret == False)

    # Test dbLibCheckImageType()
    def testdbLibCheckImageType(self) -> None:
        imageTypes = Connection.getImageTypes()
        ret = Connection.dbLibCheckImageType(image_type=0)
        assert(ret == False)
        ret = Connection.dbLibCheckImageType(image_type=len(imageTypes))
        assert(ret == True)
        ret = Connection.dbLibCheckImageType(image_type=len(imageTypes)+1)
        assert(ret == False)
        ret = Connection.dbLibCheckImageType(image_type="dfdf")
        assert(ret == False)

    # Test dbLibCheckGameComplexity()
    def testdbLibCheckGameComplexity(self) -> None:
        gameComplexity = Connection.getImageTypes()
        ret = Connection.dbLibCheckGameComplexity(game_complexity=0)
        assert(ret == False)
        ret = Connection.dbLibCheckGameComplexity(game_complexity=len(gameComplexity))
        assert(ret == True)
        ret = Connection.dbLibCheckGameComplexity(game_complexity=len(gameComplexity)+1)
        assert(ret == False)
        ret = Connection.dbLibCheckGameComplexity(game_complexity="dfdf")
        assert(ret == False)

    def testPersonsAndImageCreation(self) -> None:
        pId1 = Connection.insertPerson("Test Person 1")
        TestDB.testPersonId1 = pId1
        assert(TestDB.testPersonId1 > 0)
        assert(Connection.checkPersonExists(personId=pId1))
        assert(not Connection.checkPersonExists(personId=1000000))
        pId2 = Connection.insertPerson("Test Person 2")
        TestDB.testPersonId2 = pId2
        assert(TestDB.testPersonId2 > 0)
        pId3 = Connection.insertPerson("Test Person 3")
        TestDB.testPersonId3 = pId3
        assert(TestDB.testPersonId3 > 0)
        TestDB.testImageId1 = Connection.insertImage(personId=pId1,imageName="test image 1",year='1999 г',intYear=1999)
        assert(int(TestDB.testImageId1) > 0)
        TestDB.testImageId2 = Connection.insertImage(personId=pId1,imageName="test image 2",year='0',intYear=0)
        assert(int(TestDB.testImageId2) > 0)
        TestDB.testImageId3 = Connection.insertImage(personId=pId1,imageName="2",year='0',intYear=0)
        assert(int(TestDB.testImageId3) > 0)
        TestDB.testImageId4 = Connection.insertImage(personId=pId1,imageName="1",year='1800е г',intYear=1800)
        assert(int(TestDB.testImageId4) > 0)
        TestDB.testImageId5 = Connection.insertImage(personId=pId1,imageName="22",year='0',intYear=0)
        assert(int(TestDB.testImageId5) > 0)
        TestDB.testImageId21 = Connection.insertImage(personId=pId2,imageName="2fdsf2",year='0',intYear=0)
        assert(int(TestDB.testImageId21) > 0)

    def testPersonAndImage(self) -> None:
        pName1 = "Test Person"
        # Create person
        pId1 = Connection.insertPerson(pName1)
        assert(pId1 != None)
        pIdNonExisting = Connection.insertPerson(pName1) # Dup
        assert(pIdNonExisting == None)
        # insert image for non existing person
        imageName = 'test image new 2'
        imageName2 = '1'
        year = '1995 г'
        intYear = 1995
        # Wrong image creation
        iId1 = Connection.insertImage(personId=10000000,imageName=imageName,year=year,intYear=intYear)
        assert(iId1 == None)
        iId1 = Connection.insertImage(personId=pId1,imageName=imageName,year=year,intYear='dfdfd')
        assert(iId1 == None)
        # insert image for existing person
        iId1 = Connection.insertImage(personId=pId1,imageName=imageName,year=year,intYear=intYear)
        assert(iId1 > 0)
        iId11 = Connection.insertImage(personId=pId1,imageName=imageName2,year=year,intYear=intYear)
        assert(iId11 > 0)
        # Duplicate
        iId2 = Connection.insertImage(personId=pId1,imageName=imageName,year=year,intYear=intYear)
        assert(iId2 == None)
        pIds = Connection.getRandomPersonIds(complexity=1,n=3)
        assert(len(pIds) == 3)
        iIds = Connection.getRandomImageIdsOfPerson(personId=pId1,n=2)
        assert(len(iIds) == 2)
        iIds = Connection.getRandomImageIdsOfPerson(personId=TestDB.testPersonId1,n=5)
        assert(len(iIds) == 5)

        # Cleanup
        ret = Connection.deleteImage(imageId=iId1)
        assert(ret == True)
        ret = Connection.deleteImage(imageId=iId11)
        assert(ret == True)
        ret = Connection.deletePerson(personId=pId1)
        assert(ret == True)
        ret = Connection.deletePerson(personId=100000000)
        assert(ret == False)

    def testGame(self) -> None:
        # Create game type 1
        gameId1 = Connection.insertGame(userId=TestDB.testUserId1,game_type=1,correct_answer=1,question=2,complexity=3)
        gameInfo = Connection.getGameInfoById(gameId=gameId1)
        assert(gameInfo['id'] == gameId1)
        assert(gameInfo['userid'] == TestDB.testUserId1)
        assert(gameInfo['game_type'] == 1)
        assert(gameInfo['correct_answer'] == 1)
        assert(gameInfo['question'] == '2')
        assert(gameInfo['complexity'] == 3)
        assert(gameInfo['created'] != None)
        # Create game type 2
        gameId2 = Connection.insertGame(TestDB.testUserId2,2,5,6,1)
        assert(Connection.checkGameIsFinished(gameId=gameId1) == False)
        # Complete game type 1 with correct answer
        Connection.finishGame(gameId=gameId1,answer=1)
        # Check result game 1
        gameInfo = Connection.getGameInfoById(gameId=gameId1)
        assert(gameInfo['result'] == True)
        assert(gameInfo['finished'] != None)
        # Complete game type 2 with incorrect answer
        Connection.finishGame(gameId=gameId2,answer=1)
        # Check result game 2
        gameInfo = Connection.getGameInfoById(gameId=gameId2)
        assert(gameInfo['result'] == False)
        assert(Connection.checkGameIsFinished(gameId=gameId1) == True)
        # Delete game 1
        assert(Connection.deleteGame(gameId=gameId1))
        # Delete game 2
        assert(Connection.deleteGame(gameId=gameId2))
        pIds = Connection.getRandomPersonIds(complexity=1,n=2)
        assert(len(pIds) == 2)
        pIds = Connection.getRandomPersonIds(complexity=3)
        assert(len(pIds) == 1)
        pIds = Connection.getRandomImageIdsOfOtherPersons(personId=TestDB.testPersonId2, complexity=2,n=3)
        assert(len(pIds) == 3)
        pIds = Connection.getRandomImageIdsOfAnyPerson(complexity=3, n=2)
        assert(len(pIds) == 2)
        pIds = Connection.getNPersons(n=2,exclude=TestDB.testPersonId1,complexity=3)
        assert(len(pIds) == 2)


    def testClenup(seft) -> None:
        # Remove test images
        assert(Connection.deleteImage(imageId=TestDB.testImageId1))
        assert(Connection.deleteImage(imageId=TestDB.testImageId2))
        assert(Connection.deleteImage(imageId=TestDB.testImageId3))
        assert(Connection.deleteImage(imageId=TestDB.testImageId4))
        assert(Connection.deleteImage(imageId=TestDB.testImageId5))
        assert(Connection.deleteImage(imageId=TestDB.testImageId21))
        # Remove test persons
        pId1 = Connection.getPersonIdByName(person="Test Person")
        Connection.deletePerson(pId1)
        assert(Connection.deletePerson(personId=TestDB.testPersonId1))
        assert(Connection.deletePerson(personId=TestDB.testPersonId2))
        assert(Connection.deletePerson(personId=TestDB.testPersonId3))
        # Remove test user
        resDelete1 = False
        resDelete2 = False
        resDelete1 = Connection.deleteUser(TestDB.testUserId1)
        resDelete2 = Connection.deleteUser(TestDB.testUserId2)
        # Close connection
        Connection.closeConnection()
        assert(resDelete1)
        assert(resDelete2)

