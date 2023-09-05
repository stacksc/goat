#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, unicode_literals
from goatshell.goatshell import Goatshell

import logging
logger = logging.getLogger(__name__)

def cli():
    goat_shell = Goatshell()
    logger.debug("session start")
    goat_shell.run_cli()

if __name__ == "__main__":
    cli()
