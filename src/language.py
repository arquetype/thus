#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  language.py
#
#  Copyright 2013 Antergos (http://antergos.com/)
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

from gi.repository import Gtk, GLib
import gettext
import locale
import os
import logging

# Useful vars for gettext (translations)
APP_NAME = "thus"
LOCALE_DIR = "/usr/share/locale"

# Import functions
import canonical.i18n as i18n

_next_page = "location"
_prev_page = None


class Language(Gtk.Box):

    def __init__(self, params):
        self.title = params['title']
        self.forward_button = params['forward_button']
        self.backwards_button = params['backwards_button']
        self.settings = params['settings']

        super().__init__()
        self.ui = Gtk.Builder()
        self.ui_dir = self.settings.get('ui')
        self.ui.add_from_file(os.path.join(self.ui_dir, "language.ui"))
        self.ui.connect_signals(self)

        self.label_choose_language = self.ui.get_object("label_choose_language")
        self.treeview_language = self.ui.get_object("treeview_language")

        self.translate_ui()

        data_dir = self.settings.get('data')

        self.current_locale = locale.getdefaultlocale()[0]
        self.language_list = os.path.join(data_dir, "languagelist.data.gz")
        self.set_languages_list()

        image1 = self.ui.get_object("image1")
        image1.set_from_file(os.path.join(data_dir, "welcome-logo.png"))

        label = self.ui.get_object("welcome_label")
        label.set_name("WelcomeMessage")

        super().add(self.ui.get_object("language"))

    def translate_ui(self):
        #txt = _("Welcome to the Manjaro Installer")
        #txt = '<span weight="bold" size="large">%s</span>' % txt
        #self.title.set_markup(txt)

        txt = _("Please choose your language:")
        txt = '<span weight="bold">%s</span>' % txt
        self.label_choose_language.set_markup(txt)

        label = self.ui.get_object("welcome_label")
        txt_bold = _("Notice: This Installer is beta software.")
        txt = _("It is beta software that is under active development. \n" \
        "It does not yet properly handle RAID, btrfs subvolumes, or other  \n" \
        "advanced setups. Please proceed with caution as data loss is possible! \n\n" \
        "If you find any bugs, please report them at <a href='https://github.com/KaOSx/thus/issues'>installer issues</a>")
        txt = "<span weight='bold'>%s</span>\n\n" % txt_bold + txt
        label.set_markup(txt)

        txt = _("Welcome to KaOS!")
        txt = "<span weight='bold' size='large'>%s</span>" % txt
        self.title.set_markup(txt)

    def langcode_to_lang(self, display_map):
        # Special cases in which we need the complete current_locale string
        if self.current_locale not in ('pt_BR', 'zh_CN', 'zh_TW'):
            self.current_locale = self.current_locale.split("_")[0]

        for lang, lang_code in display_map.items():
            if lang_code[1] == self.current_locale:
                return lang

    def set_languages_list(self):
        liststore_language = Gtk.ListStore(str)

        render = Gtk.CellRendererText()
        col_languages = Gtk.TreeViewColumn(_("Languages"), render, text=0)
        self.treeview_language.set_model(liststore_language)
        self.treeview_language.append_column(col_languages)

        current_language, sorted_choices, display_map = i18n.get_languages(self.language_list)
        current_language = self.langcode_to_lang(display_map)
        for lang in sorted_choices:
            liststore_language.append([lang])
            if current_language == lang:
                self.select_default_row(self.treeview_language, current_language)

    def set_language(self, locale_code):
        if locale_code is None:
            locale_code, encoding = locale.getdefaultlocale()

        try:
            lang = gettext.translation(APP_NAME, LOCALE_DIR, [locale_code])
            lang.install()
            self.translate_ui()
        except IOError:
            logging.error(_("Can't find translation file for the %s language") % locale_code)

    # Select language loaded on boot as default
    def select_default_row(self, treeview, language):
        model = treeview.get_model()
        iterator = model.iter_children(None)
        while iterator is not None:
            if model.get_value(iterator, 0) == language:
                path = model.get_path(iterator)
                treeview.get_selection().select_path(path)
                #treeview.scroll_to_cell(path, use_align=False, row_align=0.0, col_align=0.0)
                GLib.idle_add(self.scroll_to_cell, treeview, path)
                break
            iterator = model.iter_next(iterator)

    def scroll_to_cell(self, treeview, path):
        treeview.scroll_to_cell(path)
        return False

    def on_treeview_language_cursor_changed(self, treeview):
        selected = treeview.get_selection()
        if selected:
            (ls, iter) = selected.get_selected()
            if iter:
                current_language, sorted_choices, display_map = i18n.get_languages(self.language_list)
                language = ls.get_value(iter, 0)
                language_code = display_map[language][1]
                self.set_language(language_code)

    def store_values(self):
        selected = self.treeview_language.get_selection()

        (ls, iter) = selected.get_selected()
        language = ls.get_value(iter,0)

        current_language, sorted_choices, display_map = i18n.get_languages(self.language_list)

        self.settings.set("language_name", display_map[language][0])
        self.settings.set("language_code", display_map[language][1])

        return True

    def scroll_to_selected_item(self, treeview):
        selected = treeview.get_selection()

        if selected:
            (ls, iterator) = selected.get_selected()
            model = treeview.get_model()
            path = model.get_path(iterator)
            treeview.get_selection().select_path(path)
            GLib.idle_add(self.scroll_to_cell, treeview, path)

    def prepare(self, direction):
        self.translate_ui()
        self.backwards_button.hide()

        # scroll language treeview to selected item
        self.scroll_to_selected_item(self.treeview_language)

        self.show_all()

    def get_prev_page(self):
        return _prev_page

    def get_next_page(self):
        return _next_page
