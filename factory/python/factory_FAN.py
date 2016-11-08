#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


import gtk
import pango
import os
import sys
import gobject
import time
import threading
import commands

_BLACK = gtk.gdk.Color()

def XXX_log(s):
    print >> sys.stderr, 'FACTORY: ' + s

_ACTIVE = '测试中...'
_PASSED = '通过'
_FAILED = '失败'
_UNTESTED = '等待中...'

_LABEL_COLORS = {
    _ACTIVE: gtk.gdk.color_parse('light goldenrod'),
    _PASSED: gtk.gdk.color_parse('pale green'),
    _FAILED: gtk.gdk.color_parse('tomato'),
    _UNTESTED: gtk.gdk.color_parse('dark slate grey')}

_LABEL_STATUS_SIZE = (140, 30)
_LABEL_STATUS_FONT = pango.FontDescription('courier new condensed 16')
_LABEL_FONT = pango.FontDescription('courier new condensed 20')
_LABEL_FG = gtk.gdk.color_parse('light green')
_LABEL_UNTESTED_FG = gtk.gdk.color_parse('grey40')

_SUBITEM_LIST = [
    ('fan_off','风扇 关', lambda *x: test_fan_off(*x)),
    ('fan_on','风扇 开', lambda *x: test_fan_on(*x))]

def test_fan_off(widget, event):
    fan_off=os.system('/opt/mfg/ui/tests/NUVOTON -fan -off')
    if fan_off != 256:
       return _FAILED
    else:
       time.sleep(5)
       st,rel = commands.getstatusoutput('/opt/mfg/ui/tests/NUVOTON -fan -speed | grep fan | cut -d" " -f4')
       if rel == '0':
          return _PASSED
       else:
          return _FAILED

def test_fan_on(widget, event):
    fan_on=os.system('/opt/mfg/ui/tests/NUVOTON -fan -on')
    if fan_on != 256:
       return _FAILED
    else:
       time.sleep(2) 
       st,rel = commands.getstatusoutput('/opt/mfg/ui/tests/NUVOTON -fan -speed | grep fan | cut -d" " -f4')
       rel_int = int(rel)
       if rel_int > 0:
          return _PASSED
       else:
          return _FAILED

class factory_FAN():
    version = 1

    def smoke_subitem(self):   
        if self.call_loop == 1:    
           ename, name, cb_fn = self._current_subitem
           #print "start testing...." + ename
           ret_status = cb_fn(None, None)
           #print name + " " + ret_status
           self._status_map[ename] = ret_status
           if self._status_map[ename] == _PASSED:
               self.passc = self.passc + 1
           elif self._status_map[ename] == _FAILED:
               self.fail = self.fail + 1
           self.count = self.fail + self.passc   
           if self.passc ==2:
	       sys.exit(99)
	       gtk.main_quit()
               return False      
 	   elif self.count==2:
               gtk.main_quit()
               return False
                   
          
    def pop_subitem(self):

        while self._subitem_queue:
            self._current_subitem = self._subitem_queue.pop()
            ename, name, cb_fn = self._current_subitem
            self._status_map[ename] = _ACTIVE
            ret_status = cb_fn(None, None)
            self._status_map[ename] = ret_status
            
            if self._status_map[ename] == _PASSED:
               self.passc = self.passc + 1
               if self.passc == 2:
                   self.result = True
                   exit()
            elif self._status_map[ename] == _FAILED:
               self.dect_fail = 1
               self.result = False
               exit()

    def label_status_expose(self, widget, event, name):
        status = self._status_map[name]
        widget.set_text(status)
        widget.modify_fg(gtk.STATE_NORMAL, _LABEL_COLORS[status])

    def make_subitem_label_box(self, ename, name, fn):
        eb = gtk.EventBox()
        #_BLACK = gtk.gdk.Color()
        eb.modify_bg(gtk.STATE_NORMAL, _BLACK)
        label_status = gtk.Label(_UNTESTED)
        label_status.set_size_request(*_LABEL_STATUS_SIZE)
        label_status.set_alignment(0, 0.5)
        label_status.modify_font(_LABEL_STATUS_FONT)
        label_status.modify_fg(gtk.STATE_NORMAL, _LABEL_UNTESTED_FG)

        #self.label_status_expose(label_status, name)
        expose_cb = lambda *x: self.label_status_expose(*x, **{'name':ename})
        label_status.connect('expose_event', expose_cb)
        #label_status.connect('expose_event', fn)

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

    def watch_thread(self,thd):
        if not thd.isAlive():
            if self.result :
                sys.exit(99)
            else:
            	sys.exit(1)
        return True

    def __init__(self):
        self.fail = 0
        self.count=0
        self.passc = 0
        self.call_loop = 0
        self.escape = 0
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("black"))
        self.window.move(400, 200)

        self._subitem_queue = [x for x in reversed(_SUBITEM_LIST)]       # scripts has done
        self._status_map = dict((en, _UNTESTED) for en, n, f in _SUBITEM_LIST)

        prompt_label = gtk.Label('风扇测试.....\n')
                            
        prompt_label.modify_font(_LABEL_FONT)
        prompt_label.set_alignment(0.5, 0.5)
        prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
        self._prompt_label = prompt_label

        vbox = gtk.VBox()
        vbox.pack_start(prompt_label, False, False)

        for ename, name, cb_fun in _SUBITEM_LIST:
            label_box = self.make_subitem_label_box(ename, name, cb_fun)
            vbox.pack_start(label_box, False, False)

        vbox.show()
        self.window.add(vbox)
        self.window.show_all()
	thd = threading.Thread(target = self.pop_subitem)
	thd.start()
        gobject.timeout_add(100, self.watch_thread,thd)

def main():
    gtk.main()   

if __name__ == "__main__":
    gtk.gdk.threads_init()
    try:
        gtk.gdk.threads_enter()
        factory_FAN()
        main()
    finally:
        gtk.gdk.threads_leave()
