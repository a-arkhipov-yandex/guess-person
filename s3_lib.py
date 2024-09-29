from os import system
from subprocess import run, STDOUT, PIPE
from img_fs_lib import *
from guess_common_lib import *

S3BUCKET = 's3://guess-person'

# Build cmd to upload image to S3
def buildUploadCmd(imgName) -> str:
    filePath = buildImgPathName(imgName=imgName)
    return 's3cmd put "' + filePath + '" ' + S3BUCKET

# Build cmd to delete image from S3
def buildDeleteCmd(imgName) -> str:
    return f's3cmd rm "{S3BUCKET}/{imgName}"' 


# Upload image to Bucket
def uploadImg(imgName) -> int:
    fName = uploadImg.__name__
    cmd = buildUploadCmd(imgName=imgName)
    ret = system(command=cmd)
    if (ret != 0):
        log(str=f'{fName}: Error uploading image: cmd={cmd} | ret={ret}',logLevel=LOG_ERROR)
    return ret

# Delete image from Bucket
def deleteImg(imgName) -> int:
    fName = deleteImg.__name__
    cmd = buildDeleteCmd(imgName=imgName)
    log(str=f'cmd={cmd}',logLevel=LOG_DEBUG)
    ret = system(command=cmd)
    if (ret != 0):
        log(str=f'{fName}: Error deleting image: cmd={cmd} | ret={ret}',logLevel=LOG_ERROR)
    return ret

def getImgsInBucket():    
    # указывайте полный путь к запускаемой 
    # программе/команде или она не будет работать
    cmd = 's3cmd ls ' + S3BUCKET
    # перенаправляем `stdout` и `stderr` в переменную `output`
    res = run(args=cmd.split(), stdout=PIPE, text=True)
    output = res.stdout
    arrOutput = output.split("\n")

    arrFinal = set()
    for s in arrOutput:
        index = s.find(S3BUCKET)
        if (index == -1):
            # No file - just skip
            continue
        index = index + len(S3BUCKET)+1 # get index of image name
        image = s[index:] # get image
        arrFinal.add(image) # save

    return arrFinal

# Check if image is in bucket
def checkImgInBucket(imgName, imgsInBucket) -> bool:
    ret = False
    if (imgName in imgsInBucket):
        ret = True
    return ret

def bulkUpload(persons, names, years) -> None:
    imgsInBucket = getImgsInBucket()

    for i in range(0, len(persons)):
        # Check is img is in bucket
        imgName = buildImgS3FileName(person=persons[i], name=names[i], year=years[i])
        if (not checkImgInBucket(imgName=imgName, imgsInBucket=imgsInBucket)):
            # upload image to bucket
            log(str=f"Uploading {imgName}")
            ret = uploadImg(imgName=imgName)
            if (ret != 0):
                # Fail
                log(str=f'Cannot upload image {imgName}. Returned: {ret}', logLevel=LOG_ERROR)
                break
        else:
            #print(f"Skip uploading (already uploaded): {imgName}")
            pass

def removeNonExistingFilesOnS3() -> None:
    imgsInBucket = getImgsInBucket()
    filesInDir = getFilesInImageDir()
    # Go through all files in bucket
    for img in imgsInBucket:
        # Check if file exist
        #fullpath = buildImgPathName(imgName=img)
        # Replace '.JPG' with '.jpg'
        newImg = img.replace('.JPG', '.jpg')
        if (newImg not in filesInDir):
            # remove it from s3
            log(str=f"Deleting {img} ...")
            ret = deleteImg(imgName=img)
            if (ret != 0):
                # Fail
                log(str=f'Cannot delete image {img}. Returned: {ret}', logLevel=LOG_ERROR)
                break
        else:
            pass