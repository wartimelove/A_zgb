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
import ftplib
from time import ctime
sys.path.append('/opt/mfg/ui/config/')
import factory_conf as cfg
sys.path.append('/opt/mfg/ui/pydirs/')
import factory_sdt as sdt

_BLACK = gtk.gdk.Color()

_ACTIVE = '等待中...'
_PASSED = '通过'
_FAILED = '失败'
_UNTESTED = '未启动'
_CHARGE = '电量不足'
_NOBAT  = '请插电池'
BAT_CAP = 50
_LABEL_COLORS = {
    _ACTIVE: gtk.gdk.color_parse('light goldenrod'),
    _CHARGE: gtk.gdk.color_parse('light goldenrod'),
    _NOBAT : gtk.gdk.color_parse('light goldenrod'),
    _PASSED: gtk.gdk.color_parse('pale green'),
    _FAILED: gtk.gdk.color_parse('tomato'),
    _UNTESTED: gtk.gdk.color_parse('dark slate grey')}

_LABEL_STATUS_SIZE = (140, 30)
_LABEL_STATUS_FONT = pango.FontDescription('courier new condensed 16')
_LABEL_FONT = pango.FontDescription('courier new condensed 20')
_LABEL_FG = gtk.gdk.color_parse('light green')
_LABEL_UNTESTED_FG = gtk.gdk.color_parse('grey40')

_SUBITEM_LIST = [
    ('adapter','请插入电源', lambda *x: test_adapter(*x)),
    ('switch','请转换开发开关', lambda *x: test_dev_switch(*x)),
    ('battery','电池检测', lambda *x: test_battery(*x)),
    ('upload','上传文档', lambda *x: test_uploadsh(*x)),]

def test_adapter(widget,event):
    while True :
        status,output = commands.getstatusoutput('cat /proc/acpi/ac_adapter/AC/state')
        if status == 0 :
            on_line = re.search('on-line',output)
            if on_line is not None:
                break 
        time.sleep(1)
    return _PASSED

def test_dev_switch(widget,event):
    while True :
        status,output = commands.getstatusoutput("crossystem devsw_cur")
        if output == '0' :
             status,output = commands.getstatusoutput('/opt/mfg/ui/tests/NUVOTON -info | grep bat_status=On')      
             if output :     
                   break
        time.sleep(1)
    return _PASSED
def test_battery(widget,event):
         status,output = commands.getstatusoutput('/opt/mfg/ui/tests/NUVOTON -info | grep relative | cut -d "=" -f2')
         if output :
	     sdt.log("FFT: Battery is ok!! CAP is %s " % output)
             if int(output)>=BAT_CAP and int (output)<= 100:
                 return _PASSED                
             else :
                 return _CHARGE
         else :
             status,output = commands.getstatusoutput('/opt/mfg/ui/tests/NUVOTON -info | grep bat_status=Off-line')
             if output :
                 return _NOBAT     
             else :                             
                 return _FAILED                 # bad battert


def test_hwconfig(widget,event):
    stat,hw_result=commands.getstatusoutput('/opt/mfg/ui/shdirs/hwconfchk.sh')
    if stat :
       return _FAILED
    else:
       return _PASSED

def test_grt(widget,event):


    sta_hw,hwid_text = commands.getstatusoutput('crossystem hwid')
    hwtmp=hwid_text.replace(' ','_',4)
    hwid ='components_'+hwtmp                                            

    sdt.log("sn & ftp method is %s,%s,%s(GRT) !!!" % (sn,ftp_method,hwid))

    cmd = '/opt/mfg/ui/grt/gooftool/gooftool --c --db_path=/opt/mfg/ui/grt/hardware_Components/data_x86-zgb/' + hwid
    status,text=commands.getstatusoutput(cmd)
    if status :
       sdt.log("grt verify failed(GRT) %s,%s !!!" % (status,text))
       return _FAILED
    else:
       sdt.log("grt verify is ok(GRT) %s,%s !!!" % (status,text))
       return _PASSED

def test_uploadsh(widget, event):
    sta,text=commands.getstatusoutput('/opt/mfg/ui/shdirs/uploadf.sh')
    if sta :
       sdt.log("upload sh is failed (GRT) %s,%s !!!" % (sta,text))
       return _FAILED
    else :
       sdt.log("upload sh is ok (GRT) %s,%s !!!" % (sta,text))
       return _PASSED

class factory_Csp2():
    version = 1
          
    def pop_subitem(self):
        while self._subitem_queue:
            self._current_subitem = self._subitem_queue.pop()
            ename, name, cb_fn = self._current_subitem

            self._status_map[ename] = _ACTIVE
            ret_status = cb_fn(None, None)
            self._status_map[ename] = ret_status   
        
            if ename == 'battery':
                 if  ret_status == _CHARGE :   #  wait charging
                     while True :
                            status,output = commands.getstatusoutput('/opt/mfg/ui/tests/NUVOTON -info | grep relative | cut -d "=" -f2')
                            self._status_map[ename] = _CHARGE+'('+output+')'
                            if output :
                                if int(output)>=BAT_CAP  and int(output) <=100:
                                      sdt.log("FFT: Battery is ok!! CAP is%s,(%s )" % (output,ename))
                                      self._status_map[ename] = _PASSED
                                      break    
                                time.sleep(10)

                    
            if self._status_map[ename] == _PASSED:
               self.passc = self.passc + 1
            else :
               self.fail = self.fail + 1
               while True :
                   time.sleep(10)

            self.count = self.fail + self.passc       
            if self.passc == 4:
		    status,output = commands.getstatusoutput("crossystem devsw_cur")
                    if output == '0' :  
                       os.system('reboot')   
            elif self.count == 4:
                   while True :
                        time.sleep(10)

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

        self.prompt_label = gtk.Label('出货设定\n')
        			
                            
        self.prompt_label.modify_font(_LABEL_FONT)
        self.prompt_label.set_alignment(0.5, 0.5)
        self.prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)


        vbox = gtk.VBox()
        vbox.pack_start(self.prompt_label, False, False)

        for ename, name, cb_fun in _SUBITEM_LIST:
            label_box = self.make_subitem_label_box(ename, name, cb_fun)
            vbox.pack_start(label_box, False, False)


        vbox.show()

        self.window.add(vbox)
  
        self.window.show_all()
	thd = threading.Thread(target = self.pop_subitem)
	thd.start()

def main():
    gtk.main()    
if __name__ == "__main__":
   gtk.gdk.threads_init()
   try:
       gtk.gdk.threads_enter() 
       factory_Csp2()
       main()
   finally:
       gtk.gdk.threads_leave()
