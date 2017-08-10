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
    exit(1)
from gi.repository import Gtk

from . import comun
from .comun import _


class FilesInCloudDialog(Gtk.Dialog):
    def __init__(self, service, files):
        #
        Gtk.Dialog.__init__(
            self,
            'uText | ' + _('select file from %s' % (service)),
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
        table1 = Gtk.Table(2, 1, False)
        frame1.add(table1)
        label1 = Gtk.Label(_('Select file') + ':')
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
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.tree)
        scrolled_window.set_min_content_height(100)
        table1.attach(scrolled_window, 0, 1, 1, 2, xpadding=5, ypadding=5)
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
    files = []
    file1 = {'name': 'test1'}
    file2 = {'name': 'test2'}
    file3 = {'name': 'test3'}
    file4 = {'name': 'test4'}
    file5 = {'name': 'test5'}
    files.append(file1)
    files.append(file2)
    files.append(file3)
    files.append(file4)
    files.append(file5)
    cm = FilesInCloudDialog('Drive', files)
    if cm.run() == Gtk.ResponseType.ACCEPT:
            print(cm.get_selected())
    cm.hide()
    cm.destroy()
    exit(0)
