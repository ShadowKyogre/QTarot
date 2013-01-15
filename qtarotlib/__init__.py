from os import path

## METADATA ##
APPNAME="QTarot"
APPVERSION="0.5.8"
AUTHOR="ShadowKyogre"
DESCRIPTION="A simple tarot fortune teller."
YEAR="2013"
PAGE="http://shadowkyogre.github.com/QTarot/"
EMAIL="shadowkyogre.public@gmail.com"

### CONSTANTS BEGIN ###
DATA_DIR = path.dirname(path.dirname(__file__))
### CONSTANTS END ###

VALIDATORS = path.join(DATA_DIR,'validators')
DECKS = path.join(DATA_DIR,'decks')
LAYOUTS = path.join(DATA_DIR,'layouts')
DECK_DEFS = path.join(DATA_DIR,'deck_defs')
HTMLTPL = path.join(DATA_DIR,'htmltpl')
