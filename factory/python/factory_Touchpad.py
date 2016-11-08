#!/usr/bin/python
#-*- encoding:utf-8 -*-
# Copyright (c) 2010 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


# DESCRIPTION :
#
# Intended for use during manufacturing to validate that the touchpad
# is functioning properly.

import cairo
import gobject
import gtk
import time
import os
import sys
import subprocess
import pango
from cmath import pi
from gtk import gdk
import re
sys.path.append('/opt/mfg/ui/pydirs/')
sys.path.append('/opt/mfg/ui/config/')
import factory_sdt as sdt
import factory_conf as cfg

T_out = cfg.tp_timeout * 1000

_LABEL_FONT = pango.FontDescription('courier new condensed 20')
_LABEL_FG = gtk.gdk.color_parse('light green')

_SYNCLIENT_SETTINGS_CMDLINE = '/opt/Synaptics/bin/syndetect'
_SYNCLIENT_CMDLINE = '/opt/Synaptics/bin/syncontrol packets /tmp/packet.out'

_X_SEGMENTS = 5
_Y_SEGMENTS = 4

_X_TP_OFFSET = 12
_Y_TP_OFFSET = 12
_TP_WIDTH = 396
_TP_HEIGHT = 212
_TP_SECTOR_WIDTH = (_TP_WIDTH / _X_SEGMENTS) - 1
_TP_SECTOR_HEIGHT = (_TP_HEIGHT / _Y_SEGMENTS) - 1

_X_SP_OFFSET = 428
_SP_WIDTH = 15

_F_RADIUS = 21

_X_OF_OFFSET = 486 + _F_RADIUS + 2
_Y_OF_OFFSET = 54 + _F_RADIUS + 2

_X_TFL_OFFSET = 459 + _F_RADIUS + 2
_X_TFR_OFFSET = 513 + _F_RADIUS + 2
_Y_TF_OFFSET = 117 + _F_RADIUS + 2


class TouchpadTest:

    def __init__(self, tp_image, drawing_area, test_item_flag):
    #def __init__(self, tp_image, drawing_area):
        self._tp_image = tp_image
        self._drawing_area = drawing_area
        #self._ft_state = ft_state
        self._motion_grid = {}
        for x in range(_X_SEGMENTS):
            for y in range(_Y_SEGMENTS):
                self._motion_grid['%d,%d' % (x, y)] = False
        self._scroll_array = {}
        for y in range(_Y_SEGMENTS):
            self._scroll_array[y] = False
        self._l_click = False
        self._r_click = False
        self._of_z_rad = 0
        self._tf_z_rad = 0
        self._deadline = None
        # The following flags define what test items are conducted
        self._motion_sectors_flag = test_item_flag[0]
        self._scroll_segments_flag = test_item_flag[1]
        self._l_click_flag = test_item_flag[2]
        self._r_click_flag = test_item_flag[3]
	self.start = False
	self.T_flg = False

    def calc_missing_string(self):
        missing = []
        missing_motion_sectors = sorted(
            i for i, v in self._motion_grid.items() if v is False)
        if missing_motion_sectors:
            missing.append('missing_motion_sectors = [%s]' %
                           ', '.join(missing_motion_sectors))
        missing_scroll_segments = sorted(
            str(i) for i, v in self._scroll_array.items() if v is False)
        if missing_scroll_segments:
            missing.append('missing_scroll_segments = [%s]' %
                           ', '.join(missing_scroll_segments))
        if not self._l_click:
            missing.append('missing left click')
        # XXX add self._r_click here when that is supported...
        return ', '.join(missing)

    def timer_event(self,yseg):
	for x in range(_X_SEGMENTS):
	    idx = '%d,%d' % (x, yseg)
            if not self._motion_grid[idx] :
                sdt.log("Speed test timedout!!")
                sys.exit(1)
        return False 

    def device_event(self, x, y, z, fingers=0, left=0, right=0):
        x_seg = int(round(x / (1.0 / float(_X_SEGMENTS - 1))))
        y_seg = int(round(y / (1.0 / float(_Y_SEGMENTS - 1))))
        z_rad = int(round(z / (1.0 / float(_F_RADIUS - 1))))

	if not self.start and y_seg != 0:
            self.start = True
	    gobject.timeout_add(T_out, self.timer_event,y_seg)
	
        index = '%d,%d' % (x_seg, y_seg)
        assert(index in self._motion_grid)
        assert(y_seg in self._scroll_array)

        new_stuff = False

        if left and not self._l_click:
            self._l_click = True
            self._of_z_rad = _F_RADIUS
            new_stuff = True

        elif right and not self._r_click:
            self._r_click = True
            self._tf_z_rad = _F_RADIUS
            new_stuff = True

        if fingers == 0 and not self._motion_grid[index] and \
                self._motion_sectors_flag:
            self._motion_grid[index] = True
            new_stuff = True

        elif fingers == 1 and not self._scroll_array[y_seg] and \
                self._scroll_segments_flag:
            self._scroll_array[y_seg] = True
            new_stuff = True

        if fingers == 0 and not self._l_click and z_rad != self._of_z_rad and \
                self._l_click_flag:
            self._of_z_rad = z_rad
            new_stuff = True

        elif fingers == 1 and not self._r_click and \
                z_rad != self._tf_z_rad and self._r_click_flag:
            self._tf_z_rad = z_rad
            new_stuff = True

        if new_stuff:
            self._drawing_area.queue_draw()
	    if self._deadline is None:
                self._deadline = int(time.time()) + 30

        if not self.calc_missing_string():
           # print 'completed successfully'
	    sys.exit(99)


    def expose_event(self, widget, event):
        context = widget.window.cairo_create()
        # Show touchpad image as the background.
        context.set_source_surface(self._tp_image, 0, 0)
        context.paint()
 	context.set_source_rgba(0,0.5,0,0.6)

        for index in self._motion_grid:
            if not self._motion_grid[index]:
                continue
            ind_x, ind_y = map(int, index.split(','))
            x = _X_TP_OFFSET + (ind_x * (_TP_SECTOR_WIDTH + 1))
            y = _Y_TP_OFFSET + (ind_y * (_TP_SECTOR_HEIGHT + 1))
            coords = (x, y, _TP_SECTOR_WIDTH, _TP_SECTOR_HEIGHT)
            context.rectangle(*coords)
	   
            context.fill()

        for y_seg in self._scroll_array:
            if not self._scroll_array[y_seg]:
                continue
            y = _Y_TP_OFFSET + (y_seg * (_TP_SECTOR_HEIGHT + 1))
            coords = (_X_SP_OFFSET, y, _SP_WIDTH, _TP_SECTOR_HEIGHT)
            context.rectangle(*coords)

            context.fill()

        if not self._l_click:
            context.set_source_rgba(0.6,0.6,0,0.6)
        context.arc(_X_OF_OFFSET, _Y_OF_OFFSET, self._of_z_rad, 0.0, 2.0 * pi)
        context.fill()

        if self._l_click and not self._r_click:
	    context.set_source_rgba(0.6,0.6,0,0.6)	
        context.arc(_X_TFL_OFFSET, _Y_TF_OFFSET, self._tf_z_rad, 0.0, 2.0 * pi)
        context.fill()
        context.arc(_X_TFR_OFFSET, _Y_TF_OFFSET, self._tf_z_rad, 0.0, 2.0 * pi)
        context.fill()

        return True

    def key_press_event(self, widget, event):
        #self._ft_state.exit_on_trigger(event)
        return True

    def button_press_event(self, widget, event):
	#print 'button_press_event %d,%d' % (event.x, event.y)
        return True

    def button_release_event(self, widget, event):
       # print 'button_release_event %d,%d' % (event.x, event.y)
        return True

    def motion_event(self, widget, event):
	#print 'motion_event %d,%d' %(event.x, event.y)
        return True

    def register_callbacks(self, window):
        window.connect('key-press-event', self.key_press_event)
        window.add_events(gdk.KEY_PRESS_MASK)

class SynControl:

    _PACKET_FILE = '/tmp/syncontrol_packet.out'
    _CMDLINE = '/opt/Synaptics/bin/syncontrol packets ' + _PACKET_FILE
    _PACKET_PATTERN = ('x:', 'y:', 'z:', 'w:', 'dx:', 'dy:', 'finger_index:',
                       'left_button:', 'right_button:')

    # Set the min and max values for typical bezel limits.
    # These are approximate values, and may be different for different models.
    # The following values work fine with Synaptics' touchpad on mario.
    _X_RANGE = (1400, 5700)
    _Y_RANGE = (1200, 4500)
    _Z_RANGE = (0, 255)

    def __init__(self, test):
        self._test = test
        self._xmin, self._xmax = SynControl._X_RANGE
        self._ymin, self._ymax = SynControl._Y_RANGE
        self._zmin, self._zmax = SynControl._Z_RANGE

        # Remove the packet output file if it exists
        if os.path.exists(SynControl._PACKET_FILE):
            rm_command = 'rm %s' % SynControl._PACKET_FILE
            os.system(rm_command)

        try:
            self._proc = subprocess.Popen(SynControl._CMDLINE.split(),
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
        except OSError as e:
             sdt.log('Failure on launching "%s"' % SynControl._CMDLINE)
        # delay before we poll
        time.sleep(0.1)
        if self._proc.poll() is not None:
            if self._proc.returncode != 0:
                sdt.log('Failure on "%s" [%d]' %(SynControl._CMDLINE,self._proc.returncode))
            else:
                sdt.log('Termination unexpected on "%s"' % SynControl._CMDLINE)

        # Open the packet file for read
        while not os.path.exists(SynControl._PACKET_FILE):
            time.sleep(0.1)
        self._packet_file = open(SynControl._PACKET_FILE, 'r')
        self._count = 0

        # It is preferable to set low priority for processing packets.
        # Otherwise, the other widgets may get stuck.
        gobject.idle_add(self.recv)

    def recv(self):
        _PACKET_PATTERN = SynControl._PACKET_PATTERN
        while True:
            line = self._packet_file.readline()
            if line == '':
                break

            data = line.split(',')
            self._count += 1

            # check pattern length
            if len(data) != len(_PACKET_PATTERN):
                #factory.log('unknown data : %d, %s' % (len(data), data))
                continue

            # check validity of packet pattern
            invalid_pattern = False
            for i in range(len(_PACKET_PATTERN)):
                if not data[i].lstrip().startswith(_PACKET_PATTERN[i]):
                    invalid_pattern = True
                    break
            if invalid_pattern:
                #factory.log('  invalid pattern skipped: %s' % data)
                continue
            new_data = re.sub('[a-zA-Z,:_]',' ',line).split()
	    if len(new_data) != 9:
		continue
	    data_x,data_y,data_z, w,dx,dy,f, l,r = new_data[0:9]

            # fileter out idle data
            if int(data_x) <= 10 and int(data_y) <= 10 and int(data_z) <= 4:
                continue

            x = sorted([self._xmin, float(data_x), self._xmax])[1]
            x = (x - self._xmin) / (self._xmax - self._xmin)
            y = sorted([self._ymin, float(data_y), self._ymax])[1]
            y = (y - self._ymin) / (self._ymax - self._ymin)
            y = 1 - y
            z = sorted([self._zmin, float(data_z), self._zmax])[1]
            z = (z - self._zmin) / (self._zmax - self._zmin)

	    self._test.device_event(x, y, z,int(f),int(l),int(r))

	return True

    def quit(self):
        pass
        #self._proc.kill()
       # print 'dead'

class factory_Touchpad():
    version = 1
    preserve_srcdir = True

    # test_item_flag includes the following flags
    # _motion_sectors_flag, _scroll_segments_flag, _l_click_flag, _r_click_flag
    # Ideally, all flags should be True when properly supported.
    # _TEST_ITEM_FLAG = {SynClient:(True, True, True, False), \
    #                    SynControl:(True, False, False, False)}
    _TEST_ITEM_FLAG = {SynControl:(True, True, True, True)}

def main():
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.connect('destroy', lambda w: gtk.main_quit())
    window.set_position(gtk.WIN_POS_CENTER)

    bg_color = gtk.gdk.color_parse('black')
    window.modify_bg(gtk.STATE_NORMAL, bg_color)
    tp_image = cairo.ImageSurface.create_from_png('/opt/mfg/ui/pics/touchpad.png')
    image_size = (tp_image.get_width(), tp_image.get_height())

    window.set_default_size(*image_size)
    window.move(260, 160)

    prompt_label = gtk.Label('触控板测试\n请将手指在触控板上滑动\n')
    prompt_label.modify_font(_LABEL_FONT)
    prompt_label.set_alignment(0.5, 0.5)
    prompt_label.modify_fg(gtk.STATE_NORMAL, _LABEL_FG)
   
    prompt_label.show()

    vbox = gtk.VBox()
    vbox.pack_start(prompt_label, False, False)
    drawing_area = gtk.DrawingArea()

    SynClass = SynControl

    test_item_flag = factory_Touchpad._TEST_ITEM_FLAG[SynClass]

    test = TouchpadTest(tp_image, drawing_area, test_item_flag)
    drawing_area.set_size_request(*image_size)


    drawing_area.connect('expose_event', test.expose_event)
    drawing_area.connect('button-press-event', test.button_press_event)
    drawing_area.connect('button-release-event', test.button_release_event)
    drawing_area.connect('motion-notify-event', test.motion_event)
    drawing_area.show()
    drawing_area.set_events(gdk.EXPOSURE_MASK |
                                gdk.BUTTON_PRESS_MASK |
                                gdk.BUTTON_RELEASE_MASK |
                                gdk.POINTER_MOTION_MASK)


    synobject = SynClass(test)

    vbox.pack_start(drawing_area, False, False)
    vbox.show()
    window.add(vbox)
    window.show()
    gtk.gdk.pointer_grab(window.window)
    missing = test.calc_missing_string()
    gtk.main()

if __name__ == '__main__':
    main()
