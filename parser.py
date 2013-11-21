# Earley Parser in Python 3
# Copyright (C) 2013 tobyp

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

from json import JSONEncoder
import re

class Rule:
	def __init__(self, lhs, rhs, func):
		self.lhs = lhs
		if isinstance(rhs, str):
			rhs = rhs.split(" ")
		self.rhs = rhs
		self.func = func

	def __repr__(self):
		return "Rule" + "{" + (self.lhs or "-") + " :== " + " ".join(self.rhs) + "}"

	def __eq__(self, other):
		return self.lhs == other.lhs and self.rhs == other.rhs

class Grammar:
	def __init__(self, rule_list, start):
		self.terms = {}
		for r in rule_list:
			self.terms.setdefault(r.lhs, []).append(r)
		self.start = start

	def __getitem__(self, term):
		return self.terms[term]

	def __contains__(self, term):
		return term in self.terms

	def get(self, key, default):
		return self.terms.get(key, default)

class Entry:
	def __init__(self, name, regex, func):
		self.name = name
		self.regex = re.compile(regex)
		self.func = func

class Lexicon:
	def __init__(self, entries):
		self.entries = entries

	def __iter__(self):
		return self.entries.__iter__()

class Token:
	def __init__(self, name, text, value):
		self.name = name
		self.value = value
		self.text = text

	def __repr__(self):
		return "Token{%s = %r}" % (self.name or "", self.text)

class Scanner:
	def __init__(self, lexicon):
		self.lexicon = lexicon

	def scan(self, inp):
		pos = 0
		while pos < len(inp):
			pos_start = pos
			for e in self.lexicon:
				m = e.regex.match(inp, pos)
				if m and pos == m.start():
					if e.name != None:
						yield Token(e.name, m.group(), e.func(m))
					pos = m.end()
					break
			if pos == pos_start:
				raise ValueError("No token recognized at pos=%d" % pos)

class EdgeSet:
	def __init__(self):
		self.content = []
		self.count = 0
		
	def add(self, i):
		try:
			return self.content[self.content.index(i)]
		except ValueError:
			pass
		self.content.append(i)
		self.count += 1
		return i
	
	def __delitem__(self, idx):      
		if idx >= self.count:
			raise IndexError
		del self.content[idx]
		self.count -= 1
	
	def __getitem__(self, idx):
		return self.content[idx]
	
	def __iter__(self):
		i = 0
		while i < self.count:
			yield self.content[i]
			i += 1
	
	def __len__(self):
		return self.count
	
	def __repr__(self):
		return "EdgeSet{" + ", ".join([repr(x) for x in self.content]) + "}"

class Edge:
	def __init__(self, rule, dot, start, previous=None, completing=None):
		self.rule = rule
		self.dot = dot
		self.start = start
		self.previous = previous
		self.completing = completing

	def complete(self):
		return self.dot >= len(self.rule.rhs)

	def next(self):
		return self.rule.rhs[self.dot]

	def prev(self):
		if self.dot > 0:
			return self.rule.rhs[self.dot-1]
		return None

	def __repr__(self):
		return "(" + " ".join([self.rule.lhs or "", ":=="] + list(self.rule.rhs[:self.dot]) + ["."] + list(self.rule.rhs[self.dot:]) + ["@", str(self.start)]) + ")"

	def __eq__(self, other):
		return self.dot == other.dot and self.start == other.start and self.rule == other.rule

class Chart:
	def __init__(self, length):
		self.sets = [EdgeSet() for i in range(0,length)]

	def __getitem__(self, i):
		return self.sets[i]

	def __repr__(self):
		return "\n".join(["{" + ("\n" + "\n".join(["\t" + repr(s) for s in sset]) + "\n" if len(sset) > 0 else "") + "}," for sset in self.sets])

class Recognizer:
	def __init__(self, grammar):
		self.grammar = grammar

	def recognize(self, tokens):
		def predict(chart, state, j, grammar):
			for r in grammar.get(state.next(), []):
				chart[j].add(Edge(r, 0, j))

		def scan(chart, state, j, tokens):
			if j < len(tokens) and tokens[j].name == state.next():
				chart[j+1].add(Edge(state.rule, state.dot+1, state.start, previous=state, completing=tokens[j]))
				
		def complete(chart, state, j):
			completed = state.rule.lhs
			for e in chart[state.start]:
				if not e.complete() and e.next() == state.rule.lhs:
					chart[j].add(Edge(e.rule, e.dot+1, e.start, e, state))

		chart = Chart(len(tokens)+1)
		chart[0].add(Edge(Rule(None, [self.grammar.start], lambda r: r), 0, 0))

		for i in range(0, len(tokens)+1):
			if len(chart[i]) == 0:
				raise ValueError("Unexpected %r at token %d" % (tokens[i-1], i-1), tokens, chart)
			for state in chart[i]:
				if not state.complete():
					if state.next() in self.grammar:
						predict(chart, state, i, self.grammar)
					else:
						scan(chart, state, i, tokens)
				else:
					complete(chart, state, i)
		
		return chart

class Parser:
	def __init__(self, grammar):
		self.grammar = grammar

	def parse(self, chart, tokens):
		def build_children(st):
			if st.completing is not None:
				children = [build_node(st.completing)]
			else:
				return []

			if st.previous is not None:
				children = build_children(st.previous) + children

			return children

		def build_node(state):
			if isinstance(state, Token):
				return state.value
			else:
				ch = build_children(state)
				return state.rule.func(*ch)

		complete_parses = [s for s in chart[-1] if s.rule.lhs == None and s.complete()]
		if len(complete_parses) == 0: raise ValueError("No complete parses exist.")
		return build_node(complete_parses[0])

def parse(lexicon, grammar, input):
	s = Scanner(lexicon)
	tokens = list(s.scan(input))
	
	r = Recognizer(grammar)
	chart = r.recognize(tokens)
	
	p = Parser(grammar)
	tree = p.parse(chart, tokens)
	
	return tree
