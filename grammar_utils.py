# Earley Parser in Python 3 - Utilities for custom grammars
# Copyright (C) 2013, 2016 tobyp
# See <http://tobyp.net/parsepy>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


class Node:
	'''Like a dictionary but with an extra "type identifier" for the node.'''
	def __init__(self, typ, **kwargs):
		self.type = typ
		self.data = kwargs

	def __str__(self):
		return stringify(self)

	def __repr__(self):
		return stringify(self)


def stringify(x, indent='\t', level=0):
	'''Serialize Node trees to strings with indentation. Format is similar to json, but puts the node type in front.
	Example: NodeType {
		key1: [
			value1,
			NodeType {}
		],
		key2: NodeType {
			key3: value3
		}
	}
	'''
	if isinstance(x, Node):
		return "%r " % x.type + ("{ }" if len(x.data) == 0 else "{\n" + ",\n".join([indent * (level + 1) + repr(k) + ': ' + stringify(v, indent, level + 1) for k, v in x.data.items()]) + "\n" + indent * level + "}")
	elif isinstance(x, (list, tuple)):
		return "[ ]" if len(x) == 0 else "[\n" + ",\n".join([indent * (level + 1) + stringify(v, indent, level + 1) for v in x]) + "\n" + indent * level + "]"
	else:
		return repr(x)
