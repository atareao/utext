#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import comun
import sys
import locale
import signal
import datetime
import time
import re
import tempfile
import webbrowser
from configurator import Configuration
from services import DropboxService
from logindialog import LoginDialog
from insert_image_dialog import InsertImageDialog
from insert_url_dialog import InsertUrlDialog
from filename_dialog import FilenameDialog
from files_in_dropbox_dialog import FilesInDropboxDialog
from preferences_dialog import PreferencesDialog
from search_dialog import SearchDialog
from search_and_replace_dialog import SearchAndReplaceDialog
from pprint import pprint
from jinja2 import Environment, FileSystemLoader
from markdown import Markdown, Extension
from mdx_mathjax import MathExtension
from myextension import MyExtension
from gi.repository import GObject, Gtk, Gio, WebKit, Gdk, GtkSource, GtkSpell, GdkPixbuf
from comun import _

from bs4 import BeautifulSoup

import pdfkit 
##
#import threading
##

TIME_LAPSE = 500 #ms
TAG_FOUND = 'found'

env = Environment(loader=FileSystemLoader(comun.THEMESDIR))

def add2menu(menu, text = None, icon = None, conector_event = None, conector_action = None):
	if text != None:
		menu_item = Gtk.ImageMenuItem.new_with_label(text)
		if icon:
			image = Gtk.Image.new_from_stock(icon, Gtk.IconSize.MENU)
			menu_item.set_image(image)
			menu_item.set_always_show_image(True)
	else:
		if icon == None:
			menu_item = Gtk.SeparatorMenuItem()
		else:
			menu_item = Gtk.ImageMenuItem.new_from_stock(icon, None)
			menu_item.set_always_show_image(True)
	if conector_event != None and conector_action != None:				
		menu_item.connect(conector_event,conector_action)
	menu_item.show()
	menu.append(menu_item)
	return menu_item

class uText(Gtk.Window):
	__gsignals__ = {
		'text-changed':(GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,(object,)),
		'save-me':(GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,(object,)),
		}

	def __init__(self,afile=None):		
		Gtk.Window.__init__(self, title='')
		self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
		self.set_icon_from_file(comun.ICON)
		self.set_border_width(5)
		self.set_default_size(800, 600)
		self.connect('delete-event', self.on_close_application)
		self.connect('realize',self.on_activate_preview_or_html)
		self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		# Vertical box. Contains menu and PaneView
		self.vbox = Gtk.VBox(False, 2)
		self.add(self.vbox) 	
		#
		self.number_of_lines = 0
		self.contador = 0
		self.match_end = None
		self.searched_text = ''
		self.replacement_text = ''
		#self.the_event = threading.Event()
		#self.the_event.clear()
		self.process_blocked = False
		self.markdown_content = ''
		self.html_content = ''
		self.html_rendered = ''
		css = open(os.path.join(comun.THEMESDIR,'default','style.css'), 'r')
		self.css_content = css.read()
		css.close()		
		#
		
		#Init Menu
		self.init_menu()
		
		#Init Toolbar
		self.init_toolbar()
		
		# Markdown Editor
		self.writer = GtkSource.View.new()
		self.writer.set_left_margin(5)
		self.writer.set_right_margin(5)
		self.writer.set_name("markdownContent")
		self.writer.set_show_line_numbers(True)
		self.writer.set_show_line_marks(True)
		self.writer.set_insert_spaces_instead_of_tabs(True)
		self.writer.set_tab_width(4)
		self.writer.set_auto_indent(True)
		self.writer.set_wrap_mode(Gtk.WrapMode.WORD)
		self.writer.set_highlight_current_line(True)
		
		# Textbuffer
		buffer = GtkSource.Buffer()
		buffer.connect("changed", self.on_buffer_changed)
		buffer.set_highlight_syntax(True)

		# Set textview buffer
		self.writer.set_buffer(buffer)
		self.writer.connect("key-release-event", self.on_key_release_event)
		#SpellChecker
		if GtkSpell._namespace == "Gtkspell":
			self.spellchecker = GtkSpell.Spell.new()
		elif GtkSpell._namespace == "GtkSpell":
			self.spellchecker = GtkSpell.Checker.new()
		#self.spellchecker = GtkSpell.Checker.new()
		self.spellchecker.attach(self.writer)
		#self.spellchecker.buffer_initialize()
		# Dunno
		lm = GtkSource.LanguageManager.get_default()
		language = lm.get_language("markdown")
		self.writer.get_buffer().set_language(language)		

		# WebKit
		self.webkit_viewer = WebKit.WebView()
		self.webkit_viewer.set_name("previewContent")
		self.webkit_viewer.connect("navigation-policy-decision-requested", self.on_navigation)
		settings = WebKit.WebSettings()
		#settings.set_property('enable-file-access-from-file-uris', True)
		self.webkit_viewer.set_settings(settings)

		# Html
		self.html_viewer = GtkSource.View.new()
		self.html_viewer.set_left_margin(5)
		self.html_viewer.set_right_margin(5)
		self.html_viewer.set_name("htmlContent")
		self.html_viewer.set_show_line_numbers(True)
		self.html_viewer.set_show_line_marks(True)
		self.html_viewer.set_insert_spaces_instead_of_tabs(True)
		self.html_viewer.set_tab_width(4)
		self.html_viewer.set_auto_indent(True)
		self.html_viewer.set_wrap_mode(Gtk.WrapMode.WORD)

		bufferhtml = GtkSource.Buffer()
		bufferhtml.set_highlight_syntax(True)
		self.html_viewer.set_buffer(bufferhtml)
		lm = GtkSource.LanguageManager.get_default()
		language = lm.get_language("html")
		bufferhtml.set_language(language)
		
		# Scrolled Window 1 (for markdown)
		self.scrolledwindow1 = Gtk.ScrolledWindow()
		self.scrolledwindow1.set_hexpand(False)
		self.scrolledwindow1.set_vexpand(True)
		self.action_scroll1 = self.scrolledwindow1.get_vadjustment().connect('value-changed',self.on_scrolled_value_changed,'scroll1')

		# Scrolled Window 2 (for webkit)
		self.scrolledwindow2 = Gtk.ScrolledWindow()
		self.scrolledwindow2.set_hexpand(False)
		self.scrolledwindow2.set_vexpand(True)
		self.action_scroll2 = self.scrolledwindow2.get_vadjustment().connect('value-changed',self.on_scrolled_value_changed_preview)

		# Scrolled Window 3 (for html)
		self.scrolledwindow3 = Gtk.ScrolledWindow()
		self.scrolledwindow3.set_hexpand(False)
		self.scrolledwindow3.set_vexpand(True)
		self.action_scroll3 = self.scrolledwindow3.get_vadjustment().connect('value-changed',self.on_scrolled_value_changed_html)
		#self.action_scroll3 = self.scrolledwindow3.get_vadjustment().connect('value-changed',self.on_scrolled_value_changed,'scroll3')

		# Add textview, webkit and html
		self.scrolledwindow1.add(self.writer)
		self.scrolledwindow2.add(self.webkit_viewer)
		self.scrolledwindow3.add(self.html_viewer)

		# PaneView, contains markdown editor and html view (webkit)
		self.hpaned = Gtk.HPaned()
		self.hpaned.pack1(self.scrolledwindow1, True, True)
		vbox_child = Gtk.VBox()
		vbox_child.pack_start(self.scrolledwindow2, True, True, 0)
		vbox_child.pack_start(self.scrolledwindow3, True, True, 0)
		self.hpaned.pack2(vbox_child, True, True)
		self.vbox.pack_start(self.hpaned, True, True, 0)
		
		#StatusBar
		self.statusbar =  Gtk.Statusbar()
		self.vbox.pack_start(self.statusbar, False, False, 0)
		
		# Init Jinja, markdown
		self.init_template()

		# Load editor gtk styles
		self.load_styles()

		self.current_filepath = None		
		self.load_preferences()
		# Set windows title
		self.set_win_title()
		#
		self.resize(self.preferences['width'],self.preferences['height'])
		#	
		self.show_all()
		self.show_source_code(False)
		if self.preferences['toolbar']:
			self.toolbar.set_visible(True)
			self.menus['toolbar'].set_label(_('Hide Toolbar'))
		else:
			self.toolbar.set_visible(False)
			self.menus['toolbar'].set_label(_('Show Toolbar'))
		if self.preferences['statusbar']:
			self.statusbar.set_visible(True)
			self.menus['statusbar'].set_label(_('Hide status bar'))
		else:				
			self.statusbar.set_visible(False)
			self.menus['statusbar'].set_label(_('Show status bar'))
		self.apply_preferences()
		self.menus['undo'].set_sensitive(self.writer.get_buffer().can_undo)
		self.buttons['undo'].set_sensitive(self.writer.get_buffer().can_undo)
		self.menus['redo'].set_sensitive(self.writer.get_buffer().can_redo)
		self.buttons['redo'].set_sensitive(self.writer.get_buffer().can_redo)
		#
		self.number_of_lines = 0
		self.time = time.time()
		#
		self.match_end = None
		self.tag_found = self.writer.get_buffer().create_tag(TAG_FOUND,background="orange")
		self.searched_text = ''
		self.replacement_text = ''
		self.writer.grab_focus()
		if afile is not None:
			self.load_file(afile)

	def process_content(self):
		GObject.idle_add(self.process_defereaded)
		return False
		
	def process_defereaded(self):
		print('aqui %d'%self.contador)
		self.process_blocked = False
		self.html_content = self.md.convert(self.markdown_content)
		if self.preferences['mathjax']:
			mathjax='<script type="text/javascript"	src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>'
		else:
			mathjax=''
		self.html_rendered = self.jt.render(css=self.css_content,content=self.html_content,mathjax=mathjax)	
		word_count = len(re.findall('(\S+)', BeautifulSoup(self.html_content).get_text('\n')))
		self.statusbar.push(0,(_('Lines: {0}, Words: {1}, Characters: {2}')).format(self.writer.get_buffer().get_line_count(),word_count,self.writer.get_buffer().get_char_count()))
		self.contador+=1
		self.update_preview()
		
	def apply_preferences(self):
		self.writer.set_show_line_numbers(self.preferences['markdown_editor.show_line_numbers'])
		self.writer.set_show_line_marks(self.preferences['markdown_editor.show_line_marks'])
		self.writer.set_insert_spaces_instead_of_tabs(self.preferences['markdown_editor.spaces'])
		self.writer.set_tab_width(self.preferences['markdown_editor.tab_width'])
		self.writer.set_auto_indent(self.preferences['markdown_editor.auto_indent'])
		self.writer.set_highlight_current_line(self.preferences['markdown_editor.highlight_current_line'])
		self.html_viewer.set_show_line_numbers(self.preferences['html_viewer.show_line_numbers'])
		self.html_viewer.set_show_line_marks(self.preferences['html_viewer.show_line_marks'])
		self.html_viewer.set_insert_spaces_instead_of_tabs(self.preferences['html_viewer.spaces'])
		self.html_viewer.set_tab_width(self.preferences['html_viewer.tab_width'])
		self.html_viewer.set_auto_indent(self.preferences['html_viewer.tab_width'])
		self.html_viewer.set_highlight_current_line(self.preferences['html_viewer.highlight_current_line'])
		css = open(os.path.join(self.preferences['html_viewer.preview_theme'],'style.css'), 'r')
		self.css_content = css.read()
		css.close()
		#
		self.update_buffer()
	
	def show_source_code(self,show):
		if show:
			self.scrolledwindow2.hide()			
			self.scrolledwindow3.show()
		else:
			self.scrolledwindow2.show()
			self.scrolledwindow3.hide()
		self.update_preview()
			
	def load_preferences(self):
		configuration = Configuration()
		self.preferences = {}
		self.preferences['version'] = configuration.get('version')
		self.preferences['last_dir'] = configuration.get('last_dir')
		self.preferences['width'] = configuration.get('width')
		self.preferences['height'] = configuration.get('height')
		self.preferences['toolbar'] = configuration.get('toolbar')
		self.preferences['statusbar'] = configuration.get('statusbar')
		self.preferences['autosave'] = configuration.get('autosave')
		self.preferences['spellcheck'] = configuration.get('spellcheck')
		self.preferences['mathjax'] = configuration.get('mathjax')
		#
		self.preferences['markdown_editor.show_line_numbers'] = configuration.get('markdown_editor.show_line_numbers')
		self.preferences['markdown_editor.show_line_marks'] = configuration.get('markdown_editor.show_line_marks')
		self.preferences['markdown_editor.spaces'] = configuration.get('markdown_editor.spaces')
		self.preferences['markdown_editor.tab_width'] = configuration.get('markdown_editor.tab_width')
		self.preferences['markdown_editor.auto_indent'] = configuration.get('markdown_editor.auto_indent')
		self.preferences['markdown_editor.highlight_current_line'] = configuration.get('markdown_editor.highlight_current_line')		
		self.preferences['html_viewer.show_line_numbers'] = configuration.get('html_viewer.show_line_numbers')
		self.preferences['html_viewer.show_line_marks'] = configuration.get('html_viewer.show_line_marks')
		self.preferences['html_viewer.spaces'] = configuration.get('html_viewer.spaces')
		self.preferences['html_viewer.tab_width'] = configuration.get('html_viewer.tab_width')
		self.preferences['html_viewer.auto_indent'] = configuration.get('html_viewer.auto_indent')
		self.preferences['html_viewer.highlight_current_line'] = configuration.get('html_viewer.highlight_current_line')
		self.preferences['html_viewer.preview_theme'] = configuration.get('html_viewer.preview_theme')		
		#
		if len(self.preferences['last_dir'])==0:
			self.preferences['last_dir'] = os.path.expanduser('~')
		self.preferences['last_filename'] = configuration.get('last_filename')
		self.preferences['filename1'] = configuration.get('filename1')		
		self.preferences['filename2'] = configuration.get('filename2')
		self.preferences['filename3'] = configuration.get('filename3')
		self.preferences['filename4'] = configuration.get('filename4')
		#
		self.recents.set_sensitive(len(self.preferences['filename1'])>0)
		self.filerecents['file1'].set_label(self.preferences['filename1'])
		self.filerecents['file1'].set_visible(len(self.preferences['filename1'])>0)
		self.filerecents['file2'].set_label(self.preferences['filename2'])
		self.filerecents['file2'].set_visible(len(self.preferences['filename2'])>0)
		self.filerecents['file3'].set_label(self.preferences['filename3'])
		self.filerecents['file3'].set_visible(len(self.preferences['filename3'])>0)
		self.filerecents['file4'].set_label(self.preferences['filename4'])
		self.filerecents['file4'].set_visible(len(self.preferences['filename4'])>0)		
		if self.preferences['spellcheck']:
			self.spellchecker.attach(self.writer)
		else:
			self.spellchecker.detach()	
					
	def save_preferences(self):
		configuration = Configuration()
		configuration.set('version',self.preferences['version'])
		configuration.set('last_dir',self.preferences['last_dir'])		
		configuration.set('last_filename',self.preferences['last_filename'])
		configuration.set('filename1',self.preferences['filename1'])
		configuration.set('filename2',self.preferences['filename2'])
		configuration.set('filename3',self.preferences['filename3'])
		configuration.set('filename4',self.preferences['filename4'])
		arectangle = self.get_allocation()		
		configuration.set('width',arectangle.width)
		configuration.set('height',arectangle.height)
		configuration.set('toolbar',self.toolbar.get_visible())
		configuration.set('statusbar',self.statusbar.get_visible())
		configuration.save()


	def on_scrolled_value_changed_preview(self, widget):
		value = self.scrolledwindow2.get_vadjustment().get_value()
		if value == 0: #Fix
			self.on_scrolled_value_changed(None,'scroll1')
		else:
			pass #Something better?
	def on_scrolled_value_changed_html(self, widget):
		value = self.scrolledwindow3.get_vadjustment().get_value()
		if value == 0: #Fix
			self.on_scrolled_value_changed(None,'scroll1')
		else:
			pass #Something better?

	def on_scrolled_value_changed(self, adjustment, scrolledwindow):
		#self.scrolledwindow1.get_vadjustment().handler_block(self.action_scroll1)
		self.scrolledwindow2.get_vadjustment().disconnect(self.action_scroll2)
		self.scrolledwindow3.get_vadjustment().disconnect(self.action_scroll3)
		page_size1 = self.scrolledwindow1.get_vadjustment().get_page_size()
		page_size2 = self.scrolledwindow2.get_vadjustment().get_page_size()
		page_size3 = self.scrolledwindow2.get_vadjustment().get_page_size()
		value1 = self.scrolledwindow1.get_vadjustment().get_value()
		value2 = self.scrolledwindow2.get_vadjustment().get_value()
		value3 = self.scrolledwindow3.get_vadjustment().get_value()
		lower1 = self.scrolledwindow1.get_vadjustment().get_lower()
		lower2 = self.scrolledwindow2.get_vadjustment().get_lower()
		lower3 = self.scrolledwindow3.get_vadjustment().get_lower()
		upper1 = self.scrolledwindow1.get_vadjustment().get_upper()
		upper2 = self.scrolledwindow2.get_vadjustment().get_upper()
		upper3 = self.scrolledwindow3.get_vadjustment().get_upper()		
		pos1 = value1 + page_size1 
		pos2 = value2 + page_size2 
		pos3 = value3 + page_size2 
		if pos1 == page_size1:
			pos2 = page_size2
			pos3 = page_size3
		elif pos1 == upper1:
			pos2 = upper2
			pos3 = upper3
		elif (upper1-lower1)>0:
			pos2 = pos1*(upper2-lower2)/(upper1-lower1)
			pos3 = pos1*(upper3-lower3)/(upper1-lower1)
		self.scrolledwindow2.get_vadjustment().set_value(pos2-page_size2)
		self.scrolledwindow3.get_vadjustment().set_value(pos3-page_size3)
		#
		self.action_scroll2 = self.scrolledwindow2.get_vadjustment().connect('value-changed',self.on_scrolled_value_changed_preview)
		self.action_scroll3 = self.scrolledwindow3.get_vadjustment().connect('value-changed',self.on_scrolled_value_changed_html)
	def load_file_dialog(self):
		dialog = Gtk.FileChooserDialog("Open file", self,
			Gtk.FileChooserAction.SAVE,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			 Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
		dialog.set_current_folder(self.preferences['last_dir'])
		self.add_filters(dialog)
		response = dialog.run()

		if response == Gtk.ResponseType.OK:
			self.load_file(dialog.get_filename())
		elif response == Gtk.ResponseType.CANCEL:
			pass  # TODO? User cancelled

		dialog.destroy()
					
	def on_menu_file_open(self,widget):
		filename = None
		if widget == self.filerecents['file1']:
			filename = self.preferences['filename1']
		elif widget == self.filerecents['file2']:
			filename = self.preferences['filename2']
		elif widget == self.filerecents['file3']:
			filename = self.preferences['filename3']
		elif widget == self.filerecents['file4']:
			filename = self.preferences['filename4']
		if filename is not None and os.path.exists(filename):
			self.load_file(filename)
			
	def work_with_file(self,filename):
		self.preferences['last_filename'] = filename
		self.preferences['last_dir'] = os.path.dirname(filename)
		if filename == self.preferences['filename1']:
			pass
		elif filename == self.preferences['filename2']:
			self.preferences['filename2'] = self.preferences['filename1']
			self.preferences['filename1'] = filename
		elif filename == self.preferences['filename3']:
			self.preferences['filename3'] = self.preferences['filename2']
			self.preferences['filename2'] = self.preferences['filename1']
			self.preferences['filename1'] = filename
		elif filename == self.preferences['filename4']:
			self.preferences['filename4'] = self.preferences['filename3']
			self.preferences['filename3'] = self.preferences['filename2']
			self.preferences['filename2'] = self.preferences['filename1']
			self.preferences['filename1'] = filename
		else:
			self.preferences['filename4'] = self.preferences['filename3']
			self.preferences['filename3'] = self.preferences['filename2']
			self.preferences['filename2'] = self.preferences['filename1']
			self.preferences['filename1'] = filename
		self.save_preferences()
		self.load_preferences()
		
	def load_file(self, file_path=None):
		self.current_filepath = file_path	
		if self.current_filepath:
			f = open(self.current_filepath, 'r')
			self.writer.get_buffer().set_text(f.read())
			f.close()
			self.work_with_file(file_path)
		self.set_win_title()
		self.writer.get_buffer().set_modified(False)
		self.writer.grab_focus()
		self.read_buffer()
		
	def save_as(self):
		temp_current_filepath = self.current_filepath
		self.current_filepath = None
		self.save_current_file()
		if not self.current_filepath or self.current_filepath is None:
			self.current_filepath = temp_current_filepath
			self.set_win_title()
			self.work_with_file(self.current_filepath)

	def save_as_pdf(self):
		dialog = Gtk.FileChooserDialog(_('Select a file to save pdf'),
										self,
									   Gtk.FileChooserAction.SAVE,
									   (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
										Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
		dialog.set_default_response(Gtk.ResponseType.OK)
		dialog.set_current_folder(self.preferences['last_dir'])
		filter = Gtk.FileFilter()
		filter.set_name(_('PDF files'))
		filter.add_mime_type('application/x-pdf')
		filter.add_pattern('*.pdf')
		dialog.add_filter(filter)
		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			filename = dialog.get_filename()	
			if filename is None:
				return
			if not filename.endswith('.pdf'):
				filename += '.pdf'
			data = self.get_buffer_text()
			if data is not None:
				options = {
					'page-size': 'A4',
					'margin-top': '20mm',
					'margin-right': '15mm',
					'margin-bottom': '20mm',
					'margin-left': '25mm',
					'encoding': "UTF-8",
				}			
				pdfkit.from_string(self.html_content,filename,options=options)
		dialog.destroy()
			
	def save_current_file(self):
		if not self.current_filepath or self.current_filepath is None:
			filename = None
			dialog = Gtk.FileChooserDialog(_('Select a file to save markdown'),
											self,
										   Gtk.FileChooserAction.SAVE,
										   (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
											Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
			dialog.set_default_response(Gtk.ResponseType.OK)
			dialog.set_current_folder(self.preferences['last_dir'])
			filter = Gtk.FileFilter()
			filter.set_name(_('Markdown files'))
			filter.add_mime_type('text/plain')
			filter.add_pattern('*.md')
			dialog.add_filter(filter)
			response = dialog.run()
			if response == Gtk.ResponseType.OK:
				filename = dialog.get_filename()	
				if not filename.endswith('.md'):
					filename += '.md'
			dialog.destroy()
			if filename is None:
				self.save_current_file()
				return
			if os.path.exists(filename):
				dialog_overwrite = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
				Gtk.ButtonsType.OK_CANCEL, _('File exists'))
				dialog_overwrite.format_secondary_text(_('Overwrite?'))
				response_overwrite = dialog_overwrite.run()
				if response_overwrite != Gtk.ResponseType.OK:
					dialog_overwrite.destroy()
					self.save_current_file()
					return
				dialog_overwrite.destroy()
			if filename is not None:
				self.current_filepath = filename			
		if self.current_filepath and self.current_filepath is not None:									
			data = self.get_buffer_text()
			if data is not None:
				f = open(self.current_filepath, 'w')
				f.write(data)
				f.close()
				self.set_win_title()
				self.work_with_file(self.current_filepath)
				self.writer.get_buffer().set_modified(False)

	def set_win_title(self):
		if self.current_filepath and self.current_filepath is not None:
			current_filename = self.current_filepath.split("/")[-1]
			self.dropbox_filename = current_filename
		else:
			current_filename = _('Untitled')
			self.dropbox_filename = None
		title = "uText - %s"%(current_filename)		
		self.set_title(title)

	def init_toolbar(self):
		self.toolbar =  Gtk.Toolbar()
		self.toolbar.set_style(Gtk.ToolbarStyle.ICONS)
		self.vbox.pack_start(self.toolbar, False, False, 0)
		#
		self.buttons={}
		#
		self.buttons['new'] = Gtk.ToolButton(stock_id=Gtk.STOCK_NEW)
		self.buttons['new'].set_tooltip_text(_('New file'))
		self.buttons['new'].connect('clicked',self.on_toolbar_clicked,'new')
		self.toolbar.add(self.buttons['new'])
		#
		self.buttons['open'] = Gtk.ToolButton(stock_id=Gtk.STOCK_OPEN)
		self.buttons['open'].set_tooltip_text(_('Open'))
		self.buttons['open'].connect('clicked',self.on_toolbar_clicked,'open')
		self.toolbar.add(self.buttons['open'])
		#
		self.buttons['close'] = Gtk.ToolButton(stock_id=Gtk.STOCK_CLOSE)
		self.buttons['close'].set_tooltip_text(_('Close'))
		self.buttons['close'].connect('clicked',self.on_toolbar_clicked,'close')
		self.toolbar.add(self.buttons['close'])
		#
		self.buttons['save'] = Gtk.ToolButton(stock_id=Gtk.STOCK_SAVE)
		self.buttons['save'].set_tooltip_text(_('Save'))
		self.buttons['save'].connect('clicked',self.on_toolbar_clicked,'save')
		self.toolbar.add(self.buttons['save'])
		#
		self.buttons['save_as'] = Gtk.ToolButton(stock_id=Gtk.STOCK_SAVE_AS)
		self.buttons['save_as'].set_tooltip_text(_('Save as'))
		self.buttons['save_as'].connect('clicked',self.on_toolbar_clicked,'save_as')
		self.toolbar.add(self.buttons['save_as'])
		#
		self.toolbar.add(Gtk.SeparatorToolItem())
		#
		self.buttons['undo'] = Gtk.ToolButton(stock_id=Gtk.STOCK_UNDO)
		self.buttons['undo'].set_tooltip_text(_('Undo'))
		self.buttons['undo'].connect('clicked',self.on_toolbar_clicked,'undo')
		self.toolbar.add(self.buttons['undo'])
		#
		self.buttons['redo'] = Gtk.ToolButton(stock_id=Gtk.STOCK_REDO)
		self.buttons['redo'].set_tooltip_text(_('Redo'))
		self.buttons['redo'].connect('clicked',self.on_toolbar_clicked,'redo')
		self.toolbar.add(self.buttons['redo'])
		#
		self.toolbar.add(Gtk.SeparatorToolItem())
		#
		self.buttons['bold'] = Gtk.ToolButton(stock_id=Gtk.STOCK_BOLD)
		self.buttons['bold'].set_tooltip_text(_('Bold'))
		self.buttons['bold'].connect('clicked',self.on_toolbar_clicked,'bold')
		self.toolbar.add(self.buttons['bold'])
		#
		self.buttons['italic'] = Gtk.ToolButton(stock_id=Gtk.STOCK_ITALIC)
		self.buttons['italic'].set_tooltip_text(_('Italic'))
		self.buttons['italic'].connect('clicked',self.on_toolbar_clicked,'italic')
		self.toolbar.add(self.buttons['italic'])
		#
		self.buttons['underline'] = Gtk.ToolButton(stock_id=Gtk.STOCK_UNDERLINE)
		self.buttons['underline'].set_tooltip_text(_('Underline'))
		self.buttons['underline'].connect('clicked',self.on_toolbar_clicked,'underline')
		self.toolbar.add(self.buttons['underline'])
		#
		self.buttons['strikethrough'] = Gtk.ToolButton(stock_id=Gtk.STOCK_STRIKETHROUGH)
		self.buttons['strikethrough'].set_tooltip_text(_('Strikethrough'))
		self.buttons['strikethrough'].connect('clicked',self.on_toolbar_clicked,'strikethrough')
		self.toolbar.add(self.buttons['strikethrough'])
		#
		self.toolbar.add(Gtk.SeparatorToolItem())
		#
		self.buttons['copy'] = Gtk.ToolButton(stock_id=Gtk.STOCK_COPY)
		self.buttons['copy'].set_tooltip_text(_('Copy'))
		self.buttons['copy'].connect('clicked',self.on_toolbar_clicked,'copy')
		self.toolbar.add(self.buttons['copy'])		
		#
		self.buttons['paste'] = Gtk.ToolButton(stock_id=Gtk.STOCK_PASTE)
		self.buttons['paste'].set_tooltip_text(_('Paste'))
		self.buttons['paste'].connect('clicked',self.on_toolbar_clicked,'paste')
		self.toolbar.add(self.buttons['paste'])		
		#
		self.buttons['cut'] = Gtk.ToolButton(stock_id=Gtk.STOCK_CUT)
		self.buttons['cut'].set_tooltip_text(_('Cut'))
		self.buttons['cut'].connect('clicked',self.on_toolbar_clicked,'cut')
		self.toolbar.add(self.buttons['cut'])		
		#
		self.toolbar.add(Gtk.SeparatorToolItem())
		#
		self.buttons['zoom_in'] = Gtk.ToolButton(stock_id=Gtk.STOCK_ZOOM_IN)
		self.buttons['zoom_in'].set_tooltip_text(_('Zoom in'))
		self.buttons['zoom_in'].connect('clicked',self.on_toolbar_clicked,'zoom_in')
		self.toolbar.add(self.buttons['zoom_in'])
		#
		self.buttons['zoom_out'] = Gtk.ToolButton(stock_id=Gtk.STOCK_ZOOM_OUT)
		self.buttons['zoom_out'].set_tooltip_text(_('Zoom out'))
		self.buttons['zoom_out'].connect('clicked',self.on_toolbar_clicked,'zoom_out')
		self.toolbar.add(self.buttons['zoom_out'])
		#
		self.buttons['zoom_100'] = Gtk.ToolButton(stock_id=Gtk.STOCK_ZOOM_100)
		self.buttons['zoom_100'].set_tooltip_text(_('Zoom 100%'))
		self.buttons['zoom_100'].connect('clicked',self.on_toolbar_clicked,'zoom_100')
		self.toolbar.add(self.buttons['zoom_100'])
		
	def init_menu(self):
		menubar = Gtk.MenuBar()
		self.vbox.pack_start(menubar, False, False, 0)
		accel_group = Gtk.AccelGroup()
		self.add_accel_group(accel_group)		

		################################################################
		self.filemenu = Gtk.Menu.new()
		self.filem = Gtk.MenuItem.new_with_label(_('File'))
		self.filem.set_submenu(self.filemenu)
		#
		self.menus = {}
		#
		self.menus['new']= Gtk.ImageMenuItem.new_with_label(_('New file'))
		self.menus['new'].connect('activate',self.on_toolbar_clicked,'new')
		self.menus['new'].add_accelerator('activate', accel_group,ord('N'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.filemenu.append(self.menus['new'])		
		#
		self.filemenu.append(Gtk.SeparatorMenuItem())
		#		
		self.menus['open'] = menu_open= Gtk.ImageMenuItem.new_with_label(_('Open'))
		self.menus['open'].connect('activate',self.on_toolbar_clicked,'open')
		self.menus['open'].add_accelerator('activate', accel_group,ord('O'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.filemenu.append(self.menus['open'])
		#
		self.menus['close'] = menu_open= Gtk.ImageMenuItem.new_with_label(_('Close'))
		self.menus['close'].connect('activate',self.on_toolbar_clicked,'close')
		self.menus['close'].add_accelerator('activate', accel_group,ord('C'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.filemenu.append(self.menus['close'])
		#
		menurecents = Gtk.Menu.new()
		self.recents = Gtk.MenuItem.new_with_label(_('Recent files...'))
		self.recents.set_submenu(menurecents)
		self.filemenu.append(self.recents)
		#
		self.filerecents = {}
		self.filerecents['file1'] = Gtk.MenuItem.new_with_label('file1')
		self.filerecents['file1'].connect('activate',self.on_menu_file_open)
		self.filerecents['file1'].set_visible(False)
		menurecents.append(self.filerecents['file1'])
		self.filerecents['file2'] = Gtk.MenuItem.new_with_label('file2')
		self.filerecents['file2'].connect('activate',self.on_menu_file_open)
		self.filerecents['file2'].set_visible(False)
		menurecents.append(self.filerecents['file2'])		
		self.filerecents['file3'] = Gtk.MenuItem.new_with_label('file3')
		self.filerecents['file3'].connect('activate',self.on_menu_file_open)
		self.filerecents['file3'].set_visible(False)
		menurecents.append(self.filerecents['file3'])
		self.filerecents['file4'] = Gtk.MenuItem.new_with_label('file4')
		self.filerecents['file4'].connect('activate',self.on_menu_file_open)
		self.filerecents['file4'].set_visible(False)
		menurecents.append(self.filerecents['file4'])
		#
		self.filemenu.append(Gtk.SeparatorMenuItem())		
		#		
		self.menus['open_from_dropbox'] = menu_open= Gtk.ImageMenuItem.new_with_label(_('Open from Dropbox'))
		self.menus['open_from_dropbox'].connect('activate',self.on_toolbar_clicked,'open_from_dropbox')
		self.filemenu.append(self.menus['open_from_dropbox'])
		
		#
		self.filemenu.append(Gtk.SeparatorMenuItem())		
		#
		self.menus['save']= Gtk.ImageMenuItem.new_with_label(_('Save'))
		self.menus['save'].connect('activate',self.on_toolbar_clicked,'save')
		self.menus['save'].add_accelerator('activate', accel_group,ord('S'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

		self.filemenu.append(self.menus['save'])
		#
		self.menus['save_as']= Gtk.ImageMenuItem.new_with_label(_('Save as'))
		self.menus['save_as'].connect('activate',self.on_toolbar_clicked,'save_as')
		self.menus['save_as'].add_accelerator('activate', accel_group,ord('S'), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)
		self.filemenu.append(self.menus['save_as'])
		#
		self.filemenu.append(Gtk.SeparatorMenuItem())
		#
		self.menus['save_as_pdf']= Gtk.ImageMenuItem.new_with_label(_('Save as PDF'))
		self.menus['save_as_pdf'].connect('activate',self.on_toolbar_clicked,'save_as_pdf')
		self.filemenu.append(self.menus['save_as_pdf'])
		#
		self.filemenu.append(Gtk.SeparatorMenuItem())
		#
		self.menus['save_in_dropbox']= Gtk.ImageMenuItem.new_with_label(_('Save in Dropbox'))
		self.menus['save_in_dropbox'].connect('activate',self.on_toolbar_clicked,'save_in_dropbox')
		self.filemenu.append(self.menus['save_in_dropbox'])
		#
		self.filemenu.append(Gtk.SeparatorMenuItem())
		#
		sal = Gtk.ImageMenuItem.new_with_label(_('Exit'))
		sal.connect('activate',self.on_toolbar_clicked,'exit')
		sal.add_accelerator('activate', accel_group,ord('Q'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.filemenu.append(sal)
		#
		menubar.append(self.filem)
		################################################################		
		################################################################
		self.fileedit = Gtk.Menu.new()
		self.filee = Gtk.MenuItem.new_with_label(_('Edit'))
		self.filee.set_submenu(self.fileedit)
		#
		self.menus['undo']= Gtk.ImageMenuItem.new_with_label(_('Undo'))
		self.menus['undo'].connect('activate',self.on_toolbar_clicked,'undo')
		self.menus['undo'].add_accelerator('activate', accel_group,ord('Z'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileedit.append(self.menus['undo'])
		#
		self.menus['redo']= Gtk.ImageMenuItem.new_with_label(_('Redo'))
		self.menus['redo'].connect('activate',self.on_toolbar_clicked,'redo')
		self.menus['redo'].add_accelerator('activate', accel_group,ord('Y'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileedit.append(self.menus['redo'])
		#
		self.fileedit.append(Gtk.SeparatorMenuItem())
		#
		self.menus['cut']= Gtk.ImageMenuItem.new_with_label(_('Cut'))
		self.menus['cut'].connect('activate',self.on_toolbar_clicked,'cut')
		self.menus['cut'].add_accelerator('activate', accel_group,ord('X'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileedit.append(self.menus['cut'])
		#
		self.menus['copy']= Gtk.ImageMenuItem.new_with_label(_('Copy'))
		self.menus['copy'].connect('activate',self.on_toolbar_clicked,'copy')
		self.menus['copy'].add_accelerator('activate', accel_group,ord('C'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileedit.append(self.menus['copy'])
		#
		self.menus['paste']= Gtk.ImageMenuItem.new_with_label(_('Paste'))
		self.menus['paste'].connect('activate',self.on_toolbar_clicked,'paste')
		self.menus['paste'].add_accelerator('activate', accel_group,ord('V'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileedit.append(self.menus['paste'])
		#
		self.menus['remove']= Gtk.ImageMenuItem.new_with_label(_('Remove'))
		self.menus['remove'].connect('activate',self.on_toolbar_clicked,'remove')
		self.fileedit.append(self.menus['remove'])
		#
		self.fileedit.append(Gtk.SeparatorMenuItem())
		#
		self.menus['select_all']= Gtk.ImageMenuItem.new_with_label(_('Select All'))
		self.menus['select_all'].connect('activate',self.on_toolbar_clicked,'select_all')
		self.menus['select_all'].add_accelerator('activate', accel_group,ord('A'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileedit.append(self.menus['select_all'])
		#
		self.fileedit.append(Gtk.SeparatorMenuItem())
		#
		self.menus['lowercase']= Gtk.ImageMenuItem.new_with_label(_('Convert selection to lowercase'))
		self.menus['lowercase'].connect('activate',self.on_toolbar_clicked,'lowercase')
		self.fileedit.append(self.menus['lowercase'])
		#
		self.menus['titlecase']= Gtk.ImageMenuItem.new_with_label(_('Convert selection to titlecase'))
		self.menus['titlecase'].connect('activate',self.on_toolbar_clicked,'titlecase')
		self.fileedit.append(self.menus['titlecase'])
		#
		self.menus['uppercase']= Gtk.ImageMenuItem.new_with_label(_('Convert selection to uppercase'))
		self.menus['uppercase'].connect('activate',self.on_toolbar_clicked,'uppercase')
		self.fileedit.append(self.menus['uppercase'])
		#
		self.fileedit.append(Gtk.SeparatorMenuItem())
		#
		self.menus['selection_to_html']= Gtk.ImageMenuItem.new_with_label(_('Copy selection to html'))
		self.menus['selection_to_html'].connect('activate',self.on_toolbar_clicked,'selection_to_html')
		self.fileedit.append(self.menus['selection_to_html'])
		#
		self.menus['all_to_html']= Gtk.ImageMenuItem.new_with_label(_('Copy all to html'))
		self.menus['all_to_html'].connect('activate',self.on_toolbar_clicked,'all_to_html')
		self.fileedit.append(self.menus['all_to_html'])
		#
		self.fileedit.append(Gtk.SeparatorMenuItem())
		#
		self.pref = Gtk.ImageMenuItem.new_with_label(_('Preferences'))
		self.pref.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_PREFERENCES, Gtk.IconSize.MENU))		
		self.pref.connect('activate',self.on_toolbar_clicked,'preferences')
		self.pref.set_always_show_image(True)
		self.fileedit.append(self.pref)
		#
		menubar.append(self.filee)
		################################################################
		self.fileview = Gtk.Menu.new()
		self.filev = Gtk.MenuItem.new_with_label(_('View'))
		self.filev.set_submenu(self.fileview)
		#
		self.menus['preview_or_html'] = Gtk.MenuItem.new_with_label(_('Preview'))
		self.menus['preview_or_html'].connect('activate',self.on_activate_preview_or_html)
		self.menus['preview_or_html'].add_accelerator('activate', accel_group,ord('V'), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)		
		self.fileview.append(self.menus['preview_or_html'])
		#
		self.fileview.append(Gtk.SeparatorMenuItem())
		#
		self.menus['preview'] = Gtk.MenuItem.new_with_label(_('Hide preview'))
		self.menus['preview'].connect('activate',self.on_toolbar_clicked, 'preview')
		self.fileview.append(self.menus['preview'])				
		#
		self.menus['statusbar'] = Gtk.MenuItem.new_with_label(_('Hide status bar'))
		self.menus['statusbar'].connect('activate',self.on_toolbar_clicked, 'statusbar')
		self.fileview.append(self.menus['statusbar'])		
		#
		self.menus['toolbar'] = Gtk.MenuItem.new_with_label(_('Hide Toolbar'))
		self.menus['toolbar'].connect('activate',self.on_toolbar_clicked, 'toolbar')
		self.fileview.append(self.menus['toolbar'])	
		#
		self.fileview.append(Gtk.SeparatorMenuItem())	
		#
		self.menus['nightmode'] = Gtk.MenuItem.new_with_label(_('Night mode'))
		self.menus['nightmode'].connect('activate',self.on_toolbar_clicked, 'nightmode')
		self.fileview.append(self.menus['nightmode'])	
		#
		self.fileview.append(Gtk.SeparatorMenuItem())	
		#
		self.menus['fullscreen'] = Gtk.MenuItem.new_with_label(_('Full screen'))
		self.menus['fullscreen'].connect('activate',self.on_toolbar_clicked, 'fullscreen')
		keyval, mask = Gtk.accelerator_parse('F11')
		self.menus['fullscreen'].add_accelerator('activate', accel_group, keyval,mask, Gtk.AccelFlags.VISIBLE)
		self.fileview.append(self.menus['fullscreen'])	
		#
		menubar.append(self.filev)
		################################################################
		self.filesearch = Gtk.Menu.new()
		self.filess = Gtk.MenuItem.new_with_label(_('Search'))
		self.filess.set_submenu(self.filesearch)
		#
		self.menus['search'] = Gtk.MenuItem.new_with_label(_('Search')+'...')
		self.menus['search'].connect('activate',self.on_toolbar_clicked,'search')
		self.menus['search'].add_accelerator('activate', accel_group,ord('F'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)		
		self.filesearch.append(self.menus['search'])
		#
		self.menus['removehighlight'] = Gtk.MenuItem.new_with_label(_('Remove highlight')+'...')
		self.menus['removehighlight'].connect('activate',self.on_toolbar_clicked,'removehighlight')
		self.menus['removehighlight'].add_accelerator('activate', accel_group,ord('K'), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)		
		self.filesearch.append(self.menus['removehighlight'])
		#
		self.filesearch.append(Gtk.SeparatorMenuItem())	
		#
		self.menus['searchandreplace'] = Gtk.MenuItem.new_with_label(_('Search and replace')+'...')
		self.menus['searchandreplace'].connect('activate',self.on_toolbar_clicked,'searchandreplace')
		self.menus['searchandreplace'].add_accelerator('activate', accel_group,ord('H'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)		
		self.filesearch.append(self.menus['searchandreplace'])
		#
		menubar.append(self.filess)
		################################################################
		self.formats = {}
		self.fileformat = Gtk.Menu.new()
		self.filef = Gtk.MenuItem.new_with_label(_('Format'))
		self.filef.set_submenu(self.fileformat)
		#
		self.formats['bold']=Gtk.ImageMenuItem.new_with_label(_('Bold'))
		self.formats['bold'].connect('activate',self.on_toolbar_clicked,'bold')		
		self.formats['bold'].add_accelerator('activate', accel_group,ord('B'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileformat.append(self.formats['bold'])
		#
		self.formats['italic']=Gtk.ImageMenuItem.new_with_label(_('Italic'))
		self.formats['italic'].connect('activate',self.on_toolbar_clicked,'italic')
		self.formats['italic'].add_accelerator('activate', accel_group,ord('I'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileformat.append(self.formats['italic'])
		#
		self.formats['underline']=Gtk.ImageMenuItem.new_with_label(_('Underline'))
		self.formats['underline'].connect('activate',self.on_toolbar_clicked,'underline')
		self.formats['underline'].add_accelerator('activate', accel_group,ord('U'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileformat.append(self.formats['underline'])
		#
		self.formats['strikethrough']=Gtk.ImageMenuItem.new_with_label(_('Strikethrough'))
		self.formats['strikethrough'].connect('activate',self.on_toolbar_clicked,'strikethrough')
		self.formats['strikethrough'].add_accelerator('activate', accel_group,ord('D'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileformat.append(self.formats['strikethrough'])
		#
		self.formats['highlight']=Gtk.ImageMenuItem.new_with_label(_('Highlight'))
		self.formats['highlight'].connect('activate',self.on_toolbar_clicked,'highlight')
		self.formats['highlight'].add_accelerator('activate', accel_group,ord('H'), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileformat.append(self.formats['highlight'])
		#
		self.formats['subscript']=Gtk.ImageMenuItem.new_with_label(_('Subscript'))
		self.formats['subscript'].connect('activate',self.on_toolbar_clicked,'subscript')
		self.formats['subscript'].add_accelerator('activate', accel_group,ord('-'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileformat.append(self.formats['subscript'])
		#
		self.formats['superscript']=Gtk.ImageMenuItem.new_with_label(_('Superscript'))
		self.formats['superscript'].connect('activate',self.on_toolbar_clicked,'superscript')
		self.formats['superscript'].add_accelerator('activate', accel_group,ord('+'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileformat.append(self.formats['superscript'])
		#
		self.fileformat.append(Gtk.SeparatorMenuItem())
		#
		self.formats['bullet_list']=Gtk.ImageMenuItem.new_with_label(_('Bullet List'))
		self.formats['bullet_list'].connect('activate',self.on_toolbar_clicked,'bullet_list')		
		self.fileformat.append(self.formats['bullet_list'])
		#
		self.formats['numbered_list']=Gtk.ImageMenuItem.new_with_label(_('Numbered List'))
		self.formats['numbered_list'].connect('activate',self.on_toolbar_clicked,'numbered_list')		
		self.fileformat.append(self.formats['numbered_list'])
		#
		self.fileformat.append(Gtk.SeparatorMenuItem())
		#
		self.formats['bloque_quote']=Gtk.ImageMenuItem.new_with_label(_('Bloque Quote'))
		self.formats['bloque_quote'].connect('activate',self.on_toolbar_clicked,'bloque_quote')		
		self.fileformat.append(self.formats['bloque_quote'])
		#
		self.formats['code']=Gtk.ImageMenuItem.new_with_label(_('Code'))
		self.formats['code'].connect('activate',self.on_toolbar_clicked,'code')		
		self.fileformat.append(self.formats['code'])
		#
		self.fileformat.append(Gtk.SeparatorMenuItem())
		#
		self.formats['title1']=Gtk.ImageMenuItem.new_with_label(_('Heading One'))
		self.formats['title1'].connect('activate',self.on_toolbar_clicked,'title1')		
		self.formats['title1'].add_accelerator('activate', accel_group,ord('1'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileformat.append(self.formats['title1'])
		#
		self.formats['title2']=Gtk.ImageMenuItem.new_with_label(_('Heading Two'))
		self.formats['title2'].connect('activate',self.on_toolbar_clicked,'title2')
		self.formats['title2'].add_accelerator('activate', accel_group,ord('2'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileformat.append(self.formats['title2'])
		#
		self.formats['title3']=Gtk.ImageMenuItem.new_with_label(_('Heading Three'))
		self.formats['title3'].connect('activate',self.on_toolbar_clicked,'title3')
		self.formats['title3'].add_accelerator('activate', accel_group,ord('3'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileformat.append(self.formats['title3'])
		#
		self.formats['title4']=Gtk.ImageMenuItem.new_with_label(_('Heading Four'))
		self.formats['title4'].connect('activate',self.on_toolbar_clicked,'title4')		
		self.formats['title4'].add_accelerator('activate', accel_group,ord('4'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileformat.append(self.formats['title4'])
		#
		self.formats['title5']=Gtk.ImageMenuItem.new_with_label(_('Heading Five'))
		self.formats['title5'].connect('activate',self.on_toolbar_clicked,'title5')		
		self.formats['title5'].add_accelerator('activate', accel_group,ord('5'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileformat.append(self.formats['title5'])
		#
		self.formats['title6']=Gtk.ImageMenuItem.new_with_label(_('Heading Sex'))
		self.formats['title6'].connect('activate',self.on_toolbar_clicked,'title6')		
		self.formats['title6'].add_accelerator('activate', accel_group,ord('6'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileformat.append(self.formats['title6'])
		#
		menubar.append(self.filef)
		################################################################
		self.inserts = {}
		self.fileinsert = Gtk.Menu.new()
		self.filei = Gtk.MenuItem.new_with_label(_('Insert'))
		self.filei.set_submenu(self.fileinsert)
		#
		self.inserts['rule']=Gtk.ImageMenuItem.new_with_label(_('Insert Horizontal Rule'))
		self.inserts['rule'].connect('activate',self.on_toolbar_clicked,'rule')		
		self.inserts['rule'].add_accelerator('activate', accel_group,ord('H'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileinsert.append(self.inserts['rule'])
		#
		self.inserts['timestamp']=Gtk.ImageMenuItem.new_with_label(_('Insert Timestamp'))
		self.inserts['timestamp'].connect('activate',self.on_toolbar_clicked,'timestamp')		
		self.inserts['timestamp'].add_accelerator('activate', accel_group,ord('T'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileinsert.append(self.inserts['timestamp'])
		#
		self.inserts['more']=Gtk.ImageMenuItem.new_with_label(_('Insert more'))
		self.inserts['more'].connect('activate',self.on_toolbar_clicked,'more')		
		self.inserts['more'].add_accelerator('activate', accel_group,ord('M'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileinsert.append(self.inserts['more'])
		#
		self.fileinsert.append(Gtk.SeparatorMenuItem())
		#
		self.inserts['image'] = Gtk.ImageMenuItem.new_with_label(_('Insert Image'))
		self.inserts['image'].connect('activate',self.on_toolbar_clicked,'image')		
		self.inserts['image'].add_accelerator('activate', accel_group,ord('I'), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileinsert.append(self.inserts['image'])		
		#
		self.inserts['url'] = Gtk.ImageMenuItem.new_with_label(_('Insert Url'))
		self.inserts['url'].connect('activate',self.on_toolbar_clicked,'url')		
		self.inserts['url'].add_accelerator('activate', accel_group,ord('U'), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)
		self.fileinsert.append(self.inserts['url'])		
		#
		menubar.append(self.filei)
		################################################################
		self.tools = {}
		self.filetool = Gtk.Menu.new()
		self.filet = Gtk.MenuItem.new_with_label(_('Tools'))
		self.filet.set_submenu(self.filetool)
		#
		self.tools['spellcheck']=Gtk.CheckMenuItem.new_with_label(_('Spell check'))
		self.tools['spellcheck'].connect('activate',self.on_toolbar_clicked,'spellcheck')		
		self.tools['spellcheck'].add_accelerator('activate', accel_group,ord('S'), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)
		self.filetool.append(self.tools['spellcheck'])
		#
		menubar.append(self.filet)
		################################################################		
		self.filehelp = Gtk.Menu.new()
		self.fileh = Gtk.MenuItem.new_with_label(_('Help'))
		self.fileh.set_submenu(self.get_help_menu())
		#
		menubar.append(self.fileh)
		################################################################				
		
	def on_activate_preview_or_html(self,widget):
		if self.menus['preview_or_html'].get_label() == _('Preview'):			
			self.menus['preview_or_html'].set_label(_('Html'))
			self.show_source_code(False)
		else:
			self.menus['preview_or_html'].set_label(_('Preview'))
			self.show_source_code(True)
	
	def get_help_menu(self):
		help_menu =Gtk.Menu()
		#		
		add2menu(help_menu,text = _('Web...'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('https://launchpad.net/utext'))
		add2menu(help_menu,text = _('Get help online...'),conector_event = 'activate',conector_action = lambda x:webbrowser.open('https://answers.launchpad.net/utext'))
		add2menu(help_menu,text = _('Translate this application...'),conector_event = 'activate',conector_action =lambda x:webbrowser.open('https://translations.launchpad.net/utext'))
		add2menu(help_menu,text = _('Report a bug...'),conector_event = 'activate',conector_action = lambda x:webbrowser.open('https://bugs.launchpad.net/utext'))
		add2menu(help_menu)
		web = add2menu(help_menu,text = _('Homepage'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('http://www.atareao.es/tag/utext'))
		twitter = add2menu(help_menu,text = _('Follow us in Twitter'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('https://twitter.com/atareao'))
		googleplus = add2menu(help_menu,text = _('Follow us in Google+'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('https://plus.google.com/118214486317320563625/posts'))
		facebook = add2menu(help_menu,text = _('Follow us in Facebook'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('http://www.facebook.com/elatareao'))
		add2menu(help_menu)
		add2menu(help_menu,text = _('About'),conector_event = 'activate',conector_action = self.on_about_activate)
		#		
		web.set_image(Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(os.path.join(comun.SOCIALDIR,'web.svg'),24,24)))
		web.set_always_show_image(True)
		twitter.set_image(Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(os.path.join(comun.SOCIALDIR,'twitter.svg'),24,24)))
		twitter.set_always_show_image(True)
		googleplus.set_image(Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(os.path.join(comun.SOCIALDIR,'googleplus.svg'),24,24)))
		googleplus.set_always_show_image(True)
		facebook.set_image(Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(os.path.join(comun.SOCIALDIR,'facebook.svg'),24,24)))
		facebook.set_always_show_image(True)
		#
		help_menu.show()
		return help_menu	
	def add_filters(self, dialog):
		filter_text = Gtk.FileFilter()

		filter_markdown = Gtk.FileFilter()
		filter_markdown.set_name("Markdown ")
		filter_markdown.add_mime_type("text/x-markdown")
		dialog.add_filter(filter_markdown)

		filter_text.set_name("Plain text")
		filter_text.add_mime_type("text/plain")
		dialog.add_filter(filter_text)

		filter_any = Gtk.FileFilter()
		filter_any.set_name("Any files")
		filter_any.add_pattern("*")
		dialog.add_filter(filter_any)


	def init_template(self):
		self.md = Markdown(extensions=[
			'markdown.extensions.extra',
			'markdown.extensions.abbr',
			'markdown.extensions.attr_list',
			'markdown.extensions.def_list',
			'markdown.extensions.fenced_code',
			'markdown.extensions.footnotes',
			'markdown.extensions.tables',
			'markdown.extensions.smart_strong',
			'markdown.extensions.admonition',
			'markdown.extensions.codehilite',
			'markdown.extensions.nl2br',
			'markdown.extensions.sane_lists',
			'markdown.extensions.smarty',
			'markdown.extensions.toc',
			'markdown.extensions.wikilinks',
			MathExtension(),
			MyExtension()
		])	
		# Jinja templates        
		self.jt = env.get_template('header.html')
		self.update_buffer()

	def load_styles(self):
		self.style_provider = Gtk.CssProvider()
		css = open(os.path.join(comun.THEMESDIR,'gtk.css'), 'rb')
		css_data = css.read()
		css.close()
		self.style_provider.load_from_data(css_data)

		Gtk.StyleContext.add_provider_for_screen(
			Gdk.Screen.get_default(), self.style_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
		)

	def read_buffer(self):
		markdown_content = self.get_buffer_text()
		if markdown_content is not None:
			self.markdown_content = markdown_content
			if not self.process_blocked:
				self.process_blocked = True
				GObject.timeout_add(TIME_LAPSE,self.process_content)		

	def on_key_release_event(self, widget, event):
		self.read_buffer()
		
	def on_buffer_changed(self, widget):
		self.menus['undo'].set_sensitive(self.writer.get_buffer().can_undo)
		self.buttons['undo'].set_sensitive(self.writer.get_buffer().can_undo)
		self.menus['redo'].set_sensitive(self.writer.get_buffer().can_redo)
		self.buttons['redo'].set_sensitive(self.writer.get_buffer().can_redo)
		if (self.number_of_lines != self.writer.get_buffer().get_line_count()) or (self.time + 300 < time.time())  and self.preferences['autosave']:
			self.time = time.time()
			self.number_of_lines = self.writer.get_buffer().get_line_count()
			self.save_current_file()

	def get_buffer_text(self):
		try:
			start_iter,end_iter = self.writer.get_buffer().get_bounds()
			text = self.writer.get_buffer().get_text(
				start_iter,
				end_iter, True)
			return text
		except Exception:
			print('--------------------------')
			print('Errrorrrr')
			print('--------------------------')
			pass
		return None
		

	def update_buffer(self):
		if self.menus['preview'].get_label() == _('Hide preview') and not self.process_blocked:
			self.process_blocked = True
			GObject.timeout_add(TIME_LAPSE,self.process_content)		

	def update_preview(self):
		if self.html_content is not None and self.html_viewer.is_visible():
			GObject.idle_add(self.html_viewer.get_buffer().set_text, self.html_content)
		if self.html_rendered is not None and self.webkit_viewer.is_visible():
			GObject.idle_add(self.webkit_viewer.load_string, self.html_rendered, "text/html", "utf-8", '')
		
	def on_navigation(self, web_view, frame, request, nav_action, policy_decision, data=None):
		if request.get_uri() != '/':
			policy_decision.ignore()
			webbrowser.open(request.get_uri())
			
	def on_about_activate(self,widget):
		ad=Gtk.AboutDialog()
		ad.set_name(comun.APPNAME)
		ad.set_version(comun.VERSION)
		ad.set_copyright('Copyrignt (c) 2013-2015\nLorenzo Carbonell')
		ad.set_comments(_('An application to work with markdown'))
		ad.set_license(''+
		'This program is free software: you can redistribute it and/or modify it\n'+
		'under the terms of the GNU General Public License as published by the\n'+
		'Free Software Foundation, either version 3 of the License, or (at your option)\n'+
		'any later version.\n\n'+
		'This program is distributed in the hope that it will be useful, but\n'+
		'WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY\n'+
		'or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for\n'+
		'more details.\n\n'+
		'You should have received a copy of the GNU General Public License along with\n'+
		'this program.  If not, see <http://www.gnu.org/licenses/>.')
		ad.set_website('http://www.atareao.es')
		ad.set_website_label('http://www.atareao.es')
		ad.set_authors(['Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'])
		ad.set_documenters(['Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'])
		ad.set_translator_credits(''+
		'Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>\n')
		ad.set_program_name('uText')
		ad.set_logo(GdkPixbuf.Pixbuf.new_from_file(comun.ICON))
		ad.run()
		ad.destroy()
	def on_close_application(self,widget,data):
		if self.writer.get_buffer().get_modified():
			dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
			Gtk.ButtonsType.OK_CANCEL, _('File modified'))
			dialog.format_secondary_text(_('Save file?'))
			response = dialog.run()
			if response == Gtk.ResponseType.OK:
				self.save_current_file()
			dialog.destroy()
		self.save_preferences()
		exit(0)
		
	def on_toolbar_clicked(self,widget,option):
		if option == 'new':
			self.writer.get_buffer().set_text('')
			self.load_file()
			if self.menus['preview_or_html'].get_label() == _('Html'):
				self.menus['preview_or_html'].set_label(_('Html'))
				self.show_source_code(False)
			else:
				self.menus['preview_or_html'].set_label(_('Preview'))
				self.show_source_code(True)	
		elif option == 'undo':
			if self.writer.get_buffer().can_undo():
				self.writer.get_buffer().undo()
		elif option == 'redo':
			if self.writer.get_buffer().can_redo():
				self.writer.get_buffer().redo()
		elif option == 'open':
			self.load_file_dialog()	
		elif option == 'close':
			self.save_current_file()
			self.current_filepath = None
			self.on_toolbar_clicked(None,'new')
		elif option == 'open_from_dropbox':
			files = []
			ds = DropboxService(comun.TOKEN_FILE)
			if os.path.exists(comun.TOKEN_FILE) and ds.get_account_info():
				files = ds.get_files()
			else:
				oauth_token,oauth_token_secret = ds.get_request_token()
				authorize_url = ds.get_authorize_url(oauth_token,oauth_token_secret)
				ld = LoginDialog(1024,600,authorize_url)#,'http://localhost/?uid=','not_approved=true')
				ld.run()
				oauth_token = ld.code
				uid = ld.uid
				ld.destroy()
				if oauth_token is not None:
					print(oauth_token,uid)
					ans = ds.get_access_token(oauth_token,oauth_token_secret)
					print(ans)
					print(ds.get_account_info())
					if os.path.exists(comun.TOKEN_FILE) and ds.get_account_info():
						files = ds.get_files()
			if len(files)>0:
				result = []
				for element in files:
					result.append(element['path'][1:])
				cm = FilesInDropboxDialog(result)
				if 	cm.run() == Gtk.ResponseType.ACCEPT:
					file_selected = cm.get_selected()
					self.dropbox_filename = file_selected
					text_string = ds.get_file(file_selected)
					self.writer.get_buffer().set_text(text_string)
					self.read_buffer()
				cm.destroy()				
		elif option == 'exit':
			self.on_close_application(widget,None)
		elif option == 'save':
			self.save_current_file()
		elif option == 'save_as':
			self.save_as()
		elif option == 'save_as_pdf':
			self.save_as_pdf()
		elif option  == 'save_in_dropbox':
			if self.dropbox_filename == None:
				dialog = FilenameDialog()
				if dialog.run() == Gtk.ResponseType.OK:
					filename = dialog.filename.get_text()
					dialog.destroy()
					if not filename.endswith('.md'):
						filename = filename + '.md'
					self.dropbox_filename = filename
				else:
					dialog.destroy()
					return
			temp_dropbox_file = '/tmp/%s'%self.dropbox_filename
			if os.path.exists(temp_dropbox_file):
				os.remove(temp_dropbox_file)
			data = self.get_buffer_text()
			if data is not None:				
				f = open(temp_dropbox_file, 'w')
				f.write(data)
				f.close()			
				ds = DropboxService(comun.TOKEN_FILE)
				if os.path.exists(comun.TOKEN_FILE) and ds.get_account_info():
					print(ds.put_file(temp_dropbox_file))
				else:
					oauth_token,oauth_token_secret = ds.get_request_token()
					authorize_url = ds.get_authorize_url(oauth_token,oauth_token_secret)
					ld = LoginDialog(1024,600,authorize_url)#,'http://localhost/?uid=','not_approved=true')
					ld.run()
					oauth_token = ld.code
					uid = ld.uid
					ld.destroy()
					if oauth_token is not None:
						print(oauth_token,uid)
						ans = ds.get_access_token(oauth_token,oauth_token_secret)
						print(ans)
						print(ds.get_account_info())
						if os.path.exists(comun.TOKEN_FILE) and ds.get_account_info():
							print(ds.put_file(temp_dropbox_file))
				if os.path.exists(temp_dropbox_file):
					os.remove(temp_dropbox_file)						
		elif option == 'search':
			searchDialog = SearchDialog(self.searched_text)
			if 	searchDialog.run() == Gtk.ResponseType.ACCEPT:
				searchDialog.hide()				
				self.remove_all_tag(TAG_FOUND)
				self.searched_text = searchDialog.search_text.get_text()
				self.writer.get_buffer().begin_user_action()
				self.search_and_mark(self.searched_text, self.writer.get_buffer().get_start_iter())
				self.writer.get_buffer().end_user_action()
			searchDialog.destroy()
		elif option =='removehighlight':
			self.writer.get_buffer().begin_user_action()
			self.remove_all_tag(TAG_FOUND)
			self.writer.get_buffer().end_user_action()
		elif option == 'searchandreplace':
			searchandreplaceDialog = SearchAndReplaceDialog(self.searched_text,self.replacement_text)
			if 	searchandreplaceDialog.run() == Gtk.ResponseType.ACCEPT:
				searchandreplaceDialog.hide()				
				self.remove_all_tag(TAG_FOUND)
				self.searched_text = searchandreplaceDialog.search_text.get_text()
				self.replacement_text = searchandreplaceDialog.replace_text.get_text()
				self.writer.get_buffer().begin_user_action()
				self.search_and_replace(self.searched_text, self.replacement_text,self.writer.get_buffer().get_start_iter())
				self.writer.get_buffer().end_user_action()
			searchandreplaceDialog.destroy()
			
		elif option == 'preview':
			if self.menus['preview'].get_label() == _('Show preview'):
				self.menus['preview'].set_label(_('Hide preview'))
				self.hpaned.get_child2().set_visible(True)
			else:
				self.menus['preview'].set_label(_('Show preview'))			
				self.hpaned.get_child2().set_visible(False)
			self.update_preview()
		elif option == 'fullscreen':
			if self.menus['fullscreen'].get_label() == _('Full screen'):
				self.fullscreen()
				self.menus['fullscreen'].set_label(_('Normal screen'))
			else:
				self.unfullscreen()
				self.menus['fullscreen'].set_label(_('Full screen'))
		elif option == 'zoom_100':
			self.webkit_viewer.set_zoom_level(1.0)
		elif option == 'zoom_in':
			self.webkit_viewer.zoom_in()
		elif option == 'zoom_out':
			self.webkit_viewer.zoom_out()
		elif option == 'nightmode':
			if self.menus['nightmode'].get_label() == _('Night mode'):
				self.menus['nightmode'].set_label(_('Day mode'))
				css_filename = os.path.join(comun.THEMESDIR,'gtk_night_mode.css')
			else:
				self.menus['nightmode'].set_label(_('Night mode'))			
				css_filename = os.path.join(comun.THEMESDIR,'gtk.css')
			css = open(css_filename, 'rb')
			css_data = css.read()
			css.close()
			self.style_provider = Gtk.CssProvider()			
			self.style_provider.load_from_data(css_data)
			Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.style_provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		elif option == 'preferences':
			cm = PreferencesDialog()
			if 	cm.run() == Gtk.ResponseType.ACCEPT:
				cm.close_ok()
				self.load_preferences()
				self.apply_preferences()
			cm.hide()
			cm.destroy()
		elif option == 'bloque_quote':
			self.writer.get_buffer().begin_user_action()
			self.insert_at_start_of_line('>')
			self.writer.get_buffer().end_user_action()
		elif option == 'code':
			self.insert_at_start_of_line('\t')
		elif option == 'title1':
			self.insert_at_start_of_line('#')
		elif option == 'title2':
			self.insert_at_start_of_line('##')
		elif option == 'title3':
			self.insert_at_start_of_line('###')
		elif option == 'title4':
			self.insert_at_start_of_line('####')			
		elif option == 'title5':
			self.insert_at_start_of_line('#####')			
		elif option == 'title6':
			self.insert_at_start_of_line('######')			
		elif option == 'bullet_list':
			self.insert_at_start_of_line('*')
		elif option == 'numbered_list':
			data = self.get_first_n_characters_at_previous_line(3)
			if data.find('. ')>-1:
				number = data[:data.find('. ')]
			else:
				number = 0
			self.insert_at_start_of_line('%d.'%(int(number)+1))
		elif option == 'cut':
			self.writer.get_buffer().cut_clipboard(self.clipboard,True)
		elif option == 'copy':
			self.writer.get_buffer().copy_clipboard(self.clipboard)
		elif option == 'paste':
			self.writer.get_buffer().paste_clipboard(self.clipboard,None,True)
		elif option == 'remove':
			bounds = self.writer.get_buffer().get_selection_bounds();
			if (bounds):
				iteratwordstart,iteratwordend = bounds
				self.writer.get_buffer().delete(iteratwordstart,iteratwordend)
		elif option == 'select_all':
			start_iter = self.writer.get_buffer().get_start_iter()
			end_iter =  self.writer.get_buffer().get_end_iter()
			self.writer.get_buffer().select_range(start_iter,end_iter)
		elif option == 'lowercase':
			bounds = self.writer.get_buffer().get_selection_bounds();
			if (bounds):
				iteratwordstart,iteratwordend = bounds
				text_string = self.writer.get_buffer().get_text(iteratwordstart,iteratwordend,True)
				self.writer.get_buffer().begin_user_action()
				self.writer.get_buffer().delete(iteratwordstart,iteratwordend)
				self.writer.get_buffer().insert_at_cursor(text_string.lower())
				self.writer.get_buffer().end_user_action()
		elif option == 'titlecase':
			bounds = self.writer.get_buffer().get_selection_bounds();
			if (bounds):
				iteratwordstart,iteratwordend = bounds
				text_string = self.writer.get_buffer().get_text(iteratwordstart,iteratwordend,True)
				self.writer.get_buffer().begin_user_action()
				self.writer.get_buffer().delete(iteratwordstart,iteratwordend)
				self.writer.get_buffer().insert_at_cursor(text_string.title())
				self.writer.get_buffer().end_user_action()
		elif option == 'uppercase':
			bounds = self.writer.get_buffer().get_selection_bounds();
			if (bounds):
				iteratwordstart,iteratwordend = bounds
				text_string = self.writer.get_buffer().get_text(iteratwordstart,iteratwordend,True)
				self.writer.get_buffer().begin_user_action()
				self.writer.get_buffer().delete(iteratwordstart,iteratwordend)
				self.writer.get_buffer().insert_at_cursor(text_string.upper())
				self.writer.get_buffer().end_user_action()
		elif option == 'selection_to_html':
			bounds = self.writer.get_buffer().get_selection_bounds();
			if (bounds):
				iteratwordstart,iteratwordend = bounds
				text_string = self.writer.get_buffer().get_text(iteratwordstart,iteratwordend,True)
				self.clipboard.set_text(self.md.convert(text_string), -1)	
		elif option == 'all_to_html':
			iteratwordstart = self.writer.get_buffer().get_start_iter()
			iteratwordend = self.writer.get_buffer().get_end_iter()
			text_string = self.writer.get_buffer().get_text(iteratwordstart,iteratwordend,True)
			self.clipboard.set_text(self.md.convert(text_string), -1)		
		elif option == 'statusbar':
			if self.statusbar.get_visible():				
				self.statusbar.set_visible(False)
				self.menus['statusbar'].set_label(_('Show status bar'))
			else:				
				self.statusbar.set_visible(True)
				self.menus['statusbar'].set_label(_('Hide status bar'))
		elif option == 'toolbar':
			if self.toolbar.get_visible():				
				self.toolbar.set_visible(False)
				self.menus['toolbar'].set_label(_('Show Toolbar'))
			else:				
				self.toolbar.set_visible(True)
				self.menus['toolbar'].set_label(_('Hide Toolbar'))
		elif option == 'bold':	
			self.writer.get_buffer().begin_user_action()
			self.wrap_text('**','**')
			aniter = self.writer.get_buffer().get_iter_at_mark(self.writer.get_buffer().get_insert())
			aniter.backward_chars(2)
			self.writer.get_buffer().place_cursor(aniter)
			self.writer.get_buffer().end_user_action()
			self.update_buffer()
		elif option == 'italic':
			self.writer.get_buffer().begin_user_action()
			self.wrap_text('*','*')
			aniter = self.writer.get_buffer().get_iter_at_mark(self.writer.get_buffer().get_insert())
			aniter.backward_chars(1)
			self.writer.get_buffer().place_cursor(aniter)
			self.writer.get_buffer().end_user_action()
			self.update_buffer()
		elif option == 'strikethrough':
			self.writer.get_buffer().begin_user_action()
			self.wrap_text('~~','~~')
			aniter = self.writer.get_buffer().get_iter_at_mark(self.writer.get_buffer().get_insert())
			aniter.backward_chars(1)
			self.writer.get_buffer().place_cursor(aniter)
			self.writer.get_buffer().end_user_action()
			self.update_buffer()			
		elif option == 'subscript':
			self.writer.get_buffer().begin_user_action()
			self.wrap_text('--','--')
			aniter = self.writer.get_buffer().get_iter_at_mark(self.writer.get_buffer().get_insert())
			aniter.backward_chars(2)
			self.writer.get_buffer().place_cursor(aniter)
			self.writer.get_buffer().end_user_action()
			self.update_buffer()			
		elif option == 'superscript':
			self.writer.get_buffer().begin_user_action()
			self.wrap_text('++','++')
			aniter = self.writer.get_buffer().get_iter_at_mark(self.writer.get_buffer().get_insert())
			aniter.backward_chars(2)
			self.writer.get_buffer().place_cursor(aniter)
			self.writer.get_buffer().end_user_action()
			self.update_buffer()			
		elif option == 'highlight':
			self.writer.get_buffer().begin_user_action()
			self.wrap_text('==','==')
			aniter = self.writer.get_buffer().get_iter_at_mark(self.writer.get_buffer().get_insert())
			aniter.backward_chars(2)
			self.writer.get_buffer().place_cursor(aniter)
			self.writer.get_buffer().end_user_action()
			self.update_buffer()			
		elif option == 'underline':
			self.writer.get_buffer().begin_user_action()
			self.wrap_text('__','__')
			aniter = self.writer.get_buffer().get_iter_at_mark(self.writer.get_buffer().get_insert())
			aniter.backward_chars(2)
			self.writer.get_buffer().place_cursor(aniter)
			self.writer.get_buffer().end_user_action()
			self.update_buffer()			
		elif option == 'rule':
			self.writer.get_buffer().begin_user_action()
			self.insert_at_cursor('\n---\n')
			self.writer.get_buffer().end_user_action()
		elif option == 'more':
			self.writer.get_buffer().begin_user_action()
			self.insert_at_cursor('\n<!--more-->\n')
			self.writer.get_buffer().end_user_action()
		elif option == 'image':
			cm = InsertImageDialog()
			if 	cm.run() == Gtk.ResponseType.ACCEPT:
				alt_text = cm.alt_text.get_text()
				title = cm.title.get_text()
				url = cm.url.get_text()
				if not url.startswith('http://') and not url.startswith('https://'):
					url = 'http://'+url				
				self.writer.get_buffer().begin_user_action()
				self.insert_at_cursor('![%s](%s  "%s")'%(alt_text,url,title))
				self.writer.get_buffer().end_user_action()
			cm.hide()
			cm.destroy()				
		elif option == 'url':
			cm = InsertUrlDialog()
			if 	cm.run() == Gtk.ResponseType.ACCEPT:
				alt_text = cm.alt_text.get_text()
				url = cm.url.get_text()
				if not url.startswith('http://') and not url.startswith('https://'):
					url = 'http://'+url
				self.writer.get_buffer().begin_user_action()
				self.insert_at_cursor('[%s](%s)'%(alt_text,url))
				self.writer.get_buffer().end_user_action()
			cm.hide()
			cm.destroy()				
		elif option == 'timestamp':
			self.writer.get_buffer().begin_user_action()
			self.insert_at_cursor(datetime.datetime.fromtimestamp(time.time()).strftime('%A, %d de %B de %Y'))
		elif option == 'preview':
			if self.preview_or_html.get_label() == _('Html'):
				#child.viewer1.set_view_source_mode(False)
				self.preview_or_html.set_label(_('Html'))
				self.show_source_code(False)
			else:
				#child.viewer1.set_view_source_mode(True)
				self.preview_or_html.set_label(_('Preview'))
				self.show_source_code(True)		
		elif option == 'spellcheck':
			if self.tools['spellcheck'].get_active():
				self.spellchecker.attach(self.writer)
			else:
				self.spellchecker.detach()
				
	def get_first_n_characters_at_previous_line(self,n):
		textbuffer = self.writer.get_buffer()
		cursor_mark = textbuffer.get_insert()
		iterator_cursor = textbuffer.get_iter_at_mark(cursor_mark)
		iterator  = textbuffer.get_iter_at_mark(cursor_mark)
		if iterator.get_line() > 0:
			iterator.backward_line()
		else:
			if not iterator.is_start():
				iterator.backward_chars(iterator.get_line_offset())
		left_mark = textbuffer.create_mark('left_mark',iterator,False)
		iterator.forward_chars(n)
		right_mark = textbuffer.create_mark('right_mark',iterator,False)
		iterator_left = textbuffer.get_iter_at_mark(left_mark)
		iterator_right = textbuffer.get_iter_at_mark(right_mark)
		textbuffer.delete_mark_by_name('left_mark')
		textbuffer.delete_mark_by_name('right_mark')
		thetext = textbuffer.get_text(iterator_left,iterator_right,True)
		return thetext
		
	def insert_at_start_of_line(self,tag):
		textbuffer = self.writer.get_buffer()
		cursor_mark = textbuffer.get_insert()
		iterator_cursor = textbuffer.get_iter_at_mark(cursor_mark)
		iteratwordstart = textbuffer.get_iter_at_mark(cursor_mark)
		iteratwordstart.backward_chars(1)
		left_mark = textbuffer.create_mark('left',iteratwordstart,False)
		iterator_left = textbuffer.get_iter_at_mark(left_mark)
		temporal = textbuffer.get_text(iterator_left,iterator_cursor,True)
		textbuffer.delete_mark_by_name('left')
		if temporal.find('\r')>-1 or temporal.find('\n')>-1 or iterator_cursor.is_start():
			textbuffer.insert_at_cursor('%s '%tag)
		else:				
			textbuffer.insert_at_cursor('\n%s '%tag)
		self.update_buffer()

	def insert_at_cursor(self,tag):
		textbuffer = self.writer.get_buffer()
		textbuffer.insert_at_cursor('%s'%tag)
		self.update_buffer()
		
	def wrap_text(self,start_tag,end_tag):
		textbuffer = self.writer.get_buffer()
		cursor_mark = textbuffer.get_insert()
		bounds = textbuffer.get_selection_bounds();
		if (bounds):
			iteratwordstart,iteratwordend = bounds
		else:
			iteratwordstart = textbuffer.get_iter_at_mark(cursor_mark)
			iteratwordstart.backward_chars(1)
			left = textbuffer.create_mark('left',iteratwordstart,False)
			iteratwordstart.forward_chars(2)
			right = textbuffer.create_mark('right',iteratwordstart,False)
			iterator_left = textbuffer.get_iter_at_mark(left)
			iterator_right = textbuffer.get_iter_at_mark(right)
			temporal = textbuffer.get_text(iterator_left,iterator_right,True)
			textbuffer.delete_mark_by_name('left')
			textbuffer.delete_mark_by_name('right')
			if temporal.find('\r')>-1 or temporal.find('\n')>-1 or temporal.find(' ')>-1 or temporal.find('\'')>-1 or temporal.find('\"')>-1:
				iteratwordstart = textbuffer.get_iter_at_mark(cursor_mark)
				iteratwordend = textbuffer.get_iter_at_mark(cursor_mark)
			else:
				iteratwordstart = textbuffer.get_iter_at_mark(cursor_mark)
				if not iteratwordstart.starts_word():
					iteratwordstart.backward_word_start()
				iteratwordend = textbuffer.get_iter_at_mark(cursor_mark)
				if not iteratwordend.ends_word():
					iteratwordend.forward_word_end()
		thetext = textbuffer.get_text(iteratwordstart,iteratwordend,True)
		textbuffer.delete(iteratwordstart,iteratwordend)
		textbuffer.insert_at_cursor(start_tag+thetext+end_tag)
	def wrap_selection(self, start_tag, end_tag):
		"""This fucntion is used to wrap the currently selected
		text in the gtk.TextView with start_tag and end_tag. If
		there is no selection start_tag and end_tag will be
		inserted at the cursor position
		start_tag - The text that will go at the start of the
		selection.
		end_tag - The text that will go at the end of the
		selection."""
		textbuffer = self.writer.get_buffer()
		start, end = self.get_selection_iters();
		if ((not start)or(not end)):
			self.show_error_dlg("Error inserting text")
			return;
		#Create a mark at the start and end
		start_mark = textbuffer.create_mark(None,start, True)
		end_mark = textbuffer.create_mark(None, end, False)
		#Insert the start_tag
		textbuffer.insert(start, start_tag)
		#Get the end iter again
		end = textbuffer.get_iter_at_mark(end_mark)
		#Insert the end tag
		textbuffer.insert(end, end_tag)
		#Get the start and end iters
		start = textbuffer.get_iter_at_mark(start_mark)
		end = textbuffer.get_iter_at_mark(end_mark)
		#Select the text
		textbuffer.select_range(end,start)
		#Delete the gtk.TextMark objects
		textbuffer.delete_mark(start_mark)
		textbuffer.delete_mark(end_mark)		
	def remove_all_tag(self,tag_name):
		start_iter = self.writer.get_buffer().get_start_iter()
		end_iter = self.writer.get_buffer().get_end_iter()
		self.writer.get_buffer().remove_tag_by_name(tag_name,start_iter,end_iter)
		
	def search_and_mark(self, text, start):
		end = self.writer.get_buffer().get_end_iter()
		match = start.forward_search(text, 0, end)
		if match != None:
			match_start, match_end = match
			self.writer.get_buffer().apply_tag(self.tag_found, match_start, match_end)
			self.search_and_mark(text, match_end)
			
	def search_and_replace(self,text_to_search,text_replace_with,start):
		end = self.writer.get_buffer().get_end_iter()
		match = start.forward_search(text_to_search, 0, end)
		if match != None:
			match_start, match_end = match
			self.writer.get_buffer().delete(match_start,match_end)
			self.writer.get_buffer().insert(match_start,text_replace_with)
			iterator_cursor = self.writer.get_buffer().get_iter_at_mark(self.writer.get_buffer().get_insert())
			self.search_and_replace(text_to_search,text_replace_with,iterator_cursor)

if __name__ == "__main__":
	# Use threads                                       
	GObject.threads_init()
	win = uText()
	#win.connect("delete-event", Gtk.main_quit)
	Gtk.main()
	sys.exit(Gtk.main_quit())
