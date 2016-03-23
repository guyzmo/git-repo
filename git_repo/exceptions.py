#!/usr/bin/env python

class ArgumentError(ValueError):
    pass

class ResourceError(Exception):
    pass

class ResourcePermissionError(PermissionError):
    pass

class ResourceNotFoundError(FileNotFoundError):
    pass

class ResourceExistsError(FileExistsError):
    pass

