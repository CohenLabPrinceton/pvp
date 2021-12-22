# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import mock
from pathlib import Path
import shutil
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../pvp'))
sys.path.insert(0, os.path.abspath('.'))

# copy hardware assets at build time
root_assets = Path('../assets').resolve()
docs_assets = Path('./assets').resolve()
for asset_file in root_assets.glob('**/*'):
    if asset_file.is_dir():
        continue
    new_file = docs_assets / asset_file.relative_to(root_assets)
    new_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(asset_file), str(new_file))


sys.modules['Shiboken'] = mock.Mock()
sys.modules['PySide2.QtMultimedia'] = mock.Mock()


# -- Project information -----------------------------------------------------

project = 'PVP'
copyright = '2020, jonny saunders et al'
author = 'jonny saunders et al'

# the short X.Y version
version = '0.2'
# the full version, includeing alpha/beta/rc/rags
release = '0.2.0'


# -- General configuration ---------------------------------------------------

master_doc = "index"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',     # automatically document packages
    'sphinx.ext.autosummary', # create summary tables on api doc pages
    'sphinx.ext.intersphinx', # include documentation from other projects
    'sphinx.ext.todo',        # todo directive
    'sphinx.ext.viewcode',
    'sphinx.ext.inheritance_diagram',
    # 'sphinx_automodapi.automodapi',
    'sphinxcontrib.napoleon', # parse google style docstrings
    'autodocsumm',
    'myst_perser',   # support markdown
    'sphinx_sass' # support sass/scss
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []



#####
# Napoleon
# https://sphinxcontrib-napoleon.readthedocs.io/en/latest/sphinxcontrib.napoleon.html#sphinxcontrib.napoleon.Config
napoleon_google_docstring = True
# napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
# napoleon_include_special_with_doc = False
# napoleon_use_admonition_for_examples = False
# napoleon_use_admonition_for_notes = False
# napoleon_use_admonition_for_references = False
# napoleon_use_ivar = False
# napoleon_use_param = True
# napoleon_use_rtype = True
# napoleon_use_keyword = True
# napoleon_custom_sections = None

### 
# Autodoc

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': True,
    'member-order': 'bysource',
    'autosummary': True
}
autoclass_content = "both"
autosummary_generate = True

autodoc_mock_imports = ['pigpio', "Shiboken"]


######
# Todo extension

todo_include_todos = True



########
# Intersphinx

intersphinx_mapping = {'python': ('https://docs.python.org/3', None),
                       'PySide2': ('https://doc.qt.io/qtforpython/', None),
                       #'pandas': ('http://pandas.pydata.org/pandas-docs/stable/', None),
                       #'zmq': ('https://pyzmq.readthedocs.io/en/latest/', None),
                       #'tornado': ('https://www.tornadoweb.org/en/stable/', None),
                       'pyqtgraph': ('https://pyqtgraph.readthedocs.io/en/latest/', None),
                       'numpy': ('https://numpy.readthedocs.io/en/latest/', None),
                       #'scipy': ('https://docs.scipy.org/doc/scipy/reference/', None),
                       }


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
sass_configs = [
    {
    'entry':'_src/sass/theme.sass',
    'output':'_static/pvp_theme.css'
    }
]
html_style="pvp_theme.css"
html_logo="assets/images/pvp_logo_only.png"
html_favicon="assets/images/pvp_logo_favicon.png"

html_theme_options = {
    'canonical_url': '',
    'analytics_id': 'UA-XXXXXXX-1',  #  Provided by Google in your dashboard
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': 'white',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".

html_extra_path = ['assets']