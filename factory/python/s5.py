#!/usr/bin/env python
#-*- encoding:utf-8 -*-

# example show label or label text and color controlling

import pygtk
pygtk.require('2.0')
import gtk
import pango
import os
import sys
import gobject
sys.path.append('/opt/mfg/ui/config')
import factory_conf as cfg
os.system("if [ ! -e /opt/mfg/ui/log/s5count ];then echo -n 0 >/opt/mfg/ui/log/s5count; fi")


_S5_TIMES = cfg._S5_TIMES


_S5_DELAY = 5

_MSG_PROMPT = '秒后自动重新开机'

_LABEL_STATUS_SIZE = (140, 30)
_LABEL_STATUS_FONT = pango.FontDescription('courier new condensed 16')
_LABEL_FONT = pango.FontDescription('courier new condensed 20')
_LABEL_FG = gtk.gdk.color_parse('light green')
_LABEL_FG_FAIL = gtk.gdk.color_parse('tomato')
_LABEL_UNTESTED_FG = gtk.gdk.color_parse('grey40')

_BLACK = gtk.gdk.Color()
   
class S5():
   version = 1
   
   def destroy(self, widget, data=None):
       print "destroy signal occurred"
       gtk.main_quit()
   
   def myreboot(self):
       os.system('reboot')

   def chk_ac(self):
       if self.info_ac:
           self.info_ac=os.system('/opt/mfg/ui/tests/NUVOTON -info | grep "AC_status" | grep -q On')
	   return True
       else:
           self._prompt_label.set_text('%d 秒后自动重新开机' % _S5_DELAY)
           self._prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
           gobject.timeout_add(5000, self.myreboot)
         

   def smoke_subitem(self):
       gobject.timeout_add(200, self.chk_ac)

   def __init__(self):
       
       self.count = 0
       self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
       self.window.connect("destroy", self.destroy)
       os.system('mount -o remount,rw /')
       f = open('/opt/mfg/ui/log/s5count')
       
       if f:
           self.count = f.readline()
           f.close()
       else:  
           os.system('echo 0 > /opt/mfg/ui/log/s5count')
       
       count_words = str("开机状态测试 (%d/%d)" % (int(self.count), _S5_TIMES))
       test_label = gtk.Label(count_words)
                            
       test_label.modify_font(_LABEL_FONT)
       test_label.set_alignment(0.5, 0.5)
       test_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
       test_label.show()
    
       vbox = gtk.VBox()
       vbox.pack_start(test_label, False, False)
        
       self.info_ac=os.system('/opt/mfg/ui/tests/NUVOTON -info | grep "AC_status" | grep -q On')
       if self.info_ac:
           prompt_label = gtk.Label('请插入电源!!!!')
           prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG_FAIL)
       else:
           prompt_label = gtk.Label('%d 秒后自动重新开机' % _S5_DELAY)
           prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
          
       prompt_label.modify_font(_LABEL_FONT)
       prompt_label.set_alignment(0, 0.5)
       prompt_label.show()
       self._prompt_label=prompt_label
       vbox.pack_start(self._prompt_label, False, False)

       vbox.show()

       test_widget = gtk.EventBox()
       test_widget.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
       test_widget.add(vbox)

       self._test_widget = test_widget

       self.window.add(self._test_widget)

       self._test_widget.show()

       self.window.show()

       if int(self.count) >= _S5_TIMES:
           os.system('echo pass > /opt/mfg/ui/log/s5.end')
       else:
           self.count = int(self.count) + 1
      
           f = open('/opt/mfg/ui/log/s5count', 'w')
           if f:
               count_words = str(self.count)
               print count_words
               f.write(count_words)
               f.close()

       self.smoke_subitem()

   def main(self):
       gtk.main()

if __name__ == "__main__":
   S5 = S5()
   S5.main()
