from os import listdir, path, rename
from log_lib import *
from PIL import Image
from guess_common_lib import *

# TODO: change this
#IMAGE_DIR = "/Users/a-arkhipov/Yandex.Disk.localized/Images/Личности/"
IMAGE_DIR = "/Users/a-arkhipov/Downloads/Личности/"

DEFAILT_SAVE_IMAGE_DIR = "/Users/a-arkhipov/Downloads/SavedBotImages/"

MAX_FILESIZE_KB = 256

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
    year = removeYearSigns(rawYear=rawYear)
    if (year == None):
        return None
    if year[-1] == 'е':
        year = year[0:-1]
    lYear = len(year)
    if (lYear == 4):
        # Check that this is real year
        retYear = myInt(str=year)
        if not retYear:
            log(str=f'{fName}: Problem with int conversion - {year}',logLevel=LOG_ERROR)
            return None
    elif (lYear == 9):
        years = year.split('-')
        if (len(years) != 2):
            log(str=f'{fName}: Cannot split years - {year}',logLevel=LOG_ERROR)
            return None
        year1 = myInt(str=years[0])
        year2 = myInt(str=years[1])
        if ((not year1) or (not year2)):
            log(str=f'{fName}: Problem with int conversion 2 - {year}',logLevel=LOG_ERROR)
            return None
        retYear = int((year2+year1)/2) # return average
    
    if ((retYear < 1000) or (retYear > 2030)):
        log(str=f'{fName}: Year is out of range: {rawYear}',logLevel=LOG_ERROR)
        retYear = None
    return retYear 

# Get all images in directory
def getImgs():
    fName = getImgs.__name__
    files = []
    for f in listdir(path=IMAGE_DIR):
        #log(str=fr'{fName}: Handling file "{f}"', logLevel=LOG_DEBUG)
        f1 = f[:-4]
        # Skip '.DS_S'
        if f1 != '.DS_S':
            # Remove '.jpg'
            ff = f[-4:]
            if (ff != LOCAL_EXT):
                log(str=f'Extension is not {LOCAL_EXT}: {f}',logLevel=LOG_WARNING)
                continue
            # Check for \xa0 symbol
            if ('\xa0' in f1):
                f2 = f1.replace('\xa0', ' ')
                rename(src=f'{IMAGE_DIR}/{f1}.jpg', dst=f'{IMAGE_DIR}/{f2}.jpg')
                log(str=fr'Special character "\xa0" is in file name {f1} - renaming', logLevel=LOG_WARNING)
                f1 = f2
            files.append(f1)
    numFiles = len(files)
    log(str=f'{fName}: Number of files: {numFiles}')

    persons = []
    names = []
    years = []
    intYears = []
    for f in files:
        ret = parsePersonAndImage(info=f)
        if (ret):
            persons.append(ret[0])
            names.append(ret[1])
            years.append(ret[2])
            intYears.append(ret[3])

    return [persons, names, years, intYears]
 
def parsePersonAndImage(info) -> list:
    fName = parsePersonAndImage.__name__
    ret = []
    tmp = info.split(" - ")
    lTmp = len(tmp)
    if lTmp < 2 or lTmp > 3:
        log(str=f"{fName}: Wrong numer of items: {info} - {lTmp}", logLevel=LOG_ERROR)
        return []
    person = tmp[0].strip()
    if person != tmp[0]:
        log(str=f'{fName}: Spaces in person {tmp}',logLevel=LOG_WARNING)
        return []
    ret.append(person)
    title = tmp[1].strip()
    if title != tmp[1]:
        log(str=f'{fName}: Spaces in name {tmp}',logLevel=LOG_WARNING)
        return []
    ret.append(title)
    year = '0'
    if (lTmp == 3): # There is year in file name
        year = tmp[2].strip()
        if year != tmp[2]:
            log(str=f'{fName}: Spaces in year {tmp}', logLevel=LOG_ERROR)
            return []
    ret.append(year)
    intYear = getYear(rawYear=year)
    if (intYear == None):
        log(str=f'{fName}: Cannot get int year: "{tmp}"', logLevel=LOG_ERROR)
        return []
    ret.append(intYear)
    return ret

def parsePersonAndImage2(info) -> list:
    fName = parsePersonAndImage2.__name__
    if (not info):
        return []
    ret = []
    tmp = info.split(" - ")
    lTmp = len(tmp)
    if lTmp < 1 or lTmp > 3:
        log(str=f"{fName}: Wrong numer of items: {info} - {lTmp}", logLevel=LOG_ERROR)
        return []
    person = tmp[0].strip()
    if person != tmp[0]:
        log(str=f'{fName}: Spaces in person {tmp}',logLevel=LOG_WARNING)
        return []
    ret.append(person)
    if (lTmp == 1):
        ret.append('') # no image name
        ret.append('0')
        ret.append(0)
        return ret
    title = tmp[1].strip()
    if title != tmp[1]:
        log(str=f'{fName}: Spaces in name {tmp}',logLevel=LOG_WARNING)
        return []
    ret.append(title)
    year = '0'
    if (lTmp == 3): # There is year in file name
        year = tmp[2].strip()
        if year != tmp[2]:
            log(str=f'{fName}: Spaces in year {tmp}', logLevel=LOG_ERROR)
            return []
    ret.append(year)
    intYear = getYear(rawYear=year)
    if (intYear == None):
        log(str=f'{fName}: Cannot get int year: "{tmp}"', logLevel=LOG_ERROR)
        return []
    ret.append(intYear)
    return ret

# Get all images in directory
def adjustImages(dry_run = False) -> None:
    TMP_IMAGE_DIR = IMAGE_DIR
    fName = adjustImages.__name__
    for f in listdir(path=TMP_IMAGE_DIR):
        if (f != '.DS_Store'):
            adjustImageSize(file=f'{TMP_IMAGE_DIR}/{f}',dry_run=dry_run)
    for f in listdir(path=TMP_IMAGE_DIR):
        if (f != '.DS_Store'):
            adjustImageName(file=f'{TMP_IMAGE_DIR}/{f}',dry_run=dry_run)

 # Adjust image size
 # If bigger side is larget than 500px than shorten it to 500px and adjust smaller one accordingly
def adjustImageName(file, dry_run = False) -> bool:
    fName = adjustImageName.__name__
    file1 = file.replace('ё','е') # Replace 'ё'ё
    file1 = file1.replace('ё','е') # Replace 'ё' another ё
    file2 = file1.replace('й','й') # Replace 'й'
    if (file2 != file1):
        log(str=f'{fName}: Renaming {file} to {file2}')
        if (not dry_run):
            rename(src=file, dst=file2)
    return file2

 # Adjust image size
 # If bigger side is larget than 500px than shorten it to 500px and adjust smaller one accordingly
def adjustImageSize(file, dry_run = False) -> bool:
    fName = adjustImageSize.__name__
    MAXSIZE = 500
    img = Image.open(file)
    wid, hgt = img.size
    maxSide = max(wid, hgt)
    minSide = min(wid,hgt)
    ret = False
    if (maxSide > MAXSIZE):
        oldFilesizeKB = int(path.getsize(filename=file)/1024)
        newMax = MAXSIZE
        newMin = int(minSide*MAXSIZE/maxSide)
        if (wid > hgt):
            newWid = newMax
            newHgt = newMin
        else:
            newWid = newMin
            newHgt = newMax

        newSize = (newWid,newHgt)
        img2 = img.resize(newSize, Image.HAMMING)
        if (not dry_run):
            try:
                img2.save(file)
            except Exception as error:
                log(str=f'{fName}: Error during resized file saving: {file} -> {error}',logLevel=LOG_ERROR)
            newFilesizeKB = int(path.getsize(filename=file)/1024)
            log(str=f'Image "{file}" resized from ({wid},{hgt}) to {newSize}: old file size {oldFilesizeKB} | new file size {newFilesizeKB}')
        else:
            log(str=f'Image "{file}" should be resized from ({wid},{hgt}) to {newSize}: old file size {oldFilesizeKB}')
        ret = True
    else:
        #log(str=f'No need to resize file {file} - current size ({wid},{hgt})',logLevel=LOG_DEBUG)
        pass
    return ret

def getFilesInImageDir() -> list[str]:
    files = listdir(path=IMAGE_DIR)
    return files