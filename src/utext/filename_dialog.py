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

import gi
try:
    gi.require_version('Gtk', '3.0')
except Exception as e:
    print(e, 'Repository version required not present')
    exit(-1)
from gi.repository import Gtk
from . import comun
from .comun import _


class FilenameDialog(Gtk.Dialog):
    def __init__(self, service):
        #
        Gtk.Dialog.__init__(
            self,
            'uText | ' + _('set filename for %s' % (service)),
            None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
             Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        # self.set_size_request(400, 230)
        self.connect('close', self.close_application)
        self.set_icon_from_file(comun.ICON)
        vbox0 = Gtk.VBox(spacing=5)
        vbox0.set_border_width(5)
        self.get_content_area().add(vbox0)
        frame1 = Gtk.Frame()
        vbox0.pack_start(frame1, False, True, 1)
        table1 = Gtk.Table(2, 2, False)
        frame1.add(table1)
        label0 = Gtk.Label(_('Set filename for %s' % (service)) + ':')
        label0.set_alignment(0, 0.5)
        table1.attach(label0, 0, 2, 0, 1, xpadding=5, ypadding=5)
        label1 = Gtk.Label(_('Filename') + ':')
        label1.set_alignment(0, 0.5)
        table1.attach(label1, 0, 1, 1, 2, xpadding=5, ypadding=5)
        self.filename = Gtk.Entry()
        table1.attach(self.filename, 1, 2, 1, 2, xpadding=5, ypadding=5)
        self.show_all()

    def get_filename(self):
        return self.filename.get_text()

    def close_application(self, widget, event):
        self.hide()

    def close_ok(self):
        pass


if __name__ == "__main__":
    cm = FilenameDialog('Dropbox')
    if cm.run() == Gtk.ResponseType.ACCEPT:
            cm.close_ok()
            print(cm.get_filename())
    cm.hide()
    cm.destroy()
    exit(0)
