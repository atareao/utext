#! /usr/bin/python
# -*- coding: utf-8 -*-
#
# comun.py
#
# Copyright (C) 2012 - 2016 Lorenzo Carbonell
# lorenzo.carbonell.cerezo@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#

import os
import locale
import gettext


def is_package():
    return __file__.find('src') < 0

PARAMS = {'version': '',
          'last_dir': '',
          'last_filename': '',
          'filename1': '',
          'filename2': '',
          'filename3': '',
          'filename4': '',
          'width': 900,
          'height': 600,
          'toolbar': True,
          'statusbar': True,
          'markdown_editor.show_line_numbers': True,
          'markdown_editor.show_line_marks': True,
          'markdown_editor.spaces': True,
          'markdown_editor.tab_width': 4,
          'markdown_editor.auto_indent': True,
          'markdown_editor.highlight_current_line': True,
          'markdown_editor.font': 'ubuntu 14',
          'html_viewer.show_line_numbers': True,
          'html_viewer.show_line_marks': True,
          'html_viewer.spaces': True,
          'html_viewer.tab_width': 4,
          'html_viewer.auto_indent': True,
          'html_viewer.highlight_current_line': True,
          'html_viewer.preview_theme':
          '/opt/extras.ubuntu.com/utext/share/utext/themes/default',
          'autosave': False,
          'spellcheck': False,
          'mathjax': False,
          }


APP = 'utext'
APP_CONF = APP + '.conf'
APPNAME = 'uText'
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config')
CONFIG_APP_DIR = os.path.join(CONFIG_DIR, APP)
CONFIG_FILE = os.path.join(CONFIG_APP_DIR, APP_CONF)
TOKEN_FILE = os.path.join(CONFIG_APP_DIR, 'token')
#########################################
# check if running from source
if is_package():
    ROOTDIR = '/opt/extras.ubuntu.com/utext/share/'
    LANGDIR = os.path.join(ROOTDIR, 'locale-langpack')
    APPDIR = os.path.join(ROOTDIR, APP)
    THEMESDIR = os.path.join(APPDIR, 'themes')
    ICONDIR = os.path.join(APPDIR, 'icons')
    SOCIALDIR = os.path.join(APPDIR, 'social')
    CHANGELOG = os.path.join(APPDIR, 'changelog')
else:
    ROOTDIR = os.path.dirname(__file__)
    LANGDIR = os.path.normpath(os.path.join(ROOTDIR, '../po'))
    THEMESDIR = os.path.normpath(os.path.join(ROOTDIR, './themes'))
    ICONDIR = os.path.normpath(os.path.join(ROOTDIR, '../data/icons'))
    SOCIALDIR = os.path.normpath(os.path.join(ROOTDIR, '../data/social'))
    DEBIANDIR = os.path.normpath(os.path.join(ROOTDIR, '../debian'))
    CHANGELOG = os.path.join(DEBIANDIR, 'changelog')
    APPDIR = ROOTDIR
####
f = open(CHANGELOG, 'r')
line = f.readline()
f.close()
pos = line.find('(')
posf = line.find('-', pos)
VERSION = line[pos+1:posf].strip()
if not is_package():
    VERSION = VERSION + '-src'
####
ICON = os.path.join(ICONDIR, 'utext.svg')
current_locale, encoding = locale.getdefaultlocale()
try:
    language = gettext.translation(APP, LANGDIR, [current_locale])
    language.install()
    _ = language.gettext
except:
    _ = str
