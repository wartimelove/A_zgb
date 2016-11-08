#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# DESCRIPTION :
#
# This is a factory test to test the LED display.
import gtk
import pango
import os
import sys
import gobject
import time
from gtk import gdk
NUVOTON = '/opt/mfg/ui/tests/NUVOTON '

_ACTIVE = '测试中...'
_PASSED = '通过'
_FAILED = '失败'
_UNTESTED = '等待中...'
_INQUIRE = '测试是否通过？'

_LABEL_STATUS_SIZE = (140, 30)
_LABEL_STATUS_FONT = pango.FontDescription('courier new condensed 16')
_LABEL_FONT = pango.FontDescription('courier new condensed 20')
_LABEL_FG = gtk.gdk.color_parse('light green')
_LABEL_UNTESTED_FG = gtk.gdk.color_parse('grey40')

_LABEL_COLORS = {
    _ACTIVE: gtk.gdk.color_parse('light goldenrod'),
    _PASSED: gtk.gdk.color_parse('pale green'),
    _FAILED: gtk.gdk.color_parse('tomato'),
    _UNTESTED: gtk.gdk.color_parse('dark slate grey'),
    _INQUIRE: gtk.gdk.color_parse('light goldenrod')}

def Backlight_test_fun(widget, event):
    os.system(NUVOTON + '-bl -off')
    os.system(NUVOTON + '-bl -off')
    time.sleep(2)
    os.system(NUVOTON + '-bl -on')
    return False

_LED_TEST_LIST = [
    ('Backlight','背光', lambda *x: Backlight_test_fun(*x))]



class factory_Backlight():
    version = 1

    def smoke_subitem(self):   
       ename, name, cb_fn = self._current_subitem
       #print "start testing...." + ename
       ret_status = cb_fn(None, None)
       #print name + "test ended "
       self._status_map[ename] = _INQUIRE
       return False
          
    def pop_subitem(self):
        if self._led_queue:
	    self._current_subitem = self._led_queue.pop()
            ename, name, cb_fn = self._current_subitem
            self._status_map[ename] = _ACTIVE
	    #print "status",self._status_map[ename]
            gobject.timeout_add(200, self.smoke_subitem)
        return True

    def key_release_event(self, widget, event):
        if event.keyval == gtk.keysyms.space and self.FLG == 0:
	    self.FLG = 1
            self.pop_subitem()
        elif event.keyval == gtk.keysyms.Tab and self.FLG == 1:
	    sys.exit(1)
            gtk.main_quit()
        elif event.keyval == gtk.keysyms.Return and self.FLG == 1:
            sys.exit(99)
            gtk.main_quit()
        elif event.keyval == ord('Q'):
            gtk.main_quit()
        return True
    def label_status_expose(self, widget, event, name=None):
        status = self._status_map[name]
        widget.set_text(status)
        widget.modify_fg(gtk.STATE_NORMAL, _LABEL_COLORS[status])

    def make_led_label_box(self,ename, name, cb_fun):
        eb = gtk.EventBox()
        eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
        label_status = gtk.Label(_UNTESTED)
        label_status.set_size_request(*_LABEL_STATUS_SIZE)
        label_status.set_alignment(0, 0.5)
        label_status.modify_font(_LABEL_STATUS_FONT)
        label_status.modify_fg(gtk.STATE_NORMAL, _LABEL_UNTESTED_FG)
        expose_cb = lambda *x: self.label_status_expose(*x, **{'name':ename})
        label_status.connect('expose_event', expose_cb)
        label_en = gtk.Label(name)
        label_en.set_alignment(1, 0.5)
        label_en.modify_font(_LABEL_STATUS_FONT)
        label_en.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
        label_sep = gtk.Label(' : ')
        label_sep.set_alignment(0.5, 0.5)
        label_sep.modify_font(_LABEL_FONT)
        label_sep.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
        hbox = gtk.HBox()
        hbox.pack_end(label_status, False, False)
        hbox.pack_end(label_sep, False, False)
        hbox.pack_end(label_en, False, False)
        eb.add(hbox)
        return eb



    def __init__(self):
	self.FLG = 0
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("black"))
        self.window.move(400, 200)

        self._led_queue = [x for x in reversed(_LED_TEST_LIST)]
        self._status_map = dict((en, _UNTESTED) for en,n, f in _LED_TEST_LIST)

        prompt_label = gtk.Label('背光测试,按空格键开始测试\n'
                                 '失败按Tab键，通过按回车键\n')
        prompt_label.modify_font(_LABEL_FONT)
        prompt_label.set_alignment(0.5, 0.5)
        prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
        self._prompt_label = prompt_label

        vbox = gtk.VBox()
        vbox.pack_start(prompt_label, False, False)

        for ename, name, cb_fun in _LED_TEST_LIST:
            label_box = self.make_led_label_box(ename, name, cb_fun)
            vbox.pack_start(label_box, False, False)


        vbox.show()

        self.window.add(vbox)
  
        self.window.show_all()
        gtk.gdk.keyboard_grab(self.window.window)
        self.window.connect('key-release-event', self.key_release_event)
        self.window.add_events(gdk.KEY_RELEASE_MASK)


def main():
    gtk.main()    
   

if __name__ == "__main__":
    factory_Backlight()
    main()
