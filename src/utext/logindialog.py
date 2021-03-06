#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of utext
#
# Copyright (C) 2012-2016 Lorenzo Carbonell
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

from gi.repository import Gtk
from gi.repository import WebKit
from . import comun


class LoginDialog(Gtk.Dialog):
    def __init__(self, width, height, url, isgoogle=False):
        self.code = None
        Gtk.Dialog.__init__(self)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_title(comun.APP)
        self.set_icon_from_file(comun.ICON)
        self.isgoogle = isgoogle
        #
        vbox = Gtk.VBox(spacing=5)
        self.get_content_area().add(vbox)
        hbox1 = Gtk.HBox()
        vbox.pack_start(hbox1, True, True, 0)
        #
        self.scrolledwindow1 = Gtk.ScrolledWindow()
        self.scrolledwindow1.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scrolledwindow1.set_shadow_type(Gtk.ShadowType.IN)
        hbox1.pack_start(self.scrolledwindow1, True, True, 0)
        #
        self.viewer = WebKit.WebView()
        self.scrolledwindow1.add(self.viewer)
        self.scrolledwindow1.set_size_request(width, height)
        self.viewer.connect('navigation-policy-decision-requested',
                            self.on_navigation_requested)
        self.viewer.open(url)
        self.code = None
        self.uid = None
        #
        self.show_all()

    # ###################################################################
    # ########################BROWSER####################################
    # ###################################################################
    def on_navigation_requested(self, view, frame, req, nav, pol):
        try:
            uri = req.get_uri()
            print('=========================================')
            print(uri)
            print('=========================================')
            if self.isgoogle:
                pos = uri.find('http://localhost/?code=')
                if pos > -1:
                    self.code = uri.split('=')[1]
                    self.hide()
            else:
                pos = uri.find('http://localhost/?oauth_token=')
                if pos > -1:
                    self.code, self.uid = (uri[30:]).split('&')
                    self.hide()
        except Exception as e:
            print(e)
            print('Error')
    # ###################################################################
    # ########################ACTIONS####################################
    # ###################################################################

if __name__ == '__main__':
    ld = LoginDialog('http://www.google.com')
    ld.run()
