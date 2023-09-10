from toolbox.logger import Log

class nv():
    # name-value pairs
    def __init__(self, *args):
        for arg in args:
            if type(arg) is list and len(arg) is 2:
                NAME = arg[0]
                VALUE = arg[1]
                setattr(self, NAME, VALUE)

class rv():
    # binary result (true/false) and a value (message, code etc)
    def __init__(self, result, value):
        if type(result) is bool:
            self.ok = result
            self.msg = value
    def print(self, quit_on_fail=True):
        if self.ok:
            Log.info(self.msg)
        elif quit_on_fail:
            Log.critical(self.msg)
        else:
            Log.warn(self.msg)

class rnv():
    # binary result and name-vlaue pairs
    def __init___(self, result, *args):
        if type(result) is bool:
            self.ok = result
            for arg in args:
                if type(arg) is list and len(arg) is 2:
                    NAME = arg[0]
                    VALUE = arg[1]
                    setattr(self, NAME, VALUE)
    def print(self, quit_on_fail=True):
        if self.ok:
            Log.info(self.msg)
        elif quit_on_fail:
            Log.critical(self.msg)
        else:
            Log.warn(self.msg)
