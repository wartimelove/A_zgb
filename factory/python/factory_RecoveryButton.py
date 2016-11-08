#!/usr/bin/env python
# -*- coding: utf-8 -*-
#


import gtk
import pango
import os
import sys
import gobject
import time
import threading
import commands
_BLACK = gtk.gdk.Color()



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
    ('recoverbtn','复原按钮测试', lambda *x: try_check_rcbtn(*x))]
def try_check_rcbtn(widget, event):
    st,rel = commands.getstatusoutput('crossystem recoverysw_cur')
    if rel != '0':
	return _FAILED
    else:
        start_time = time.time()
        while True:
	    st,rel = commands.getstatusoutput('crossystem recoverysw_cur')
            if rel == '1':
		return _PASSED
	    else:
		time.sleep(1)
            if start_time + 3000 <= time.time():
                return _FAILED

class factory_RecoveryButton():
    version = 1

    def smoke_subitem(self):  
       ename, name, cb_fn = self._current_subitem
       self._status_map[ename] = _ACTIVE                 
       ret_status = cb_fn(None, None)
       self._status_map[ename] = ret_status
       if ret_status == _PASSED:
               sys.exit(99)
       else:
	   sys.exit(1)
 
          
    def pop_subitem(self):
        if self._subitem_queue:
	    self._current_subitem = self._subitem_queue.pop()
            ename, name, cb_fn = self._current_subitem
            self._status_map[ename] = _ACTIVE
            ret_status = cb_fn(None, None)
            self._status_map[ename] = ret_status
            
            if self._status_map[ename] == _PASSED:
                self.result = True
            exit()

    def label_status_expose(self, widget, event, name):
        status = self._status_map[name]
        widget.set_text(status)
        widget.modify_fg(gtk.STATE_NORMAL, _LABEL_COLORS[status])

    def make_subitem_label_box(self, ename, name, fn):
        eb = gtk.EventBox()

        eb.modify_bg(gtk.STATE_NORMAL, _BLACK)
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
        
    def watch_thread(self,thd):
        if not thd.isAlive():
            if self.result :
                sys.exit(99)
            else:
            	sys.exit(1)
        return True


    def __init__(self):
        self.result = False
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("black"))
        self.window.move(400, 200)

        self._subitem_queue = [x for x in reversed(_SUBITEM_LIST)]
        self._status_map = dict((en, _UNTESTED) for en, n, f in _SUBITEM_LIST)

        self.prompt_label = gtk.Label('复原按钮测试...\n'
                                      '请按下复原按钮\n')
        self.prompt_label.modify_font(_LABEL_FONT)
        self.prompt_label.set_alignment(0.5, 0.5)
        self.prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
        self.prompt_label.show()

        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.prompt_label, False, False)

        for ename, name, cb_fun in _SUBITEM_LIST:
            self.label_box = self.make_subitem_label_box(ename, name, cb_fun)
            self.vbox.pack_start(self.label_box, False, False)

        self.vbox.show()
        self.window.add(self.vbox)
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
       factory_RecoveryButton()
       main()
   finally:
       gtk.gdk.threads_leave()
