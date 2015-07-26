#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
