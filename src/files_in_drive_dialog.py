#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# files_in_drive_dialog.py
#
# This file is part of utext
#
# Copyright (C) 2016
# Lorenzo Carbonell Cerezo <lorenzo.carbonell.cerezo@gmail.com>
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
from gi.repository import Gtk
from gi.repository import Gdk
import comun
from comun import _


class FilesInDriveDialog(Gtk.Dialog):
    def __init__(self, files):
        #
        Gtk.Dialog.__init__(
            self,
            'uText | '+_('select file from Dropbox'),
            None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
             Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.connect('close', self.close_application)
        self.set_icon_from_file(comun.ICON)
        #
        vbox0 = Gtk.VBox(spacing=5)
        vbox0.set_border_width(5)
        self.get_content_area().add(vbox0)
        frame1 = Gtk.Frame()
        vbox0.pack_start(frame1, False, True, 1)
        table1 = Gtk.Table(1, 2, False)
        frame1.add(table1)
        label1 = Gtk.Label(_('Select file')+':')
        label1.set_alignment(0, 0.5)
        table1.attach(label1, 0, 1, 0, 1, xpadding=5, ypadding=5)
        self.store = Gtk.ListStore(str, object)
        for afile in files:
            self.store.append([afile['name'], afile])
        self.tree = Gtk.TreeView(self.store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(None, renderer, text=0)
        self.tree.append_column(column)
        self.tree.set_headers_visible(False)
        table1.attach(self.tree, 1, 2, 0, 1, xpadding=5, ypadding=5)
        #
        self.show_all()

    def get_selected(self):
        select = self.tree.get_selection()
        if select:
            model, treeiter = select.get_selected()
            return model[treeiter][1]
        return None

    def close_application(self, widget, event):
        self.hide()

    def close_ok(self):
        pass

if __name__ == "__main__":
    cm = FilesInDriveDialog([
        "En un lugar de la mancha 1",
        "En un lugar de la mancha 1",
        "En un lugar de la mancha 1",
        "En un lugar de la mancha 1",
        "En un lugar de la mancha 1",
        ])
    if cm.run() == Gtk.ResponseType.ACCEPT:
            print(cm.get_selected())
    cm.hide()
    cm.destroy()
    exit(0)
