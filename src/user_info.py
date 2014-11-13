#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  user_info.py
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

from gi.repository import Gtk

import os
import canonical.validation as validation
import show_message as show

_next_page = "slides"
_prev_page = None


class UserInfo(Gtk.Box):
    """ Asks for user information """
    def __init__(self, params):

        self.title = params['title']
        self.forward_button = params['forward_button']
        self.backwards_button = params['backwards_button']
        self.settings = params['settings']

        super().__init__()

        self.ui = Gtk.Builder()
        self.ui_dir = self.settings.get('ui')
        self.ui.add_from_file(os.path.join(self.ui_dir, "user_info.ui"))

        self.is_ok = dict()
        self.is_ok['fullname'] = self.ui.get_object('fullname_ok')
        self.is_ok['hostname'] = self.ui.get_object('hostname_ok')
        self.is_ok['username'] = self.ui.get_object('username_ok')
        self.is_ok['password'] = self.ui.get_object('password_ok')
        self.is_ok['root_password'] = self.ui.get_object('root_password_ok')

        self.error_label = dict()
        self.error_label['hostname'] = self.ui.get_object('hostname_error_label')
        self.error_label['username'] = self.ui.get_object('username_error_label')
        self.error_label['password'] = self.ui.get_object('password_error_label')
        self.error_label['root_password'] = self.ui.get_object('root_password_error_label')

        self.password_strength = self.ui.get_object('password_strength')
        self.root_password_strength = self.ui.get_object('root_password_strength')

        self.entry = dict()
        self.entry['fullname'] = self.ui.get_object('fullname')
        self.entry['hostname'] = self.ui.get_object('hostname')
        self.entry['username'] = self.ui.get_object('username')
        self.entry['password'] = self.ui.get_object('password')
        self.entry['verified_password'] = self.ui.get_object('verified_password')
        self.entry['root_password'] = self.ui.get_object('root_password')
        self.entry['verified_root_password'] = self.ui.get_object('verified_root_password')

        self.login = dict()
        self.login['auto'] = self.ui.get_object('login_auto')
        self.login['pass'] = self.ui.get_object('login_pass')
        self.login['encrypt'] = self.ui.get_object('login_encrypt')

        self.ui.connect_signals(self)

        self.require_password = True
        self.encrypt_home = False

        super().add(self.ui.get_object("user_info"))

    def translate_ui(self):
        """ Translate all widgets """
        label = self.ui.get_object('fullname_label')
        txt = _("Your name:")
        label.set_markup(txt)

        label = self.ui.get_object('fullname')
        txt = _("Your name")
        label.set_placeholder_text(txt)

        label = self.ui.get_object('hostname')
        txt = _("Hostname")
        label.set_placeholder_text(txt)

        label = self.ui.get_object('hostname_label')
        txt = _("Your computer's name:")
        label.set_markup(txt)

        label = self.ui.get_object('username_label')
        txt = _("Pick a username:")
        label.set_markup(txt)

        label = self.ui.get_object('username')
        txt = _("Username")
        label.set_placeholder_text(txt)

        label = self.ui.get_object('password_label')
        txt = _("Choose a password:")
        label.set_markup(txt)

        label = self.ui.get_object('password')
        txt = _("Password")
        label.set_placeholder_text(txt)

        label = self.ui.get_object('verified_password_label')
        txt = _("Confirm your password:")
        label.set_markup(txt)

        label = self.ui.get_object('verified_password')
        txt = _("Confirm password")
        label.set_placeholder_text(txt)

        label = self.ui.get_object('root_password_label')
        txt = _("Choose a root password:")
        label.set_markup(txt)

        label = self.ui.get_object('root_password')
        txt = _("Password")
        label.set_placeholder_text(txt)

        label = self.ui.get_object('verified_root_password_label')
        txt = _("Confirm root password:")
        label.set_markup(txt)

        label = self.ui.get_object('verified_root_password')
        txt = _("Confirm password")
        label.set_placeholder_text(txt)

        label = self.ui.get_object('hostname_extra_label')
        txt = _("Its name as it appears to other computers.")
        txt = '<span size="small">%s</span>' % txt
        label.set_markup(txt)

        txt = _("You must enter a name")
        txt = '<small><span color="darkred">%s</span></small>' % txt
        self.error_label['hostname'].set_markup(txt)

        txt = _("You must enter a username")
        txt = '<small><span color="darkred">%s</span></small>' % txt
        self.error_label['username'].set_markup(txt)

        txt = _("You must enter a password")
        txt = '<small><span color="darkred">%s</span></small>' % txt
        self.error_label['password'].set_markup(txt)

        txt = _("You must enter a password")
        txt = '<small><span color="darkred">%s</span></small>' % txt
        self.error_label['root_password'].set_markup(txt)

        self.login['auto'].set_label(_("Log in automatically"))
        self.login['pass'].set_label(_("A password is required to log in"))
        self.login['encrypt'].set_label(_("Encrypt home folder"))

        txt = _("Who are you?")
        txt = "<span weight='bold' size='large'>%s</span>" % txt
        self.title.set_markup(txt)

        btn = self.ui.get_object('checkbutton_show_password')
        btn.set_label(_("Show password"))

        btn = self.ui.get_object('checkbutton_show_root_password')
        btn.set_label(_("Show root password"))

        btn = self.ui.get_object('checkbutton_root_password')
        btn.set_label(_("Use a root password"))

    def show_root_password(self):
        """ Show root password """
        box = self.ui.get_object('hbox4')
        box.show()
        box = self.ui.get_object('hbox5')
        box.show()
        label = self.ui.get_object('root_password_label')
        label.show()
        label = self.ui.get_object('verified_root_password_label')
        label.show()
        btn = self.ui.get_object('checkbutton_show_root_password')
        btn.show()
        self.ui.get_object('root_password').set_text(' ')
        self.ui.get_object('root_password').set_text('')
        self.ui.get_object('verified_root_password').set_text('')

    def hide_root_password(self):
        """ Hide root password """
        box = self.ui.get_object('hbox4')
        box.hide()
        box = self.ui.get_object('hbox5')
        box.hide()
        label = self.ui.get_object('root_password_label')
        label.hide()
        label = self.ui.get_object('verified_root_password_label')
        label.hide()
        btn = self.ui.get_object('checkbutton_show_root_password')
        btn.hide()
        self.ui.get_object('root_password').set_text(' ')
        self.ui.get_object('root_password').set_text('')
        self.ui.get_object('verified_root_password').set_text('')

    def hide_widgets(self):
        """ Hide unused and message widgets """
        ok_widgets = self.is_ok.values()
        for ok_widget in ok_widgets:
            ok_widget.hide()

        error_label_widgets = self.error_label.values()
        for error_label in error_label_widgets:
            error_label.hide()

        self.password_strength.hide()
        self.root_password_strength.hide()

        self.hide_root_password()

        # Hide encryption if using LUKS encryption (user must use one or the other but not both)
        if self.settings.get('use_luks'):
            self.login['encrypt'].hide()

        # TODO: Fix home encryption and stop hidding its widget
        # Disable hidden features
        if not self.settings.get("z_hidden"):
            self.login['encrypt'].hide()

    def store_values(self):
        """ Store all user values in self.settings """
        self.settings.set('fullname', self.entry['fullname'].get_text())
        self.settings.set('hostname', self.entry['hostname'].get_text())
        self.settings.set('username', self.entry['username'].get_text())
        self.settings.set('password', self.entry['password'].get_text())
        self.settings.set('root_password', self.entry['root_password'].get_text())
        self.settings.set('require_password', self.require_password)

        self.settings.set('encrypt_home', False)
        if self.encrypt_home:
            m = _("KaOS will use eCryptfs to encrypt your home directory. Unfortunately, eCryptfs does not handle sparse files well.\n\n")
            m += _("Don't worry, for most intents and purposes this deficiency does not pose a problem.\n\n")
            m += _("Anyway, one popular and inadvisable application of eCryptfs is to encrypt a BitTorrent download location as this often requires eCryptfs to handle sparse files of 10 GB or more and may lead to intense disk starvation.\n\n")
            m += _("A simple workaround is to place sparse files in an unencrypted .Public directory\n\n")
            m += _("Look at https://wiki.archlinux.org/index.php/ECryptfs for detailed information\n\n")
            m += _("Are you sure you want to encrypt your home directory?\n")
            res = show.question(m)
            if res == Gtk.ResponseType.YES:
                self.settings.set('encrypt_home', True)

        # this way installer_process will know all info has been entered
        self.settings.set('user_info_done', True)

    def prepare(self, direction):
        """ Prepare screen """
        self.translate_ui()
        self.show_all()
        self.hide_widgets()
        self.is_ok['root_password'].show()

        desktop = self.settings.get('desktop')
        if desktop != "nox" and self.login['auto']:
            self.login['auto'].set_sensitive(True)
        else:
            self.login['auto'].set_sensitive(False)

        self.forward_button.set_sensitive(False)

        # restore forward button text (from install now! to next)
        self.forward_button.set_label("gtk-go-forward")

    def get_prev_page(self):
        return _prev_page

    def get_next_page(self):
        return _next_page

    def on_checkbutton_root_password_toggled(self, widget):
        """ Show/hide root password options """
        btn = self.ui.get_object('checkbutton_root_password')
        show = btn.get_active()
        if show:
            self.show_root_password()
        else:
            self.hide_root_password()
            self.is_ok['root_password'].show()
        self.info_loop

    def on_checkbutton_show_password_toggled(self, widget):
        """ Show/hide user password """
        btn = self.ui.get_object('checkbutton_show_password')
        show = btn.get_active()
        self.entry['password'].set_visibility(show)
        self.entry['verified_password'].set_visibility(show)

    def on_checkbutton_show_root_password_toggled(self, widget):
        """ Show/hide root password """
        btn = self.ui.get_object('checkbutton_show_root_password')
        show = btn.get_active()
        self.entry['root_password'].set_visibility(show)
        self.entry['verified_root_password'].set_visibility(show)

    def on_authentication_toggled(self, widget):
        """ User has changed autologin or home encrypting """
        if widget == self.login['auto']:
            if self.login['auto'].get_active():
                self.require_password = False
            else:
                self.require_password = True

        if widget == self.login['encrypt']:
            if self.login['encrypt'].get_active():
                self.encrypt_home = True
            else:
                self.encrypt_home = False

    def validate(self, element, value):
        """ Check that what the user is typing is ok """
        if len(value) == 0:
            self.is_ok[element].set_from_stock("gtk-no", Gtk.IconSize.BUTTON)
            self.is_ok[element].show()
            self.error_label[element].show()
        else:
            result = validation.check(element, value)
            if len(result) == 0:
                self.is_ok[element].set_from_stock("gtk-yes", Gtk.IconSize.BUTTON)
                self.is_ok[element].show()
                self.error_label[element].hide()
            else:
                self.is_ok[element].set_from_stock("gtk-no", Gtk.IconSize.BUTTON)
                self.is_ok[element].show()

                if validation.NAME_BADCHAR in result:
                    txt = _("Invalid characters entered")
                    txt = "<small><span color='darkred'>%s</span></small>" % txt
                    self.error_label[element].set_markup(txt)
                elif validation.NAME_BADDOTS in result:
                    txt = _("Username can't contain dots")
                    txt = "<small><span color='darkred'>%s</span></small>" % txt
                    self.error_label[element].set_markup(txt)
                elif validation.NAME_LENGTH in result:
                    txt = _("Too many characters")
                    txt = "<small><span color='darkred'>%s</span></small>" % txt
                    self.error_label[element].set_markup(txt)

                self.error_label[element].show()

    def info_loop(self, widget):
        """ User has introduced new information. Check it here. """

        if widget == self.entry['fullname']:
            fullname = self.entry['fullname'].get_text()
            if len(fullname) > 0:
                self.is_ok['fullname'].show()
            else:
                self.is_ok['fullname'].hide()

        if widget == self.entry['hostname']:
            hostname = self.entry['hostname'].get_text()
            self.validate('hostname', hostname)

        if widget == self.entry['username']:
            username = self.entry['username'].get_text()
            self.validate('username', username)

        if widget == self.entry['password'] or \
                widget == self.entry['verified_password']:
            validation.check_password(self.entry['password'],
                                      self.entry['verified_password'],
                                      self.is_ok['password'],
                                      self.error_label['password'],
                                      self.password_strength)

        btn = self.ui.get_object('checkbutton_root_password')
        show = btn.get_active()
        if show:
            if widget == self.entry['root_password'] or \
                    widget == self.entry['verified_root_password']:
                validation.check_password(self.entry['root_password'],
                                          self.entry['verified_root_password'],
                                          self.is_ok['root_password'],
                                          self.error_label['root_password'],
                                          self.root_password_strength)
        else:
            self.is_ok['root_password'].show()

        # Check if all fields are filled and ok
        all_ok = True
        ok_widgets = self.is_ok.values()
        for ok_widget in ok_widgets:
            (icon_name, icon_size) = ok_widget.get_stock()
            visible = ok_widget.get_visible()
            if visible is False or icon_name != "gtk-yes":
                all_ok = False

        self.forward_button.set_sensitive(all_ok)
