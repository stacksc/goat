import shutil, sys, os

def set_terminal_width():
    return max(90, shutil.get_terminal_size().columns - 2)
