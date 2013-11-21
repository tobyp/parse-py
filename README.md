# parse-py
Earley Parser in Python 3

Copyright (C) 2013 tobyp. Licensed under the GNU General Public License v3+. See the code and the LICENSE file.
***

## Overview
Jay Earley's parsing algorithm can parse pretty much all context-free languages (though they might need to be processed in some way first -- see Advanced Grammars below). The algorithm is easy to understand and follow, simple enough to implement, and (in my opinion) simply beautiful. This parser is intended more as a proof-of-concept parser than a performance-optimized, practically feasible parser.

## Implementation description
Everything needed for simple parsing is included in the file `parser.py`.
In this implementation, tokens are scanned greedily using regular expressions. Each terminal type can contain a function to produce a more useful/desirable form of value for continued parsing than a simple substring of the input, by transforming a re.MatchObject. (The special `None` token is used to swallow whitespace/comments/whatever you don't need.)

Each production rule is also provided with a function to transform its parsed parts into a more useful/processed form, to be passed up as arguments into rule-functions of other productions containing it in their right-hand side. This is especially useful for creating trees like ASTs (`grammar_utilities.py` contains a bit of code that might help for this sort of thing).

## Example
The file `calc.py` contains a simple calculator for mathematical expressions (read line-by-line from standard input), supporting basic arithmetic operators, a handful of functions, and a few constants.

## Advanced Grammars
Grammars with epsilon rules (i.e. productions with no symbols on the right-hand side) can be used with the EpsilonGrammar class (`epsilon_grammar.py`). This works by converting the grammar into a form without epsilon-rules. CAUTION: grammars with an epsilon rule for the start nonterminal are not supported. Check for this trivial case manually before you parse.

### Complex Grammars
To save some work with frequently used constructs like optional symbols, alternatives, or repetition of symbols, the ComplexGrammar class (`complex_grammar.py`) will process a grammar with special syntax for the right-hand sides of the production rules, and produce an EpsilonGrammar (that will in turn produce a normal Grammar) that works equivalently. The rule functions of this grammar are a bit more complicated. A small example is contained at the bottom of `complex_grammar.py`

#### Complex Grammar syntax
* `term2` (tightest binding):
    * `(term)`
        * description: group symbols.
        * passed as: list
        * example: `A (LPAREN RPAREN) B` parsing `A LPAREN RPAREN B` would pass of `'A', ['LPAREN', 'RPAREN'], 'B'`
    * `[term]`
        * description: optional term.
        * passed as: None or list
        * example: `A [LPAREN RPAREN] B` parsing `A LPAREN RPAREN B` would pass `'A', ['LPAREN', 'RPAREN'], 'B'`
        * example: `A [LPAREN RPAREN] B` parsing `A B` would pass `'A', None, 'B'`
    * `{term}`
        * description: repeat term
        * passed as: list
        * example: `A {B} C` parsing `A B B B C` would pass `'A', ['B', 'B', 'B'], 'C'`
    * `{term:token}`
        * description: list with seperator (note that the seperator can only be a token, not a term)
        * passed as: list (without seperators, those are dropped)
        * example: `A {B:C} D` parsing `A B C B D` would pass `'A', ['B', 'B'], 'D'`
* `term1` (medium binding)
    * `term1 | term2`
        * description: alternative. Groups left to right.
        * passed as: however the alternative that was picked is passed
        * example: `A | B` parsing `A` would pass `'A'`
        * example: `A | (B | C)` parsing `B` would pass `['B']`
    * `term2`
        * description: anything that can be a `term2` can also be a `term1` - for obvious reasons.
* `term` (loostest binding)
    * `term term1`
        * description: concatenation. Groups left to right.
        * passed as: seperate arguments.
        * example: `A B C` parsing `A B C` would simply pass `'A', 'B', 'C'` (not `'A', ['B', 'C']` and not `['A', 'B', 'C']`!)

A good way to check out how this works would be to wrap the lambda function creation in `ComplexGrammar.simplify_term` in a way that gives you useful information (stack dumps are rather unhelpful if there are a lot of lambdas involved), and then look at the the `terms` member of the `ComplexGrammar` object (which will have the rules as simplified by `ComplexGrammar` and `EpsilonGrammar`).