# NAC – NFT Art Creator

A Python program to create NFT art and NFT metadata with support for OpenSea and many other NFT marketplaces.

### [Install](#install) · [Usage](#usage) · [Documentation](#documentation)

The project is under MIT license

---

## Install

### Linux
- Install Python 3:
    - [**Python 3**](https://www.python.org/downloads/source/) (Python v3.9+)

- Install requirements:
    - ```shell
      pip install -r requirements.txt
      ```

### macOS
- Install Python 3:
    - [**Python 3**](https://www.python.org/downloads/macos/) (Python v3.9+)

- Install requirements:
    - ```shell
      pip3 install -r requirements.txt
      ```

### Windows
- Install Python 3:
    - [**Python 3**](https://www.python.org/downloads/windows/) (Python v3.9+)

- Install requirements:
    - ```shell
      pip install -r requirements.txt
      ```

---

## Usage

`Create 10k NFT arts`
### Linux
```shell
python nft_art_creator.py 10000
```
### macOS
```shell
python3 nft_art_creator.py 10000
```

### Windows
```shell
python nft_art_creator.py 10000
```

---

## Documentation

### Add layers
- **The images used must be PNG files**
- **The name of each layer (PNG file) will be the name used for the metadata**
    - For example, if the name of a layer into a subdirectory is red.png, the name used will be "red"
- **To add layers, you need to add them into the LAYERS directory**
    - Place the background layers into the BASE_LAYER directory
    - Place the other layers with theirs respective directories (subdirectories) into the LAYERS directory
    - The name of the subdirectories for each category of layer will be the name used for the metadata
    - For example, the subdirectory "cercle" will be used to describe the layers that are into this directory

### Add Constrains
- **To add or modify constrains, you need to edit the CONST.txt file**
    - An example of a constrain:
        - The cercle 1.png cannot be with the square 1.png
        - cercle 1.png, square 1.png
    - Each part of the constrain is separated by a comma (,)
    - 1 constrain max per line
    - Each constrain contains 4 items:
        - Subdirectory 1
        - File name with extension
        - Subdirectory 2
        - File name with extension


