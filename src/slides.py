#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  slides.py
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

""" Shows slides while installing. Also manages installing messages and progress bars """

from gi.repository import Gtk, WebKit, Gdk, GLib
import config
import os

import queue
from multiprocessing import Queue, Lock

import show_message as show
import logging
import subprocess
import canonical.misc as misc

# When we reach this page we can't go neither backwards nor forwards
_next_page = None
_prev_page = None


class Slides(Gtk.Box):

    def __init__(self, params):
        """ Initialize class and its vars """
        self.title = params['title']
        self.forward_button = params['forward_button']
        self.backwards_button = params['backwards_button']
        self.exit_button = params['exit_button']
        self.callback_queue = params['callback_queue']
        self.settings = params['settings']
        self.main_progressbar = params['main_progressbar']
        self.should_pulse = False
        self.dest_dir = "/install"

        super().__init__()

        builder = Gtk.Builder()
        self.ui_dir = self.settings.get('ui')
        builder.add_from_file(os.path.join(self.ui_dir, "slides.ui"))
        builder.connect_signals(self)

        self.progress_bar = builder.get_object("progressbar")
        self.progress_bar.set_show_text(True)

        self.global_progress_bar = builder.get_object("global_progressbar")
        self.global_progress_bar.set_show_text(True)

        self.info_label = builder.get_object("info_label")
        self.scrolled_window = builder.get_object("scrolledwindow")

        # Add a webkit view to show the slides
        self.webview = WebKit.WebView()

        if self.settings is None:
            html_file = '/usr/share/thus/data/slides.html'
        else:
            html_file = os.path.join(self.settings.get("data"), 'slides.html')

        try:
            with open(html_file) as html_stream:
                html = html_stream.read(None)
                data = os.path.join(os.getcwd(), "data")
                self.webview.load_html_string(html, "file://" + data)
        except IOError:
            pass

        self.scrolled_window.add(self.webview)

        self.install_ok = _("Installation finished!\n" \
                            "Do you want to restart your system now?")

        super().add(builder.get_object("slides"))

        self.fatal_error = False

    def translate_ui(self):
        txt = _("Installing KaOS...")
        txt = "<span weight='bold' size='large'>%s</span>" % txt
        self.title.set_markup(txt)

        if len(self.info_label.get_label()) <= 0:
            self.set_message(_("Please wait..."))

        self.install_ok = _("Installation finished!\n" \
                            "Do you want to restart your system now?")

    def show_global_progress_bar_if_hidden(self):
        if self.global_progress_bar_is_hidden:
            self.global_progress_bar.show_all()
            self.global_progress_bar_is_hidden = False

    def prepare(self, direction):
        self.translate_ui()
        self.show_all()

        # Last screen reached, hide main progress bar.
        self.main_progressbar.hide()

        # Hide global progress bar
        self.global_progress_bar.hide()
        self.global_progress_bar_is_hidden = True

        self.backwards_button.hide()
        self.forward_button.hide()
        self.exit_button.hide()

    def store_values(self):
        """ Nothing to be done here """
        return False

    def get_prev_page(self):
        """ No previous page available """
        return _prev_page

    def get_next_page(self):
        """ This is the last page """
        return _next_page

    def set_message(self, txt):
        """ Show information message """
        txt = "<span color='black'>%s</span>" % txt
        self.info_label.set_markup(txt)

    def stop_pulse(self):
        """ Stop pulsing progressbar """
        self.should_pulse = False

    def do_progress_pulse(self):
        """ Pulsing progressbar """
        def pbar_pulse():
            if(not self.should_pulse):
                return False
            self.progress_bar.pulse()
            return self.should_pulse
        if(not self.should_pulse):
            self.should_pulse = True
            GLib.timeout_add(100, pbar_pulse)
        else:
            # asssume we're "pulsing" already
            self.should_pulse = True
            pbar_pulse()

    def manage_events_from_cb_queue(self):
        """ This function is called from cnchi.py with a timeout function
            We should do as less as possible here, we want to maintain our
            queue message as empty as possible """
        if self.fatal_error:
            return False

        while self.callback_queue.empty() is False:
            try:
                event = self.callback_queue.get_nowait()
            except queue.Empty:
                return True

            if event[0] == 'percent':
                self.progress_bar.set_fraction(event[1])
            elif event[0] == 'global_percent':
                self.show_global_progress_bar_if_hidden()
                self.global_progress_bar.set_fraction(event[1])
            elif event[0] == 'pulse':
                self.do_progress_pulse()
            elif event[0] == 'stop_pulse':
                self.stop_pulse()
            elif event[0] == 'finished':
                logging.info(event[1])
                self.should_pulse = False

                # Warn user about GRUB and ask if we should open wiki page.
                if not self.settings.get('bootloader_ok'):
                    import webbrowser
                    self.boot_warn = _("IMPORTANT: There may have been a problem with the Grub(2) bootloader\n"
                                       "installation which could prevent your system from booting properly. Before\n"
                                       "rebooting, you may want to verify whether or not GRUB(2) is installed and\n"
                                       "configured. The KaOS Tutorials contain some info to re-configure:\n"
                                       "\thttp://kaosx.us/phpBB3/viewtopic.php?f=7&t=260\n"
                                       "\nWould you like to view the forum page now?")
                    response = show.question(self.boot_warn)
                    if response == Gtk.ResponseType.YES:
                        webbrowser.open('http://kaosx.us/phpBB3/viewtopic.php?f=7&t=260')

                self.set_message(self.install_ok)
                response = show.question(self.install_ok)

                if response == Gtk.ResponseType.YES:
                    logging.shutdown()
                    self.reboot()
                else:
                    tmp_files = [".setup-running", ".km-running", "setup-pacman-running", "setup-mkinitcpio-running", ".tz-running", ".setup", "thus.log"]
                    for t in tmp_files:
                        p = os.path.join("/tmp", t)
                        if os.path.exists(p):
                            # TODO: some of these tmp files are created with sudo privileges
                            # (this should be fixed) meanwhile, we need sudo privileges to remove them
                            with misc.raised_privileges():
                                os.remove(p)
                    self.callback_queue.task_done()
                    logging.shutdown()
                    os._exit(0)

                return False
            elif event[0] == 'error':
                self.callback_queue.task_done()
                # A fatal error has been issued. We empty the queue
                self.empty_queue()
                self.fatal_error = True
                show.fatal_error(event[1])
                # Ask if user wants to retry
                res = show.question(_("Do you want to retry?"))
                if res == GTK_RESPONSE_YES:
                    # Restart installation process
                    logging.debug("Restarting installation process...")
                    p = self.settings.get('installer_thread_call')

                    self.process = installation_process.InstallationProcess(
                        self.settings,
                        self.callback_queue,
                        p['mount_devices'],
                        p['fs_devices'],
                        p['ssd'],
                        p['alternate_package_list'],
                        p['blvm'])

                    self.process.start()
                    return True
                else:
                    self.fatal_error = True
                    return False
            elif event[0] == 'debug':
                logging.debug(event[1])
            elif event[0] == 'warning':
                logging.warning(event[1])
            else:
                logging.info(event[1])
                self.set_message(event[1])

            self.callback_queue.task_done()

        return True

    def empty_queue(self):
        """ Empties messages queue """
        while self.callback_queue.empty() is False:
            try:
                event = self.callback_queue.get_nowait()
                self.callback_queue.task_done()
            except queue.Empty:
                return

    @misc.raise_privileges
    def reboot(self):
        """ Reboots the system, used when installation is finished """
        os.system("sync")
        subprocess.call(["/usr/bin/systemctl", "reboot", "--force", "--no-wall"])
