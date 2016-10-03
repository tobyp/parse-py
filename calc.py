#!/bin/python3

# Earley Parser in Python 3 - Example program
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

from parser import Grammar, Rule, Lexicon, Entry, parse
from math import sin, cos, tan, asin, acos, atan, sqrt, exp, log, log10, floor, ceil, fabs, erf, gamma

constants = {
	'PI': 3.14159265358979323846264338327950288,
	'E': 2.71828182845904523536028747135266249,
	'PHI': 1.61803398874989484820458683436563811,
	'GAMMA': 0.57721566490153286060651209008240243
}

functions = {
	'sin': sin,
	'cos': cos,
	'tan': tan,
	'asin': asin,
	'acos': acos,
	'atan': atan,
	'sqrt': sqrt,
	'rt': lambda l, r: l**(1 / r),
	'exp': exp,
	'log': log,
	'log10': lambda x: log10(x),
	'ln': lambda x: log(x),
	'floor': floor,
	'ceil': ceil,
	'abs': fabs,
	'erf': erf,
	'gamma': gamma,
	'+': lambda l, r: l + r,
	'-': lambda l, r: l - r,
	'*': lambda l, r: l * r,
	'/': lambda l, r: l / r,
	'//': lambda l, r: l // r,
	'%': lambda l, r: l % r,
	'^': lambda l, r: l ** r
}

math_lexicon = Lexicon([
	Entry('(', r'\(', lambda m: None),
	Entry(')', r'\)', lambda m: None),
	Entry(',', r',', lambda m: None),
	Entry('number', r'[0-9]+(\.[0-9]+)?', lambda m: float(m.group(0))),
	Entry('op0', r'[\+-]', lambda m: m.group(0)),
	Entry('op1', r'[\*/%]|//', lambda m: m.group(0)),
	Entry('op2', r'[\^]', lambda m: m.group(0)),
	Entry('ident', r'[a-z_A-Z][a-z_A-Z0-9]*', lambda m: m.group(0)),
	Entry(None, r'\s+', lambda *args: None)
])

math_grammar = Grammar([
	Rule('expression0', ('number',), lambda n: n),
	Rule('expression0', ('ident',), lambda n: constants[n]),

	Rule('expression0', ('ident', '(', ')'), lambda n, l, r: functions[n]()),
	Rule('expression0', ('ident', '(', 'arglist', ')'), lambda n, l, a, r: functions[n](*a)),

	Rule('arglist', ('expression4',), lambda e: [e]),
	Rule('arglist', ('arglist', ',', 'expression4',), lambda al, e: al + [e]),

	Rule('expression0', ('(', 'expression4', ')'), lambda l, i, r: i),

	Rule('expression1', ('expression0',), lambda e: e),
	Rule('expression1', ('op0', 'expression0',), lambda s, e: e * (-1.0 if s == '-' else 1.0)),

	Rule('expression2', ('expression2', 'op0', 'expression1'), lambda l, o, r: functions[o](l, r)),
	Rule('expression2', ('expression1',), lambda e: e),

	Rule('expression3', ('expression3', 'op1', 'expression2'), lambda l, o, r: functions[o](l, r)),
	Rule('expression3', ('expression2',), lambda e: e),

	Rule('expression4', ('expression4', 'op2', 'expression3'), lambda l, o, r: functions[o](l, r)),
	Rule('expression4', ('expression3',), lambda e: e),

	Rule('expression', ('expression4',), lambda e: e),
])

if __name__ == '__main__':
	from sys import stdin

	for l in stdin:
		try:
			print(parse(math_lexicon, math_grammar, 'expression', l))
		except:
			print("Error")
