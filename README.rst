pylatexparse
------------

If you need:

* to turn your "non-crazy" LaTeX document into a document tree,
* to rewrite that document tree using a visitor pattern, and
* to near-exactly recreate your document (or a transformed version) 
  from this document tree,

then this package may be for you.

The package *does* need to know the number of arguments supplied to each macro
and environment encountered. There is a list of these in the code, but it is
not currently complete. Contributions to this for popular and common macros are
welcome. For custom macros and environments, an interface exists for this data
to be supplied.

The package is Python 3-only.

https://github.com/inducer/pylatexparse

Copyright 2019 Andreas Kloeckner

Released under the MIT License
