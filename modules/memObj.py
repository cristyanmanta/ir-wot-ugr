from __future__ import print_function
from sys import getsizeof, stderr
from itertools import chain
from pyllist import dllist
from collections import deque
try:
    from reprlib import repr
except ImportError:
    pass

def get_dllist_size(dllist, verbose=False):
    size = 0
    node = dllist.first
    s = getsizeof(node)
    if verbose:
        print(s, type(node), repr(node), file=stderr)
    size += total_size(node.value, verbose=verbose)+s
    for i in range(dllist.size):
        node = node.next
        if node != None:
            value = node.value
            s = getsizeof(node)
            if verbose:
                print(s, type(node), repr(node), file=stderr)
            size += total_size(value, verbose=verbose) + s
    return size

def total_size(o, handlers={}, verbose=False):
    """ Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """
    dict_handler = lambda d: chain.from_iterable(d.items())
    all_handlers = {tuple: iter,
                    list: iter,
                    deque: iter,
                    dict: dict_handler,
                    set: iter,
                    frozenset: iter,
                   }
    all_handlers.update(handlers)     # user handlers take precedence
    seen = set()                      # track which object id's have already been seen
    default_size = getsizeof(0)       # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:       # do not double count the same object
            return 0
        seen.add(id(o))
        s = getsizeof(o, default_size)
        if verbose:
            print(s, type(o), repr(o), file=stderr)
        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)

def total_size2(o, handlers={}, verbose=False):
    """ Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """
    dict_handler = lambda d: chain.from_iterable(d.items())
    dllist_handler = lambda d,verbose: get_dllist_size(d, verbose)
    all_handlers = {tuple: iter,
                    list: iter,
                    deque: iter,
                    dict: dict_handler,
                    set: iter,
                    frozenset: iter,
                    dllist: dllist_handler
                   }
    all_handlers.update(handlers)     # user handlers take precedence
    seen = set()                      # track which object id's have already been seen
    default_size = getsizeof(0)       # estimate sizeof object without __sizeof__

    def sizeof(o):
        s = getsizeof(o, default_size)
        if verbose:
            print(s, type(o), repr(o), file=stderr)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                if typ == dllist:
                    s += handler(o,verbose)
                    break
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)

##### Example call #####

#if __name__ == '__main__':
#    d = dict(a=1, b=2, c=3, d=[4,5,6,7], e='a string of chars')
#    print(total_size(d, verbose=True))
