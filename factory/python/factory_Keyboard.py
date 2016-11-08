#!/usr/bin/python
#
# Copyright (c) 2010 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# Modified by REX 2010-08-14

import cairo
import gobject
import gtk
import sys
import time
import os


_OUTPUT_HEADER = \
'''
# AUTOMATICALLY GENERATED -- This data structure is printed out by
# BindingsSetup during execution, and modifications can be pasted from
# there back to here.
'''


class BindingsSetup:
    """Facilitate generation of the binding map for the actual
    KeyboardTest -- it takes the name of a png keyboard image file and
    optionally a corresponding bindings file as its first and second
    command line arguments, respectively.  On each assignment of a new
    binding, it will output the contents for a new bindings file to
    stdout (a bit verbose, but simple).

    UI -- select key region to be highlighted with the mouse, hit
    corresponding key, double click to active tweak mode, fine tune
    highlighted region with the arrow keys (hold shift for neg
    effect), double click to confirm and output current bindings
    datastructure, repeat."""


    def __init__(self, kbd_image, bindings):
        self._kbd_image = kbd_image
        self._press_xy = None
        self._last_coords = None
        self._last_key = None
        self._tweak_mode = False
        self._bindings = bindings
	self.successful_keys = set()
        self._pressed_keys = set()

    def fmt_key(self, key):
        return '%4x,%-4x' % key

    def expose_event(self, widget, event):
        context = widget.window.cairo_create()
        context.set_source_surface(self._kbd_image, 0, 0)
        context.paint()
	
	for key in self.successful_keys:
            draw_position = self._bindings[key]
            context.rectangle(*draw_position)
            context.set_source_rgba(0, 0.5, 0, 0.6)		#green(key released)
	    context.fill()
	for key in self._pressed_keys:
            context.rectangle(*self.draw_position)
            context.set_source_rgba(0.6, 0.6, 0, 0.6)		#yellow(key pressed)
	    context.fill()
        return False	
	
    def calc_position(self,widget,keyval):
	#print keyval
        px, py ,x, y = self._bindings[keyval]
        x = px + x
        y = py + y
        xmin, xmax = sorted([px, x])
        ymin, ymax = sorted([py, y])
        xdelta = xmax - xmin
        ydelta = ymax - ymin
        if xdelta and ydelta:
            self.draw_position = (xmin, ymin, xdelta, ydelta)
            widget.queue_draw()
	return True

    def key_press_event(self, widget, event):
        key = (event.keyval, event.hardware_keycode)
       # print 'key pressed   fmt_key=%s event.string=%s' % (self.fmt_key(key), repr(event.string))
	if event.keyval in self._bindings:
	    self._pressed_keys.add(event.keyval)
            self.calc_position(widget,event.keyval)
        else:
            #print "Keyval not in bindings"
	    return False
        return True

    def key_release_event(self, widget, event):
	key = (event.keyval, event.hardware_keycode)
        if event.keyval not in self._pressed_keys:
            return False
	self._pressed_keys.remove(event.keyval)
        self.successful_keys.add(event.keyval)
       # print 'key released   fmt_key=%s event.string=%s' % (self.fmt_key(key), repr(event.string))
	if event.keyval in self._bindings:
            self.calc_position(widget,event.keyval)
        else:
           # print "Keyval not in bindings"
	    return False
        if len(self._bindings) == len(self.successful_keys):
	#if 5 == len(self.successful_keys):
	  #  print "KB test end"
            sys.exit(99)
	    #gtk.main_quit()
        return True

def main():
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.connect('destroy', lambda w: gtk.main_quit())
    #window.set_position(gtk.WIN_POS_CENTER)
    #window.set_default_size(911, 380)
    window.move(80, 100)

    bg_color = gtk.gdk.color_parse('midnight blue')
    window.modify_bg(gtk.STATE_NORMAL, bg_color)

    kbd_image = cairo.ImageSurface.create_from_png('/opt/mfg/ui/pics/en_us.png')
    kbd_image_size = (kbd_image.get_width(), kbd_image.get_height())

    bindings = {}
    f = open('/opt/mfg/ui/config/en_us.bindings', 'r')
    bindings = eval(f.read())
    f.close()

    drawing_area = gtk.DrawingArea()
    drawing_area.set_size_request(*kbd_image_size)

    kt = BindingsSetup(kbd_image, bindings)
    window.connect('key-press-event', kt.key_press_event)
    window.connect('key-release-event', kt.key_release_event)
    drawing_area.connect('expose_event', kt.expose_event)

    drawing_area.show()
    align = gtk.Alignment(xalign=0.5, yalign=0.5)
    align.add(drawing_area)
    align.show()



    drawing_area.set_events(gtk.gdk.EXPOSURE_MASK |
                            gtk.gdk.KEY_PRESS_MASK |
                            gtk.gdk.KEY_RELEASE_MASK )

    window.add(align)
    window.show()
    gtk.gdk.keyboard_grab(window.window)
    gtk.main()

if __name__ == '__main__':
    main()
