from distutils.core import setup
from distutils.command.install import install as _install
from distutils import log
from stat import ST_ATIME, ST_MTIME, S_IMODE, ST_MODE
import os, glob, sys
from qtarotlib import APPNAME,APPVERSION,AUTHOR,DESCRIPTION,YEAR,PAGE,EMAIL

# http://mammique.net/distutils_setup/
if sys.version_info < (3,0,0):
	print("Python 3.x is required!",file=sys.stderr)
	exit(1)

class install(_install):
	description = """Install and set constants"""
	user_options = _install.user_options

	def initialize_options(self):
		self.root = None
		self.install_data = None
		_install.initialize_options(self)

	def finalize_options(self):
		_install.finalize_options(self)

	def run (self):
		_install.run(self)

		# Rewrite with constants if needed
		for f in self.get_outputs():
			# If is package __init__.py file holding some constants
			if os.path.basename(f) == '__init__.py':
				script = open(f, encoding='utf-8')
				content = script.read()
				script.close()
				const_begin = content.find('### CONSTANTS BEGIN ###')
				const_end   = content.find('### CONSTANTS END ###')

				# If needs constants
				if (const_begin != -1) and (const_end != -1):
					log.info("Setting constants of %s" % f)

					at = os.stat(f) # Store attributes

					if self.install_data:
						replace_me = os.path.join(self.install_data,'share/qtarot')
					elif self.prefix:
						replace_me = os.path.join(self.prefix,'share/qtarot')
					if self.root[-1] == '/':
						consts = [['DATA_DIR', replace_me.replace(self.root[:-2],'')]]
					else:
						consts = [['DATA_DIR', replace_me.replace(self.root,'')]]
					script = open(f, 'w', encoding='utf-8')
					script.write(content[:const_begin] + \
								 "### CONSTANTS BEGIN ###")

					for const in consts:
						script.write("\n{} = '{}'".format(const[0], const[1]))
					script.write("\n" + content[const_end:])
					script.close()

					# Restore attributes
					os.utime(f, (at[ST_ATIME], at[ST_MTIME]))
					os.chmod(f, S_IMODE(at[ST_MODE]))

def globby_decks():
	decks=glob.glob(os.path.join('decks','*'))
	file_pairs = []
	for d in decks:
		file_pairs.append(('share/qtarot/{}'.format(d),
							glob.glob(os.path.join(d,'*'))))
	return file_pairs

data_files = [('share/qtarot/validators',glob.glob(os.path.join('validators', '*'))),
  		  ('share/qtarot/deck_defs',glob.glob(os.path.join('deck_defs', '*'))),
		  ('share/qtarot/htmltpl',glob.glob(os.path.join('htmltpl', '*'))),
		  ('share/qtarot/layouts',glob.glob(os.path.join('layouts','*'))),
		  ('share/applications',['QTarot.desktop']),
		  ('share/icons/hicolor/scalable/apps', ['hicolor/scalable/apps/qtarot.svg'])]
data_files.extend(globby_decks())

setup(
	name = APPNAME,
	version = APPVERSION,
	author = AUTHOR,
	author_email = EMAIL,
	description = DESCRIPTION,
	url = PAGE,
	packages = ['qtarotlib'],
	cmdclass={'install': install},
	data_files = data_files,
	scripts=['qtarot.py']
)

