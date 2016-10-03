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

from .parser import Grammar, Rule, Lexicon, Entry, parse
from .epsilon_grammar import EpsilonGrammar


class ComplexGrammar(EpsilonGrammar):
	'''Write grammars with some more complicated syntax for optional, alternative, or repeated parts.
	term2 (tightest binding operators)
		(term) - grouping. In a rule, this is passed as a tuple of the contents
		[term] - optional. In a rulefunc, this is either None or a tuple of the contents
		{term} - repeat one or more. In a rulefunc, these are passed as a list.
		{term:token} - repeat one or more with seperator. Passed like {term}. The seperators are all dropped.
	term1
		term1 | term2 - alternative. Groups left to right. A rulefunc gets the alternative that appears in the parsed text.
		term2 - for obvious reasons.
	term
		term term1 - concatenation. Groups left to right. A rulefunc gets each of these as seperate arguments.
		term1 - for obvious reasons.

	Check out the normal grammar this generates. Might be interesting to see how it's done.
	Regex analogy: [] = ?, {} = +, [{}] = *
	{A:B} can be A, or A B A, or A B A B A, or A B A B A B A, ...
	'''
	gr_tokens = Lexicon([
		Entry('rule', r'::=|:==', lambda x: None),
		Entry('alt', r'\|', lambda x: None),
		Entry('lbrack', r'\[', lambda x: None),
		Entry('rbrack', r'\]', lambda x: None),
		Entry('lbrace', r'\{', lambda x: None),
		Entry('rbrace', r'\}', lambda x: None),
		Entry('detail', r':', lambda x: None),
		Entry('lgroup', r'\(', lambda x: None),
		Entry('rgroup', r'\)', lambda x: None),
		Entry('token', r'[A-Za-z_][A-Za-z_0-9]*', lambda m: m.group(0)),
		Entry(None, r'\s+', lambda x: None),
	])

	gr_grammar = Grammar([
		Rule('term', ('term', 'term1'), lambda t1, t2: {'type': 'concat', 'left': t1, 'right': t2}),
		Rule('term', ('term1',), lambda t: t),
		Rule('term1', ('term1', 'alt', 'term2'), lambda t1, x, t2: {'type': 'alt', 'left': t1, 'right': t2}),
		Rule('term1', ('term2',), lambda t: t),
		Rule('term2', ('lbrack', 'term', 'rbrack'), lambda x, t, y: {'type': 'optional', 'term': t}),
		Rule('term2', ('lbrace', 'term', 'rbrace'), lambda x, t, z: {'type': 'many', 'term': t}),
		Rule('term2', ('lbrace', 'term', 'detail', 'token', 'rbrace'), lambda x, t, y, u, z: {'type': 'many_sep', 'term': t, 'sep': u}),
		Rule('term2', ('lgroup', 'term', 'rgroup'), lambda l, t, r: {'type': 'group', 'term': t}),
		Rule('term2', ('token',), lambda t: {'type': 'token', 'token': t})
	])

	def __init__(self, rule_list):
		def gen_name(name, sub, runners):
			n = name + "_" + sub
			num = runners.setdefault(n, 0)
			runners[n] = num + 1
			return n + str(num)

		def simplify_term(parent, term, prods, runners={}):
			if term["type"] == "concat":
				return simplify_term(parent, term["left"], prods, runners) + simplify_term(parent, term["right"], prods, runners)
			elif term["type"] == "alt":
				alt_name = gen_name(parent, "alt", runners)
				prods.append(Rule(alt_name, simplify_term(alt_name, term["left"], prods, runners), lambda x: x))
				prods.append(Rule(alt_name, simplify_term(alt_name, term["right"], prods, runners), lambda x: x))
				return [alt_name]
			elif term["type"] == "optional":
				opt_name = gen_name(parent, "opt", runners)
				prods.append(Rule(opt_name, [], lambda: None))
				prods.append(Rule(opt_name, simplify_term(opt_name, term["term"], prods, runners), lambda *a: a))
				return [opt_name]
			elif term["type"] == "many":
				many_name = gen_name(parent, "many", runners)
				many_sim = simplify_term(many_name, term["term"], prods, runners)
				prods.append(Rule(many_name, many_sim, lambda x: [x]))
				prods.append(Rule(many_name, many_sim + [many_name], lambda x, y: [x] + y))
				return [many_name]
			elif term["type"] == "many_sep":
				many_sep_name = gen_name(parent, "sep", runners)
				many_sep_sim = simplify_term(many_sep_name, term["term"], prods, runners)
				prods.append(Rule(many_sep_name, many_sep_sim, lambda x: [x]))
				prods.append(Rule(many_sep_name, many_sep_sim + [term["sep"], many_sep_name], lambda x, y, z: [x] + z))
				return [many_sep_name]
			elif term["type"] == "group":
				grp_name = gen_name(parent, "grp", runners)
				grp_sim = simplify_term(grp_name, term["term"], prods, runners)
				prods.append(Rule(grp_name, grp_sim, lambda *a: a))
				return [grp_name]
			elif term["type"] == "token":
				return [term["token"]]
			return []

		prods = []
		for rule in rule_list:
			if isinstance(rule, (tuple, list)):
				rule = Rule(*rule)
			prods.append(Rule(rule.lhs, tuple(simplify_term(rule.lhs, parse(ComplexGrammar.gr_tokens, ComplexGrammar.gr_grammar, 'term', " ".join(rule.rhs)), prods)), rule.func))
		EpsilonGrammar.__init__(self, prods)


def main():
	lex = Lexicon([
		Entry('LPAREN', r'\(', lambda x: None),
		Entry('RPAREN', r'\)', lambda x: None),
		Entry('LBRACE', r'\{', lambda x: None),
		Entry('RBRACE', r'\}', lambda x: None),
		Entry('NUMBER', r'[0-9]+', lambda m: int(m.group(0))),
		Entry('COMMA', r',', lambda x: None),
		Entry(None, r'\s+', lambda x: None)
	])

	grm = ComplexGrammar([
		('item', ('NUMBER',), lambda n: n),
		('item', ('(LPAREN|LBRACE) [{item:COMMA}] (RPAREN|RBRACE)',), lambda l, i, a: list(i and i[0] or []))
	])

	print(parse(lex, grm, 'item', '({5, 3}, ((1, 2), (4, 7, {)}))'))

if __name__ == "__main__":
	main()
