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
from gtk import gdk
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
_RETRY = '重测中...'
BAT_CAP = 50
_LABEL_COLORS = {
    _ACTIVE: gtk.gdk.color_parse('light goldenrod'),
    _CHARGE: gtk.gdk.color_parse('light goldenrod'),
    _NOBAT : gtk.gdk.color_parse('light goldenrod'),
    _PASSED: gtk.gdk.color_parse('pale green'),
    _FAILED: gtk.gdk.color_parse('tomato'),
    _UNTESTED: gtk.gdk.color_parse('dark slate grey'),
    _RETRY:gtk.gdk.color_parse('light goldenrod')}

_LABEL_STATUS_SIZE = (140, 30)
_LABEL_STATUS_FONT = pango.FontDescription('courier new condensed 16')
_LABEL_FONT = pango.FontDescription('courier new condensed 20')
_LABEL_FG = gtk.gdk.color_parse('light green')
_LABEL_UNTESTED_FG = gtk.gdk.color_parse('grey40')

_SUBITEM_LIST = [
    ('adapter','请插入电源', lambda *x: test_adapter(*x)),
    ('switch','请转换开发开关', lambda *x: test_dev_switch(*x)),
    ('network','连接网络', lambda *x: test_wifi(*x)),
    ('time sync','时间同步', lambda *x: test_syt(*x)),
    ('battery','电池检测', lambda *x: test_battery(*x)),
    ('HW check','硬件检测', lambda *x: test_hwconfig(*x)),
    ('finalize','GRT检测', lambda *x: test_grt(*x)),
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
                 return _FAILED                 

def test_wifi(widget,event):
    cmd='/usr/local/lib/flimflam/test/connect-wifi  I-FFT quantaqms wpa|grep "Success: Ture" '
    r,o = commands.getstatusoutput(cmd)
    if r == 0 :
	return _PASSED
    conn = '''ifconfig wlan0 |grep "inet addr:" '''
    time.sleep(2)
    i = 0
    while i < 20:
      rtn,opt = commands.getstatusoutput(conn)
      if rtn == 0:
        sdt.log("wireless is  connected")
        return _PASSED
      else:
        sdt.log("one more time")
	os.system(cmd)
        time.sleep(5)
      i += 1
    sdt.log("Connect to AP Fail, abort!!")
    return _FAILED

  

def test_syt(widget, event):
    stat,info=commands.getstatusoutput('htpdate -u ntp:ntp -m 5 -s -t -w ' + cfg.timesync_ip)    #time_sync_ip  !!!!!!!!!!!!!!!!!!!!!!!!!172.28.164.16!!!!!!!!!!!!!!!!
    match = re.search('failed', info)
    if match is not None:
	sdt.log("Time Sync fail!!( %s)" % info )
        return _FAILED
    else:
        sdt.log("FFT : after time syn, time is %s" % info)
        return _PASSED

def test_hwconfig(widget,event):
    stat,hw_result=commands.getstatusoutput('/opt/mfg/ui/shdirs/hwconfchk.sh')
    if stat :
       return _FAILED
    else:
       return _PASSED

def test_grt(widget,event):
    #import FFT test log to factory.log

    os.system("echo [QUANTA] >>/var/log/factory.log")
    os.system("cat log/fft.log >>/var/log/factory.log")
    os.system("echo [/QUANTA]>>/var/log/factory.log")

    #-----------------get sn & set ftp method -------------------------------
    sta, gsn = commands.getstatusoutput('vpd -l | grep "serial_number"')
    if sta :
       sdt.log("vpd -l | grep sn failed(GRT) !!!(%s)" % sta)
       return _FAILED
    tmp=gsn.split('"',4)
    sn=tmp[3]
    sta_hw,hwid_text = commands.getstatusoutput('crossystem hwid')
    hwtmp=hwid_text.replace(' ','_',4)
    hwid ='components_'+hwtmp                                            
    ftp_method ='ftp://google:google@'+ cfg.grt_ftp_ip + ':21/ACER_M/Gft/'
    #ftp_method ='ftp://sdt:sdt123@172.21.144.45:21/tmp/'
    sdt.log("sn & ftp method is %s,%s,%s(GRT) !!!" % (sn,ftp_method,hwid))

    cmd = '/opt/mfg/ui/grt/gooftool/gooftool --finalize  --report_path=/opt/mfg/ui/log/grt_'+sn+'.log --upload_method='+ftp_method+'grt_'+sn+'.log '
    status,text=commands.getstatusoutput(cmd)
    #grt_result=os.system(cmd)
    if status :
       sdt.log("grt status failed(GRT) %s,%s !!!" % (status,text))
       return _FAILED
    else:
       sdt.log("google finalize is ok(GRT) %s,%s !!!" % (status,text))
       return _PASSED

def test_uploadsh(widget, event):
    sta,text=commands.getstatusoutput('/opt/mfg/ui/shdirs/uploadf.sh')
    if sta :
       sdt.log("upload sh is failed (GRT) %s,%s !!!" % (sta,text))
       return _FAILED
    else :
       sdt.log("upload sh is ok (GRT) %s,%s !!!" % (sta,text))
       return _PASSED

class factory_GRT():
    version = 1
    def key_release_event(self, widget, event):
	if self.fail :
	    if event.keyval == ord('r'):
		self.retry = True


             
    def pop_subitem(self):
        while self._subitem_queue:
            self._current_subitem = self._subitem_queue.pop()
            ename, name, cb_fn = self._current_subitem

            if ename == 'upload':
		    stat,result = commands.getstatusoutput('''grep -w "ERR_MSG=No QCI_PN_1 in FAI_PN table,call FQA." /opt/mfg/ui/log/D2Rsp.bak''')
		    if not stat:
			sdt.log("Need do CQA!!!")
			self.prompt_label.set_text("ERR_MSG=No QCI_PN_1 in FAI_PN table\ncall FQA.")
			self.prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_COLORS[_FAILED])
			while True:
			    time.sleep(1000)    

		    stat,result = commands.getstatusoutput('''grep -E "(CSP=N|CSL=N)" /opt/mfg/ui/log/D2Rsp.bak''')
		    if not stat:
			sdt.log("Need do QA!!!")
			self.prompt_label.set_text("QA-CSP2.\n")
			self.prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_COLORS[_FAILED])
			while True:
			    time.sleep(1000) 

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
               while True :
                   self.fail = True
                   time.sleep(2)
                   if self.retry:
                        self.fail = False
                        self.retry = False
                        self._status_map[ename] = _RETRY
                        ret_status = cb_fn(None, None)
                        self._status_map[ename] = ret_status 
                        if self._status_map[ename] == _PASSED:
                           self.passc = self.passc + 1
                           break

       

            if self.passc == len(_SUBITEM_LIST):
		    status,output = commands.getstatusoutput("crossystem devsw_cur")
                    if output == '0' :  
                       sdt.log("reboot !!%s" % output)
                       os.system('reboot')   
                       self.result = True
                       exit()
#            elif self.count == 8:
#                   os.system('rm /opt/mfg/ui/log/sdt_allpass')
#                   while True :
#                        time.sleep(10)
#                   self.result = False
#                   exit()

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
        self.fail = False
        self.count=0
        self.passc = 0
        self.call_loop = 0
        self.escape = 0
	self.retry = False
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

        gtk.gdk.keyboard_grab(self.window.window)
        self.window.connect('key-release-event', self.key_release_event)
        self.window.add_events(gdk.KEY_RELEASE_MASK)
	os.system('rm /opt/mfg/ui/log/sdt_allpass')

	thd = threading.Thread(target = self.pop_subitem)
	thd.start()
        #gobject.timeout_add(100, self.watch_thread,thd)

def main():
    gtk.main()    
if __name__ == "__main__":
   gtk.gdk.threads_init()
   try:
       gtk.gdk.threads_enter() 
       factory_GRT()
       main()
   finally:
       gtk.gdk.threads_leave()
