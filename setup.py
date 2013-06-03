from distutils.core import setup
import py2exe

setup(
    name = "Template Emailer",
    version = '0.4',
    windows = [
        {
            'script': 'main.py',
        }
               ],
    options = {
        'py2exe': {
            'packages':'encodings',
            'includes':'cairo, pango, pangocairo, atk, gobject, gio',
            }
        },
    data_files = [
        'main.db',
        'config.ini'
        ]
    )
