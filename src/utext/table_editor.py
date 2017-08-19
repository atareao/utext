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
from gi.repository import Pango
#from . import comun
#from .comun import _
_ = str

def set_margin(widget, margin):
    widget.set_margin_top(margin)
    widget.set_margin_bottom(margin)
    widget.set_margin_left(margin)
    widget.set_margin_right(margin)
    if type(widget) == Gtk.Grid:
        widget.set_column_spacing(margin)
        widget.set_row_spacing(margin)


class TableEditorDialog(Gtk.Dialog):
    def __init__(self, parent, rows, columns):
        #
        Gtk.Dialog.__init__(self,
                            'uText | ' + _('Table Editor'),
                            parent,
                            Gtk.DialogFlags.MODAL |
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                             Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.connect('close', self.close_application)
        #self.set_icon_from_file(comun.ICON)

        frame = Gtk.Frame()
        set_margin(frame, 5)
        self.get_content_area().add(frame)

        self.grid = Gtk.Grid()
        set_margin(self.grid, 5)
        frame.add(self.grid)

        label1 = Gtk.Label(_('Rows'))
        label1.set_alignment(0, 0.5)
        self.grid.attach(label1, 0, 0, 1, 1)

        label2 = Gtk.Label(_('Columns'))
        label2.set_alignment(0, 0.5)
        self.grid.attach(label2, 1, 0, 1, 1)

        self.rows = Gtk.SpinButton.new_with_range(1.0, 100.0, 1.0)
        self.rows.set_value(rows)
        self.rows.connect('value-changed', self.on_rows_or_columns_changed)
        self.grid.attach(self.rows, 0, 1, 1, 1)

        self.columns = Gtk.SpinButton.new_with_range(1.0, 100.0, 1.0)
        self.columns.set_value(columns)
        self.columns.connect('value-changed', self.on_rows_or_columns_changed)
        self.grid.attach(self.columns, 1, 1, 1, 1)

        # self.sheet_view = Gtk.TreeView()
        # self.sheet_view.set_headers_visible(False)
        self.sheet_view = None
        self.create_sheet_model(rows, columns)
        # self.grid.attach(self.sheet_view, 0, 2, 2, 1)

        self.show_all()

    def on_rows_or_columns_changed(self, widget):
        rows = self.rows.get_value_as_int()
        columns = self.columns.get_value_as_int()
        self.create_sheet_model(rows, columns)
        self.show_all()

    def close_application(self, widget, event):
        self.hide()

    def close_ok(self):
        pass

    def create_sheet_model(self, rows, columns):
        print(10)
        if self.sheet_view is not None:
            self.grid.remove(self.sheet_view)
        self.sheet_view = Gtk.TreeView()
        self.sheet_view.set_headers_visible(False)
        self.sheet_model = Gtk.ListStore(*([str] * (columns + 1)))
        self.sheet_view.set_model(self.sheet_model)
        print(20)
        for i in range(columns + 1):
            # cellrenderer to render the text
            cell = Gtk.CellRendererText()
            cell.set_property('editable', i != 0)
            cell.connect('edited', self.on_cell_edited, i)
            # the text in the first column should be in boldface
            if i == 0:
                cell.props.weight_set = True
                cell.props.weight = Pango.Weight.BOLD
            # the column is created
            col = Gtk.TreeViewColumn(i, cell, text=i)
            # and it is appended to the treeview
            self.sheet_view.append_column(col)
        for i in range(rows + 1):
            if i == 0:
                data = [_('Caption {0}').format(x) for x in range(columns + 1)]
                data[0] = _('Captions')
                print(data)
            else:
                data = [_('Row {0}').format(i)] + [''] * columns
            self.sheet_model.append((data))
        self.grid.attach(self.sheet_view, 0, 2, 2, 1)

    def on_cell_edited(self, widget, path, text, i):
        self.sheet_model[path][i] = text

    def get_table(self):
        rows = self.rows.get_value_as_int()
        columns = self.columns.get_value_as_int()
        table_string = ''
        for row in range(0, rows + 1):
            row_string = '|'
            for column in range(1, columns + 1):
                row_string += self.sheet_model[row][column] + '|'
            row_string += '\n'
            if row == 0:
                row_string += '|---' * (columns) + '|\n'
            table_string += row_string
        return table_string
        '''
        while iter is not None:
            if contador == 0:
                defrows = '|---' * columns + '|\n'
                pass
            print(self.sheet_model[iter])

            print(2)
            iter = self.sheet_model.iter_next(iter)
        '''


if __name__ == "__main__":
    cm = TableEditorDialog(None, 5, 5)
    if cm.run() == Gtk.ResponseType.ACCEPT:
            cm.close_ok()
            print(cm.rows.get_value_as_int())
            print(cm.columns.get_value_as_int())
    cm.hide()
    cm.destroy()
    exit(0)
