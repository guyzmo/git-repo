#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.kwargparse')

class KeywordArgumentParser:
    '''
    Argument parser tailored for use with docopt:

    Will parse all arguments returned by docopt, and will store them as instance
    attributes. Then it will launch actions based on the keyword argument list.

    * Parameter arguments (starting with -- or within <>) will automagically be
    parsed, dashes will be converted to underscores and stored as attributes of
    the parser instance.
    * Though if a parameter is matching a method decorated with "store_parameter",
    it won't be automagically setup, but will use that method instead.

    Then the keywords used as arguments of the program will be used to call an
    "action" method, which have been decorated with "register_action".

    '''
    _action_dict = dict()
    _parameter_dict = dict()

    def __init__(self, args):
        '''
        Stores the docopt args as class member
        '''
        self.args = args

    def init(self):
        '''
        method to be defined for anything that needs to be done before launching
        the parser.
        '''
        pass

    def run(self):
        '''
        This method iterates over the docopt's arguments and matches them against
        the parameters list. All leftover values are used to resolve the action to
        run, and it will run the action, or run the fallback() method if no action
        is found.
        '''
        self.init()

        args = []
        missed = []

        # go through setters
        for arg, value in self.args.items():
            if arg in self._parameter_dict:
                self._parameter_dict[arg](self, value)
                #log.debug('calling setter: {} → {}'.format(arg, value))
            elif arg.startswith('--') or arg.startswith('<'):
                arg_renamed = arg.lstrip('-<').rstrip('>').replace('-', '_')
                if not hasattr(self, arg_renamed):
                    setattr(self, arg_renamed, value)
                    #log.debug('auto-setting:   self.{} → {}'.format(arg_renamed, value))
            else:
                #log.debug('keeping: {} → {}'.format(arg, value))
                if self.args[arg]:
                    args.append(arg)

        if frozenset(args) in self._action_dict:
            #log.debug('running action: {}'.format(self._action_dict[frozenset(args)]))
            return self._action_dict[frozenset(args)](self)
        else:
            return self.fallback()

    def fallback(self):
        log.error('Unknown action.')
        log.error('Please consult help page (--help).')
        return 1



def store_parameter(parameter):
    '''
    Decorator for a parameter, use the full length parameter name as specified in the
    docopt configuration, like '--verbose'
    '''
    def decorator(fun):
        KeywordArgumentParser._parameter_dict[parameter] = fun
        return fun
    return decorator

def register_action(*args, **kwarg):
    '''
    Decorator for an action, the arguments order is not relevant, but it's best
    to use the same order as in the docopt for clarity.
    '''
    def decorator(fun):
        KeywordArgumentParser._action_dict[frozenset(args)] = fun
        return fun
    return decorator
