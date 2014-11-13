#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  thus.py
#
#  Copyright 2013 Antergos, Manjaro
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
#
#  Antergos Team:
#   Alex Filgueira (faidoc) <alexfilgueira.antergos.com>
#   Raúl Granados (pollitux) <raulgranados.antergos.com>
#   Gustau Castells (karasu) <karasu.antergos.com>
#   Kirill Omelchenko (omelcheck) <omelchek.antergos.com>
#   Marc Miralles (arcnexus) <arcnexus.antergos.com>
#   Alex Skinner (skinner) <skinner.antergos.com>

""" Main Thus (Manjaro Installer) module """
import os.path

# TODO: Remove all force_grub code


# Useful vars for gettext (translations)
APP_NAME = "thus"
LOCALE_DIR = "/usr/share/locale"

# This allows to translate all py texts (not the glade ones)
import gettext
gettext.textdomain(APP_NAME)
gettext.bindtextdomain(APP_NAME, LOCALE_DIR)

import locale
locale_code, encoding = locale.getdefaultlocale()
lang = gettext.translation(APP_NAME, LOCALE_DIR, [locale_code], None, True)
lang.install()

from gi.repository import Gtk, Gdk, GObject, GLib
import os
import sys
import getopt
import locale
import multiprocessing
import logging

# Insert the src directory at the front of the path
BASE_DIR = os.path.dirname(__file__) or '.'
SRC_DIR = os.path.join(BASE_DIR, 'src')
sys.path.insert(0, SRC_DIR)

import config

import language
import location
import check
import keymap
import timezone
import user_info
import slides
import canonical.misc as misc
import info
import updater
import show_message as show

from installation import ask as installation_ask
from installation import automatic as installation_automatic
from installation import alongside as installation_alongside
from installation import advanced as installation_advanced

# Command line options
cmd_line = None

# Constants (must be uppercase)
MAIN_WINDOW_WIDTH = 800
MAIN_WINDOW_HEIGHT = 526

# At least this GTK version is needed
_gtk_version_needed = "3.9.6"


# Some of these tmp files are created with sudo privileges
# (this should be fixed) meanwhile, we need sudo privileges to remove them
@misc.raise_privileges
def remove_temp_files():
    """ Remove Thus temporary files """
    temp_files = [".setup-running", ".km-running", "setup-pacman-running",
                  "setup-mkinitcpio-running", ".tz-running", ".setup", "thus.log"]
    for temp in temp_files:
        path = os.path.join("/tmp", temp)
        if os.path.exists(path):
            os.remove(path)


class Main(Gtk.Window):
    """ Thus main window """
    def __init__(self):
        ## This allows to translate all py texts (not the glade ones)
        #gettext.textdomain(APP_NAME)
        #gettext.bindtextdomain(APP_NAME, LOCALE_DIR)
        #
        #locale_code, encoding = locale.getdefaultlocale()
        #lang = gettext.translation(APP_NAME, LOCALE_DIR, [locale_code], None, True)
        #lang.install()
        #
        ## With this we can use _("string") to translate
        #gettext.install(APP_NAME, localedir=LOCALE_DIR, codeset=None, names=[locale_code])

        # Check if we have administrative privileges
        if os.getuid() != 0:
            show.fatal_error(_('This installer must be run with administrative'
                         ' privileges and cannot continue without them.'))

        setup_logging()

        # Check if we're already running
        tmp_running = "/tmp/.setup-running"
        if os.path.exists(tmp_running):
            show.error(_('You cannot run two instances of this installer.\n\n'
                          'If you are sure that another installer is not already running\n'
                          'you can manually delete the file %s\n'
                          'and run this installer again.') % tmp_running)
            sys.exit(1)

        super().__init__()

        # workaround for dconf
        os.system("mkdir -p /root/.cache/dconf")
        os.system("chmod -R 777 /root/.cache")

        logging.info(_("Thus installer version %s"), info.THUS_VERSION)

        current_process = multiprocessing.current_process()
        logging.debug("[%d] %s started", current_process.pid, current_process.name)

        self.settings = config.Settings()

        thus_dir = os.path.join(os.path.dirname(__file__), './')
        if os.path.exists(thus_dir):
            self.settings.set('thus', thus_dir)
        else:
            thus_dir = self.settings.get('thus')

        ui_dir = os.path.join(os.path.dirname(__file__), 'ui/')
        if os.path.exists(ui_dir):
            self.settings.set('ui', ui_dir)
        else:
            ui_dir = self.settings.get('ui')

        data_dir = os.path.join(os.path.dirname(__file__), 'data/')
        if os.path.exists(data_dir):
            self.settings.set('data', data_dir)
        else:
            data_dir = self.settings.get('data')

        if os.path.exists("/sys/firmware/efi"):
            self.settings.set('efi', True)

        self.ui = Gtk.Builder()
        self.ui.add_from_file(ui_dir + "thus.ui")

        self.add(self.ui.get_object("main"))

        self.header = self.ui.get_object("header")

        self.forward_button = self.ui.get_object("forward_button")

        self.logo = self.ui.get_object("logo")

        logo_dir = os.path.join(data_dir, "manjaro-logo-mini.png")

        self.logo.set_from_file(logo_dir)

        self.title = self.ui.get_object("title")

        # To honor our css
        self.title.set_name("header")
        self.logo.set_name("header")

        self.main_box = self.ui.get_object("main_box")
        self.progressbar = self.ui.get_object("progressbar1")

        self.forward_button = self.ui.get_object("forward_button")
        self.exit_button = self.ui.get_object("exit_button")
        self.backwards_button = self.ui.get_object("backwards_button")

        # Create a queue. Will be used to report pacman messages (pac.py)
        # to the main thread (installer_*.py)
        self.callback_queue = multiprocessing.JoinableQueue()

        # Load all pages
        # (each one is a screen, a step in the install process)

        self.pages = dict()

        params = dict()
        params['title'] = self.title
        params['forward_button'] = self.forward_button
        params['backwards_button'] = self.backwards_button
        params['exit_button'] = self.exit_button
        params['callback_queue'] = self.callback_queue
        params['settings'] = self.settings
        params['main_progressbar'] = self.ui.get_object('progressbar1')
        params['alternate_package_list'] = ""
        params['testing'] = cmd_line.testing

        self.pages["language"] = language.Language(params)
        self.pages["location"] = location.Location(params)
        self.pages["check"] = check.Check(params)
        self.pages["keymap"] = keymap.Keymap(params)
        self.pages["timezone"] = timezone.Timezone(params)
        self.pages["installation_ask"] = installation_ask.InstallationAsk(params)
        self.pages["installation_automatic"] = installation_automatic.InstallationAutomatic(params)
        self.pages["installation_alongside"] = installation_alongside.InstallationAlongside(params)
        self.pages["installation_advanced"] = installation_advanced.InstallationAdvanced(params)
        self.pages["user_info"] = user_info.UserInfo(params)
        self.pages["slides"] = slides.Slides(params)

        self.connect("delete-event", Gtk.main_quit)
        self.ui.connect_signals(self)

        self.set_title(_('KaOS Installer'))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)
        self.set_size_request(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        # Set window icon
        icon_dir = os.path.join(data_dir, 'manjaro-icon.png')

        self.set_icon_from_file(icon_dir)

        # Set the first page to show
        self.current_page = self.pages["language"]

        self.main_box.add(self.current_page)

        # Header style testing

        style_provider = Gtk.CssProvider()

        style_css = os.path.join(data_dir, "css", "gtk-style.css")

        with open(style_css, 'rb') as css:
            css_data = css.read()

        style_provider.load_from_data(css_data)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Show main window
        self.show_all()

        self.current_page.prepare('forwards')

        # Hide backwards button
        self.backwards_button.hide()

        # Hide titlebar but show border decoration
        self.get_window().set_accept_focus(True)
        #self.get_window().set_decorations(Gdk.WMDecoration.BORDER)

        # Hide progress bar as it's value is zero
        self.progressbar.set_fraction(0)
        self.progressbar.hide()
        self.progressbar_step = 1.0 / (len(self.pages) - 2)

        with open(tmp_running, "w") as tmp_file:
            tmp_file.write("Thus %d\n" % 1234)

        GLib.timeout_add(1000, self.pages["slides"].manage_events_from_cb_queue)

    def on_exit_button_clicked(self, widget, data=None):
        """ Quit Thus """
        remove_temp_files()
        logging.info(_("Quiting installer..."))
        os._exit(0)

    def set_progressbar_step(self, add_value):
        new_value = self.progressbar.get_fraction() + add_value
        if new_value > 1:
            new_value = 1
        if new_value < 0:
            new_value = 0
        self.progressbar.set_fraction(new_value)
        if new_value > 0:
            self.progressbar.show()
        else:
            self.progressbar.hide()

    def on_forward_button_clicked(self, widget, data=None):
        """ Show next screen """
        next_page = self.current_page.get_next_page()

        if next_page is not None:
            stored = self.current_page.store_values()

            if stored is not False:
                self.set_progressbar_step(self.progressbar_step)
                self.main_box.remove(self.current_page)

                self.current_page = self.pages[next_page]

                if self.current_page is not None:
                    self.current_page.prepare('forwards')
                    self.main_box.add(self.current_page)

                    if self.current_page.get_prev_page() is not None:
                        # There is a previous page, show button
                        self.backwards_button.show()
                        self.backwards_button.set_sensitive(True)
                    else:
                        self.backwards_button.hide()

    def on_backwards_button_clicked(self, widget, data=None):
        """ Show previous screen """
        prev_page = self.current_page.get_prev_page()

        if prev_page is not None:
            self.set_progressbar_step(-self.progressbar_step)

            # If we go backwards, don't store user changes
            # self.current_page.store_values()

            self.main_box.remove(self.current_page)
            self.current_page = self.pages[prev_page]

            if self.current_page is not None:
                self.current_page.prepare('backwards')
                self.main_box.add(self.current_page)
                # Restore "Next" button's text
                self.forward_button.set_label("gtk-go-forward")
                self.forward_button.set_sensitive(True)
                self.forward_button.set_use_stock(True)

                if self.current_page.get_prev_page() is None:
                    # We're at the first page
                    self.backwards_button.hide()


def setup_logging():
    """ Configure our logger """
    logger = logging.getLogger()

    if cmd_line.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logger.setLevel(log_level)

    # Log format
    formatter = logging.Formatter('%(asctime)s - %(filename)s:%(funcName)s() - %(levelname)s: %(message)s')

    # Create file handler
    file_handler = logging.FileHandler('/tmp/thus.log', mode='w')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if cmd_line.verbose:
        # Show log messages to stdout
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

def check_gtk_version():
    """ Check GTK version """
    # Check desired GTK Version
    major_needed = int(_gtk_version_needed.split(".")[0])
    minor_needed = int(_gtk_version_needed.split(".")[1])
    micro_needed = int(_gtk_version_needed.split(".")[2])

    # Check system GTK Version
    major = Gtk.get_major_version()
    minor = Gtk.get_minor_version()
    micro = Gtk.get_micro_version()

    # Thus will be called from our liveCD that already has the latest GTK version
    # This is here just to help testing Thus in our environment.
    if major_needed > major or (major_needed == major and minor_needed > minor) or \
      (major_needed == major and minor_needed == minor and micro_needed > micro):
        print("Detected GTK %d.%d.%d but %s is needed. Can't run this installer." %
              (major, minor, micro, _gtk_version_needed))
        return False
    else:
        print("Using GTK v%d.%d.%d" % (major, minor, micro))

    return True

def parse_options():
    """ argparse http://docs.python.org/3/howto/argparse.html """

    import argparse
    parser = argparse.ArgumentParser(description="Thus v%s - KaOS Installer" % info.THUS_VERSION)
    parser.add_argument("-d", "--debug", help=_("Sets Thus log level to 'debug'"), action="store_true")
    parser.add_argument("-u", "--update", help=_("Update Thus to the latest version (-uu will force the update)"), action="count")
    parser.add_argument("-t", "--testing", help=_("Do not perform any changes (useful for developers)"), action="store_true")
    parser.add_argument("-v", "--verbose", help=_("Show logging messages to stdout"), action="store_true")
    parser.add_argument("-z", "--z_hidden", help=_("Show options in development (DO NOT USE THIS!)"), action="store_true")

    return parser.parse_args()

def init_thus():
    """ This function initialises Thus """

    # Command line options
    global cmd_line

    if not check_gtk_version():
        sys.exit(1)

    # Command line options
    global cmd_line
    cmd_line = parse_options()

    #setup_logging()

    if cmd_line.update is not None:
        force = False
        if cmd_line.update == 2:
            force = True
        upd = updater.Updater(force)
        if upd.update():
            # Remove /tmp/.setup-running to be able to run another
            # instance of Thus
            remove_temp_files()
            if force:
                # Remove -uu option
                new_argv = []
                for argv in sys.argv:
                    if argv != "-uu":
                        new_argv.append(argv)
            else:
                new_argv = sys.argv
            print("Program updated! Restarting...")
            # Run another instance of Thus (which will be the new version)
            os.execl(sys.executable, *([sys.executable] + new_argv))
            sys.exit(0)

    # Drop root privileges
    misc.drop_privileges()

    # Start Gdk stuff and main window app
    GObject.threads_init()

    myapp = Main()

    Gtk.main()

if __name__ == '__main__':
    init_thus()
