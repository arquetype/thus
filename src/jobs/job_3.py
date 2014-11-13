#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  job_setup_hardware
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

""" Setup graphics drivers and sound """

from jobs.helpers import *
import logging
import os
import shutil
import glob
import subprocess

def job_setup_hardware(self):
  msg_job_start('job_setup_hardware')

  # remove any db.lck
  db_lock = os.path.join(self.dest_dir, "var/lib/pacman/db.lck")
  if os.path.exists(db_lock):
      with misc.raised_privileges():
          os.remove(db_lock)
      logging.debug(_("%s deleted"), db_lock)


  # setup alsa volume levels, alsa blacklist for the pc speaker, blacklist for broken realtek nics
  msg('setup alsa config')
  files_to_copy = ['/etc/asound.state', '/etc/modprobe.d/alsa_blacklist.conf', '/etc/modprobe.d/realtek_blacklist.conf']
  for f in files_to_copy:
    if os.path.exists(f):
      shutil.copy2(f, os.path.join(self.dest_dir))

  # setup proprietary drivers, if detected
  msg('setup proprietary drivers')
  if os.path.exists('/tmp/nvidia'):
    msg('nvidia detected')
    msg('removing unneeded packages')
    self.chroot(['pacman', '-Rdd', '--noconfirm', 'libgl'])
    self.chroot(['pacman', '-Rdd', '--noconfirm', 'xf86-video-nouveau'])
    msg('installing driver')
    shutil.copytree('/opt/kdeos/pkgs', '%s/opt/kdeos/pkgs' % (self.dest_dir))
    for nvidia_utils in glob.glob('/opt/kdeos/pkgs/nvidia-utils-34*'):
      self.chroot(['pacman', '-Ud', '--force', '--noconfirm', nvidia_utils])
    for nvidia in glob.glob('/opt/kdeos/pkgs/nvidia-34*'):
      self.chroot(['pacman', '-Ud', '--force', '--noconfirm', nvidia])
    shutil.rmtree('%s/opt/kdeos/pkgs' % (self.dest_dir))
  elif os.path.exists('/tmp/nvidia-304xx'):
    msg('nvidia-304xx detected')
    msg('removing unneeded packages')
    self.chroot(['pacman', '-Rdd', '--noconfirm', 'libgl'])
    self.chroot(['pacman', '-Rdd', '--noconfirm', 'xf86-video-nouveau'])
    msg('installing driver')
    shutil.copytree('/opt/kdeos/pkgs', '%s/opt/kdeos/pkgs' % (self.dest_dir))
    for nvidia_304_utils in glob.glob('/opt/kdeos/pkgs/nvidia-304xx-utils*'):
      self.chroot(['pacman', '-Ud', '--force', '--noconfirm', nvidia_304_utils])
    for nvidia_304 in glob.glob('/opt/kdeos/pkgs/nvidia-304xx-3*'):
      self.chroot(['pacman', '-Ud', '--force', '--noconfirm', nvidia_304])
    shutil.rmtree('%s/opt/kdeos/pkgs' % (self.dest_dir))

  # fixing alsa
  #self.chroot(['alsactl', '-f', '/var/lib/alsa/asound.state', 'store'])
  
  msg_job_done('job_setup_hardware')
