#!/usr/bin/env python
# -*- coding: utf-8 -*-


import gtk
import pango
import os
import sys
import gobject
import time
import threading
import commands
from gtk import gdk
from time import ctime
_BLACK = gtk.gdk.Color()


_ACTIVE = '录音中...'
_PLAY   = '正在播放...'
_PASSORNOT = '是否正常？'
_PASSED = '通过'
_FAILED = '失败'
_UNTESTED = '等待中...'
_WAIT   = '请插入麦克风'

_LABEL_COLORS = {
    _ACTIVE: gtk.gdk.color_parse('light goldenrod'),
    _PLAY: gtk.gdk.color_parse('light goldenrod'),
    _PASSORNOT:gtk.gdk.color_parse('light goldenrod'),
    _WAIT: gtk.gdk.color_parse('light goldenrod'),
    _PASSED: gtk.gdk.color_parse('pale green'),
    _FAILED: gtk.gdk.color_parse('tomato'),
    _UNTESTED: gtk.gdk.color_parse('dark slate grey')}

_LABEL_STATUS_SIZE = (140, 30)
_LABEL_STATUS_FONT = pango.FontDescription('courier new condensed 16')
_LABEL_FONT = pango.FontDescription('courier new condensed 20')
_LABEL_FG = gtk.gdk.color_parse('light green')
_LABEL_UNTESTED_FG = gtk.gdk.color_parse('grey40')

_SUBITEM_LIST = [
    ('D_Micphone','内置麦克风测试', lambda *x: test_D_Micphone(*x)),
    ('Micphone','外置麦克风测试', lambda *x: test_Micphone(*x))]

def test_Micphone(widget, event):
    #status,output = commands.getstatusoutput("sudo arecord -c 2 -f cd -d 3 /opt/mfg/ui/wavs/ex_m.wav")    
    status,output = commands.getstatusoutput("sudo arecord -c 2 -f cd -d 4 /opt/mfg/ui/wavs/ex_m.wav")   
    if status:
       return _FAILED
    else:
       return _PASSED
def test_D_Micphone(widget, event):
    status,output = commands.getstatusoutput('sudo arecord -c 2 -f cd -d 4 /opt/mfg/ui/wavs/d_m.wav')
    if status:
       return _FAILED
    else:
       return _PASSED 



class factory_Microphone():
    version = 1

    def key_release_event(self, widget, event):
 
        if event.keyval == 0x73 and self.start == False:
            self.start =True
            thd = threading.Thread(target = self.pop_subitem)
            thd.start()
            gobject.timeout_add(100, self.watch_thread,thd)

        if event.keyval == gtk.keysyms.Tab and self.can_press==True:
            logfile=open('/opt/mfg/ui/log/fft.log','a')
            print  >>logfile,"FFT: press key failed " , self.ename,ctime()
            logfile.close()
            self.can_press=False
            self._status_map[self.ename] = _FAILED
            self.all_test = self.all_test +1
            self.can_pop=True   

        elif event.keyval == gtk.keysyms.Return and self.can_press==True:
            logfile=open('/opt/mfg/ui/log/fft.log','a')
            print  >>logfile,"FFT: press key passed " ,self.ename,ctime()
            logfile.close()
            self.can_press=False
            self.all_test = self.all_test +1
            if self.ename == 'D_Micphone' :
                self.dmpass=1
            else :
                self.exmpass=1
            self._status_map[self.ename] = _PASSED
            if self.ename == 'D_Micphone' :
                self.can_pop=True   

        if self.all_test == 2 :
            if self.dmpass == 1 and self.exmpass==1 :
               self.not_over = False
               self.result=True
            else :
               self.not_over = False

        return True              
          
    def pop_subitem(self):

        while self.not_over :
          if self.can_pop == True:  
            self.can_pop = False
            self._current_subitem = self._subitem_queue.pop()
            ename, name, cb_fn = self._current_subitem
            self.ename = ename
            if ename == 'Micphone' :
                while True :
                    self._status_map[ename] = _WAIT
                    command = "cat /proc/asound/card0/codec#0 | grep -A4 'Node 0x22' | grep '0x18\*'"
                    #status,output = commands.getstatusoutput(command)
                    status = os.system(command)
                    if status == 0:
                        break
                    time.sleep(1)

            self._status_map[ename] = _ACTIVE
            ret_status = cb_fn(None, None)
            if ret_status == _PASSED:
                self._status_map[ename] = _PLAY
                if ename == 'D_Micphone' :
                    status = os.system('sudo aplay /opt/mfg/ui/wavs/d_m.wav')
                else :
                    status = os.system('sudo aplay /opt/mfg/ui/wavs/ex_m.wav')
                if status :
                   self._status_map[ename] = _FAILED
                   self.all_test = self.all_test +1
                   self.can_pop=True
                else :
                   self.can_press=True
                   self._status_map[ename] = _PASSORNOT
            else :
                logfile=open('/opt/mfg/ui/log/fft.log','a')
                print  >>logfile,"FFT:  failed " , ename,ctime()
                logfile.close()
                self._status_map[ename] = _FAILED
                self.all_test = self.all_test +1
                if self.ename == 'D_Micphone' :
                    self.can_pop=True  
                else : 
                    self.not_over = False


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
        self.can_pop = True
        self.all_test = 0
        self.can_press=False
        self.dmpass=0
        self.exmpass=0
        self.ename =''
        self.not_over = True
        self.start = False

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("black"))
        self.window.move(400, 200)

        self._subitem_queue = [x for x in reversed(_SUBITEM_LIST)]		  
        self._status_map = dict((en, _UNTESTED) for en, n, f in _SUBITEM_LIST)

        prompt_label = gtk.Label('麦克风测试\n按S键开始\n成功按回车键,失败按Tab键\n')
                            
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

        gtk.gdk.keyboard_grab(self.window.window)
        self.window.connect('key-release-event', self.key_release_event)
        self.window.add_events(gdk.KEY_RELEASE_MASK)

        #gobject.timeout_add(200, self.pop_subitem)




def main():
    gtk.main()    
   

if __name__ == "__main__":
   gtk.gdk.threads_init()
   try:
       gtk.gdk.threads_enter() 
       factory_Microphone()
       main()
   finally:
       gtk.gdk.threads_leave()

