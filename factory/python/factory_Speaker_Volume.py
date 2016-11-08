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
import random
from gtk import gdk
import subprocess
import thread
import gobject
import commands
import time
sys.path.append('/opt/mfg/ui/pydirs/')
import factory_sdt as sdt

SPEAK_RPOMPT = '请输入听到的数字并回车: '
VOL_PROMPT = '        按上下键改变音量大小\n        通过按回车，失败按Tab键\n'
_ACTIVE = '测试中...'
_PASSED = '通过'
_FAILED = '失败'
_UNTESTED = '等待测试...'
_INQUIRE = '等待输入'
_VOL_INQ = '测试是否通过?'
_NO_SPEAKER = '未接入外接喇叭(耳机)'

WAV_PATH = 'aplay /opt/mfg/ui/wavs/'
PLAY_FLG = 0

_BLACK = gtk.gdk.Color()

_LABEL_COLORS = {
    SPEAK_RPOMPT:gtk.gdk.color_parse('light goldenrod'),
    VOL_PROMPT:gtk.gdk.color_parse('light goldenrod'),
    _ACTIVE: gtk.gdk.color_parse('light goldenrod'),
    _PASSED: gtk.gdk.color_parse('pale green'),
    _FAILED: gtk.gdk.color_parse('tomato'),
    _UNTESTED: gtk.gdk.color_parse('dark slate grey'),
    _INQUIRE: gtk.gdk.color_parse('light goldenrod'),
    _VOL_INQ:gtk.gdk.color_parse('light goldenrod'),
    _NO_SPEAKER:gtk.gdk.color_parse('light goldenrod')}
 
_LABEL_STATUS_SIZE = (240, 30)
_LABEL_STATUS_FONT = pango.FontDescription('courier new condensed 16')
_LABEL_FONT = pango.FontDescription('courier new condensed 20')
_LABEL_FG = gtk.gdk.color_parse('light green')
_LABEL_UNTESTED_FG = gtk.gdk.color_parse('grey40')

_SUBITEM_LIST = [
    ('Speaker','  喇叭测试', lambda *x: test_Speaker(*x)),
    ('HP','  耳机测试',lambda *x: test_Headphone(*x)),
    ('Volume','  音量测试', lambda *x: test_Volume(*x))]
    
def play_sound():
    global PLAY_FLG
    PLAY_FLG = 2
    while True:
        PLAY_WAV = 'aplay /opt/mfg/ui/wavs/PQCTEST_03.wav'
        os.system(PLAY_WAV)
    
def test_Volume(widget, event):
    VOL_CTRL = 'amixer set Master 0 cap 80%,80%'
    os.system(VOL_CTRL)
    global PLAY_FLG
    if not PLAY_FLG:
        PLAY_FLG = 1
        thread.start_new_thread(play_sound,())
    return False

def test_Speaker(widget, event):
    rand_num = random.randint(0,9)
    CMD = WAV_PATH + str(rand_num) + '.wav'
    subprocess.Popen(CMD,shell = True, stdout=subprocess.PIPE)
    return rand_num
       
   
def test_Headphone(widget, event):

    rand_num = random.randint(0,9)
    CMD = WAV_PATH + str(rand_num) + '.wav'
    subprocess.Popen(CMD,shell = True, stdout=subprocess.PIPE)
    return rand_num      

class factory_Speaker_Volume():
    version = 1

    def jack_detect(self,ename):
        jack = ''' grep -w "Pin-ctls: 0x00:" /proc/asound/card0/codec#0|wc -l'''
        status,output = commands.getstatusoutput(jack)
        if output != '2':
	    self._status_map[ename] = _NO_SPEAKER
            i = 0
            while i <= 3000:
                time.sleep(1)
                status,output = commands.getstatusoutput(jack)
                if output == '2':
                  sdt.log("audio jack %s" % output)
                  break
                i += 1

    def play_status(self,ename):
        if PLAY_FLG == 2:
            self._status_map[ename] = _VOL_INQ
            return False
        return True
   
    def enter_callback(self,widget, entry):
        ename, name, cb_fn = self._current_subitem
        if self._status_map[ename] == _NO_SPEAKER:
	    return
        if str(entry.get_text()) == str(self.play_num):
	    self._status_map[ename] = _PASSED
            print self._status_map[ename]
	    entry.set_text('')
            thread.start_new_thread(self.pop_subitem,())
        else:
            entry.set_text('')
            self._status_map[ename] = _ACTIVE
            self.play_num = cb_fn(None, None)
            self._status_map[ename] = _INQUIRE
            
                
    def pop_subitem(self):
    	if not self._subitem_queue:
    	    gtk.main_quit()
        else:
            self._current_subitem = self._subitem_queue.pop()
            ename, name, cb_fn = self._current_subitem
            self._status_map[ename] = _ACTIVE
            if ename == 'HP':
		self.jack_detect(ename)

            self.play_num = cb_fn(None, None)
            if ename == 'Volume':
                self.input_area.destroy()
                self.window.connect('key-press-event', self.key_press_event)
                self.prompt_label.set_text(VOL_PROMPT)
                gobject.timeout_add(100,self.play_status,ename)
            else:
                self._status_map[ename] = _INQUIRE
        return True
        
    def key_press_event(self, widget, event):
        if PLAY_FLG ==2:
            os.system('amixer set Master 0 cap 80%,80%')
            if event.keyval == gtk.keysyms.Return:
                os.system('kill $(ps|grep aplay |cut -d" " -f2)')
                sys.exit(99)
            elif event.keyval == gtk.keysyms.Tab:
                os.system('kill $(ps|grep aplay |cut -d" " -f2)')
                sys.exit(1)
            
    def cb_value(self,get,set):
        vol_value = set.value
        VOL_CTRL = 'amixer set Master 0 cap '+ str(vol_value) +'%,' + str(vol_value) + '%'
        subprocess.Popen(VOL_CTRL,shell = True, stdout=subprocess.PIPE)
    
    def label_status_expose(self, widget, event, name=None):
        if name or name != None:
            status = self._status_map[name]
            widget.set_text(status)
            widget.modify_fg(gtk.STATE_NORMAL, _LABEL_COLORS[status])
        widget.queue_draw()

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
        
       
    def __init__(self):
        self.play_num = 10100112
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("black"))
        self.window.move(300, 200)

        self._subitem_queue = [x for x in reversed(_SUBITEM_LIST)]       # scripts has done
        self._status_map = dict((en, _UNTESTED) for en, n, f in _SUBITEM_LIST)

        item_label = gtk.Label('音量控制及喇叭测试.....\n')
        item_label.modify_font(_LABEL_FONT)
        item_label.set_alignment(0.5, 0.5)
        item_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)

        self.prompt_label = gtk.Label(SPEAK_RPOMPT)
        self.prompt_label.modify_font(pango.FontDescription('courier new condensed 14'))
        self.prompt_label.set_alignment(0.5, 0.5)
        self.prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
        self.prompt_label.show()
        
        self.input_area = gtk.Entry()
        self.input_area.set_max_length(1)
        self.input_area.set_size_request(40,25)
        self.input_area.modify_font(pango.FontDescription('courier new condensed 13'))
        self.input_area.grab_focus
        self.input_area.connect("activate", self.enter_callback,self.input_area)
        self.input_area.connect("expose-event", self.label_status_expose)
        

        self.input_area.show()
        hbox1 = gtk.HBox()
        hbox1.pack_start(self.prompt_label,False,False)
        hbox1.pack_start(self.input_area,False,False)

        hbox1.show()
        vbox = gtk.VBox()
        vbox.pack_start(item_label, False, False)
        vbox.pack_start(hbox1, False, False)
        
        for ename, name, cb_fun in _SUBITEM_LIST:
            label_box = self.make_subitem_label_box(ename, name, cb_fun)
            vbox.pack_start(label_box, False, False)
               
        adj = gtk.Adjustment(80.0, 0.0, 101.0, 1.0, 1.0, 1.0)
        adj.connect("value_changed",self.cb_value,adj)       
        hscale = gtk.HScale(adj)
        hscale.modify_fg(gtk.STATE_NORMAL,gtk.gdk.color_parse('pale green'))
        hscale.set_update_policy(gtk.UPDATE_CONTINUOUS)

        
        hscale.set_digits(0)
        hscale.set_value_pos(gtk.POS_BOTTOM)
        hscale.set_draw_value(True)
        hscale.show() 
        vbox.pack_start(hscale,False,False)
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
       factory_Speaker_Volume()
       main()
   finally:
       gtk.gdk.threads_leave()
