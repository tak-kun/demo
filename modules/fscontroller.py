import os  
import shutil
import subprocess
import uuid
from distutils.dir_util import copy_tree

def moveDirectoryTo(source_path, destination_path, make_cash, make_ID_name):
    try:
        # Source path  
        source = source_path
        id_name = None
        # Destination path  
        destination = destination_path #'../Batches/Imported/ID'
        if make_ID_name is True:
            id_name = uuid.uuid4()
            destination = destination + str(id_name)
        dest = shutil.move(source, destination)
        return str(id_name)
    except:
        return False

def copyDirectoryTo(source_path, destination_path, make_cash, make_ID_name):
    # try:
    #     # Source path  
    #     source = source_path
    #     id_name = None
    #     # Destination path  
    #     destination = destination_path #'../Batches/Imported/ID'
    #     if make_ID_name is True:
    #         id_name = uuid.uuid4()
    #         destination = destination + str(id_name)
    #     dest = shutil.copy(source_path, destination)
    #     return str(id_name)
    # except:
    #     print('Copy Error!')
    #     return False

    source = source_path
    id_name = None
    destination = destination_path #'../Batches/Imported/ID'
    if make_ID_name is True:
        id_name = uuid.uuid4()
        destination = destination + str(id_name)
    copy_tree(source, destination, update=1)


def makePathToImage(imageName, currentBatchType, currentBatch):
    if currentBatchType == 0:
        batchDir = "Imported"
        imageFullPath = "./Batches/{}/{}/{}".format(batchDir, currentBatch, imageName)
    else:
        batchDir = "Labeled"
        imageFullPath = "./Batches/{}/{}/sources/{}".format(batchDir, currentBatch, imageName)
    return imageFullPath

def makePathToMask(imageName, currentBatchType, currentBatch):
    maskFullPath = "./Batches/Labeled/{}/labeled/{}".format(currentBatch, imageName)
    return maskFullPath

def createSaveDirectoryies(current_focused_batch_uuid):
    path = './Batches/Labeled/' + current_focused_batch_uuid
    path_sources = './Batches/Labeled/' + current_focused_batch_uuid + '/sources'
    path_labeled = './Batches/Labeled/' + current_focused_batch_uuid + '/labeled'
    try:
        for directory in [path, path_sources, path_labeled]:
            os.makedirs(directory)
            subprocess.call(['chmod', '777', directory])
    except OSError:
        print ("Creation of the directory %s failed" % path)
        return False
    else:
        print ("Successfully created the directory %s" % path)
        return True
