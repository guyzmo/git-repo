#!/usr/bin/env python

import sys
import shutil

def print_tty(*args, **kwarg):
    if sys.stdout.isatty():
        print(*args, **kwarg)

def print_iter(generator):
    fmt = next(generator)
    print_tty(fmt.format(*next(generator)))
    for item in generator:
        print(fmt.format(*item))

def loop_input(*args, method=input, **kwarg):
    out = ''
    while len(out) == 0:
        out = method(*args, **kwarg)
    return out

def confirm(what, where):
    '''
    Method to show a CLI based confirmation message, waiting for a yes/no answer.
    "what" and "where" are used to better define the message.
    '''
    ans = input('Are you sure you want to delete the '
                '{} {} from the service?\n[yN]> '.format(what, where))
    if 'y' in ans:
        ans = loop_input('Are you really sure? there\'s no coming back!\n'
                    '[type \'burn!\' to proceed]> ')
        if 'burn!' != ans:
            return False
    else:
        return False
    return True

def columnize(lines, indent=0, pad=2):
    term_width = shutil.get_terminal_size((80, 20)).columns
    # prints a list of items in a fashion similar to the dir command
    # borrowed from https://gist.github.com/critiqjo/2ca84db26daaeb1715e1
    n_lines = len(lines)
    if n_lines == 0:
        return
    col_width = max(len(line) for line in lines)
    n_cols = int((term_width + pad - indent)/(col_width + pad))
    n_cols = min(n_lines, max(1, n_cols))
    col_len = int(n_lines/n_cols) + (0 if n_lines % n_cols == 0 else 1)
    if (n_cols - 1) * col_len >= n_lines:
        n_cols -= 1
    cols = [lines[i*col_len : i*col_len + col_len] for i in range(n_cols)]
    rows = list(zip(*cols))
    rows_missed = zip(*[col[len(rows):] for col in cols[:-1]])
    rows.extend(rows_missed)
    for row in rows:
        yield [" "*indent + (" "*pad).join(line.ljust(col_width) for line in row)]
