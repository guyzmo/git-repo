#!/usr/bin/env python

from os import listdir
from os.path import abspath, dirname, isfile, join
# get location of __init__.py
init_path = abspath(__file__)
# get folder name of __init__.py
init_dir = dirname(init_path)
# get all python files
py_files = [file_name.replace(".py", "") for file_name in listdir(init_dir) \
           if isfile(join(init_dir, file_name)) and ".py" in file_name and not ".pyc" in file_name]
# remove this __init__ file from the list
py_files.remove("__init__")
py_files.remove("base")

__all__ = py_files

