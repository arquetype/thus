#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  generate_update_info.py
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

""" This script generates an update.info file used to update Thus """

import os
import hashlib
import src.info as info

def get_md5(file_name):
    """ Gets md5 hash from a file """
    md5_hash = hashlib.md5()
    with open(file_name, "rb") as myfile:
        for line in myfile:
            md5_hash.update(line)
    return md5_hash.hexdigest()

def get_files(path):
    """ Returns all files from a directory """
    all_files = []
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)) and filename[0] != ".": # and filename[-3:] == ".py":
            all_files.append(os.path.join(path, filename))
    return all_files

def create_update_info():
    """ Creates update.info file """
    myfiles = []

    myfiles.extend(get_files("."))

    myfiles.extend(get_files("src"))
    myfiles.extend(get_files("src/parted3"))
    myfiles.extend(get_files("src/installation"))
    myfiles.extend(get_files("src/canonical"))

    myfiles.extend(get_files("data"))

    myfiles.extend(get_files("po"))

    myfiles.extend(get_files("ui"))

    myfiles.extend(get_files("scripts"))

    txt = '{"version":"%s","files":[\n' % info.THUS_VERSION

    for filename in myfiles:
        md5 = get_md5(filename)
        txt += '{"name":"%s","md5":"%s"},\n' % (filename, md5)

    # remove last comma and close
    txt = txt[:-3]
    txt += '}]}\n'

    with open("update.info", "w") as update_info:
        update_info.write(txt)

if __name__ == '__main__':
    create_update_info()
