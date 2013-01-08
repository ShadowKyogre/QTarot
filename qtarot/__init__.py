from os import path

## METADATA ##
APPNAME="QTarot"
APPVERSION="0.5.2"
AUTHOR="ShadowKyogre"
DESCRIPTION="A simple tarot fortune teller."
YEAR="2013"
PAGE="http://shadowkyogre.github.com/QTarot/"
EMAIL="shadowkyogre.public@gmail.com"

### CONSTANTS BEGIN ###
DATA_DIR = path.dirname(path.dirname(__file__))
### CONSTANTS END ###

# implies we're not running this in download and run context
# if this fails
if DATA_DIR == path.dirname(path.dirname(__file__)):
	DATA_DIR_QTAROT = DATA_DIR
else:
	DATA_DIR_QTAROT = path.join(DATA_DIR,'qtarot')

VALIDATORS = path.join(DATA_DIR_QTAROT,'validators')
DECKS = path.join(DATA_DIR_QTAROT,'decks')
LAYOUTS = path.join(DATA_DIR_QTAROT,'layouts')
DECK_DEFS = path.join(DATA_DIR_QTAROT,'deck_defs')
HTMLTPL = path.join(DATA_DIR_QTAROT,'htmltpl')
