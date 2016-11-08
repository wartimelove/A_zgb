#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
import pango
import os
import sys
import gobject
import time
import threading
from gtk import gdk
_LABEL_STATUS_SIZE = (140, 30)
_LABEL_STATUS_FONT = pango.FontDescription('courier new condensed 16')
_LABEL_FONT = pango.FontDescription('courier new condensed 20')
_LABEL_FG = gtk.gdk.color_parse('light green')
_LABEL_UNTESTED_FG = gtk.gdk.color_parse('grey40')

class factory_notice3G():
    version = 1
    def key_release_event(self, widget, event):

        if event.keyval == gtk.keysyms.Return :
     
            os.system('sync')
            os.system('init 0')
            
            gtk.main_quit()


      
    def __init__(self):
        self.result = False
        self.fail = 0
        self.count=0
        self.passc = 0

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_keep_above(True)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("black"))
        self.window.move(400, 200)


        prompt_label = gtk.Label('3G测试.....\n \
                                  \n请按回车键（Enter）关机后，插入SIM卡')
                            
        prompt_label.modify_font(_LABEL_FONT)
        prompt_label.set_alignment(0.5, 0.5)
        prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
        self._prompt_label = prompt_label

        vbox = gtk.VBox()
        vbox.pack_start(prompt_label, False, False)


        vbox.show()

        self.window.add(vbox)
  
        self.window.show_all()
        gtk.gdk.keyboard_grab(self.window.window)
        self.window.connect('key-release-event', self.key_release_event)
        self.window.add_events(gdk.KEY_RELEASE_MASK)
    	

def main():
    gtk.main()    

if __name__ == "__main__":
    factory_notice3G()
    main()
