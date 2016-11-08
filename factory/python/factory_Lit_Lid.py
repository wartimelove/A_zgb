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
    ('LightSensor','光感应/合盖测试', lambda *x: try_check_sensor(*x))]

def try_check_sensor(widget, event):
    _lid_flg = 9
    _sensor_flg = 9
    start_time = time.time()

    stat,info = commands.getstatusoutput('''initctl list | grep "powerm start/running" ''')
    if stat == 0:
        os.system('initctl stop powerm')
    
    #if not os.path.isfile('/sys/bus/iio/device0/lux'):
    #    os.system('sudo echo tsl2563 0x29 > /sys/class/i2c-adapter/i2c-2/new_device')

    #st,rel = commands.getstatusoutput('sudo lsmod | grep -q tsl2563')
    #if st != 0:
    #    return _FAILED
    #time.sleep(1)
    st_before,rel_before=commands.getstatusoutput('cat /sys/bus/iio/devices/device0/illuminance0_input')
    rel_before_int=int(rel_before) - 5
    while True:
        st_after,rel_after=commands.getstatusoutput('cat /sys/bus/iio/devices/device0/illuminance0_input')
        rel_after_int=int(rel_after)
        time.sleep(0.5)
        if rel_before_int >= rel_after_int  or rel_after_int == 0:
            _sensor_flg=0
        rel_lid=os.system('/opt/mfg/ui/tests/NUVOTON -lidswitch')
        if rel_lid == 512:
            _lid_flg=0
        if _sensor_flg == 0 and _lid_flg == 0:
            os.system('amixer set Master 0 cap 80% 80%') 
            os.system('aplay -d 3 /opt/mfg/ui/wavs/PQCTEST_03.wav &')
            return _PASSED

        if start_time + 3000 <= time.time():
            if _sensor_flg == 9 or _lid_flg == 9:
                return _FAILED

class factory_Lit_Lid():
    version = 1

    def smoke_subitem(self):  
       ename, name, cb_fn = self._current_subitem
       self._status_map[ename] = _ACTIVE                 
       #print "start testing...." + ename
       ret_status = cb_fn(None, None)
       #print name + " " + ret_status
       self._status_map[ename] = ret_status
       if ret_status == _PASSED:
               sys.exit(99)
       gtk.main_quit()
 
          
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

        self.prompt_label = gtk.Label('光感应/合盖测试.....\n'
                                      '请合上显示屏\n')
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
       factory_Lit_Lid()
       main()
   finally:
       gtk.gdk.threads_leave()
