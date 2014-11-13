#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  job_remove_packages
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

""" Package removal module. Live only packages, surplus language packs removal """

from jobs.helpers import *
import logging
import os
import shutil
import subprocess 
import locale

def job_remove_packages(self):
  msg_job_start('job_remove_packages')
  
  # Packages to be removed
  self.conflicts = []
  self.running = True
  self.error = False
  self.packages = []

  # remove any db.lck
  db_lock = os.path.join(self.dest_dir, "var/lib/pacman/db.lck")
  if os.path.exists(db_lock):
      with misc.raised_privileges():
          os.remove(db_lock)
      logging.debug(_("%s deleted"), db_lock)

  # Remove thus and depends
  if os.path.exists("%s/usr/bin/thus" % self.dest_dir):
      self.queue_event('info', _("Removing installer (packages)"))
      self.chroot(['pacman', '-Rns', '--noconfirm', 'thus'])
            
  # Remove welcome
  if os.path.exists("%s/usr/bin/welcome" % self.dest_dir):
      self.queue_event('info', _("Removing live ISO (packages)"))
      self.chroot(['pacman', '-R', '--noconfirm', 'welcome'])
            
  # Remove hardware detection
  if os.path.exists("%s/etc/kdeos-hwdetect.conf" % self.dest_dir):
      self.queue_event('info', _("Removing live start-up (packages)"))
      self.chroot(['pacman', '-Rns', '--noconfirm', 'kdeos-hardware-detection'])
            
  # Remove init-live
  if os.path.exists("%s/etc/live" % self.dest_dir):
      self.queue_event('info', _("Removing live configuration (packages)"))
      self.chroot(['pacman', '-R', '--noconfirm', 'init-live'])
  
  # Remove KDE l10n 
  thisLocale = self.settings.get("language_code")[:2]
  listOfPkgs = []
  
  print (thisLocale)
 
  p = subprocess.Popen("pacman -Q | grep -i kde-l10n | awk '{print $1}'", 
      shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
 
  # Iterates over every found pkg and put each one in a list
  for line in p.stdout.readlines():
      s = line.decode('ascii')
      s = s.rstrip('\n')
      listOfPkgs.append(s)
    
  print (listOfPkgs)
 
  # Print the pkgs that do not have the locale 'thisLocale' for future removal!
  for pkg in listOfPkgs:
      if pkg[9:] != thisLocale:
        print (pkg)
        
  # Remove the pkgs that do not have the locale 'thisLocale'
  for pkg in listOfPkgs:
      if pkg[9:] != thisLocale:
        self.queue_event('info', _("Removing KDE l10n (packages)"))
        self.chroot(['pacman', '-Rddn', '--noconfirm', '%s' % (pkg)])

  # Remove Calligra l10n 
  listOfPkgs = []
 
  p = subprocess.Popen("pacman -Q | grep -i calligra-l10n | awk '{print $1}'", 
      shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
 
  # Iterates over every found pkg and put each one in a list
  for line in p.stdout.readlines():
      s = line.decode('ascii')
      s = s.rstrip('\n')
      listOfPkgs.append(s)
    
  print (listOfPkgs)
 
  # Print the pkgs that do not have the locale 'thisLocale' for future removal!
  for pkg in listOfPkgs:
      if pkg[14:] != thisLocale:
        print (pkg)

  # Remove the pkgs that do not have the locale 'thisLocale'
  for pkg in listOfPkgs:
      if pkg[14:] != thisLocale:
        self.queue_event('info', _("Removing Calligra l10n (packages)"))
        self.chroot(['pacman', '-Rddn', '--noconfirm', '%s' % (pkg)])

  msg_job_done('job_remove_packages')
