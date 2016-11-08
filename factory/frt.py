#!/usr/bin/env python
#-*- encoding:utf-8 -*-


import pygtk
pygtk.require('2.0')
import gtk
import pango
import os
import sys
import gobject
import thread, time
import datetime
from datetime import timedelta
sys.path.append('/opt/mfg/ui/config')
import factory_conf as cfg

SCRIPT_PATH='/opt/mfg/ui/shdirs/frt4py.sh -'

os.system("if [ ! -e /opt/mfg/ui/log/s3count ];then echo -n 0 >/opt/mfg/ui/log/s3count; fi")

_ACTIVE = 'Testing....'
_PASSED = 'Pass'
_FAILED = 'Fail'
_UNTESTED = 'Waiting'


_S3_TIMES = cfg._S3_TIMES
_RUN_TIME_H = cfg._RUN_TIME_H
_RUN_TIME_M = cfg._RUN_TIME_M
_RUN_TIME_S = cfg._RUN_TIME_S
_RUN_GLX_S = cfg._RUN_GLX_S

_LABEL_COLORS = {
    _ACTIVE: gtk.gdk.color_parse('light goldenrod'),
    _PASSED: gtk.gdk.color_parse('pale green'),
    _FAILED: gtk.gdk.color_parse('tomato'),
    _UNTESTED: gtk.gdk.color_parse('dark slate grey')}

_LABEL_STATUS_SIZE = (180, 30)
_LABEL_TIME_SIZE = (550, 30)
_LABEL_STATUS_FONT = pango.FontDescription('courier new condensed 20')
_LABEL_FONT = pango.FontDescription('courier new condensed 20')
RUNIN_LABEL_FONT = pango.FontDescription('courier new condensed 40')
_LABEL_FG = gtk.gdk.color_parse('light green')
_LABEL_UNTESTED_FG = gtk.gdk.color_parse('grey40')

_BLACK = gtk.gdk.Color()


#options:
# -a:brunbat (battery dis/charge)
# -b:chkbt
# -c:burncpu
# -d:burnssd
# -e:checkbat (CAP)
# -g:burnlcd
# -m:burnmem
# -r:s5
# -s:s3

_SUBITEM1_LIST = [
    ('S5',       '开机状态测试',lambda *x: test_func(*x,**{'test_item':'r'})),
    ('S3',       '待机状态测试',lambda *x: test_func(*x,**{'test_item':'s'}))]
_SUBITEM2_LIST = [
    ('BURN_CPU', 'CPU测试',lambda *x: test_func(*x,**{'test_item':'c'})),
    ('BURN_MEM', '内存测试',lambda *x: test_func(*x,**{'test_item':'m'})),
    ('BURN_SSD', '固态硬盘测试',lambda *x: test_func(*x,**{'test_item':'d'}))]
_SUBITEM3_LIST = [
    ('_3D',      '3D效能测试',lambda *x: test_func(*x,**{'test_item':'g ' + str(_RUN_GLX_S) })),
    ('BURN_BAT', '电池充放电测试', lambda *x: test_func(*x,**{'test_item':'a'})),
#    ('TEST_BT', '测试蓝牙',lambda *x: test_func(*x,**{'test_item':'b'})),
    ('CHECK_CAP', '检测电量',lambda *x: test_func(*x,**{'test_item':'e'}))]

def test_func(widget, event, test_item):
    test_rlt=os.system(SCRIPT_PATH+test_item)
    if test_rlt == 0:
        return _PASSED
    else:
        return _FAILED
   

class FRT():
   version = 1
   
   def smoke_subitem1(self):

       escapeloop = 0
       while not escapeloop:
           ename, name, cb_fn = self._current_subitem
           ret_status = cb_fn(None, None)

           self._status_map[ename] = ret_status
       
           if self._status_map[ename] == _PASSED:
               self._count_map[ename] = int(self._count_map[ename]) + 1
               print ename, " (", self._count_map[ename], ")"

               if ename == "S3":
                   if self._count_map[ename] >= _S3_TIMES:
                       cmd = ''' echo -n ''' + str(self._count_map[ename]) + ''' > /opt/mfg/ui/log/s3count'''
	               os.system(cmd)
                       os.system('reboot')
               else:
                   self.can_pop = 1
                   escapeloop = 1
           
           elif self._status_map[ename] == _FAILED:
               escapeloop = 1
               self.escape = 1
               self.fails = self.fails + 1
                    
           time.sleep(1)
       self.escape = 1

   def smoke_subitem2(self):
       ename, name, cb_fn = self._current_subitem
       ret_status = cb_fn(None, None)

       self._count_map[ename] = int(self._count_map[ename]) + 1
           
       self._status_map[ename] = ret_status

       print ret_status
       self.can_pop = 1

       if ret_status == _FAILED:
           self.fails = self.fails + 1
           self.item_failed = 1
   
   def pop_subitem3(self):
       self.can_pop = 0 
       while self._subitem3_queue and self.item_failed == 0:
           self._current_subitem = self._subitem3_queue.pop()

           ename, name, cb_fn = self._current_subitem
           
           self._status_map[ename] = _ACTIVE
           thread.start_new_thread(self.smoke_subitem2, ())
           while 1:
               if self.can_pop == 1:
                   self.can_pop = 0
                   break
               time.sleep(1)
           time.sleep(1)
           
       if self.fails == 0:
           print "FRT END"
           os.system("echo `date` >/opt/mfg/ui/log/frt.end")
	   os.system("mv /etc/init/frt.conf /etc/init/frt.conf.hide")
	   os.system("mv /etc/init/fft.conf.hide /etc/init/fft.conf")
           os.system("reboot")

   def pop_subitem2(self):

       dt = datetime.datetime.today()
       duration = datetime.timedelta(hours=_RUN_TIME_H, minutes=_RUN_TIME_M, seconds=_RUN_TIME_S)
       sdate = dt.strftime("%Y-%m-%d")
       stime = dt.strftime("%H:%M:%S")
       sdatetime = str("开始时间 : %s %s" % (sdate, stime))
       self.label_stime.set_text(sdatetime)
       self.label_stime.show()

       edt = dt + duration
       edate = edt.strftime("%Y-%m-%d")
       etime = edt.strftime("%H:%M:%S")
       edatetime = str("结束时间 : %s %s" % (edate, etime))
       self.label_etime.set_text(edatetime)
       self.label_etime.show()
       
       self.deadline = edt

       thread.start_new_thread(self.calculate_time, ())
       self.can_pop = 0
       out_loop = 0
      
       while self._subitem2_queue and self.item_failed == 0 and out_loop == 0:
           self._current_subitem = self._subitem2_queue.pop()

           if self.timeline == 0:
               self._subitem2_queue.insert(0, self._current_subitem)
           else:
               out_loop = 1
               break

           ename, name, cb_fn = self._current_subitem
           
           self._status_map[ename] = _ACTIVE
           thread.start_new_thread(self.smoke_subitem2, ())

           while 1:
               if self.can_pop == 1:
                   self.can_pop = 0
                   break
               time.sleep(1)
           time.sleep(1)

       if self.item_failed == 0:
           self.pop_subitem3()
       
   def pop_subitem1(self):
       
       self._subitem1_queue.pop()

       self._current_subitem = self._subitem1_queue.pop()
       ename, name, cb_fn = self._current_subitem
       if ename == "S3":
           f = open('/opt/mfg/ui/log/s3count')
           if f:
               self._count_map[ename] = int(f.readline())
               f.close()

       if self._count_map[ename] >= _S3_TIMES:
           self._status_map[ename] = _PASSED
           thread.start_new_thread(self.pop_subitem2, ())

       else:
           self._status_map[ename] = _ACTIVE
           thread.start_new_thread(self.smoke_subitem1, ())
           while 1:
               if self.can_pop == 1:
                   self.can_pop = 0
                   break
           while self.escape == 0:
           
               time.sleep(1)

           thread.start_new_thread(self.pop_subitem2, ())

   def calculate_time(self):
       while 1:
           if self.deadline < datetime.datetime.today():
               print "end loop"
               self.timeline = 1
               break
           time.sleep(1)

   def destroy(self, widget, data=None):
       print "destroy signal occurred"
       failed_set = set(ename for ename, status in self._status_map.items()
                        if status is not _PASSED)
       if failed_set:
           print ('some patterns failed (%s)' % ', '.join(failed_set))

       gtk.main_quit()

   def label_status_expose(self, widget, event, name=None):
       status = self._status_map[name]
       
       widget.set_text(status)
       widget.modify_fg(gtk.STATE_NORMAL, _LABEL_COLORS[status])
       widget.queue_draw()

   def label_count_expose(self, widget, event, name=None):
       
       
       countwords = str("(%s)" % self._count_map[name])
       #print name, " ", countwords
       widget.set_text(countwords)

       widget.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
       widget.queue_draw()

   def make_subitem_label_box(self, ename, name, count):
       
       eb = gtk.EventBox()
       
       eb.modify_bg(gtk.STATE_NORMAL, _BLACK)
       if ename == "S5":
            label_status = gtk.Label(_PASSED)
            label_status.modify_fg(gtk.STATE_NORMAL, _LABEL_COLORS[_PASSED])
       else:
            label_status = gtk.Label(_UNTESTED)
            label_status.modify_fg(gtk.STATE_NORMAL, _LABEL_UNTESTED_FG)
       label_status.set_size_request(*_LABEL_STATUS_SIZE)
       label_status.set_alignment(0, 0.5)
       label_status.modify_font(_LABEL_STATUS_FONT)
       
       label_status.show()

       expose_cb_status = lambda *x: self.label_status_expose(*x, **{'name':ename})
       label_status.connect('expose_event', expose_cb_status)
       
       label_en = gtk.Label(name)
       label_en.set_alignment(1, 0.5)
       label_en.modify_font(_LABEL_STATUS_FONT)
       label_en.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
       label_en.show()

       if ename == "S5":
           f = open('/opt/mfg/ui/log/s5count')
           if f:
               self._count_map[ename] = f.readline()
               f.close()

       label_count = gtk.Label("(%s)" % self._count_map[ename])

       expose_cb_count = lambda *x: self.label_count_expose(*x, **{'name':ename})
       label_count.connect('expose_event', expose_cb_count)

       label_count.set_alignment(1, 0.5)
       label_count.modify_font(_LABEL_STATUS_FONT)
       label_count.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
       label_count.show()

       label_sep = gtk.Label(' : ')
       label_sep.set_alignment(0.5, 0.5)
       label_sep.modify_font(_LABEL_FONT)
       label_sep.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
       label_sep.show()

       label_null = gtk.Label('                                                                                                                                                                   ')
       label_null.show()

       hbox = gtk.HBox()
       hbox.pack_end(label_null, False, False)
       hbox.pack_end(label_status, False, False)
       hbox.pack_end(label_sep, False, False)
       hbox.pack_end(label_count, False, False)
       hbox.pack_end(label_en, False, False)
       hbox.show()
       eb.add(hbox)
       return eb
     
   def __init__(self):
       
       self.deadline = None
       self.item_failed = 0
       self.can_pop = 0
       self.pop_count = 0
       self.escape = 0
       self.timeline = 0
       self.fails = 0
       os.system('mount -o remount,rw /')
       self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
       self.window.set_default_size(self.window.get_screen().get_width(), self.window.get_screen().get_height())
#       self.window.set_position(gtk.WIN_POS_CENTER)
       self.window.connect("destroy", self.destroy)


       self._subitem1_queue = [x for x in reversed(_SUBITEM1_LIST)]
       self._subitem2_queue = [x for x in reversed(_SUBITEM2_LIST)]
       self._subitem3_queue = [x for x in reversed(_SUBITEM3_LIST)]

       self._status_map1 = dict((en, _UNTESTED) for en, n, f in _SUBITEM1_LIST)
       self._status_map2 = dict((en, _UNTESTED) for en, n, f in _SUBITEM2_LIST)
       self._status_map3 = dict((en, _UNTESTED) for en, n, f in _SUBITEM3_LIST)
       for x, y in self._status_map2.iteritems():
           self._status_map1[x] =y
       for x, y in self._status_map3.iteritems():
           self._status_map1[x] =y
       self._status_map = self._status_map1
       self._status_map['S5'] = _PASSED

       self._count_map1 = dict((en, 0) for en, n, f in _SUBITEM1_LIST)
       self._count_map2 = dict((en, 0) for en, n, f in _SUBITEM2_LIST)
       self._count_map3 = dict((en, 0) for en, n, f in _SUBITEM3_LIST)

       for x, y in self._count_map2.iteritems():
           self._count_map1[x] = y
       for x, y in self._count_map3.iteritems():
           self._count_map1[x] = y
       self._count_map = self._count_map1
   
       prompt_label = gtk.Label('RUNIN...\n')                   
       prompt_label.modify_font(RUNIN_LABEL_FONT)
       prompt_label.set_alignment(0.5, 0.5)
       prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)

       prompt_label.show()
    
       vbox = gtk.VBox()
       vbox.pack_start(prompt_label, False, False)
       
       for ename, name, cb_fn in _SUBITEM1_LIST:
           label_box = self.make_subitem_label_box(ename, name, self._count_map[ename])
           label_box.show()
           vbox.pack_start(label_box, False, False)

       for ename, name, cb_fn in _SUBITEM2_LIST:
           label_box = self.make_subitem_label_box(ename, name, self._count_map[ename])
           label_box.show()
           vbox.pack_start(label_box, False, False)

       for ename, name, cb_fn in _SUBITEM3_LIST:
           label_box = self.make_subitem_label_box(ename, name, self._count_map[ename])
           label_box.show()
           vbox.pack_start(label_box, False, False)

       ebst = gtk.EventBox()
       
       ebst.modify_bg(gtk.STATE_NORMAL, _BLACK)
       
       dt = datetime.datetime.today()

       _sdateword = str(datetime.date.fromtimestamp(time.time()))
       _stimeword = time.strftime("%H:%M:%S")
       _sdatetime_word = str("开始时间 : %s %s" % (_sdateword, _stimeword))
       label_stime = gtk.Label(_sdatetime_word)
       label_stime.modify_fg(gtk.STATE_NORMAL, _LABEL_UNTESTED_FG)
       label_stime.set_size_request(*_LABEL_TIME_SIZE)
       label_stime.set_alignment(0, 0.5)
       label_stime.modify_font(_LABEL_STATUS_FONT)
       
       self.label_stime = label_stime
       self.label_stime.hide()
       
       hbox2 = gtk.HBox()
       hbox2.pack_start(label_stime, True, False)
       hbox2.show()
       ebst.add(hbox2)
       ebst.show()
  
       vbox.pack_start(ebst, False, False)

       ebet = gtk.EventBox()
       
       ebet.modify_bg(gtk.STATE_NORMAL, _BLACK)
       
       duration = datetime.timedelta(hours=1.5, seconds=20)
       dt = dt + duration
       
       #_edateword = str(datetime.date.fromtimestamp(time.time()+_RUN_TIME))
       #_etimeword = time.strftime("%H:%M:%S")
       _edateword = dt.strftime("%Y-%m-%d")
       _etimeword = dt.strftime("%H:%M:%S")

       _edatetime_word = str("结束时间 : %s %s" % (_edateword, _etimeword))
       label_etime = gtk.Label(_edatetime_word)
       label_etime.modify_fg(gtk.STATE_NORMAL, _LABEL_UNTESTED_FG)
       label_etime.set_size_request(*_LABEL_TIME_SIZE)
       label_etime.set_alignment(0, 0.5)
       label_etime.modify_font(_LABEL_STATUS_FONT)
       
       self.label_etime = label_etime
       self.label_etime.hide()
       hbox3 = gtk.HBox()
       hbox3.pack_start(label_etime, True, False)
       hbox3.show()
       ebet.add(hbox3)
       ebet.show()

       
       vbox.pack_start(ebet, False, False)

       vbox.show()

       test_widget = gtk.EventBox()
       test_widget.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
       test_widget.add(vbox)

       self._test_widget = test_widget

       self.window.add(self._test_widget)

       self._test_widget.show()

       self.window.show()
       
       thread.start_new_thread(self.pop_subitem1, ())
       
       #gobject.timeout_add(1000, self.pop_subitem1)

   def main(self):
       gtk.main()
   
       

if __name__ == "__main__":

   frt = FRT()
   frt.main()
