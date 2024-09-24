from os import listdir
from log_lib import *

# TODO: change this
IMAGE_DIR = "/Users/a-arkhipov/Yandex.Disk.localized/Images/Личности/"
IMAGE_DIR = "/Users/a-arkhipov/Downloads/Личности/"

# Build image full path name
def buildImgPathName(imgName:str) -> str:
    return IMAGE_DIR + imgName

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

# Get year (possible nearly)
# Returns:
#   int year - int year
#   False - error parsing year
#   0 - year is too small or too big
def getYear(rawYear):
    fName = getYear.__name__
    retYear = 0
    if (rawYear == '0'):
        return 0
    year = removeYearSigns(rawYear)
    if (year == None):
        return None
    if year[-1] == 'е':
        year = year[0:-1]
    lYear = len(year)
    if (lYear == 4):
        # Check that this is real year
        retYear = myInt(year)
        if not retYear:
            log(f'{fName}: Problem with int conversion - {year}',LOG_ERROR)
            return None
    elif (lYear == 9):
        years = year.split('-')
        if (len(years) != 2):
            log(f'{fName}: Cannot split years - {year}',LOG_ERROR)
            return None
        year1 = myInt(years[0])
        year2 = myInt(years[1])
        if ((not year1) or (not year2)):
            log(f'{fName}: Problem with int conversion 2 - {year}',LOG_ERROR)
            return None
        retYear = int((year2+year1)/2) # return average
    
    if ((retYear < 1000) or (retYear > 2030)):
        log(f'{fName}: Year is out of range: {rawYear}',LOG_ERROR)
        retYear = 0
    return retYear 

# Get all images in directory
def getImgs():
    fName = getImgs.__name__
    files = []
    for f in listdir(path=IMAGE_DIR):
        f1 = f[:-4]
        # Skip '.DS_S'
        if f1 != '.DS_S':
            # Remove '.jpg'
            ff = f[-4:]
            if (ff != '.jpg'):
                log(f'Is not .jpg: {f}',LOG_WARNING)
            else:
                files.append(f1)
    numFiles = len(files)
    log(f'{fName}: Number of files: {numFiles}')

    persons = []
    names = []
    years = []
    intYears = []
    for f in files:
        tmp = f.split(" - ")
        lTmp = len(tmp)
        if lTmp < 2 or lTmp > 3:
            log(f"{fName}: Wrong numer of items: {f} - {lTmp}", LOG_ERROR)
            continue
        person = tmp[0].strip()
        if person != tmp[0]:
            log(f'{fName}: Spaces in person {tmp}',LOG_WARNING)
        persons.append(person)
        title = tmp[1].strip()
        if title != tmp[1]:
            log(f'{fName}: Spaces in name {tmp}',LOG_WARNING)
        names.append(title)
        year = '0'
        if (lTmp == 3): # There is year in file name
            year = tmp[2].strip()
            if year != tmp[2]:
                log(f'{fName}: Spaces in year {tmp}', LOG_WARNING)
        years.append(year)

        intYear = getYear(year)
        if (intYear == None):
            log(f'{fName}: Cannot get int year: "{tmp}"', LOG_ERROR)
            intYear = 0
        intYears.append(intYear)

    return [persons, names, years, intYears]
 