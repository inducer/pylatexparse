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

CSEQ_RE = re.compile(
        r"\\(%|#|&|_|\n|,|;|\\|\(|\)|\{|\}| |\[|\]|\"|[a-zA-Z*]+)")
ENVNAME_RE = re.compile(r"^([a-zA-Z*]+)\s*$")


# {{{ node types

class LatexDoc:
    def __str__(self):
        return StringifyMapper().rec(self)


class WhiteSpace(LatexDoc):
    def __init__(self, text):
        self.text = text

    mapper_method = "map_whitespace"


class Text(LatexDoc):
    def __init__(self, text):
        self.text = text

    mapper_method = "map_text"


class EndOfLine(LatexDoc):
    mapper_method = "map_eol"


class _MathDelimiter(LatexDoc):
    """Internal, not encountered in user doc trees."""
    pass


class _InlineMathDelimiter(_MathDelimiter):
    """Internal, not encountered in user doc trees."""

    mapper_method = "map_inline_math_delimiter"


class _DisplayMathDelimiter(_MathDelimiter):
    """Internal, not encountered in user doc trees."""

    mapper_method = "map_display_math_delimiter"


class LatexDocContainer(LatexDoc):
    def __init__(self, content):
        self.content = content

    mapper_method = "map_container"


class Group(LatexDocContainer):
    mapper_method = "map_group"


class Superscript(LatexDoc):
    def __init__(self, arg):
        self.arg = arg

    mapper_method = "map_superscript"


class Subscript(LatexDoc):
    def __init__(self, arg):
        self.arg = arg

    mapper_method = "map_subscript"


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

    map_whitespace = map_text

    def map_eol(self, node):
        return "\n"

    def map_inline_math_delimiter(self, node):
        return "$"

    def map_display_math_delimiter(self, node):
        return "$$"

    def map_container(self, node):
        return "".join(self.rec(ch) for ch in node.content)

    def map_group(self, node):
        return "{%s}" % "".join(self.rec(ch) for ch in node.content)

    def map_superscript(self, node):
        ch = {
                Superscript: "^",
                Subscript: "_",
                }[type(node)]

        if node.arg is None:
            # These only occur internally before argument gathering.
            return ch

        if (
                (isinstance(node.arg, ControlSequence)
                    and not node.arg.args
                    and not node.arg.optargs)
                or (isinstance(node.arg, Text)
                    and len(node.arg.text) == 1)):
            return "%s%s" % (ch, self.rec(node.arg))
        else:
            return "%s{%s}" % (ch, self.rec(node.arg))

    map_subscript = map_superscript

    def map_controlseq(self, node):
        if node.args is None:
            # These only occur internally before argument gathering.
            return "\\" + node.name

        args = (
            "".join("[%s]" % self.rec(arg) for arg in node.optargs)
            +
            "".join("{%s}" % self.rec(arg) for arg in node.args)
            )

        if not args and node.name[-1].isalpha():
            args = " "

        return r"\%s%s" % (
                node.name,
                args)

    def map_environment(self, node):
        if node.name == "$":
            return r"$%s$ " % (
                    "".join(self.rec(ch) for ch in node.content))
        if node.name == "$$":
            return r"$$%s$$" % (
                    "".join(self.rec(ch) for ch in node.content))
        elif node.name == "(":
            return r"\(%s\)" % (
                    "".join(self.rec(ch) for ch in node.content))
        elif node.name == "[":
            return r"\[%s\]" % (
                    "".join(self.rec(ch) for ch in node.content))

        args = (
            "".join("[%s]" % self.rec(arg) for arg in node.optargs)
            +
            "".join("{%s}" % self.rec(arg) for arg in node.args)
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

    map_inline_math_delimiter = map_eol
    map_display_math_delimiter = map_eol
    map_text = map_eol
    map_whitespace = map_eol

    def map_superscript(self, node):
        if node.arg is None:
            # These only occur internally before argument gathering.
            return node

        return type(node)(self.rec(node.arg))

    map_subscript = map_superscript

    def map_controlseq(self, node):
        if node.args is None:
            # These only occur internally before argument gathering.
            return node

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

# }}}


# {{{ tokenizer

WHITESPACE = " \t"


def make_text(s):
    stripped = s.strip(WHITESPACE)
    if stripped == s:
        return Text(s)
    elif not stripped:
        return WhiteSpace(s)
    else:
        assert False, "received text with leading or trailing whitespace"


def tokenize(s, i=0, end_i_box=None):

    yielded_node = None

    cur_str = ""
    while i < len(s):
        c = s[i]

        # {{{ case distinction

        if c == "%":
            while s[i] != "\n" and i < len(s):
                i += 1
            if i < len(s):
                # skip the newline
                i += 1

        elif c == "\n":
            yielded_node = EndOfLine()
            i += 1

        elif c == "{":
            i_box = [None]
            i += 1
            yielded_node = Group(tuple(tokenize(s, i, end_i_box=i_box)))
            i = i_box[0]

        elif c == "}":
            if end_i_box is not None:
                end_i_box[0] = i+1
            if "".join(cur_str):
                yield Text("".join(cur_str))
            return

        elif c in "[]":
            # These must occur in Text nodes by themselves,
            # to facilitate recognizing optional arg lists.
            yielded_node = Text(c)
            i += 1

        elif c == "$":
            i += 1
            if i < len(s) and s[i] == "$":
                yielded_node = _DisplayMathDelimiter()
                i += 1
            else:
                yielded_node = _InlineMathDelimiter()

        elif c == "\\":
            cseq_match = CSEQ_RE.match(s, i)
            assert cseq_match
            name = cseq_match.group(1)
            i += len(name) + 1

            yielded_node = ControlSequence(name, None, None)

        elif c in "^_":
            i += 1
            yielded_node = {
                "^": Superscript,
                "_": Subscript,
                }[c](None)

        else:
            if cur_str:
                c_is_space = c in WHITESPACE
                cur_str_is_space = cur_str.strip(WHITESPACE) == ""

                if c_is_space != cur_str_is_space:
                    if cur_str_is_space:
                        yield WhiteSpace(cur_str)
                    else:
                        yield Text(cur_str)

                    cur_str = c
                else:
                    cur_str += c
            else:
                cur_str += c

            i += 1

        # }}}

        if yielded_node is not None:
            if "".join(cur_str):
                yield make_text(cur_str)
            cur_str = ""

            yield yielded_node
            yielded_node = None

    if "".join(cur_str):
        yield Text("".join(cur_str))

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
        "subsubsection": (1, 0),
        "footnote": (1, 0),
        "label": (1, 0),
        "ref": (1, 0),
        "eqref": (1, 0),
        "renewcommand": (2, 0),
        "arraystretch": (1, 0),
        "url": (1, 0),
        "cr": (1, 0),
        "phantom": (1, 0),
        "overset": (1, 0),

        "newpage": (0, 0),
        "vspace": (1, 0),
        "vspace*": (1, 0),
        "resizebox": (2, 0),
        "raisebox": (2, 0),
        "height": (0, 0),
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
        "widehat": (1, 0),
        "overline": (1, 0),
        "widetilde": (1, 0),
        "hat": (0, 0),
        "tilde": (0, 0),

        "oplus": (0, 0),
        "in": (0, 0),
        "sum": (0, 0),
        "int": (0, 0),
        "prod": (0, 0),
        "bigcup": (0, 0),
        "bigcap": (0, 0),
        "[": (0, 0),
        "]": (0, 0),

        "Alpha": (0, 0),
        "Delta": (0, 0),
        "Sigma": (0, 0),
        "Omega": (0, 0),
        "Phi": (0, 0),

        "ell": (0, 0),
        "triangle": (0, 0),
        "partial": (0, 0),

        "alpha": (0, 0),
        "beta": (0, 0),
        "gamma": (0, 0),
        "delta": (0, 0),
        "epsilon": (0, 0),
        "varepsilon": (0, 0),
        "phi": (0, 0),
        "varphi": (0, 0),
        "psi": (0, 0),
        "pi": (0, 0),
        "mu": (0, 0),
        "nu": (0, 0),
        "theta": (0, 0),
        "lambda": (0, 0),
        "rho": (0, 0),
        "sigma": (0, 0),
        "tau": (0, 0),
        "kappa": (0, 0),
        "omega": (0, 0),
        "xi": (0, 0),

        "neq": (0, 0),
        "leq": (0, 0),
        "leqslant": (0, 0),
        "geqslant": (0, 0),
        "geq": (0, 0),
        "gg": (0, 0),
        "ll": (0, 0),
        "sim": (0, 0),

        "approx": (0, 0),
        "perp": (0, 0),
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

        "Huge": (0, 0),
        "huge": (0, 0),
        "Large": (0, 0),
        "large": (0, 0),
        "scriptsize": (0, 0),
        "footnotesize": (0, 0),
        "tiny": (0, 0),

        "nobracket": (0, 0),
        "nocomma": (0, 0),
        "langle": (0, 0),
        "rangle": (0, 0),
        "star": (0, 0),
        "dagger": (0, 0),
        "ast": (0, 0),
        "cong": (0, 0),
        "pm": (0, 0),

        "lim": (0, 0),
        "det": (0, 0),
        "max": (0, 0),
        "min": (0, 0),
        "left": (0, 0),
        "right": (0, 0),
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
        "exp": (0, 0),
        "sin": (0, 0),
        "cos": (0, 0),
        "tan": (0, 0),
        "arcsin": (0, 0),
        "arccos": (0, 0),
        "arctan": (0, 0),

        "titlepage": (0, 0),
        "item": (0, 0),
        "bf": (0, 0),
        "it": (0, 0),

        "Leftrightarrow": (0, 0),
        "Rightarrow": (0, 0),
        "rightarrow": (0, 0),
        "leftarrow": (0, 0),
        "leftrightarrow": (0, 0),
        "downarrow": (0, 0),
        "to": (0, 0),

        "\\": (0, 1),
        ",": (0, 0),
        ";": (0, 0),
        "\"": (0, 0),
        "{": (0, 0),
        "}": (0, 0),
        "(": (0, 0),
        ")": (0, 0),
        " ": (0, 0),
        "_": (0, 0),
        "&": (0, 0),
        "#": (0, 0),
        "%": (0, 0),
        }

ENVNAME_TO_ARG_COUNTS = {
        "document": (0, 0),
        "frame": (1, 1),
        "itemize": (0, 0),
        "enumerate": (0, 0),
        "equation": (0, 0),
        "equation*": (0, 0),
        "align": (0, 0),
        "align*": (0, 0),
        "alignat*": (0, 0),
        "eqnarray*": (0, 0),
        "bmatrix": (0, 0),
        "cases": (0, 0),
        "center": (0, 0),
        "tabular": (1, 0),
        "array": (1, 0),
        "matrix": (1, 0),

        "theorem": (1, 1),
        }

# }}}


# {{{ argument gatherer

def make_container(iterable):
    nodes = tuple(iterable)
    if len(nodes) == 1:
        node, = nodes
        return node
    else:
        return LatexDocContainer(tuple(nodes))


def skip_whitespace(nodes, i):
    while i < len(nodes) and isinstance(nodes[i], WhiteSpace):
        i += 1
    return i


def skip_whitespace_and_eol(nodes, i):
    while i < len(nodes) and isinstance(nodes[i], (WhiteSpace, EndOfLine)):
        i += 1
    return i


def chomp_character(nodes, i):
    t = nodes[i]
    assert isinstance(t, Text)

    assert t.text
    result = t.text[0]
    remainder = t.text[1:]
    if remainder:
        nodes[i] = Text(remainder)
    else:
        del nodes[i]

    return result


class ArgumentGatherer(IdentityMapper):
    def __init__(self, csname_to_arg_counts, envname_to_arg_counts):
        self.csname_to_arg_counts = csname_to_arg_counts
        self.envname_to_arg_counts = envname_to_arg_counts

    def map_iterable(self, iterable, i=0, end_i_box=None):
        result = []
        nodes = list(iterable)

        while i < len(nodes):
            n = nodes[i]

            if isinstance(n, (ControlSequence, Subscript, Superscript)):
                i += 1

                # {{{ determine arg count

                if isinstance(n, (Subscript, Superscript)):
                    nargs = 1
                    nopt_args = 0

                elif n.name == "begin":
                    i = skip_whitespace_and_eol(nodes, i)
                    assert isinstance(nodes[i], Group)
                    assert len(nodes[i].content) == 1
                    assert isinstance(nodes[i].content[0], Text)

                    env_name = nodes[i].content[0].text
                    assert ENVNAME_RE.match(env_name)

                    i += 1

                    try:
                        nargs, nopt_args = self.envname_to_arg_counts[env_name]
                    except KeyError:
                        raise NotImplementedError(
                            f"no arg count known for environment '{env_name}'")

                else:
                    try:
                        nargs, nopt_args = self.csname_to_arg_counts[n.name]
                    except KeyError:
                        raise NotImplementedError(
                            "no arg count known for control sequence "
                            f"\\{n.name}")

                # }}}

                # {{{ optional arguments

                opt_args = []
                while len(opt_args) < nopt_args:
                    i = skip_whitespace_and_eol(nodes, i)

                    # tokenizer ensures [] are singled out
                    if (isinstance(nodes[i], Text) and nodes[i].text == "["):
                        i += 1
                        arg = []
                        while (
                                i < len(nodes)
                                and not (

                                    isinstance(nodes[i], Text)
                                    and nodes[i].text == "]")):
                            arg.append(nodes[i])
                            i += 1

                        # skip final ']'
                        i += 1

                        opt_args.append(LatexDocContainer(tuple(arg)))

                    else:
                        break

                # }}}

                # {{{ mandatory arguments

                args = []
                while len(args) < nargs:
                    i = skip_whitespace_and_eol(nodes, i)

                    if isinstance(nodes[i], Text):
                        args.append(Text(chomp_character(nodes, i)))
                        # i remains where it is
                    elif isinstance(nodes[i], ControlSequence):
                        args.append(
                                ControlSequence(nodes[i].name, (), ()))
                        i += 1
                    elif isinstance(nodes[i], Group):
                        args.append(
                                make_container(nodes[i].content))
                        i += 1
                    else:
                        raise RuntimeError("unexpected argument type")

                # }}}

                if not (args or opt_args):
                    i = skip_whitespace(nodes, i)

                if isinstance(n, (Subscript, Superscript)):
                    assert len(args) == 1
                    result.append(type(n)(args[0]))
                elif n.name == "begin":
                    result.append(ControlSequence(
                            n.name,
                            (Text(env_name),) + tuple(args),
                            tuple(opt_args)))
                else:
                    result.append(ControlSequence(
                            n.name, tuple(args), tuple(opt_args)))
            else:
                result.append(n)
                i += 1

        return tuple(result)

# }}}


# {{{ environment gatherer

def math_delim_to_env_name(n):
    if isinstance(n, _InlineMathDelimiter):
        return "$"
    elif isinstance(n, _DisplayMathDelimiter):
        return "$$"
    else:
        raise ValueError("unrecognized math delimiter")


class EnvironmentGatherer(IdentityMapper):
    def map_iterable(self, iterable, i=0, end_i_box=None, env_name=None):
        result = []
        nodes = list(iterable)
        while i < len(nodes):
            n = nodes[i]

            if isinstance(n, ControlSequence) and n.name == "end":
                assert env_name == n.args[0].text
                assert end_i_box is not None
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

            elif isinstance(n, ControlSequence) and n.name in ["[", "("]:
                i_box = [None]
                result.append(Environment(
                    n.name, (), (),
                    self.map_iterable(
                        nodes, i=i+1, end_i_box=i_box,
                        env_name=n.name)))
                i = i_box[0]
                assert i is not None

            elif isinstance(n, ControlSequence) and n.name in ["]", ")"]:
                assert env_name in "[("
                assert end_i_box is not None
                end_i_box[0] = i+1
                return result

            elif isinstance(n, _MathDelimiter):
                math_env_name = math_delim_to_env_name(n)

                if env_name == math_env_name:
                    # end math
                    assert end_i_box is not None
                    end_i_box[0] = i+1
                    return result
                else:
                    # begin math
                    i_box = [None]
                    result.append(Environment(
                        math_env_name, (), (),
                        self.map_iterable(
                            nodes, i=i+1, end_i_box=i_box,
                            env_name=math_env_name)))
                    i = i_box[0]
                    assert i is not None

            else:
                result.append(n)
                i += 1

        if env_name is not None:
            raise ValueError("missing end of environment '%s'" % env_name)

        return result

# }}}


class InlineMathWhiteSpaceEater(IdentityMapper):
    def map_environment(self, node):
        if node.name == "$":
            content = node.content
            i = 0
            while i < len(content) and isinstance(content[i], WhiteSpace):
                i += 1

            j = len(content)-1
            while j >= 0 and isinstance(content[j], WhiteSpace):
                j -= 1

            return type(node)(
                    node.name, (), (),
                    tuple(self.rec(ch) for ch in content[i:j+1]))

        else:
            return super().map_environment(node)


def parse_latex(s, csname_to_arg_counts=None, envname_to_arg_counts=None):
    if csname_to_arg_counts is None:
        csname_to_arg_counts = CSNAME_TO_ARG_COUNTS
    if envname_to_arg_counts is None:
        envname_to_arg_counts = ENVNAME_TO_ARG_COUNTS

    doc = LatexDocContainer(tuple(tokenize(s)))
    doc = ArgumentGatherer(
            csname_to_arg_counts=csname_to_arg_counts,
            envname_to_arg_counts=envname_to_arg_counts).rec(doc)
    doc = EnvironmentGatherer().rec(doc)
    return doc

# vim: foldmethod=marker
