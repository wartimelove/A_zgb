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
sys.path.append('/opt/mfg/ui/pydirs/')
import factory_sdt as sdt
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
    ('left usbstorage','USB(左)', lambda *x: test_usb_storage_l(*x,**{'l_r':'1-4'})),
    ('right usbstorage','USB(右)', lambda *x: test_usb_storage_r(*x,**{'l_r':'1-1'}))]

def test_usb_storage_l(widget, event,l_r):
    start_time = time.time()
    cmd = ''' ls -al /sys/block/* | grep '''+l_r+''' | cut -d "/" -f4 |cut -d" " -f1'''
    while True:
        stat,devname = commands.getstatusoutput(cmd)
        if not os.path.isfile('/dev/' + devname):
            sdt.log("left need sleep")
            time.sleep(1)
        if devname:
            sdt.log("FFT: left port usb device name is: /dev/%s ,port is %s" % (devname,l_r))
            cmd2 = ''' hdparm -t /dev/'''+ devname +''' | grep "MB/sec" '''
            stat,relt = commands.getstatusoutput(cmd2)
            sdt.log("FFT:left USB hdparm status is:%s,speed is:%s" % (stat,relt))
            if stat == 0:
                return _PASSED
            else:
                return _FAILED
        if start_time + 3000 <= time.time():
            return _FAILED
        time.sleep(0.5)

def test_usb_storage_r(widget, event,l_r):
    start_time = time.time()
    cmd = ''' ls -al /sys/block/* | grep '''+l_r+''' | cut -d "/" -f4 |cut -d" " -f1'''
    while True:
        stat,devname = commands.getstatusoutput(cmd)
        if not os.path.isfile('/dev/' + devname):
            sdt.log("right need sleep")
            time.sleep(1)
        if devname:
            sdt.log("FFT: right port usb device name is: /dev/%s ,port is %s" % (devname,l_r))
            cmd2 = ''' hdparm -t /dev/'''+ devname +''' | grep "MB/sec" '''
            stat,relt = commands.getstatusoutput(cmd2)
            sdt.log("FFT:right USB hdparm status is:%s,speed is:%s" % (stat,relt))
            if stat == 0:
                return _PASSED
            else:
                return _FAILED
        if start_time + 3000 <= time.time():
            return _FAILED
        time.sleep(0.5)

class factory_Usbstorage():
    version = 1

    def smoke_subitem(self):  
	ename, name, cb_fn = self._current_subitem
	ret_status = cb_fn(None, None)
	self._status_map[ename] = ret_status
	if self._status_map[ename] == _PASSED:
	   time.sleep(1)
           self.passc = self.passc + 1
        elif self._status_map[ename] == _FAILED:        
           self.fail = 1
	self.count += 1
	sdt.log("Stop USB Storage test %s,result :%s" % (ename, self._status_map[ename]))

    def pop_subitem(self):
        while self._subitem_queue:
            self._current_subitem = self._subitem_queue.pop()
            ename, name, cb_fn = self._current_subitem
            if self._status_map[ename] == _UNTESTED:
               self._status_map[ename] = _ACTIVE
	       sdt.log("Start USB Storage test %s" % ename)
	       t = threading.Thread(target = self.smoke_subitem)
               t.start()

	while True:
	    time.sleep(1)
	    if self.count == 2:
	       if self.passc == 2:
		    self.result = True
               elif self.fail:
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
    	self.result = False
        self.fail = 0
        self.count=0
        self.passc = 0
        self.call_loop = 0
        self.escape = 0
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("black"))
        self.window.move(400, 200)
        self._subitem_queue = [x for x in reversed(_SUBITEM_LIST)]
        self._status_map = dict((en, _UNTESTED) for en, n, f in _SUBITEM_LIST)

        prompt_label = gtk.Label('USB存储设备测试\n'
        			 '请按提示插入USB设备\n')
                            
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
       factory_Usbstorage()
       main()
   finally:
       gtk.gdk.threads_leave()

