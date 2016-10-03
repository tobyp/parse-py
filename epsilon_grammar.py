# Earley Parser in Python 3
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

from .parser import Rule, Grammar
from itertools import chain


def space_out_args(nrs, spacing, args):
	res = ()
	g = (a for a in args)
	for t, nonnull in spacing:
		if not nonnull:
			res += (nrs[t].func(),)
		else:
			res += (next(g),)
	return res


def gen_lambda(nrs, rule, variant):
	# Don't define the lambda in situ. Closing over loop variables will be immensely frustrating.
	return lambda *args: rule.func(*space_out_args(nrs, variant, args))


class EpsilonGrammar(Grammar):
	'''This grammar accepts rules with no terms on the right side (Epsilon rules).
	It works by converting the epsilon-grammar to a non-epsilon grammar.
	'''
	def __init__(self, rules):
		Grammar.__init__(self, rules)
		self.nullability = {}
		self.nully_rules = {}

		def nullable(term):
			if term in self.nullability:  # already calculated nullability? I read this sort of thing is a part of "dynamic programming", which sounds impressive, but I don't think it's a thing you _design_ towards anyway. You just look back and say, "hey, doesn't that fit what I read about dyna..." *deja vu*
				return self.nullability[term]
			self.nullability[term] = False  # this will stop us recursing, see above. It will not, however, stop us cursing in the first place. </pun>
			if term not in self.terms:
				return False  # a non-non-terminal, is, of course, non-non-non-nullable.
			for rule in self.terms[term]:  # a rule is nullable <=> all of its terms are nullable (obviously if it at some point contains itself, that makes at least this rule not nullable (unless it already is (in which case I hope I've now confused you completely), in which case it will be nullable anyway).
				if len(rule.rhs) == 0:
					self.nully_rules[rule.lhs] = rule
				for t in rule.rhs:
					if not nullable(t):
						break
				else:  # Don't you love python? This is called if the loop exists normally, not via break
					self.nullability[term] = True
					return True
			return False

		for t in self.terms:
			nullable(t)

		def null_variants(terms):
			if len(terms) == 0:
				yield ()
			else:
				head = terms[0]
				tail = terms[1:]
				for v in null_variants(tail):
					yield ((head, True),) + v
					if self.nullability.get(head, False):
						yield ((head, False),) + v

		new_terms = {}
		for rul in chain(*self.terms.values()):
			for variant in null_variants(rul.rhs):
				if len(variant) > 0:  # leave out "T := " rules
					nrf = gen_lambda(self.nully_rules, rul, variant)
					new_terms.setdefault(rul.lhs, []).append(Rule(rul.lhs, tuple(x[0] for x in variant if x[1]), nrf))

		self.terms = new_terms
