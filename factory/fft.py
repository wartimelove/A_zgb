#!/usr/bin/env python
#-*- encoding:utf-8 -*-
#3g

import pygtk
pygtk.require('2.0')
import gtk
import pango
import subprocess
import threading
import thread
import time
from time import ctime
import os
import sys
import gobject
import commands
import re
sys.path.append('/opt/mfg/ui/pydirs/')
import factory_sdt as sdt

_LABEL_CN_FONT = pango.FontDescription('normal 18')
_LABEL_EN_FONT = pango.FontDescription('courier new extra-condensed 18')
_LABEL_CN_SIZE = (300, 28)
_LABEL_EN_SIZE = (530, 28)

_TEST_WINDOW_SIZE = (1000, 520)
_LOG_WINDOW_SIZE = (1000, 150)
_H_SEPRATOR_SIZE = (-1, 3)
_V_SEPRATOR_SIZE = (3, -1)

fp = open('/opt/mfg/ui/version')
if fp:
    ver_time = str(fp.readline())
fp.close()
_VER = '\nQSMC\nSDT\n' + ver_time


_ACTIVE = 'ACTIVE'
_PASSED = 'PASSED'
_FAILED = 'FAILED'
_WAITED = 'WAITED'



_LABEL_BG_COLORS = {
    _ACTIVE: gtk.gdk.color_parse('light goldenrod'),
    _PASSED: gtk.gdk.color_parse('pale green'),
    _FAILED: gtk.gdk.color_parse('tomato'),
    _WAITED: gtk.gdk.color_parse('dark slate grey')}

_LABEL_FG_COLORS = {
    _ACTIVE: gtk.gdk.color_parse('black'),
    _PASSED: gtk.gdk.color_parse('black'),
    _FAILED: gtk.gdk.color_parse('black'),
    _WAITED: gtk.gdk.color_parse('grey40')}

_NORMAL_FG = gtk.gdk.color_parse('black')
_WAITED_FG = gtk.gdk.color_parse('grey40')

_LABEL_FG = gtk.gdk.color_parse('light green')

_TEST_WINDOW_BG = gtk.gdk.color_parse('black')


_SUBITEM_LIST = [
    ('SDC', '安全数码卡',      lambda *x: chk_func(*x,**{'test_item':'factory_CardReader.pyc sdc'})),
    ('CCD', '摄像头',         lambda *x: chk_func(*x,**{'test_item':'factory_Camera.pyc'})),
    ('MIC', '麦克风',         lambda *x: chk_func(*x,**{'test_item':'factory_Microphone.pyc'})),
    ('XDC', '闪存卡',         lambda *x: chk_func(*x,**{'test_item':'factory_CardReader.pyc xdc'})),
    ('USB', 'USB 存储器',     lambda *x: chk_func(*x,**{'test_item':'factory_Usbstorage.pyc'})),
    ('BLT', '背光模组',       lambda *x: chk_func(*x,**{'test_item':'factory_Backlight.pyc'})),
    ('TPD', '触控板',         lambda *x: chk_func(*x,**{'test_item':'factory_Touchpad.pyc'})),     
    ('BRS', '明亮控制',       lambda *x: chk_func(*x,**{'test_item':'factory_Brightness.pyc'})),
    ('MSC', '记忆棒',         lambda *x: chk_func(*x,**{'test_item':'factory_CardReader.pyc msc'})),
    ('SPV', '喇叭与音量',      lambda *x: chk_func(*x,**{'test_item':'factory_Speaker_Volume.pyc'})),
    ('HDM', '高解析多媒体界面', lambda *x: chk_func(*x,**{'test_item':'factory_HDMI.pyc'})),
    ('RCB', '复原按钮',        lambda *x: chk_func(*x,**{'test_item':'factory_RecoveryButton.pyc'})),
    ('LSH', '亮度与翻盖',      lambda *x: chk_func(*x,**{'test_item':'factory_Lit_Lid.pyc'})),
    ('FAN', '风扇',           lambda *x: chk_func(*x,**{'test_item':'factory_FAN.pyc'})),
    ('LED', '侧灯与显屏',      lambda *x: chk_func(*x,**{'test_item':'factory_Display_LED.pyc'})),
    ('KBD', '键盘',           lambda *x: chk_func(*x,**{'test_item':'factory_Keyboard.pyc'})),
    ('3GM', '第三代通讯',      lambda *x: chk_func(*x,**{'test_item':'factory_3G.pyc'})),
    ('GRT', '出货设定',        lambda *x: chk_func(*x,**{'test_item':'factory_GRT.pyc'}))]


_INFO_DICT = {'SN':''' vpd -l 2>/dev/null |grep "serial_number" |cut -d"=" -f2|sed 's/"//g' ''', 
	      'BIOS':''' crossystem |grep -w "fwid"|cut -d"=" -f2|cut -d"#" -f1 |sed 's/ //' '''
	     }

def chk_func(widget, event,test_item = None):
##############################################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #if test_item != "factory_GRT.pyc" and  test_item != "factory_3G.pyc":
    #     return _PASSED
##############################################

    cmd = 'python /opt/mfg/ui/pydirs/' + test_item
    relt = subprocess.Popen(cmd,shell = True, stdout=subprocess.PIPE)
    while True:
        relt.stdout.flush()
	sub_out = relt.stdout.readline()
        sdt.log('FFT: %s' % sub_out) 
	if not sub_out:
           ret=relt.wait()
	   break
    
    if ret == 99:
        return _PASSED
    else:
        return _FAILED
        
        
class Console:
    '''Display a progress log.  Implemented by launching an borderless
    xterm at a strategic location, and running tail against the log.'''

    def __init__(self, allocation):
        xterm_coords = '135x14+%d+%d' % (allocation.x, allocation.y)

        xterm_cmd = (('/opt/mfg/ui/utils/aterm --geometry %s -bw 0 -e bash -c ' % xterm_coords).split() +['tail -f /opt/mfg/ui/log/fft.log |grep "FFT:" '])
        #xterm_opts = ('-bg black -fg lightgray -bw 0 -g %s' % xterm_coords)
        #xterm_cmd = (('urxvt %s -e bash -c ' % xterm_opts).split() + ['tail -f /opt/mfg/ui/log/fft.log |grep "FFT:" '])
        self._proc = subprocess.Popen(xterm_cmd)


class FFT:

    # This callback quits the program
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def smoke_subitem(self,ename, name, cb_fn):

       if ename == 'KBD' and  self.have3G  and not self.allpass_flag:
           self.passed_items = 0
           for item in self._status_map.keys():
               if item == 'KBD' or item == '3GM' or item == 'GRT':
                   continue
               if self._status_map[item] != _PASSED:
                   self.shortcut_status = True
                   self.label1.set_text("键盘测试之前有测试项未通过，请先重测！") 
                   self.label1.modify_fg(gtk.STATE_NORMAL, _LABEL_BG_COLORS[_FAILED])
                   self.label1.show()
                   sdt.log("FFT: FFT stopped,there are some items(before %s) failed!! %s" % (ename,ctime()))
                   self._status_map[ename] = _WAITED
                   self.can_pop = 0
                   exit()
                   return False
               else:
                   self.passed_items += 1
           if self.passed_items == len(self._status_map) - 3:
               sdt_all=os.system('touch /opt/mfg/ui/log/sdt_allpass') 
               if sdt_all:
                   sdt.log("FFT: touch sdt allpass file failed! %s" % time())  
                   return False 
               else : 
                   sdt.log("FFT: sdt all pass success!!!   %s" % ctime())           
               os.system('''modem_set_carrier "Generic UMTS"''')
               relt3g = subprocess.Popen("python /opt/mfg/ui/pydirs/factory_notice3g.pyc",shell = True, stdout=subprocess.PIPE)
               while True :
                   time.sleep(1000) 


       if ename =='GRT':
           self.shortcut_status = True
           for item in self._status_map.keys():
               if item != 'GRT' and self._status_map[item] != _PASSED:
                   self.label1.set_text("有测试项未测或未通过，不能进行出货设定！") 
                   self.label1.modify_fg(gtk.STATE_NORMAL, _LABEL_BG_COLORS[_FAILED])
                   self.label1.show()
                   sdt.log("FFT: FFT stopped,there are some items(before %s) failed!! %s" % (ename,ctime()))
		   return False


       sdt.log("FFT: Start test   %s,            %s" % (ename,ctime()))      
       ret_status = cb_fn(None, None)
       self._status_map[ename] = ret_status
       sdt.log("FFT: End test     %s,    %s,    %s" % (ename,self._status_map[ename],ctime()))
       self.can_pop = 0
       return False

           
    def pop_subitem(self):
       if self.allpass_flag :
           length =1
           while length <= self.itemlistlen-3 :
               self._current_subitem = self._subitem_queue.pop()
               ename, name, cb_fn = self._current_subitem
               self._status_map[ename] = _PASSED
               length+=1
          
       while self._subitem_queue and not self.can_pop:
           self.can_pop = 1 
           self._current_subitem = self._subitem_queue.pop()
           ename, name, cb_fn = self._current_subitem
           if self._status_map[ename] == _WAITED:
               self._status_map[ename] = _ACTIVE
               self.smoke_subitem(ename, name, cb_fn)
	       #t = threading.Thread(target = self.smoke_subitem,args=(ename, name, cb_fn))
               #t.start()
               while self.can_pop == 1:
                   time.sleep(0.1)


    def shortcut_test_subitem(self,test_item):
       self.label1.hide()
       for ename, name, cb_fn in _SUBITEM_LIST:
           if ename == test_item and self._status_map[ename] == _FAILED:
               self.can_pop = 1
               self._current_subitem = ename,name,cb_fn
               self._status_map[ename] = _ACTIVE
               self.smoke_subitem(ename, name, cb_fn)
               #st = threading.Thread(target = self.smoke_subitem,args=(ename, name, cb_fn))
               #st.start()
               self._status_map['GRT'] = _WAITED
               while self.can_pop == 1:
                   time.sleep(0.1)

       for ename, name, cb_fn in _SUBITEM_LIST:        
           if self._status_map[ename] == _WAITED:
               self.can_pop = 1
               self._current_subitem = ename,name,cb_fn
               self._status_map[ename] = _ACTIVE
               self.smoke_subitem(ename, name, cb_fn)
               #st = threading.Thread(target = self.smoke_subitem,args=(ename, name, cb_fn))
               #st.start()
               while self.can_pop == 1:
                   time.sleep(0.1)



    def label_status_expose(self, widget, event, name=None):
        status = self._status_map[name]
        widget.modify_bg(gtk.STATE_NORMAL, _LABEL_BG_COLORS[status])
        widget.modify_fg(gtk.STATE_NORMAL, _LABEL_FG_COLORS[status])
        widget.queue_draw()

    def make_info_label_box(self, name,value):
    	eb = gtk.EventBox()
   	eb.modify_bg(gtk.STATE_NORMAL, _LABEL_BG_COLORS[_WAITED])
    	label = gtk.Label("%s: %s" % (name,value))
    	label.set_size_request(*_LABEL_EN_SIZE)
    	label.modify_font(_LABEL_CN_FONT) 
    	#label.set_alignment(0, 0.5)
    	label.set_justify(gtk.JUSTIFY_LEFT) 
    	label.set_line_wrap(True) 
    	label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
    	eb.add(label)
    	label.show()
    	return eb

    def make_subitem_label_box(self, ename, name):
        eb = gtk.EventBox()
        eb.modify_bg(gtk.STATE_NORMAL, _LABEL_BG_COLORS[_WAITED])
        label = gtk.Label(name)
        label.modify_font(_LABEL_CN_FONT)
        label.set_size_request(*_LABEL_CN_SIZE)
        label.set_justify(gtk.JUSTIFY_LEFT) 
        label.set_line_wrap(True)        
        label.modify_fg(gtk.STATE_NORMAL, _WAITED_FG)                
        expose_fg_status = lambda *x: self.label_status_expose(*x, **{'name':ename})
        label.connect('expose_event', expose_fg_status)
        expose_bg_status = lambda *x: self.label_status_expose(*x, **{'name':ename})
        eb.connect('expose_event', expose_bg_status)
        eb.add(label)
        label.show()
        return eb     
 
    def key_press_event(self,widget,event):
        if event.keyval == ord('s'):
             self.label1.hide()
             thd = threading.Thread(target = self.pop_subitem)
             thd.start()

    def key_release_event(self, widget, event):
	if 'GDK_CONTROL_MASK' in event.state.value_names:
            #sdt.log("Retest %s" % self.shortcut[event.keyval])
            if self.shortcut_status and self.shortcut.has_key(event.keyval):
              thread.start_new_thread(self.shortcut_test_subitem, (self.shortcut[event.keyval],))
              #sct = threading.Thread(target = self.shortcut_test_subitem,args=self.shortcut[event.keyval])
              #sct.start()

    def make_hsep(self):  
	hsep = gtk.EventBox()
	hsep.set_size_request(*_H_SEPRATOR_SIZE)
	hsep.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse('grey20'))
	return hsep
	
    def make_vsep(self):  
	vsep = gtk.EventBox()
	vsep.set_size_request(*_V_SEPRATOR_SIZE)
	vsep.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse('grey20'))
	return vsep


    def __init__(self):
        os.system('mount -o remount,rw /')
	os.system('amixer set Capture 0 cap 80%,80%')
        os.system('amixer set Master 0 cap 95%,95%')
        self.shortcut_status = False
        self.can_pop = 0 
	self.DEBUG_MODE = False
	self.allpass_flag= False
        self.have3G = False
        self.passed_items = 0
        self.shortcut = {}

        if len(sys.argv) >= 2 and sys.argv[1] == 'd':
	    self.DEBUG_MODE = True

        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        screen = self.window.get_screen()
        screen_size = (screen.get_width(), screen.get_height())
        self.window.set_size_request(*screen_size)

        # Set the window title
        self.window.set_title("FFT")
        self.window.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse('black'))

        # Set a handler for delete_event that immediately
        # exits GTK.
        self.window.connect("delete_event", self.delete_event)

        # Sets the border width of the window.
        self.window.set_border_width(5)

       
        hbox1 = gtk.HBox(False, 0)
        for info in _INFO_DICT.keys():
            stat, value = commands.getstatusoutput(_INFO_DICT[info])
            info_box = self.make_info_label_box(info, value)
            hbox1.pack_start(info_box, False, False, 0)
            info_box.show()

        vbox1 = gtk.VBox(False, 0)
        vbox1.pack_start(hbox1, False, False, 0)
            
        self.label1 = gtk.Label("开始测试请按S键！")
        self.label1.modify_font(_LABEL_CN_FONT)
        self.label1.set_alignment(0.5, 0.5)
        self.label1.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
        self.label1.show()

        eb = gtk.EventBox()
        eb.set_size_request(*_TEST_WINDOW_SIZE)
        eb.modify_bg(gtk.STATE_NORMAL,_TEST_WINDOW_BG) 
        eb.add(self.label1) 

        vbox1.pack_start(eb, False, False, 0)
        vbox1.pack_start(self.make_hsep(), False, False, 0)
        
        console_box = gtk.EventBox()
        console_box.set_size_request(-1, 220)
        console_box.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse('black'))
        vbox1.pack_end(console_box, True, True, 0)

        
        hbox2 = gtk.HBox(False, 0)
        hbox2.pack_start(vbox1, False, False, 0)
        hbox2.pack_start(self.make_vsep(), False, False, 0)
        self.label1.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)

        
        status,output = commands.getstatusoutput('cat /opt/mfg/ui/log/fft.log')
        sdt_allpass=os.system('ls /opt/mfg/ui/log/sdt_allpass')
        if sdt_allpass == 0 :
	    sdt.log("FFT: Start KB test %s" % ctime())         
	    self.allpass_flag=True
        else :
  	    sdt.log("FFT: Start FFT first time %s" % ctime()) 
	    self.allpass_flag=False

        stahw,outhw = commands.getstatusoutput('crossystem hwid')
        outhwid = outhw.replace(' ','_',4)     
        cmd ='''grep "id_3g': \[''\]" /opt/mfg/ui/grt/chromeos-hwid/components_'''+outhwid 
        sta3g,out3g = commands.getstatusoutput(cmd)
        if sta3g :
            self.have3G = True
            sdt.log("FFT: Have ThreeG %s" % ctime())
        else :
            self.have3G = False
            sdt.log("FFT: No ThreeG %s" % ctime()) 
        if not self.have3G:
	    del _SUBITEM_LIST[len(_SUBITEM_LIST)-2]
	self.itemlistlen=len(_SUBITEM_LIST)

        self._subitem_queue = [x for x in reversed(_SUBITEM_LIST)]
        self._status_map = dict((en, _WAITED) for en, n, f in _SUBITEM_LIST)
	
        base = 97
        for en, n, f in _SUBITEM_LIST:
            self.shortcut.setdefault(base,en)
            base += 1
       

        vbox2 = gtk.VBox(False, 0)

        for ename, name, cbfn in _SUBITEM_LIST:
            label_box = self.make_subitem_label_box(ename, name)
            label_box.show()
            vbox2.pack_start(label_box, False, False, 0)
            vbox2.pack_start(self.make_hsep(), False, False, 0)
            
        Ver_label = gtk.Label(_VER)                   
        Ver_label.modify_font(_LABEL_CN_FONT)
        Ver_label.set_alignment(0.5, 0.5)
        Ver_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
        Ver_label.show()
        vbox2.pack_start(Ver_label, False, False, 0)

        hbox2.pack_start(vbox2, False, False, 0)
        self.window.add(hbox2)
        
        self.window.connect('key-press-event',self.key_press_event)
        self.window.add_events(gtk.gdk.KEY_PRESS_MASK)

	if self.DEBUG_MODE:
            self.window.connect('key-release-event', self.key_release_event)
            self.window.add_events(gtk.gdk.KEY_RELEASE_MASK)

        self.window.show_all()
	#gtk.gdk.pointer_grab(self.window.window)	
        #console = Console(console_box.get_allocation())


def main():
       gtk.main() 

if __name__ == "__main__":
   gtk.gdk.threads_init()
   try:
       gtk.gdk.threads_enter() 
       FFT()
       main()
   finally:
       gtk.gdk.threads_leave()
