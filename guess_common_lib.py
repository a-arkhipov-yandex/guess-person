from os import path
from os import getenv, environ
from datetime import datetime as dt
from Levenshtein import distance
from dotenv import load_dotenv
import re
import csv
from log_lib import *

EXT = '.JPG'

PERSONS_FILE_CVS = 'persons.csv'
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

ENV_BOTTOKEN = 'BOTTOKEN'
ENV_BOTTOKENTEST = 'BOTTOKENTEST'

ENV_TESTDB = 'TESTDB'
ENV_TESTBOT = 'TESTBOT'

MIN_SIMILARITY = 3

def isStrSimilar(str1,str2) -> bool:
    dist = getStrDistance(str1=str1,str2=str2)
    return dist <= MIN_SIMILARITY

def getStrDistance(str1, str2) -> int:
    return distance(s1=str1, s2=str2)

def isTestBot() -> bool:
    load_dotenv()
    ret = True
    testbot = getenv(ENV_TESTBOT)
    if (testbot):
        if (testbot == "False"):
            ret = False
    return ret

def isTestDB() -> bool:
    load_dotenv()
    ret = True
    testdb = getenv(ENV_TESTDB)
    if (testdb):
        if (testdb == "False"):
            ret = False
    return ret    

def getBotToken(test):
    load_dotenv()
    token = getenv(ENV_BOTTOKEN)
    if (test):
        token = getenv(ENV_BOTTOKENTEST)
    return token

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

def readCSV(fileName):
    data = []
    if (not path.exists(path=fileName)):
        return data
    with open(file=fileName, mode='r') as file:
        reader = csv.reader(file)
        header = next(reader)
        for row in reader:
            dataItem = {}
            for i in range(0,len(header)):
                fieldName = header[i]
                dataItem[fieldName] = row[i]
            data.append(dataItem)
    return data

def readPersonsCSV():
    fName = readPersonsCSV.__name__
    persons = readCSV(fileName=PERSONS_FILE_CVS)
    resPersons = []
    # Check and transform
    for person in persons:
        personId = person.get('id')
        if (not personId):
            log(str=f'{fName}: No ID in CSV file: {person}',logLevel=LOG_ERROR)
            continue
        personName = person.get('name')
        if (not personName):
            log(str=f'{fName}: No Name in CSV file: {person}',logLevel=LOG_ERROR)
            continue
        newPerson = {}
        newPerson['id'] = int(personId)
        newPerson['name'] = personName
        gender = None
        if (person.get('gender')):
            gender = int(person.get('gender'))
        newPerson['gender'] = gender
        birth = None
        if (person.get('birth')):
            birth = int(person.get('birth'))
        newPerson['birth'] = birth
        death = None
        if (person.get('death')):
            death = int(person.get('death'))
        newPerson['death'] = death
        country = None
        if (person.get('country')):
            country = person.get('country')
        newPerson['country'] = country
        complexity = None
        if (person.get('complexity')):
            complexity = int(person.get('complexity'))
        newPerson['complexity'] = complexity
        speciality = None
        if (person.get('speciality')):
            try:
                speciality = int(person.get('speciality'))
            except:
                log(str=f'{fName}: Speciality is not int for person {personName}: {speciality}',logLevel=LOG_WARNING)
        newPerson['speciality'] = speciality
        resPersons.append(newPerson)
    return resPersons

def checkUserNameFormat(user) -> bool:
    ret = False
    res = re.match(r'^[a-zA-Z][a-zA-Z0-9-_]+$', user)
    if res and len(user) > 2:
        ret = True
    return ret

# remove 'ок ' and ' г' from year of image
# Returns:
#   None - something wrong with format (len <4 or no 'г.' at the end)
#   year - str withour ' г' and precending 'ok. '
def removeYearSigns(rawYear):
    if (len(rawYear) < 4):
        return None
    # Remove ' г' from year
    year_sign = rawYear[-2:]
    if (year_sign == ' г'):
        year = rawYear[:-2]
    else:
        return None
    if year[0:3] == 'ок ':
        year = year[3:]
    return year

# Transofrm str to int
# Returns:
#   int i - if correct it
#   False - if cannot transform
def myInt(str):
    try:
        iYear = int(str)
    except:
        return False
    return iYear

# Build image name from parts
def buildImgName(person, name, year) -> str:
    yearTxt = ''
    if (year != '0'):
        yearTxt = f' - {year}'
    url = f'{person} - {name}{yearTxt}{EXT}'
    return url

# Build URL to image
def buildImgUrl(base_url:str, person, imageName, year) -> str:
    space = '%20'
    url1 = base_url + buildImgName(person=person, name=imageName, year=year)
    url = url1.replace(' ', space)
    return url

# Get year (possible nearly)
# Returns:
#   int year - int year
#   False - error parsing year
#   0 - year is too small or too big
def getYear(rawYear):
    retYear = 0
    year = removeYearSigns(rawYear)
    if (year == None):
        return False
    if year[-1] == 'е':
        year = year[0:-1]
    lYear = len(year)
    if (lYear == 4):
        # Check that this is real year
        retYear = myInt(year)
        if not retYear:
            log(f'Problem with int conversion - {year}',LOG_ERROR)
            return False
    elif (lYear == 9):
        years = year.split('-')
        if (len(years) != 2):
            log(f'Cannot split years - {year}',LOG_ERROR)
            return False
        year1 = myInt(years[0])
        year2 = myInt(years[1])
        if ((not year1) or (not year2)):
            log(f'Problem with int conversion 2 - {year}',LOG_ERROR)
            return False
        retYear = int((year2+year1)/2) # return average
    
    if ((retYear < 1000) or (retYear > 2030)):
        log(f'Year is out of range: {rawYear}',LOG_ERROR)
        retYear = 0
    return retYear 
