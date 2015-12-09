#!/usr/bin/env python
# This file is part of Xpra.
# Copyright (C) 2009-2014 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

"""
    about.py
"""

import sys
import os.path

from xpra.gtk_common.gobject_compat import import_gtk, is_gtk3
gtk = import_gtk()
import webbrowser

from xpra.scripts.config import get_build_info
from xpra import __version__
from xpra.gtk_common.gtk_util import add_close_accel
from xpra.log import Logger
log = Logger("info")


APPLICATION_NAME = "Xpra"
SITE_DOMAIN = "xpra.org"
SITE_URL = "http://%s/" % SITE_DOMAIN


GPL2 = None
def load_license():
    global GPL2
    if GPL2 is None:
        from xpra.platform.paths import get_resources_dir
        gpl2_file = os.path.join(get_resources_dir(), "COPYING")
        if os.path.exists(gpl2_file):
            with open(gpl2_file, mode='rb') as f:
                GPL2 = f.read().decode('latin1')
    return GPL2


global about_dialog
about_dialog = None
def about(on_close=None):
    global about_dialog
    if about_dialog:
        about_dialog.show()
        about_dialog.present()
        return
    from xpra.platform.paths import get_icon
    xpra_icon = get_icon("xpra.png")
    dialog = gtk.AboutDialog()
    if not is_gtk3():
        def on_website_hook(dialog, web, *args):
            ''' called when the website item is selected '''
            webbrowser.open(SITE_URL)
        def on_email_hook(dialog, mail, *args):
            webbrowser.open("mailto://shifter-users@lists.devloop.org.uk")
        gtk.about_dialog_set_url_hook(on_website_hook)
        gtk.about_dialog_set_email_hook(on_email_hook)
        if xpra_icon:
            dialog.set_icon(xpra_icon)
    dialog.set_name("Xpra")
    dialog.set_version(__version__)
    dialog.set_authors(('Antoine Martin <antoine@devloop.org.uk>',
                        'Nathaniel Smith <njs@pobox.com>',
                        'Serviware - Arthur Huillet <ahuillet@serviware.com>'))
    _license = load_license()
    dialog.set_license(_license or "Your installation may be corrupted,"
                    + " the license text for GPL version 2 could not be found,"
                    + "\nplease refer to:\nhttp://www.gnu.org/licenses/gpl-2.0.txt")
    dialog.set_comments("\n".join(get_build_info()))
    dialog.set_website(SITE_URL)
    dialog.set_website_label(SITE_DOMAIN)
    if xpra_icon:
        dialog.set_logo(xpra_icon)
    if hasattr(dialog, "set_program_name"):
        dialog.set_program_name(APPLICATION_NAME)
    def close(*args):
        close_about()
        #the about function may be called as a widget callback
        #so avoid calling the widget as if it was a function!
        if on_close and hasattr(on_close, '__call__'):
            on_close()
    dialog.connect("response", close)
    add_close_accel(dialog, close)
    about_dialog = dialog
    dialog.show()

def close_about(*args):
    global about_dialog
    if about_dialog:
        about_dialog.destroy()
        about_dialog = None


def main():
    about(on_close=gtk.main_quit)
    gtk.main()


if __name__ == "__main__":
    from xpra.platform import init, clean
    from xpra.platform.gui import init as gui_init
    try:
        init("About")
        gui_init()
        v = main()
    finally:
        clean()
    sys.exit(v)
