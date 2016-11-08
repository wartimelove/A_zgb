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
import random
import subprocess
import thread
_BLACK = gtk.gdk.Color()

def XXX_log(s):
    print >> sys.stderr, 'FACTORY: ' + s

_ACTIVE = '测试中...'
_PASSED = '通过'
_FAILED = '失败'
_UNTESTED = '等待中...'

WAV_PATH = 'aplay /opt/mfg/ui/wavs/'

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
    ('chk_Vnum','HDMI 视频 '),
    ('chk_Anum','HDMI 音频 ')]




class factory_HDMI():
    version = 1


    def label_status_expose(self, widget, event, name=None):
        if name or name != None:
            status = self._status_map[name]
            widget.set_text(status)
            widget.modify_fg(gtk.STATE_NORMAL, _LABEL_COLORS[status])
        widget.queue_draw()


    def make_subitem_label_box(self, ename, name):
        eb = gtk.EventBox()
        #_BLACK = gtk.gdk.Color()
        eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
        label_status = gtk.Label(_UNTESTED)
        label_status.set_size_request(*_LABEL_STATUS_SIZE)
        label_status.set_alignment(0, 0.5)
        label_status.modify_font(_LABEL_STATUS_FONT)
        label_status.modify_fg(gtk.STATE_NORMAL, _LABEL_UNTESTED_FG)

        #self.label_status_expose(label_status, name)
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

    def play_sound(self):
        self.rand1 = random.randint(0,9)
        CMD = WAV_PATH + str(self.rand1) + '.wav'
        subprocess.Popen(CMD,shell = True, stdout=subprocess.PIPE)
        return self.rand1


    def enter_callback(self, widget, entry):
        entry_text = entry.get_text()
        ename, name = self._current_subitem
        entry.set_text('')
	if self.rand1 == int(entry_text):
	    self._status_map[ename] = _PASSED
	    if ename == 'chk_Anum':
	        sys.exit(99)
	    self.rand1 = 10100112
	    if self._subitem_queue:
	        self.pop_subitem()
	    self.play_sound() 
        else:
	    if  ename == 'chk_Vnum':
	        sys.exit(1)
	    else:
		self.play_sound() 


    def pop_subitem(self):
       if not self._subitem_queue:
    	  pass
       else:
          self._current_subitem = self._subitem_queue.pop()
          ename, name = self._current_subitem
          self._status_map[ename] = _ACTIVE
          if ename == 'chk_Anum':
	    self.p.set_text("请输入听到的数字并回车:")



    def key_press_event(self, widget, event):
        self.prompt_label1.modify_fg(gtk.STATE_NORMAL,gtk.gdk.Color("black"))


    def __init__(self):
        os.system('sudo /opt/mfg/ui/tests/NUVOTON -bl -off')
        os.system('sudo /opt/mfg/ui/tests/NUVOTON -bl -off')
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("black"))
        self.window.move(400, 200)
        self.window.connect('key-press-event',self.key_press_event)

        self._subitem_queue = [x for x in reversed(_SUBITEM_LIST)]       
        self._status_map = dict((en, _UNTESTED) for en, n in _SUBITEM_LIST)

        prompt_label = gtk.Label('HDMI测试.....\n')
                            
        prompt_label.modify_font(_LABEL_FONT)
        prompt_label.set_alignment(0.5, 0.5)
        prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)


        self.word='显示数字 : '
        self.rand1=random.randint(0,9)
        self.cat=self.word + str(self.rand1)

        self.prompt_label1 = gtk.Label(self.cat)
        self.prompt_label1.modify_font(_LABEL_FONT)
        self.prompt_label1.set_alignment(0.5, 0.5)
        self.prompt_label1.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)

    
        entry = gtk.Entry()
        entry.set_max_length(1)
        entry.set_size_request(40,30)
        entry.modify_font(pango.FontDescription('courier new condensed 15'))
        entry.grab_focus
        entry.connect("activate", self.enter_callback, entry)
        entry.connect("expose-event", self.label_status_expose)
        entry.show()
        
        self.p = gtk.Label("请输入看到的数字并回车:")
        self.p.modify_font(pango.FontDescription('courier new condensed 14'))
        self.p.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('light goldenrod'))

        hbox1 = gtk.HBox()
        hbox1.pack_start(self.p,False,False)
        hbox1.pack_start(entry, False, False)
        hbox1.show()
        
        vbox = gtk.VBox()
        vbox.pack_start(prompt_label, False, False)
        vbox.pack_start(self.prompt_label1, False, False)
        vbox.pack_start(hbox1, False, False)

        for ename, name in _SUBITEM_LIST:
            label_box = self.make_subitem_label_box(ename, name)
            vbox.pack_start(label_box, False, False)
        vbox.show()
        self.window.add(vbox)
        self.window.show_all()
	gtk.gdk.keyboard_grab(self.window.window)
	thread.start_new_thread(self.pop_subitem, ())


def main():
    gtk.main()    
   

if __name__ == "__main__":
    gtk.gdk.threads_init()
    try:
       gtk.gdk.threads_enter() 
       factory_HDMI()
       main()
    finally:
       gtk.gdk.threads_leave()
