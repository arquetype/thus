#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  job_cleanup_drivers
#
#  Copyright 2014 KaOS (http://kaosx.us)
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

""" Clean up unused drivers """

from jobs.helpers import *
import logging
import os
import shutil
import subprocess 

def job_cleanup_drivers(self):
  msg_job_start('job_cleanup_drivers')

  ###########################################################################
  # CLEANUP XORG DRIVERS
  ###########################################################################
  msg('cleaning up video drivers')

  # remove any db.lck
  db_lock = os.path.join(self.dest_dir, "var/lib/pacman/db.lck")
  if os.path.exists(db_lock):
    with misc.raised_privileges():
      os.remove(db_lock)
    logging.debug(_("%s deleted"), db_lock)
  
  if os.path.exists("/tmp/used_drivers"):
    with open("/tmp/used_drivers", "r") as searchfile:
      for line in searchfile:
        if "intel" in line:
          print(line)
        else:
          try:
            self.chroot(['pacman', '-Rns', '--noconfirm', 'xf86-video-vmware'])
          except Exception as e:
            pass
        if "nouveau" in line:
          print(line)
        else:
          try:
            self.chroot(['pacman', '-Rns', '--noconfirm', 'xf86-video-nouveau', 'xf86-video-vmware'])
          except Exception as e:
            pass
        if "ati" in line or "radeon" in line:
          print(line)
        else:
          try:
            self.chroot(['pacman', '-Rns', '--noconfirm', 'xf86-video-ati', 'xf86-video-vmware'])
          except Exception as e:
            pass
    searchfile.close()
  else:
    try:
      self.chroot(['pacman', '-Rns', '--noconfirm', 'xf86-video-ati', 'xf86-video-vmware'])
    except Exception as e:
      pass

  msg('video driver removal complete')

  ###########################################################################
  # CLEANUP INPUT DRIVERS
  ###########################################################################
  msg('cleaning up input drivers')

  with open("/var/log/Xorg.0.log", "r") as f:
    has_synaptics, has_wacom = False, False
    for line in f:
      if not has_synaptics and "synaptics" in line:
        has_synaptics = True
      if not has_wacom and "wacom" in line:
        has_wacom = True
    if not has_synaptics:
      try:
        self.chroot(['pacman', '-Rncs', '--noconfirm', 'xf86-input-synaptics'])
      except Exception as e:
        pass
    if not has_wacom:
      try:
        self.chroot(['pacman', '-Rncs', '--noconfirm', 'xf86-input-wacom'])
      except Exception as e:
        pass
  f.close()
  
  msg_job_done('job_cleanup_drivers')

  msg('input driver removal complete')

  msg_job_done('job_cleanup_drivers')
