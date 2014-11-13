#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  installation_ask.py
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

""" Asks user which type of installation wants to perform """

from gi.repository import Gtk

import bootinfo
import logging
import os

_prev_page = "keymap"

class InstallationAsk(Gtk.Box):

    def __init__(self, params):
        self.title = params['title']
        self.forward_button = params['forward_button']
        self.backwards_button = params['backwards_button']
        self.settings = params['settings']

        super().__init__()
        self.ui = Gtk.Builder()
        self.ui_dir = self.settings.get('ui')
        self.ui.add_from_file(os.path.join(self.ui_dir, "installation_ask.ui"))

        partitioner_dir = os.path.join(self.settings.get("data"), "partitioner/small/")

        image = self.ui.get_object("automatic_image")
        image.set_from_file(partitioner_dir + "automatic.png")

        image = self.ui.get_object("alongside_image")
        image.set_from_file(partitioner_dir + "alongside.png")

        image = self.ui.get_object("advanced_image")
        image.set_from_file(partitioner_dir + "advanced.png")

        self.ui.connect_signals(self)

        super().add(self.ui.get_object("installation_ask"))

        oses = {}
        oses = bootinfo.get_os_dict()

        self.other_os = ""
        for k in oses:
            if "sda" in k and oses[k] != "unknown":
                self.other_os = oses[k]

        # by default, select automatic installation
        self.next_page = "installation_automatic"

    def enable_automatic_options(self, status):
        """ Enables or disables automatic installation options """
        names = ["encrypt_checkbutton", "encrypt_label",
                 "lvm_checkbutton", "lvm_label",
                 "home_checkbutton", "home_label"]
        for name in names:
            obj = self.ui.get_object(name)
            obj.set_sensitive(status)

    def prepare(self, direction):
        """ Prepare screen """
        self.translate_ui()
        self.show_all()

        # Always hide alongside option. It is not ready yet
        # if "windows" not in self.other_os.lower():
        radio = self.ui.get_object("alongside_radiobutton")
        radio.hide()
        label = self.ui.get_object("alongside_description")
        label.hide()

    def translate_ui(self):
        """ Translate screen before showing it """
        txt = _("Installation type")
        txt = "<span weight='bold' size='large'>%s</span>" % txt
        self.title.set_markup(txt)

        # In case we're coming from an installer screen, we change
        # to go-next stock button and we activate it
        #image1 = Gtk.Image()
        #image1.set_from_icon_name("go-next", Gtk.IconSize.BUTTON)
        #self.forward_button.set_label("")
        #self.forward_button.set_image(image1)
        #self.forward_button.set_sensitive(True)

        # Automatic Install
        radio = self.ui.get_object("automatic_radiobutton")
        radio.set_label(_("Erase disk and install KaOS (automatic)"))

        label = self.ui.get_object("automatic_description")
        txt = _("Warning: This will delete all data on your disk")
        txt = '<span weight="light" size="small">%s</span>' % txt
        label.set_markup(txt)
        label.set_line_wrap(True)

        button = self.ui.get_object("encrypt_checkbutton")
        txt = _("Encrypt this installation for increased security.")
        button.set_label(txt)

        label = self.ui.get_object("encrypt_label")
        txt = _("You will be asked for the encryption key in the next step.")
        txt = '<span weight="light" size="small">%s</span>' % txt
        label.set_markup(txt)

        button = self.ui.get_object("lvm_checkbutton")
        txt = _("Use LVM with this installation.")
        button.set_label(txt)

        label = self.ui.get_object("lvm_label")
        txt = _("This will set up LVM allowing you to make snapshots and change partition sizes in a straightforward way.")
        txt = '<span weight="light" size="small">%s</span>' % txt
        label.set_markup(txt)

        button = self.ui.get_object("home_checkbutton")
        txt = _("Set your Home in a different partition/volume")
        button.set_label(txt)

        label = self.ui.get_object("home_label")
        txt = _("This will setup your /home directory in a different partition or volume.")
        txt = '<span weight="light" size="small">%s</span>' % txt
        label.set_markup(txt)

        # Alongside Install (still experimental. Needs a lot of testing)
        if "windows" in self.other_os.lower():
            radio = self.ui.get_object("alongside_radiobutton")
            label = self.ui.get_object("alongside_description")
            radio.set_label(_("Install KaOS alongside %s") % self.other_os)

            txt = _("Install KaOS alongside %s") % self.other_os
            txt = '<span weight="light" size="small">%s</span>' % txt
            label.set_markup(txt)
            label.set_line_wrap(True)

        # Advanced Install
        radio = self.ui.get_object("advanced_radiobutton")
        radio.set_label(_("Manage your partitions and where to install KaOS (advanced)"))

        label = self.ui.get_object("advanced_description")
        txt = _("You will be able to create/delete partitions, choose where to install KaOS and also choose additional mount points.")
        txt = '<span weight="light" size="small">%s</span>' % txt
        label.set_markup(txt)
        label.set_line_wrap(True)

    def store_values(self):
        """ Store selected values """
        check = self.ui.get_object("encrypt_checkbutton")
        use_luks = check.get_active()

        check = self.ui.get_object("lvm_checkbutton")
        use_lvm = check.get_active()

        check = self.ui.get_object("home_checkbutton")
        use_home = check.get_active()

        if self.next_page == "installation_automatic":
            self.settings.set('use_lvm', use_lvm)
            self.settings.set('use_luks', use_luks)
            self.settings.set('use_home', use_home)
        else:
            self.settings.set('use_lvm', False)
            self.settings.set('use_luks', False)
            self.settings.set('use_home', False)

        if self.settings.get('use_luks'):
            logging.info(_("KaOS installation will be encrypted using LUKS"))

        if self.settings.get('use_lvm'):
            logging.info(_("KaOS will be installed using LVM volumes"))
            if self.settings.get('use_home'):
                logging.info(_("KaOS will be installed using a separate /home volume."))
        elif self.settings.get('use_home'):
            logging.info(_("KaOS will be installed using a separate /home partition."))

        if self.next_page == "installation_alongside":
            self.settings.set('partition_mode', 'alongside')
        elif self.next_page == "installation_advanced":
            self.settings.set('partition_mode', 'advanced')
        elif self.next_page == "installation_automatic":
            self.settings.set('partition_mode', 'automatic')

        return True

    def get_next_page(self):
        return self.next_page

    def get_prev_page(self):
        return _prev_page

    def on_automatic_radiobutton_toggled(self, widget):
        """ Automatic selected, enable all options """
        if widget.get_active():
            self.next_page = "installation_automatic"
            self.enable_automatic_options(True)

    def on_alongside_radiobutton_toggled(self, widget):
        """ Alongside selected, disable all automatic options """
        if widget.get_active():
            self.next_page = "installation_alongside"
            self.enable_automatic_options(False)

    def on_advanced_radiobutton_toggled(self, widget):
        """ Advanced selected, disable all automatic options """
        if widget.get_active():
            self.next_page = "installation_advanced"
            self.enable_automatic_options(False)

