#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  rank_mirrors.py
#
#  This file was forked from Cnchi (graphical installer from Antergos)
#  Check it at https://github.com/antergos
#
#  Copyright 2013 Antergos (http://antergos.com/)
#  Copyright 2013 Manjaro (http://manjaro.org)
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

""" Sorts mirrorlist to use the closest mirrors first """

import threading
import subprocess
import logging
import time
import os
import canonical.misc as misc
import show_message as show


class AutoRankmirrorsThread(threading.Thread):
    """ Thread class that searches the closest mirrors available """
    def __init__(self):
        """ Initialize thread class """
        super(AutoRankmirrorsThread, self).__init__()
        self.rankmirrors_pid = None
        self.rankmirrors_script = "/usr/share/thus/scripts/rankmirrors-script"

    def run(self):
        """ Run thread """

        # Wait until there is an Internet connection available
        while not misc.has_connection():
            time.sleep(2)  # Delay

        if not os.path.exists(self.rankmirrors_script):
            logging.warning(_("Can't find rank mirrors script"))
            return

        # Run rankmirrors command
        try:
            self.rankmirrors_pid = subprocess.Popen(["/usr/share/thus/scripts/rankmirrors-script"]).pid
        except subprocess.CalledProcessError as err:
            txt = _("Couldn't execute auto mirroring selection")
            logging.error(txt)
            show.error(txt)
            logging.error(err)
