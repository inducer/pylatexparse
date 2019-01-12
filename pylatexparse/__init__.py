__copyright__ = "Copyright (C) 2019 Andreas Kloeckner"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import re

CSEQ_RE = re.compile(r"\\(,|;|\\|\(|\)|\{|\}| |\[|\]|\"|[a-zA-Z*]+)")
ENVNAME_RE = re.compile(r"([a-zA-Z*]+)\s*}")


# {{{ node types

class LatexDoc:
    def __str__(self):
        return StringifyMapper().rec(self)


class Text(LatexDoc):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text

    mapper_method = "map_text"


class EndOfLine(LatexDoc):
    mapper_method = "map_eol"


class LatexDocContainer(LatexDoc):
    def __init__(self, content):
        self.content = content

    mapper_method = "map_container"


class Group(LatexDocContainer):
    mapper_method = "map_group"


class ControlSequence(LatexDoc):
    def __init__(self, name, args, optargs=None):
        self.name = name
        self.args = args
        if optargs is None:
            optargs = ()
        self.optargs = optargs

    mapper_method = "map_controlseq"


class Environment(LatexDocContainer):
    def __init__(self, name, args, optargs, content):
        self.name = name
        super().__init__(content)
        self.args = args
        self.optargs = optargs

    mapper_method = "map_environment"


# }}}


# {{{ visitors/mappers

class Mapper:
    def rec(self, node, *args):
        return getattr(self, node.mapper_method)(node, *args)


class StringifyMapper(Mapper):
    def map_text(self, node):
        return node.text

    def map_eol(self, node):
        return "\n"

    def map_container(self, node):
        return "".join(self.rec(ch) for ch in node.content)

    def map_group(self, node):
        return "{%s}" % "".join(self.rec(ch) for ch in node.content)

    def map_controlseq(self, node):
        args = (
            "".join("[%s]" % str(arg) for arg in node.optargs)
            +
            "".join("{%s}" % str(arg) for arg in node.args)
            )

        if not args:
            args = " "

        return r"\%s%s" % (
                node.name,
                args)

    def map_environment(self, node):
        args = (
            "".join("[%s]" % str(arg) for arg in node.optargs)
            +
            "".join("{%s}" % str(arg) for arg in node.args)
            )

        return r"\begin{%s}%s%s\end{%s}" % (
                node.name, args,
                "".join(self.rec(ch) for ch in node.content),
                node.name)


class IdentityMapper(Mapper):
    def map_iterable(self, iterable):
        return tuple(iterable)

    def map_container(self, node):
        return type(node)(
                self.map_iterable(self.rec(ch) for ch in node.content))

    map_group = map_container

    def map_eol(self, node):
        return node

    map_text = map_eol

    def map_controlseq(self, node):
        return type(node)(
                node.name,
                self.map_iterable(self.rec(ch) for ch in node.args),
                self.map_iterable(self.rec(ch) for ch in node.optargs))

    def map_environment(self, node):
        return type(node)(
                node.name,
                self.map_iterable(self.rec(ch) for ch in node.args),
                self.map_iterable(self.rec(ch) for ch in node.optargs),
                self.map_iterable(self.rec(ch) for ch in node.content),
                )


class EnvironmentGatherer(IdentityMapper):
    def map_iterable(self, iterable, i=0, end_i_box=None, env_name=None):
        result = []
        nodes = list(iterable)
        while i < len(nodes):
            n = nodes[i]

            if isinstance(n, ControlSequence) and n.name == "end":
                assert env_name == n.args[0].text
                if end_i_box is not None:
                    end_i_box[0] = i+1
                return result
            elif isinstance(n, ControlSequence) and n.name == "begin":
                i_box = [None]
                result.append(Environment(
                    n.args[0].text,
                    n.args[1:],
                    n.optargs,
                    self.map_iterable(
                        nodes, i=i+1, end_i_box=i_box,
                        env_name=n.args[0].text)))
                i = i_box[0]
                assert i is not None
            else:
                result.append(n)
                i += 1

        if env_name is not None:
            raise ValueError("missing end of environment '%s'" % env_name)

        return result

# }}}


# {{{ arg count table

CSNAME_TO_ARG_COUNTS = {
        "documentclass": (1, 1),
        "input": (1, 0),
        "subtitle": (1, 0),
        "date": (1, 0),
        "begin": (1, 0),
        "end": (1, 0),
        "section": (1, 0),
        "subsection": (1, 0),
        "footnote": (1, 0),
        "label": (1, 0),
        "ref": (1, 0),
        "eqref": (1, 0),
        "renewcommand": (2, 0),
        "arraystretch": (1, 0),
        "url": (1, 0),
        "cr": (1, 0),

        "vspace": (1, 0),
        "vspace*": (1, 0),
        "smallskip": (0, 0),
        "smallskip": (0, 0),
        "medskip": (0, 0),
        "bigskip": (0, 0),
        "hfill": (0, 0),
        "centering": (0, 0),
        "includegraphics": (1, 1),

        "textcolor": (1, 0),
        "color": (1, 0),
        "textbf": (1, 0),
        "textit": (1, 0),
        "emph": (1, 0),

        "frac": (2, 0),
        "sfrac": (2, 0),
        "sqrt": (1, 1),

        "bar": (0, 0),
        "hat": (0, 0),
        "tilde": (0, 0),

        "in": (0, 0),
        "sum": (0, 0),
        "int": (0, 0),
        "prod": (0, 0),
        "bigcup": (0, 0),
        "bigcap": (0, 0),
        "[": (0, 0),
        "]": (0, 0),

        "Delta": (0, 0),
        "Sigma": (0, 0),
        "Omega": (0, 0),
        "Phi": (0, 0),

        "alpha": (0, 0),
        "beta": (0, 0),
        "gamma": (0, 0),
        "delta": (0, 0),
        "epsilon": (0, 0),
        "phi": (0, 0),
        "psi": (0, 0),
        "pi": (0, 0),
        "mu": (0, 0),
        "nu": (0, 0),
        "lambda": (0, 0),
        "rho": (0, 0),
        "sigma": (0, 0),
        "kappa": (0, 0),
        "omega": (0, 0),
        "xi": (0, 0),

        "neq": (0, 0),
        "leq": (0, 0),
        "geq": (0, 0),
        "ll": (0, 0),

        "approx": (0, 0),
        "equiv": (0, 0),
        "subset": (0, 0),
        "subseteq": (0, 0),
        "cdot": (0, 0),
        "otimes": (0, 0),
        "times": (0, 0),
        "setminus": (0, 0),
        "cup": (0, 0),
        "cap": (0, 0),
        "land": (0, 0),
        "lor": (0, 0),
        "ldots": (0, 0),
        "cdots": (0, 0),
        "ddots": (0, 0),
        "vdots": (0, 0),
        "dots": (0, 0),
        "forall": (0, 0),
        "exists": (0, 0),
        "nabla": (0, 0),

        "Big": (0, 0),
        "Bigg": (0, 0),
        "big": (0, 0),
        "bigg": (0, 0),

        "hline": (0, 0),

        "Large": (0, 0),
        "tiny": (0, 0),

        "langle": (0, 0),
        "rangle": (0, 0),
        "star": (0, 0),
        "dagger": (0, 0),
        "cong": (0, 0),
        "pm": (0, 0),

        "lim": (0, 0),
        "det": (0, 0),
        "max": (0, 0),
        "min": (0, 0),
        "left": (1, 0),
        "right": (1, 0),
        "underbrace": (1, 0),
        "overbrace": (1, 0),

        "mathcal": (1, 0),
        "mathit": (1, 0),
        "mathbf": (1, 0),
        "mathbb": (1, 0),
        "mathop": (1, 0),
        "boldsymbol": (1, 0),
        "text": (1, 0),

        "quad": (0, 0),
        "qquad": (0, 0),
        "infty": (0, 0),
        "lfloor": (0, 0),
        "rfloor": (0, 0),
        "log": (0, 0),
        "sin": (0, 0),
        "cos": (0, 0),
        "arcsin": (0, 0),
        "arccos": (0, 0),

        "titlepage": (0, 0),
        "item": (0, 0),
        "bf": (0, 0),
        "it": (0, 0),

        "Leftrightarrow": (0, 0),
        "Rightarrow": (0, 0),
        "to": (0, 0),

        "\\": (0, 1),
        ",": (0, 0),
        "\"": (0, 0),
        "{": (0, 0),
        "}": (0, 0),
        "(": (0, 0),
        ")": (0, 0),
        " ": (0, 0),
        }

ENVNAME_TO_ARG_COUNTS = {
        "document": (0, 0),
        "frame": (1, 1),
        "itemize": (0, 0),
        "enumerate": (0, 0),
        "align": (0, 0),
        "align*": (0, 0),
        "alignat*": (0, 0),
        "bmatrix": (0, 0),
        "cases": (0, 0),
        "center": (0, 0),
        "tabular": (1, 0),
        "array": (1, 0),
        "matrix": (1, 0),
        }

# }}}


def skip_whitespace(s, i):
    while s[i] in ' \n\t' and i < len(s):
        i += 1
    return i


def make_container(iterable):
    nodes = tuple(iterable)
    if len(nodes) == 1:
        node, = nodes
        return node
    else:
        return LatexDocContainer(tuple(nodes))


# {{{ tokenizer

def tokenize(
        s, i, csname_to_arg_counts, envname_to_arg_counts,
        in_optional_arg=False, end_i_box=None):

    cur_str = []
    while i < len(s):
        c = s[i]

        if c == "%":
            while s[i] != "\n" and i < len(s):
                i += 1

        elif c == "\n":
            if "".join(cur_str):
                yield Text("".join(cur_str))
            del cur_str[:]

            yield EndOfLine()
            i += 1

        elif c == "{":
            if "".join(cur_str):
                yield Text("".join(cur_str))
            del cur_str[:]

            i_box = [None]
            i += 1
            yield Group(list(tokenize(
                s, i, end_i_box=i_box,
                csname_to_arg_counts=csname_to_arg_counts,
                envname_to_arg_counts=envname_to_arg_counts)))
            i = i_box[0]

        elif c == "}" or (c == "]" and in_optional_arg):
            if "".join(cur_str):
                yield Text("".join(cur_str))
            del cur_str[:]

            if end_i_box is not None:
                end_i_box[0] = i+1
            return

        elif c == "\\":
            if "".join(cur_str):
                yield Text("".join(cur_str))
            del cur_str[:]

            cseq_match = CSEQ_RE.match(s, i)
            assert cseq_match
            name = cseq_match.group(1)
            i += len(name) + 1

            args = []
            if name == "begin":
                i = skip_whitespace(s, i)
                assert s[i] == "{"
                i += 1

                envname_match = ENVNAME_RE.match(s, i)
                assert envname_match
                env_name = envname_match.group(1)
                i += len(envname_match.group(0))

                try:
                    nargs, nopt_args = ENVNAME_TO_ARG_COUNTS[env_name]
                except KeyError:
                    raise NotImplementedError(
                        f"no arg count known for environment '{env_name}'")

            else:
                try:
                    nargs, nopt_args = csname_to_arg_counts[name]
                except KeyError:
                    raise NotImplementedError(
                        f"no arg count known for control sequence \\{name}")
            opt_args = []
            while nopt_args:
                i = skip_whitespace(s, i)
                if s[i] == "[":
                    i_box = [None]
                    opt_args.append(
                            make_container(tokenize(
                                s, i+1, end_i_box=i_box,
                                in_optional_arg=True,
                                csname_to_arg_counts=csname_to_arg_counts,
                                envname_to_arg_counts=envname_to_arg_counts)))
                    i = i_box[0]
                    nopt_args -= 1
                else:
                    break

            while nargs:
                i = skip_whitespace(s, i)
                if s[i] == "{":
                    i_box = [None]
                    args.append(make_container(
                        tokenize(
                            s, i+1, end_i_box=i_box,
                            csname_to_arg_counts=csname_to_arg_counts,
                            envname_to_arg_counts=envname_to_arg_counts)))
                    i = i_box[0]
                    nargs -= 1
                else:
                    break

            if name == "begin":
                yield ControlSequence(
                        name, (Text(env_name),) + tuple(args), tuple(opt_args))
            else:
                yield ControlSequence(name, tuple(args), tuple(opt_args))

        else:
            cur_str.append(c)
            i += 1

    if "".join(cur_str):
        yield Text("".join(cur_str))

# }}}


def parse_latex(s, csname_to_arg_counts=None, envname_to_arg_counts=None):
    if csname_to_arg_counts is None:
        csname_to_arg_counts = CSNAME_TO_ARG_COUNTS
    if envname_to_arg_counts is None:
        envname_to_arg_counts = ENVNAME_TO_ARG_COUNTS

    doc = LatexDocContainer(tuple(tokenize(
        s, i=0,
        csname_to_arg_counts=csname_to_arg_counts,
        envname_to_arg_counts=envname_to_arg_counts)))
    doc = EnvironmentGatherer().rec(doc)
    return doc

# vim: foldmethod=marker
