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

'''
Math extension for Python-Markdown
==================================

Adds support for displaying math formulas using
[MathJax](http://www.mathjax.org/).

Author: 2015, Dmitry Shachnev <mitya57@gmail.com>.
'''

import markdown


class MathExtension(markdown.extensions.Extension):
    def __init__(self, *args, **kwargs):
        self.config = {
            'enable_dollar_delimiter': [False,
                                        'Enable single-dollar delimiter'],
        }
        super(MathExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        def handle_match_inline(m):
            node = markdown.util.etree.Element('script')
            node.set('type', 'math/tex')
            node.text = markdown.util.AtomicString(m.group(3))
            return node

        def handle_match(m):
            node = markdown.util.etree.Element('script')
            node.set('type', 'math/tex; mode=display')
            if '\\begin' in m.group(2):
                node.text = markdown.util.AtomicString(m.group(2) +
                                                       m.group(4) +
                                                       m.group(5))
            else:
                node.text = markdown.util.AtomicString(m.group(3))
            return node

        inlinemathpatterns = (
            # $...$
            markdown.inlinepatterns.Pattern(r'(?<!\\|\$)(\$)([^\$]+)(\$)'),
            # \(...\)
            markdown.inlinepatterns.Pattern(r'(?<!\\)(\\\()(.+?)(\\\))')
        )
        mathpatterns = (
            # $$...$$
            markdown.inlinepatterns.Pattern(r'(?<!\\)(\$\$)([^\$]+)(\$\$)'),
            # \[...\]
            markdown.inlinepatterns.Pattern(r'(?<!\\)(\\\[)(.+?)(\\\])'),
            markdown.inlinepatterns.Pattern(
                r'(?<!\\)(\\begin{([a-z]+?\*?)})(.+?)(\\end{\3})')
        )
        if not self.getConfig('enable_dollar_delimiter'):
            inlinemathpatterns = inlinemathpatterns[1:]
        for i, pattern in enumerate(inlinemathpatterns):
            pattern.handleMatch = handle_match_inline
            md.inlinePatterns.add('math-inline-%d' % i, pattern, '<escape')
        for i, pattern in enumerate(mathpatterns):
            pattern.handleMatch = handle_match
            md.inlinePatterns.add('math-%d' % i, pattern, '<escape')


def makeExtension(*args, **kwargs):
    return MathExtension(*args, **kwargs)
