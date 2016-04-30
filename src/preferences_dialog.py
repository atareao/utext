#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# preferences_dialog.py
#
# This file is part of PushBullet-Indicator
#
# Copyright (C) 2014
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
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
import comun
import os
import shutil
import glob
import webbrowser
from comun import _
from configurator import Configuration


def get_selected_value_in_combo(combo):
    model = combo.get_model()
    return model.get_value(combo.get_active_iter(), 1)


def select_value_in_combo(combo, value):
    model = combo.get_model()
    for i, item in enumerate(model):
        if value == item[1]:
            combo.set_active(i)
            return
    combo.set_active(0)


def get_themes():
    themes = []
    personal_dir = os.path.expanduser('~/.config/utext/themes')
    if os.path.exists(personal_dir):
        for dirname, dirnames, filenames in os.walk(personal_dir):
            for subdirname in dirnames:
                themes.append([subdirname, os.path.join(dirname, subdirname)])
    installation_dir = '/opt/extras.ubuntu.com/utext/share/utext/themes'
    if os.path.exists(installation_dir):
        for dirname, dirnames, filenames in os.walk(installation_dir):
            for subdirname in dirnames:
                themes.append([subdirname, os.path.join(dirname, subdirname)])
    return themes


class PreferencesDialog(Gtk.Dialog):
    def __init__(self):
        #
        Gtk.Dialog.__init__(self, 'uText | '+_('Preferences'),None,Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        #self.set_size_request(400, 230)
        self.connect('close', self.close_application)
        self.set_icon_from_file(comun.ICON)
        #
        vbox0 = Gtk.VBox(spacing = 5)
        vbox0.set_border_width(5)
        self.get_content_area().add(vbox0)
        #***************************************************************
        notebook = Gtk.Notebook.new()
        vbox0.add(notebook)
        #***************************************************************
        '''
        vbox1 = Gtk.VBox(spacing = 5)
        vbox1.set_border_width(5)
        notebook.append_page(vbox1,Gtk.Label.new(_('Main')))
        frame1 = Gtk.Frame()
        vbox1.pack_start(frame1,False,True,1)
        table1 = Gtk.Table(8, 2, False)
        frame1.add(table1)
        #***************************************************************
        label1 = Gtk.Label(_('Set session length (minutes)')+':')
        label1.set_alignment(0, 0.5)
        table1.attach(label1,0,1,0,1, xpadding=5, ypadding=5)
        self.spinbutton1 = Gtk.SpinButton()
        self.spinbutton1.set_adjustment(Gtk.Adjustment(25, 1, 1440, 1, 10, 0))
        table1.attach(self.spinbutton1,1,2,0,1, xpadding=5, ypadding=5)

        label2 = Gtk.Label(_('Set break length (minutes)')+':')
        label2.set_alignment(0, 0.5)
        table1.attach(label2,0,1,1,2, xpadding=5, ypadding=5)
        self.spinbutton2 = Gtk.SpinButton()
        self.spinbutton2.set_adjustment(Gtk.Adjustment(25, 1, 1440, 1, 10, 0))
        table1.attach(self.spinbutton2,1,2,1,2, xpadding=5, ypadding=5)

        label4 = Gtk.Label(_('Play sounds')+':')
        label4.set_alignment(0, 0.5)
        table1.attach(label4,0,1,3,4, xpadding=5, ypadding=5)
        self.switch4 = Gtk.Switch()
        table1.attach(self.switch4,1,2,3,4, xpadding=5, ypadding=5, xoptions = Gtk.AttachOptions.SHRINK)

        sounds = Gtk.ListStore(str,str)
        #for sound in get_sounds():
        #	sounds.append(sound)

        label5 = Gtk.Label(_('Sound on session end')+':')
        label5.set_alignment(0, 0.5)
        table1.attach(label5,0,1,4,5, xpadding=5, ypadding=5)
        self.comboboxsound5 = Gtk.ComboBox.new()
        self.comboboxsound5.set_model(sounds)
        cell1 = Gtk.CellRendererText()
        self.comboboxsound5.pack_start(cell1, True)
        self.comboboxsound5.add_attribute(cell1, 'text', 0)
        table1.attach(self.comboboxsound5,1,2,4,5,xoptions=Gtk.AttachOptions.FILL, yoptions=Gtk.AttachOptions.FILL, xpadding=5, ypadding=5)

        label6 = Gtk.Label(_('Sound on break end')+':')
        label6.set_alignment(0, 0.5)
        table1.attach(label6,0,1,5,6, xpadding=5, ypadding=5)
        self.comboboxsound6 = Gtk.ComboBox.new()
        self.comboboxsound6.set_model(sounds)
        cell1 = Gtk.CellRendererText()
        self.comboboxsound6.pack_start(cell1, True)
        self.comboboxsound6.add_attribute(cell1, 'text', 0)
        table1.attach(self.comboboxsound6,1,2,5,6,xoptions=Gtk.AttachOptions.FILL, yoptions=Gtk.AttachOptions.FILL, xpadding=5, ypadding=5)

        label7 = Gtk.Label(_('Autostart')+':')
        label7.set_alignment(0, 0.5)
        table1.attach(label7,0,1,6,7, xpadding=5, ypadding=5)
        self.switch7 = Gtk.Switch()
        table1.attach(self.switch7,1,2,6,7, xpadding=5, ypadding=5, xoptions = Gtk.AttachOptions.SHRINK)

        label8 = Gtk.Label(_('Icon light')+':')
        label8.set_alignment(0, 0.5)
        table1.attach(label8,0,1,7,8, xpadding=5, ypadding=5)
        self.switch8 = Gtk.Switch()
        table1.attach(self.switch8,1,2,7,8, xpadding=5, ypadding=5, xoptions = Gtk.AttachOptions.SHRINK)
        '''
        #***************************************************************
        vbox2 = Gtk.VBox(spacing = 5)
        vbox2.set_border_width(5)
        notebook.append_page(vbox2,Gtk.Label.new(_('Markdown editor')))
        frame2 = Gtk.Frame()
        vbox2.pack_start(frame2,False,True,1)
        table2 = Gtk.Table(8, 2, False)
        frame2.add(table2)
        #***************************************************************
        label21 = Gtk.Label(_('Show line numbers')+':')
        label21.set_alignment(0, 0.5)
        table2.attach(label21,0,1,0,1, xpadding=5, ypadding=5)
        self.switch21 = Gtk.Switch()
        table2.attach(self.switch21,1,2,0,1, xpadding=5, ypadding=5)
        label22 = Gtk.Label(_('Show line marks')+':')
        label22.set_alignment(0, 0.5)
        table2.attach(label22,0,1,1,2, xpadding=5, ypadding=5)
        self.switch22 = Gtk.Switch()
        table2.attach(self.switch22,1,2,1,2, xpadding=5, ypadding=5)
        label23 = Gtk.Label(_('Insert spaces instead of tabs')+':')
        label23.set_alignment(0, 0.5)
        table2.attach(label23,0,1,2,3, xpadding=5, ypadding=5)
        self.switch23 = Gtk.Switch()
        table2.attach(self.switch23,1,2,2,3, xpadding=5, ypadding=5)
        label24 = Gtk.Label(_('Set tab width')+':')
        label24.set_alignment(0, 0.5)
        table2.attach(label24,0,1,3,4, xpadding=5, ypadding=5)
        self.spinbutton24 = Gtk.SpinButton()
        self.spinbutton24.set_adjustment(Gtk.Adjustment(25, 2, 32, 2, 4, 0))
        self.spinbutton24.set_value(4)
        table2.attach(self.spinbutton24,1,2,3,4, xpadding=5, ypadding=5)
        label25 = Gtk.Label(_('Set auto indent')+':')
        label25.set_alignment(0, 0.5)
        table2.attach(label25,0,1,4,5, xpadding=5, ypadding=5)
        self.switch25 = Gtk.Switch()
        table2.attach(self.switch25,1,2,4,5, xpadding=5, ypadding=5)
        label26 = Gtk.Label(_('Highlight current line')+':')
        label26.set_alignment(0, 0.5)
        table2.attach(label26,0,1,5,6, xpadding=5, ypadding=5)
        self.switch26 = Gtk.Switch()
        table2.attach(self.switch26,1,2,5,6, xpadding=5, ypadding=5)
        self.button27 = Gtk.Button()
        self.button27.connect('clicked', self.on_button27_clicked)
        table2.attach(self.button27,0,2,6,7, xpadding=5, ypadding=5)
        #***************************************************************
        vbox3 = Gtk.VBox(spacing = 5)
        vbox3.set_border_width(5)
        notebook.append_page(vbox3,Gtk.Label.new(_('Html viewer')))
        frame3 = Gtk.Frame()
        vbox3.pack_start(frame3,False,True,1)
        table3 = Gtk.Table(9, 2, False)
        frame3.add(table3)
        #***************************************************************
        label31 = Gtk.Label(_('Show line numbers')+':')
        label31.set_alignment(0, 0.5)
        table3.attach(label31,0,1,0,1, xpadding=5, ypadding=5)
        self.switch31 = Gtk.Switch()
        table3.attach(self.switch31,1,2,0,1, xpadding=5, ypadding=5)
        label32 = Gtk.Label(_('Show line marks')+':')
        label32.set_alignment(0, 0.5)
        table3.attach(label32,0,1,1,2, xpadding=5, ypadding=5)
        self.switch32 = Gtk.Switch()
        table3.attach(self.switch32,1,2,1,2, xpadding=5, ypadding=5)
        label33 = Gtk.Label(_('Insert spaces instead of tabs')+':')
        label33.set_alignment(0, 0.5)
        table3.attach(label33,0,1,2,3, xpadding=5, ypadding=5)
        self.switch33 = Gtk.Switch()
        table3.attach(self.switch33,1,2,2,3, xpadding=5, ypadding=5)
        label34 = Gtk.Label(_('Set tab width')+':')
        label34.set_alignment(0, 0.5)
        table3.attach(label34,0,1,3,4, xpadding=5, ypadding=5)
        self.spinbutton34 = Gtk.SpinButton()
        self.spinbutton34.set_adjustment(Gtk.Adjustment(25, 2, 32, 2, 4, 0))
        self.spinbutton34.set_value(4)
        table3.attach(self.spinbutton34,1,2,3,4, xpadding=5, ypadding=5)
        label35 = Gtk.Label(_('Set auto indent')+':')
        label35.set_alignment(0, 0.5)
        table3.attach(label35,0,1,4,5, xpadding=5, ypadding=5)
        self.switch35 = Gtk.Switch()
        table3.attach(self.switch35,1,2,4,5, xpadding=5, ypadding=5)
        label36 = Gtk.Label(_('Highlight current line')+':')
        label36.set_alignment(0, 0.5)
        table3.attach(label36,0,1,5,6, xpadding=5, ypadding=5)
        self.switch36 = Gtk.Switch()
        table3.attach(self.switch36,1,2,5,6, xpadding=5, ypadding=5)
        label37 = Gtk.Label(_('Preview Theme')+':')
        label37.set_alignment(0, 0.5)
        table3.attach(label37,0,1,6,7, xpadding=5, ypadding=5)

        self.preview_themes = Gtk.ListStore(str,str)
        for preview_theme in get_themes():
            self.preview_themes.append(preview_theme)
        self.combobox_preview_theme = Gtk.ComboBox.new()
        self.combobox_preview_theme.set_model(self.preview_themes)
        cell1 = Gtk.CellRendererText()
        self.combobox_preview_theme.pack_start(cell1, True)
        self.combobox_preview_theme.add_attribute(cell1, 'text', 0)
        table3.attach(self.combobox_preview_theme,1,2,6,7, xpadding=5, ypadding=5)
        #***************************************************************
        vbox4 = Gtk.VBox(spacing = 5)
        vbox4.set_border_width(5)
        notebook.append_page(vbox4,Gtk.Label.new(_('General options')))
        frame4 = Gtk.Frame()
        vbox4.pack_start(frame4,False,False,1)
        table4 = Gtk.Table(3, 2, False)
        frame4.add(table4)
        #***************************************************************
        label41 = Gtk.Label(_('Autosave')+':')
        label41.set_alignment(0, 0.5)
        table4.attach(label41,0,1,0,1, xpadding=5, ypadding=5)
        self.switch41 = Gtk.Switch()
        table4.attach(self.switch41,1,2,0,1, xpadding=5, ypadding=5)
        label42 = Gtk.Label(_('Spell check')+':')
        label42.set_alignment(0, 0.5)
        table4.attach(label42,0,1,1,2, xpadding=5, ypadding=5)
        self.switch42 = Gtk.Switch()
        table4.attach(self.switch42,1,2,1,2, xpadding=5, ypadding=5)
        label52 = Gtk.Label(_('Use MathJax')+':')
        label52.set_alignment(0, 0.5)
        table4.attach(label52,0,1,2,3, xpadding=5, ypadding=5)
        self.switch52 = Gtk.Switch()
        table4.attach(self.switch52,1,2,2,3, xpadding=5, ypadding=5)

        #
        self.load_preferences()
        #
        self.show_all()

    def on_button27_clicked(self, widget):
        dialog = Gtk.FontChooserDialog.new(_('Select font'))
        if not self.button27.get_label() is None\
                and self.button27.get_label() != '':
            font = Pango.font_description_from_string(
                self.button27.get_label())
            dialog.set_font_desc(font)
        if (dialog.run() == Gtk.ResponseType.OK):
            font_description = dialog.get_font_desc()
            self.button27.set_label(font_description.to_string())
            dialog.hide()
        dialog.destroy()

    def close_application(self, widget):
        self.hide()

    def messagedialog(self,title,message):
        dialog = Gtk.MessageDialog(None,Gtk.DialogFlags.MODAL,Gtk.MessageType.INFO,buttons=Gtk.ButtonsType.OK)
        dialog.set_markup("<b>%s</b>" % title)
        dialog.format_secondary_markup(message)
        dialog.run()
        dialog.destroy()

    def close_ok(self):
        self.save_preferences()

    def load_preferences(self):
        configuration = Configuration()
        self.switch21.set_active(configuration.get('markdown_editor.show_line_numbers'))
        self.switch22.set_active(configuration.get('markdown_editor.show_line_marks'))
        self.switch23.set_active(configuration.get('markdown_editor.spaces'))
        self.spinbutton24.set_value(configuration.get('markdown_editor.tab_width'))
        self.switch25.set_active(configuration.get('markdown_editor.auto_indent'))
        self.switch26.set_active(configuration.get('markdown_editor.highlight_current_line'))
        self.button27.set_label(configuration.get('markdown_editor.font'))
        self.switch31.set_active(configuration.get('html_viewer.show_line_numbers'))
        self.switch32.set_active(configuration.get('html_viewer.show_line_marks'))
        self.switch33.set_active(configuration.get('html_viewer.spaces'))
        self.spinbutton34.set_value(configuration.get('html_viewer.tab_width'))
        self.switch35.set_active(configuration.get('html_viewer.auto_indent'))
        self.switch36.set_active(configuration.get('html_viewer.highlight_current_line'))
        select_value_in_combo(self.combobox_preview_theme,configuration.get('html_viewer.preview_theme'))
        self.switch41.set_active(configuration.get('autosave'))
        self.switch42.set_active(configuration.get('spellcheck'))
        self.switch52.set_active(configuration.get('mathjax'))

    def save_preferences(self):
        configuration = Configuration()
        configuration.set('markdown_editor.show_line_numbers',self.switch21.get_active())
        configuration.set('markdown_editor.show_line_marks',self.switch22.get_active())
        configuration.set('markdown_editor.spaces',self.switch23.get_active())
        configuration.set('markdown_editor.tab_width',self.spinbutton24.get_value())
        configuration.set('markdown_editor.auto_indent',self.switch25.get_active())
        configuration.set('markdown_editor.highlight_current_line',self.switch26.get_active())
        configuration.set('markdown_editor.font', self.button27.get_label())
        configuration.set('html_viewer.show_line_numbers',self.switch31.get_active())
        configuration.set('html_viewer.show_line_marks',self.switch32.get_active())
        configuration.set('html_viewer.spaces',self.switch33.get_active())
        configuration.set('html_viewer.tab_width',self.spinbutton34.get_value())
        configuration.set('html_viewer.auto_indent',self.switch35.get_active())
        configuration.set('html_viewer.highlight_current_line',self.switch36.get_active())
        configuration.set('html_viewer.preview_theme',get_selected_value_in_combo(self.combobox_preview_theme))
        configuration.set('autosave',self.switch41.get_active())
        configuration.set('spellcheck',self.switch42.get_active())
        configuration.set('mathjax',self.switch52.get_active())
        configuration.save()


if __name__ == "__main__":
    cm = PreferencesDialog()
    if 	cm.run() == Gtk.ResponseType.ACCEPT:
            print(1)
            cm.close_ok()
    cm.hide()
    cm.destroy()
    exit(0)
