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
_ACTIVE = '测试中...'
_PASSED = '通过'
_FAILED = '失败'
_UNTESTED = '等待中...'

CARD_TYPE = None

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

_BLACK = gtk.gdk.Color("black")

_SUBITEM_LIST = [
    ('detect card','侦测设备', lambda *x: try_dect(*x)),
    ('compare data','读写比较', lambda *x: try_comp(*x))]

def try_dect(widget, event):
    state,dect_rlt = commands.getstatusoutput('/opt/mfg/ui/tests/cr-util-read /dev/sdb ' + CARD_TYPE)

    if state :
       return _PASSED
    else:
	start_time = time.time()
	while True:
            time.sleep(2)
	    state,dect_rlt = commands.getstatusoutput('/opt/mfg/ui/tests/cr-util-read /dev/sdb ' + CARD_TYPE)
	    if state :
              return _PASSED
	    if start_time + 3000 <= time.time():
              return _FAILED


def try_comp(widget, event):
    comp_rlt=os.system('/opt/mfg/ui/tests/CardReader -t -d /dev/sdb')
    if comp_rlt:
       return _FAILED
    else:
       return _PASSED
       

class factory_CardReader:

    def smoke_subitem(self):   
        if self.call_loop == 1:    
           ename, name, cb_fn = self._current_subitem
           ret_status = cb_fn(None, None)
           self._status_map[ename] = ret_status
           if self._status_map[ename] == _PASSED:
               self.passc = self.passc + 1
               if self.passc == 1:
                   exit(99)
                   gtk.main_quit()
           elif self._status_map[ename] == _FAILED:
               self.dect_fail = 1
               exit(1)

         
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
        if name or name != None:
            status = self._status_map[name]
            widget.set_text(status)
            widget.modify_fg(gtk.STATE_NORMAL, _LABEL_COLORS[status])
        widget.queue_draw()


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

        self.dect_fail = 0
        self.passc = 0
        self.call_loop = 0
        self.escape = 0
        
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        #self.window.set_keep_above(True)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("black"))
        self.window.move(400, 200)
        global CARD_TYPE
	if len(sys.argv) == 2:
	    if sys.argv[1] == 'sdc':
	        prompt = '读卡器测试\n请插入SD卡\n'
	        CARD_TYPE = 'SD'
	    if sys.argv[1] == 'xdc':
	        prompt = '读卡器测试\n请插入XD卡\n'
	        CARD_TYPE = 'xD'
	    if sys.argv[1] == 'msc':
	        prompt = '读卡器测试\n请插入MS卡\n'
	        CARD_TYPE = 'MS'
        self._subitem_queue = [x for x in reversed(_SUBITEM_LIST)]
        self._status_map = dict((en, _UNTESTED) for en, n, f in _SUBITEM_LIST)
  
        prompt_label = gtk.Label(prompt)
                            
        prompt_label.modify_font(_LABEL_FONT)
        prompt_label.set_alignment(0.5, 0.5)
        prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
    
        prompt_label.show()

        vbox = gtk.VBox()
        vbox.pack_start(prompt_label, False, False)

        for ename, name, cb_fun in _SUBITEM_LIST:
            label_box = self.make_subitem_label_box(ename, name, cb_fun)
            label_box.show()
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
       factory_CardReader()
       main()
   finally:
       gtk.gdk.threads_leave()
