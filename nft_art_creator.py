from aifc import Error
from datetime import datetime
import hashlib
import itertools
import json
import os
from PIL import Image
from random import randint, shuffle
import requests
import sqlite3
from sqlite3.dbapi2 import IntegrityError
import sys
import time



BASE_LAYER_PATCH = 'Background'

def db_connection(dbPath):
    """ Create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(dbPath)
        return conn
    except Error as e:
        print(e)

    return conn


def db_option():
    """ Return a string of layers formatted for the database request """
    option = None
    for item in poss[0]:
        layerType = item[0].split('/')[-1]

        if option == None:
            option = layerType + ' text'
        
        else:
            option = option + ', ' + layerType + ' text'

    return option


def create_table(conn):
    """ Create a table from the table statement """

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
    """ Create a database file into the path directory """
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
    # Maybe use # in the file to remove the line to be read!**

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


def rarity_file_create(force):
        if os.path.exists('rarity.json') and not force:
            return

        BASE_PATH = './LAYERS'
        lPaths = layer_root(BASE_PATH)
        freq = {}
        for root in lPaths:
            nbLayers = 0
            for imgLayer in os.listdir(lPaths[root]):
                if imgLayer.endswith('.png'):
                    nbLayers = nbLayers + 1

            freq[lPaths[root][2:]] = float(1 / nbLayers)

        layers = {}
        for root in lPaths:
            layer = {}
            for imgLayer in os.listdir(lPaths[root]):
                if imgLayer.endswith('.png'):
                    layer[imgLayer] = freq[lPaths[root][2:]]

            layers[str(lPaths[root][2:]).split('/')[-1]] = layer

        jsonString = json.dumps(layers, indent=4)
        jsonFile = open("rarity.json", "w")
        jsonFile.write(jsonString)
        jsonFile.close()


def rarity_verify():
    BASE_PATH = './LAYERS'
    lPaths = layer_root(BASE_PATH)
    fileObject = open("rarity.json", "r")
    jsonContent = fileObject.read()
    rarity = json.loads(jsonContent)

    for root in lPaths:
        layer = str(lPaths[root]).split('/')[-1]

        if round(sum(rarity[layer].values()), 2) != 1:
            print('ERROR: The rarity sum of {layer} is not equal to 1!'.format(layer=layer))
            sys.exit()


def get_rarity():
    fileObject = open("rarity.json", "r")
    jsonContent = fileObject.read()
    return json.loads(jsonContent)


def get_nb_rarity(nbPossTo):
    layersRarity = get_rarity()

    layersNb = {}
    for layer in layersRarity:
        layerNb = {}
        for layerName in layersRarity[layer]:
            nb = round(float(layersRarity[layer][layerName]) * int(nbPossTo))
            layerNb[layerName] = nb

        while sum(layerNb.values()) - int(nbPossTo) != 0:
            if 0 in layerNb.values():
                for key, value in layerNb.items():
                    if value == 0:
                        layerNb[key] = value + 1
                        break

            if sum(layerNb.values()) - int(nbPossTo) > 0:
                maxVal = max(layerNb.values())
                for key, value in layerNb.items():
                    if value == maxVal:
                        layerNb[key] = value - 1
                        break

            elif sum(layerNb.values()) - int(nbPossTo) < 0:
                minVal = min(layerNb.values())
                for key, value in layerNb.items():
                    if value == minVal:
                        layerNb[key] = value + 1
                        break

        layersNb[layer] = layerNb

    return layersNb


def trim(possFrom, nbPossTo):
    try:
        if int(nbPossTo) > len(possFrom):
            raise OverflowError

        elif int(nbPossTo) < 20:
            raise ValueError

        possTrimmed = []
        possDiscarted = []
        tmpPossTrimmed = []
        tmpPossDiscarted = []

        i = 0
        while len(possTrimmed) != int(nbPossTo):
            if i >= 10:
                break

            possTrimmed = []
            possDiscarted = []

            layersNb = get_nb_rarity(nbPossTo)
            shuffle(possFrom)

            for poss in possFrom:
                isAvailable = True
                
                for item in poss:
                    if layersNb[str(item[0]).split('/')[-1]][item[1]] == 0:
                        isAvailable = False
                        break

                if isAvailable:
                    if poss not in possTrimmed:
                        possTrimmed.append(poss)
                    for item in poss:
                        layersNb[str(item[0]).split('/')[-1]][item[1]] = layersNb[str(item[0]).split('/')[-1]][item[1]] - 1

                else:
                    possDiscarted.append(poss)

            tmpPossTrimmed.append(possTrimmed)
            tmpPossDiscarted.append(possDiscarted)

            i = i + 1

        maxPoss = [0, None, None]
        for i in range(len(tmpPossTrimmed)):
            length = len(tmpPossTrimmed[i])
            if length > maxPoss[0]:
                maxPoss[0] = length
                maxPoss[1] = tmpPossTrimmed[i]
                maxPoss[2] = tmpPossDiscarted[i]

        if maxPoss[0] < int(nbPossTo):
            print('Cannot rapidly find a solution with the current rarity settings')
            print('You currently have {poss} possibilities registered'.format(poss=maxPoss[0]))
            diff = int(nbPossTo) - maxPoss[0]
            userInput = input('Do you want to add {diff} random possibilities to complete the set of {nb}? (Y/N) '.format(nb=nbPossTo, diff=diff)).capitalize()

            if userInput in ['Y', 'YES']:
                for i in range(int(nbPossTo) - maxPoss[0]):
                    maxPoss[1].append(maxPoss[2][i])

            else:
                userInput = input('Do you want to continue to the production? (Y/N) ').capitalize()
                if userInput not in ['Y', 'YES']:
                    sys.exit()

        # Shake the possibilities to add randomness
        shuffle(maxPoss[1])

        return maxPoss[1]

    except OverflowError:
        print('ERROR: The number given ({input}) is more than the number of possibilities!'.format(input=nbPossTo))
        sys.exit()

    except ValueError:
        print('ERROR: ({input}) needs to be a whole number higher than 20!'.format(input=nbPossTo))
        sys.exit()


def pad_start(val, length):
    return str(val).rjust(length, '0')


def metadata_create(poss, collectionDir, cID):
    dbPath = '{dir}/metadata.db'.format(dir=collectionDir)
    collectionPath = '{dir}/collection'.format(dir=collectionDir)
    metadataPath = '{dir}/metadata'.format(dir=collectionDir)
    create_db(dbPath)

    for item in poss:
        data = []
        for layer in item:
            data.append(str(layer[1]).replace('.png', ''))

        db_insert(dbPath, data)

    layerRatio = {}
    options = db_option().replace(' text', '')
    options = options.split(', ')
    for option in options:
        layerRatio[option] = []

        query = '''SELECT {layer}, (1.0 * COUNT(*)) / 
                  (SELECT COUNT(*) FROM metadata)  AS POURCENTAGE 
                  FROM metadata GROUP BY {layer};'''.format(layer=option)

        for layer in db_query(dbPath, query):
            layerImage = [layer[0], layer[1]]
            layerRatio[option].append(layerImage)

    valid_metadata = ['dna', 'rna', 'name', 'description', 'image', 'timestamp', 'attributes']
    var_attr = ['Strength', 'Stamina', 'Dexterity', 'Agility', 'Intelligence', 
                'Emotion', 'Determined', 'Friendly', 'Hard-working', 'Humble', 'Generous', 
                'Punctual', 'Brave', 'Loyal', 'Perseveres', 'Honest', 'Sincere', 'Kind']

    i = 0
    for item in os.listdir(collectionPath):
        if str(item).endswith('.png'):
            with open('metadata_template.json', 'r') as file:
                json_data = json.load(file)
                rarityRatio = 1

                # Add layers as trait_type in the metadata file
                j = 0
                lPath = layer_root('./LAYERS')
                for path in lPath:
                    traitType = str(lPath[path]).split('/')[-1]
                    query = '''SELECT {layer} FROM metadata WHERE id={id};'''.format(layer=traitType, id=i+1)
                    val = str(db_query(dbPath, query)[0][0])

                    for layer in layerRatio[traitType]:
                        if layer[0] == val:
                            rarityRatio = float(rarityRatio) * float(layer[1])

                    if traitType == 'BASE_LAYER':
                        traitType = BASE_LAYER_PATCH   

                    json_data['attributes'].insert(j, {"trait_type": traitType, "value": val})
                    j = j + 1

                timestamp = int(datetime.timestamp(datetime.now()))
                life = randint(3, 100)
                for metadata in json_data:
                    if metadata not in valid_metadata:
                        print('ERROR: The metadata attribute ({attr}) is not supported at this time!'.format(attr=metadata))
                        sys.exit()

                    elif metadata == 'dna':
                        json_data[metadata] = ''

                    elif metadata == 'rna':
                        json_data[metadata] = hash_file(collectionPath + '/' + item)

                    elif metadata == 'name':
                        json_data[metadata] = str(json_data[metadata]) + ' {i}'.format(i=i)

                    elif metadata == 'description':
                        json_data[metadata] = json_data['name'] + ' has a rarity of ' + '{:.4f}%. '.format(rarityRatio * 100) + json_data[metadata]

                    elif metadata == 'image':
                        json_data[metadata] = 'ipfs://' + cID + '/{i}.png'.format(i=i)

                    elif metadata == 'timestamp':
                        json_data[metadata] = timestamp

                    elif metadata == 'attributes':
                        for attr in json_data[metadata]:
                            if attr['trait_type'] in var_attr:
                                attr['value'] = randint(0, 100)

                            elif attr['trait_type'] == 'Life':
                                attr['value'] = life

                            elif attr['trait_type'] == 'Birthday':
                                yearTime = 31557600
                                aging = randint(1, (life - 1))
                                bdTime = timestamp - (yearTime * aging) + randint(0, yearTime)
                                attr['value'] = bdTime

            fileName = '{id}.json'.format(id=pad_start(i, 64))
            with open('{dir}/{file}'.format(dir=metadataPath, file=fileName), 'w') as file:
                json.dump(json_data, file, indent=2)

            file.close()

            with open('{dir}/{file}'.format(dir=metadataPath, file=fileName), 'r') as file:
                json_data = json.load(file)

                for metadata in json_data:
                    if metadata == 'dna':
                        json_data[metadata] = hash_file(metadataPath + '/' + fileName)
                        break

            with open('{dir}/{file}.json'.format(dir=metadataPath, file=pad_start(i, 64)), 'w') as file:
                json.dump(json_data, file, indent=2)

            file.close()
            i = i + 1

    return collectionDir


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
                    baseLayer = Image.open('{path}/{file}'.format(path=layer[0], file=layer[1])).convert('RGBA')
                    isBaseLayer = True

            if isBaseLayer:
                for layer in poss[i]:
                    if not str(layer[0]).endswith('BASE_LAYER'):
                        foreLayer = Image.open('{path}/{file}'.format(path=layer[0], file=layer[1])).convert('RGBA')
                        baseLayer.paste(foreLayer, (0, 0), foreLayer)

            else:
                print('ERROR: No BASE_LAYER has been recognized!')
                sys.exit()
            
            baseLayer.save("{dir}/collection/{i}.png".format(dir=collectionDir, i=i))
            prog_GUI(i + 1)

    except Error as e:
        print(e)

    return collectionDir


def hash_file(path):
    fileHash = hashlib.sha256()
    with open(path,"rb") as f:
        # Read and update hash string value in blocks of 4K
        for block in iter(lambda: f.read(4096),b""):
            fileHash.update(block)

        return fileHash.hexdigest()


def verify_unique_set(collectionDir):
    hashDict = {}
    i = 0
    while True:
        try:
            imgName = "{i}.png".format(i=i)
            imgPath = '{dir}/collection/{img}'.format(dir=collectionDir, img=imgName)
            imgHash = hash_file(imgPath)

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


def ipfs_upload(collectionDir, nbFiles, subdirectory, fileType):
    files = []
    for i in range(int(nbFiles)):
        if fileType == 'json':
            i = pad_start(i, 64)

        files.append(('file', ('{dir}/{sub}/{i}.{type}'.format(dir=collectionDir, sub=subdirectory, i=i, type=fileType), open('{dir}/{sub}/{i}.{type}'.format(dir=collectionDir, sub=subdirectory, i=i, type=fileType), "rb"))))
  
    ipfs_url = "https://ipfs.infura.io:5001/api/v0/add"
    response = requests.post(url=ipfs_url, files=files)

    if int(response.status_code) == 200:
        print('Uploaded Successfully to IPFS!')
        textRaw = response.text.replace('\n', '')
        dictFormat = textRaw.split('}')[-3]  + '}'
        jsonURL = json.loads(dictFormat)
        cID = jsonURL['Hash']
        return cID

    else:
        print('ERROR: {response}'.format(response=response.status_code))
        sys.exit()


if __name__ == '__main__':
    # add the possibility of a blank layer!!!***

    for arg in sys.argv[1:]:
        if arg == '-f':
            rarity_file_create(force=True)

    rarity_file_create(force=False)
    rarity_verify()
    print('Applying Constrains To The Possibilities...')
    poss = img_poss()
    possFiltered = apply_const(poss, read_const())
    print(len(poss) - len(possFiltered), 'Possibilities Has Been Removed')
    time.sleep(1)
    print(len(possFiltered), 'Possibilities Registered')
    time.sleep(1)
    print('Trimming Possibilities Registered...')
    possTrimmed = trim(possFiltered, sys.argv[1])
    print(len(possTrimmed), 'Possibilities Ready For Production')
    collectionDir = create_directory()
    print('Beginning Production...')
    verify_unique_set(img_create(possTrimmed, collectionDir))

    cID = None
    isIPFS = input('Do you want to upload the collection directory to IPFS? (Y/N) ').capitalize()
    if isIPFS in ['YES', 'Y']:
        isAccept = input('By continuing, you are aware and you accept to take all the risks of non pinned data stored to IPFS node services. Do you wish to continue? (Y/N) ').capitalize()
        if isAccept in ['YES', 'Y']:
            cID = ipfs_upload(collectionDir, sys.argv[1], 'collection', 'png')
        else:
            sys.exit()

    else:
        cID = input('Please upload your collection directory to an IPFS pinning service and paste the CID of the directory here: ')

    metadata_create(possTrimmed, collectionDir, cID)

    cID = None
    isIPFS = input('Do you want to upload the metadata directory to IPFS? (Y/N) ').capitalize()
    if isIPFS in ['YES', 'Y']:
        isAccept = input('By continuing, you are aware and you accept to take all the risks of non pinned data stored to IPFS node services. Do you wish to continue? (Y/N) ').capitalize()
        if isAccept in ['YES', 'Y']:
            cID = ipfs_upload(collectionDir, sys.argv[1], 'metadata', 'json')
        else:
            sys.exit()

    else:
        cID = input('Please upload your metadata directory to an IPFS pinning service and paste the CID of the directory here: ')

    print('Metadata CID:', cID)

    # Create the contract solidity file!!