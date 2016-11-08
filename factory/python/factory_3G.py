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
import re
sys.path.append('/opt/mfg/ui/pydirs/')
sys.path.append('/opt/mfg/ui/config/')
import factory_sdt as sdt
import factory_conf as cfg
import string
_BLACK = gtk.gdk.Color()

ATCOM = '/opt/mfg/ui/utils/com /dev/ttyUSB1 '


_ACTIVE = '激活'
_PASSED = '通过'
_FAILED = '失败'
_UNTESTED = '未测'

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
    ('imei','IMEI 检测', lambda *x: get_info(*x,**{'cmd':'AT+CGSN'})),
    ('imsi','IMSI 检测', lambda *x: get_info(*x,**{'cmd':'AT+CIMI'})),
    ('fw','F/W  检测',   lambda *x: get_info(*x,**{'cmd':'AT+GMR'})),
    ('main','主天线信号检测', lambda *x: get_rssi(*x,**{'cmd':'main'})),
    ('aux','副天线信号检测', lambda *x: get_rssi(*x,**{'cmd':'aux'}))]

def get_info(widget, event,cmd):
    CMD = ATCOM + cmd + ' | grep "OK"'
    stat,info = commands.getstatusoutput(CMD)
    sdt.log("FFT: %s" % info)
    if info:
	return _PASSED
    else:
	return _FAILED


def get_rssi(widget, event,cmd):
    os.system(ATCOM + 'at+cfun=5')
    CMD =  ATCOM + '\'at$qcagc="wcdma_1900",9662,"' + cmd + '"\' | grep "RSSI:" | cut -d ":" -f 2 | sed "s/ //g"'
    stat,info = commands.getstatusoutput(CMD)
    sdt.log("FFT:%s signal strength:%s" % (cmd,info))
    #os.system(ATCOM + 'at+cfun=1')
    if info != "":
        signal = string.atoi(info,10)
    else:
        return _FAILED
    if signal >= cfg.Gobi_signal_max[cmd] and signal <= cfg.Gobi_signal_min[cmd] :
	return _PASSED
    else:
        return _FAILED

class factory_3G():
    version = 1

                
          
    def pop_subitem(self):
        while self._subitem_queue:
            self._current_subitem = self._subitem_queue.pop()
            ename, name, cb_fn = self._current_subitem
            self._status_map[ename] = _ACTIVE
            if ename == 'imei':
                time.sleep(5)
            ret_status = cb_fn(None, None)
            self._status_map[ename] = ret_status
            
            if self._status_map[ename] == _PASSED:
               self.passc = self.passc + 1
               if self.passc == len(_SUBITEM_LIST):
                   self.result = True
                   exit()
            elif self._status_map[ename] == _FAILED:
               self.result = False
        exit()


    def label_status_expose(self, widget, event, name):
        status = self._status_map[name]
        widget.set_text(status)
        widget.modify_fg(gtk.STATE_NORMAL, _LABEL_COLORS[status])
        #gobject.timeout_add(200,widget.queue_draw)

    def make_subitem_label_box(self, ename, name, fn):
        eb = gtk.EventBox()
        #_BLACK = gtk.gdk.Color()
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
	        stat,carrier = commands.getstatusoutput('''vpd -l 2>/dev/null |grep CARRIER |cut -d"=" -f2|sed 's/"//g' ''')
	        if carrier != '' or carrier !='N/A'   :
                    st,rel=commands.getstatusoutput('''modem_set_carrier ''' + carrier + '''| grep "Unknow carrier name" ''' )
                    if rel == '':
                       os.system(ATCOM + 'at+cfun=1')
                       sys.exit(99)
                    else:
          	        sys.exit(1)
            else:
            	sys.exit(1)
        return True
        
    def __init__(self):
        self.result = False
        self.count=0
        self.passc = 0

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_keep_above(True)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("black"))
        self.window.move(400, 200)
        self._subitem_queue = [x for x in reversed(_SUBITEM_LIST)]       # scripts has done
        self._status_map = dict((en, _UNTESTED) for en, n, f in _SUBITEM_LIST)

        prompt_label = gtk.Label('3G测试.....\n')
                            
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
       factory_3G()
       main()
    finally:
       gtk.gdk.threads_leave()
