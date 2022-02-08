from aifc import Error
import os
import hashlib
from PIL import Image
import random
import sys
from datetime import datetime
import itertools
import sqlite3
from sqlite3.dbapi2 import IntegrityError
import json



def db_connection(dbPath):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(dbPath)
        return conn
    except Error as e:
        print(e)

    return conn


def db_option():
    option = None
    for item in poss[0]:
        layerType = item[0].split('/')[-1]

        if option == None:
            option = layerType + ' text'
        
        else:
            option = option + ', ' + layerType + ' text'

    return option


def create_table(conn):
    """ create a table from the table statement """

    options = 'id integer PRIMARY KEY, ' + db_option()

    table = """CREATE TABLE IF NOT EXISTS metadata (
                                        {options}
                                    );""".format(options=options)     

    try:
        c = conn.cursor()
        c.execute(table)
    except Error as e:
            print(e)
            sys.exit()


def create_db(dbPath):
    conn = db_connection(dbPath)

    if conn is not None:
        create_table(conn)
        conn.close()
    else:
        print("Error! Can't create the database connection.")
        sys.exit()


def db_query(dbPath,  query):
    conn = db_connection(dbPath)
    cursor = conn.cursor()
    cursor.execute(query)
    database = cursor.fetchall()

    return database


def db_insert(dbPath, data):
    conn = db_connection(dbPath)
    cursor = conn.cursor()
    options = db_option().replace(' text', '')

    sq_query = """INSERT INTO metadata
                ({options}) 
                VALUES 
                (?, ?, ?);""".format(options=options)
    
    data_tuple = tuple(data)
    cursor = conn.cursor()
    try:
        cursor.execute(sq_query, data_tuple)
    except IntegrityError as e:
        print(e)
        sys.exit()
    
    conn.commit()
    conn.close()


def layer_root(BASE_PATH):
    BASE_PATH = './LAYERS'
    lPaths = {}
    i = 0
    for path, dirs, files in os.walk(BASE_PATH):
        if path == BASE_PATH:
            pass
        elif path == (BASE_PATH + 'BASE_LAYER') and len(files) > 0:
            lPaths[0] = path
        else:
            i = i + 1
            lPaths[i] = path

    return lPaths


def img_poss():
    BASE_PATH = './LAYERS'
    lPaths = layer_root(BASE_PATH)
    layers = []
    for root in lPaths:
        layer = []
        for imgLayer in os.listdir(lPaths[root]):
            if imgLayer.endswith('.png'):
                layer.append([lPaths[root], imgLayer])

        layers.append(layer)
                
    return list(itertools.product(*layers))


def read_const():
    constrain_file = open('CONST.txt', "r")
    rFile = constrain_file.read()
    rFile = rFile.replace(',', '')
    rFile = rFile.split()[4:]

    constrain = []
    arg = []
    args = []
    
    for item in rFile:
        arg.append(item)

        if len(arg) % 2 == 0:
            args.append(arg)
            arg = []

        if len(args) == 2:
            constrain.append(args)
            args = []

    return constrain


def apply_const(poss, const):
    possToRemove = []
    possFiltered = []

    for possibility in poss:
        for constrain in const:
            i = 0
            j = 0
            for item in possibility:
                i = i + 1
                if str(item[0]).endswith(constrain[0][0]) or str(item[0]).endswith(constrain[1][0]):

                    if str(item[0]).endswith(constrain[0][0]) and str(item[1]).endswith(constrain[0][1]):
                        j = j + 1

                    elif str(item[0]).endswith(constrain[1][0]) and str(item[1]).endswith(constrain[1][1]):
                        j = j + 1

                    if i % 2 == 1 and j == 2:
                        possToRemove.append(possibility)

    for possibility in poss:
        if possibility not in possToRemove:
             possFiltered.append(possibility)

    return possFiltered


def trim(possFrom, nbPossTo):
    try:
        if int(nbPossTo) > len(possFrom):
            raise OverflowError

        indexToAdd = []
        i = 0
        while i < int(nbPossTo):
            rnd = random.randint(0, len(possFrom) - 1)
            if rnd not in indexToAdd:
                indexToAdd.append(rnd)
                i = i + 1

        possTrimmed = []
        for index in indexToAdd:
            possTrimmed.append(possFrom[index])

        return possTrimmed

    except OverflowError:
        print('ERROR: The number given ({input}) is more than the number of possibilities!'.format(input=nbPossTo))
        sys.exit()

    except ValueError:
        print('ERROR: ({input}) needs to be a whole number!'.format(input=nbPossTo))
        sys.exit()


def create_directory():
    timestamp = int(datetime.timestamp(datetime.now()))
    collectionDir = './collection_{id}'.format(id=timestamp)

    if os.path.isdir(collectionDir):
        print('ERROR: The collection already exists!')
        sys.exit()

    else:
        os.mkdir(collectionDir)
        os.mkdir('{dir}/metadata'.format(dir=collectionDir))
        os.mkdir('{dir}/collection'.format(dir=collectionDir))

    return collectionDir


def prog_GUI(i):
    sys.stdout.write('\r'+'{i} Possibilities Produced'.format(i=i))


def img_create(poss, collectionDir):
    try:
        for i in range(len(poss)):

            baseLayer = None
            isBaseLayer = False
            for layer in poss[i]:

                if str(layer[0]).endswith('BASE_LAYER'):
                    #Create the base layer
                    baseLayer = Image.open('{path}/{file}'.format(path=layer[0], file=layer[1]))
                    isBaseLayer = True

            if isBaseLayer:
                for layer in poss[i]:
                    if not str(layer[0]).endswith('BASE_LAYER'):
                        foreLayer = Image.open('{path}/{file}'.format(path=layer[0], file=layer[1]))
                        baseLayer.paste(foreLayer, (0, 0), foreLayer)

            else:
                print('ERROR: No BASE_LAYER has been recognized!')
                sys.exit()
            
            baseLayer.save("{dir}/collection/{i}.png".format(dir=collectionDir, i=i))
            prog_GUI(i + 1)

    except Error as e:
        print(e)

    return collectionDir


def hash_image(path):
    imgHash = hashlib.sha256()
    with open(path,"rb") as f:
        # Read and update hash string value in blocks of 4K
        for block in iter(lambda: f.read(4096),b""):
            imgHash.update(block)

        return imgHash.hexdigest()


def verify_unique_set(collectionDir):
    hashDict = {}
    i = 0
    while True:
        try:
            imgName = "{i}.png".format(i=i)
            imgPath = '{dir}/collection/{img}'.format(dir=collectionDir, img=imgName)
            imgHash = hash_image(imgPath)

            if (imgHash in hashDict):
                hashDict[imgHash][1] += 1
                hashDict[imgHash][0].append(imgName)
            else:
                hashDict[imgHash] = [[imgName], 1]

            i = i + 1

        except FileNotFoundError:
            break
 
    log = []
    is_unique = True
    for item in hashDict.items():
        if item[1][1] > 1:
            is_unique = False
            log.append(item[1][0])

    if is_unique:
        print('\nAll The Possibilities In The Set Are Unique!')

    else:
        if len(log) == 1:
            print("\nNon Unique Possibility Found...")
        else:
            print("\nNon Unique Possibilities Found...")

        for item in log:
            print(item)
        
        sys.exit()


if __name__ == '__main__':

    # add the possibility of a blank layer!!!***

    print('Applying Constrains To The Possibilities...')
    poss = img_poss()
    possFiltered = apply_const(poss, read_const())
    print(len(poss) - len(possFiltered), 'Possibilities Has Been Removed')
    print(len(possFiltered), 'Possibilities Registered')

    print('Trimming Possibilities Registered...')
    possTrimmed = trim(possFiltered, sys.argv[1])

    print(len(possTrimmed), 'Possibilities Ready For Production')

    collectionDir = create_directory()

    print('Beginning Production...')
    verify_unique_set(img_create(possTrimmed, collectionDir))

    # metadata_create(possTrimmed, collectionDir)



