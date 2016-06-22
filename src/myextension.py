##!/usr/bin/env python
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

import markdown
from markdown.extensions import Extension
import markdown.inlinepatterns

DEL_RE = r'(~~)(.*?)~~'
SUB_RE = r'(--)(.*?)--'
SUP_RE = r'(\++)(.*?)\++'
MARK_RE = r'(==)(.*?)=='
UNDERLINE_RE = r'(__)(.*?)__'

class MyExtension(Extension):
	def extendMarkdown(self, md, md_globals):
		## DEL
		# Create the del pattern
		del_tag = markdown.inlinepatterns.SimpleTagPattern(DEL_RE, 'del')
		# Insert del pattern into markdown parser
		md.inlinePatterns.add('del', del_tag, '>not_strong')
		## SUB
		# Create the sub pattern
		sub_tag = markdown.inlinepatterns.SimpleTagPattern(SUB_RE, 'sub')
		# Insert sub pattern into markdown parser
		md.inlinePatterns.add('sub', sub_tag, '>not_strong')

		## SUP
		# Create the sup pattern
		sup_tag = markdown.inlinepatterns.SimpleTagPattern(SUP_RE, 'sup')
		# Insert sup pattern into markdown parser
		md.inlinePatterns.add('sup', sup_tag, '>not_strong')

		## MARK
		# Create the mark pattern
		mark_tag = markdown.inlinepatterns.SimpleTagPattern(MARK_RE, 'mark')
		# Insert mark pattern into markdown parser
		md.inlinePatterns.add('mark', mark_tag, '>not_strong')

		## UNDERLINE
		# Create the mark pattern
		underline_tag = markdown.inlinepatterns.SimpleTagPattern(UNDERLINE_RE, 'u')
		# Insert mark pattern into markdown parser
		md.inlinePatterns.add('u', underline_tag, '>not_strong')

def makeExtension(configs=None):
	return MyExtension(configs=configs)

if __name__ == "__main__":
	print(markdown.markdown('foo ~~deleted~~ bar', extensions=[MyExtension()]))
	print(markdown.markdown('foo --sub-- bar', extensions=[MyExtension()]))
	print(markdown.markdown('foo ++sup++ bar', extensions=[MyExtension()]))
	print(markdown.markdown('foo ==highlight== bar', extensions=[MyExtension()]))
	print(markdown.markdown('foo __underline__ bar', extensions=[MyExtension()]))
