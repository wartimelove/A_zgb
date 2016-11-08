#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This is a factory test to test the LCD display & LED .


import gtk
import pango
import os
import sys
from gtk import gdk

_ACTIVE = '请按键'
_PASSED = '通过'
_FAILED = '失败'
_UNTESTED = '等待中...'
NUVOTON = '/opt/mfg/ui/tests/NUVOTON '

_LABEL_STATUS_SIZE = (140, 30)
_LABEL_STATUS_FONT = pango.FontDescription('courier new condensed 16')
_LABEL_FONT = pango.FontDescription('courier new condensed 20')
_LABEL_FG = gtk.gdk.color_parse('light green')
_LABEL_UNTESTED_FG = gtk.gdk.color_parse('grey40')

_LABEL_COLORS = {
    _ACTIVE: gtk.gdk.color_parse('light goldenrod'),
    _PASSED: gtk.gdk.color_parse('pale green'),
    _FAILED: gtk.gdk.color_parse('tomato'),
    _UNTESTED: gtk.gdk.color_parse('dark slate grey')}

def pattern_cb_solid(widget, event, color=None, led=None):
    if led == 'aoff':
  	os.system('ifconfig wlan0 up')
	os.system(NUVOTON + '-sleepled -off')
	os.system(NUVOTON + '-battfulled -off')
	os.system(NUVOTON + '-powerled -off')
	os.system(NUVOTON + '-battchgled -off')
 	os.system(NUVOTON + '-battchgled -off')
	os.system(NUVOTON + '-3g -off')
        os.system('ifconfig wlan0 down')
    elif led == 'bon':
	os.system('ifconfig wlan0 up')
	os.system(NUVOTON + '-3g -on')
	os.system(NUVOTON + '-battfulled -on')
	os.system(NUVOTON + '-powerled -on')
    elif led == 'boff':
	os.system(NUVOTON + '-powerled -off')
	os.system(NUVOTON + '-battfulled -off')
	os.system(NUVOTON + '-3g -off')
	os.system('ifconfig wlan0 down')
    elif led == 'yon':
	os.system(NUVOTON + '-sleepled -on')
	os.system(NUVOTON + '-battchgled -on')
        #os.system('ifconfig wlan0 up')
    elif led == 'yoff':
	os.system(NUVOTON + '-sleepled -off')
	os.system(NUVOTON + '-battchgled -off')
        #os.system('ifconfig wlan0 down')
    elif led == 'normal':
	os.system(NUVOTON + '-ledrelease')
        os.system('ifconfig wlan0 up')

    dr = widget.window
    xmax, ymax = dr.get_size()
    gc = gtk.gdk.GC(dr)
    gc.set_rgb_fg_color(color)
    dr.draw_rectangle(gc, True, 0, 0, xmax, ymax)
    return False


def pattern_cb_grid(widget, event, color=None ):
    
    dr = widget.window
    xmax, ymax = dr.get_size()
    gc = gtk.gdk.GC(dr)
    gc.set_rgb_fg_color(gtk.gdk.Color("black"))
    dr.draw_rectangle(gc, True, 0, 0, xmax, ymax)
    gc.set_rgb_fg_color(color)
    gc.set_line_attributes(1,
                           gtk.gdk.LINE_SOLID,
                           gtk.gdk.CAP_BUTT,
                           gtk.gdk.JOIN_MITER)
    for x in range(0, xmax, 20):
        dr.draw_line(gc, x, 0, x, ymax)
    for y in range(0, ymax, 20):
        dr.draw_line(gc, 0, y, xmax, y)
    return False


_ITEM_LIST = [
    ('red/led off','LCD屏红/LED灯灭', lambda *x: pattern_cb_solid(*x, **{'color':gtk.gdk.color_parse('red'),'led':'aoff'})),
    ('green/led blue on','LCD屏绿/LED灯蓝', lambda *x: pattern_cb_solid(*x, **{'color':gtk.gdk.color_parse('green'),'led':'bon'})),
    ('blue/led bule off','LCD屏蓝/LED灯灭', lambda *x: pattern_cb_solid(*x, **{'color':gtk.gdk.color_parse('blue'),'led':'boff'})),
    ('black/led yellow on','LCD屏黑/LED灯黄', lambda *x: pattern_cb_solid(*x, **{'color':gtk.gdk.color_parse('black'),'led':'yon'})),
    ('white/led yellow off','LCD屏白/LED灯灭', lambda *x: pattern_cb_solid(*x, **{'color':gtk.gdk.color_parse('white'),'led':'yoff'})),
    ('gray/ led normal','LCD屏灰/LED常态', lambda *x: pattern_cb_solid(*x, **{'color':gtk.gdk.color_parse('grey'),'led':'normal'}))]
#    ('grid','栅格', lambda *x: pattern_cb_grid(*x, **{'color':ful.GREEN}))]


class factory_Display_LED():
    version = 1

    def display_full_screen(self, pattern_callback):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        screen = window.get_screen()
        screen_size = (screen.get_width(), screen.get_height())
        window.set_size_request(*screen_size)
        drawing_area = gtk.DrawingArea()
        window.add(drawing_area)
        window.show_all()
        self._fs_window = window
        gtk.gdk.keyboard_grab(self.window.window)

        drawing_area.connect('expose_event', pattern_callback)

    def goto_next_pattern(self):
        if not self._pattern_queue:
            if self.RESULT:
	        sys.exit(99)
            else:
                sys.exit(1)
        self._current_pattern = self._pattern_queue.pop()
        ename,name, cb_fn = self._current_pattern
        self._status_map[ename] = _ACTIVE
        self._current_pattern_shown = False

    def key_press_callback(self, widget, event):
        ename,pattern_name, pattern_cb = self._current_pattern
        if event.keyval == gtk.keysyms.space and not self._fs_window:
            self.display_full_screen(pattern_cb)
        return True

    def key_release_callback(self, widget, event):
        ename,pattern_name, pattern_cb = self._current_pattern
        if event.keyval == gtk.keysyms.space and not self._fs_window and self._FLG == 0:
            self._FLG = 1
            self.display_full_screen(pattern_cb)
        elif event.keyval == gtk.keysyms.space and self._fs_window is not None and self._FLG== 1:
            self._FLG = 0 
            self._status_map[ename] = _PASSED
            self._fs_window.destroy()
            self._fs_window = None
            self.goto_next_pattern()
            self._current_pattern_shown = True
        elif event.keyval == gtk.keysyms.Tab and self._fs_window is not None and self._FLG== 1:
	    self._FLG = 0 
            self._status_map[ename] = _FAILED
            self.RESULT = False
            self._fs_window.destroy()
            self._fs_window = None
            self.goto_next_pattern()
        elif event.keyval == ord('Q'):
            gtk.main_quit()
        else:
            print "no thing"
        #self._test_widget.queue_draw()
        return True

    def label_status_expose(self, widget, event, name=None):
        status = self._status_map[name]
        widget.set_text(status)
        widget.modify_fg(gtk.STATE_NORMAL, _LABEL_COLORS[status])

    def make_pattern_label_box(self,ename, name, cb_fun):
        eb = gtk.EventBox()
        eb.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse('black'))
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
        self._FLG = 0
        self._fs_window = None
        self.RESULT = True
        xset_status = os.system('xset r off')
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("black"))
        self.window.move(400, 100)

        self._pattern_queue = [x for x in reversed(_ITEM_LIST)]
        self._status_map = dict((en, _UNTESTED) for en,n, f in _ITEM_LIST)

        prompt_label = gtk.Label('侧灯与显屏测试\n按空格键测试\n'
                                 '失败按TAB键\n')
        prompt_label.modify_font(_LABEL_FONT)
        prompt_label.set_alignment(0.5, 0.5)
        prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
        self._prompt_label = prompt_label

        vbox = gtk.VBox()
        vbox.pack_start(prompt_label, False, False)

        for ename, name, cb_fun in _ITEM_LIST:
            label_box = self.make_pattern_label_box(ename, name, cb_fun)
            vbox.pack_start(label_box, False, False)

        self.window.add(vbox)
        self.window.show_all()
        gtk.gdk.pointer_grab(self.window.window, confine_to=self.window.window)
        gtk.gdk.keyboard_grab(self.window.window)
        self.window.connect('key-release-event', self.key_release_callback)
        self.window.add_events(gdk.KEY_RELEASE_MASK)

        self.goto_next_pattern()

def main():
    '''do nothing'''    
    gtk.main()

if __name__ == "__main__":
    factory_Display_LED()
    main()
