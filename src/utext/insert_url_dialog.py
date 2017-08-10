#!/usr/bin/env python3
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
    print(e)
    exit(-1)
from gi.repository import Gtk
from . import comun
from .comun import _


def set_margin(widget, margin):
    widget.set_margin_top(margin)
    widget.set_margin_bottom(margin)
    widget.set_margin_left(margin)
    widget.set_margin_right(margin)
    if type(widget) == Gtk.Grid:
        widget.set_column_spacing(margin)
        widget.set_row_spacing(margin)


class InsertUrlDialog(Gtk.Dialog):
    def __init__(self, parent):
        #
        Gtk.Dialog.__init__(self,
                            'uText | ' + _('Insert Url'),
                            parent,
                            Gtk.DialogFlags.MODAL |
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                             Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.connect('close', self.close_application)
        self.set_icon_from_file(comun.ICON)

        frame = Gtk.Frame()
        set_margin(frame, 5)
        self.get_content_area().add(frame)

        grid = Gtk.Grid()
        set_margin(grid, 5)
        frame.add(grid)

        label1 = Gtk.Label(_('Alt text') + ':')
        label1.set_alignment(0, 0.5)
        grid.attach(label1, 0, 0, 1, 1)

        self.alt_text = Gtk.Entry()
        grid.attach(self.alt_text, 1, 0, 1, 1)

        label2 = Gtk.Label(_('Url') + ':')
        label2.set_alignment(0, 0.5)
        grid.attach(label2, 0, 1, 1, 1)

        self.url = Gtk.Entry()
        grid.attach(self.url, 1, 1, 1, 1)
        #
        self.show_all()

    def close_application(self, widget, event):
        self.hide()

    def close_ok(self):
        pass


if __name__ == "__main__":
    cm = InsertUrlDialog()
    if cm.run() == Gtk.ResponseType.ACCEPT:
            cm.close_ok()
            print(cm.alt_text.get_text())
            print(cm.url.get_text())
    cm.hide()
    cm.destroy()
    exit(0)
