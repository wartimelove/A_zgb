#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


# DESCRIPTION :
#
# This test looks in "/dev/video0" for a v4l2 video capture device,
# and starts streaming captured frames on the monitor.
# The observer then decides if the captured image looks good or defective,
# pressing enter key to let it pass or tab key to fail.

import sys
import gtk
from gtk import gdk
import glib
import pango
import numpy
import v4l2

DEVICE_NAME = "/dev/video0"
PREFERRED_WIDTH = 480
PREFERRED_HEIGHT = 320
PREFERRED_BUFFER_COUNT = 4

class factory_Camera():
    version = 1
    key_good = gdk.keyval_from_name('Return')
    key_bad = gdk.keyval_from_name('Tab')
    @staticmethod
    def get_best_frame_size(dev, pixel_format, width, height):
        """Given the preferred frame size, find a reasonable frame size the
        capture device is capable of.

        currently it returns the smallest frame size that is equal or bigger
        than the preferred size in both axis. this does not conform to
        chrome browser's behavior, but is easier for testing purpose.
        """
        sizes = [(w, h) for w, h in dev.enum_framesizes(pixel_format)
                 if type(w) is int or type(w) is long]
        if not sizes:
            return (width, height)
        if False: # see doc string above
            for w, h in sizes:
                if w >= width and h >= height:
                    return (w,h)
        good_sizes = [(w, h) for w, h in sizes if w >= width and h >= height]
        if good_sizes:
            return min(good_sizes, key=lambda x: x[0] * x[1])
        return max(sizes, key=lambda x: x[0] * x[1])

    def render(self, pixels):
        numpy.maximum(pixels, 0, pixels)
        numpy.minimum(pixels, 255, pixels)
        self.pixels[:] = pixels
        self.img.queue_draw()

    def key_release_callback(self, widget, event):
        #print 'key_release_callback ' ,\
        #            (event.keyval, gdk.keyval_name(event.keyval))
        if event.keyval == self.key_good:
            self.fail = False
            sys.exit(99)
        if event.keyval == self.key_bad:
            gtk.main_quit()
        return

    def run_test_widget(self,
                        test_widget=None,
                        test_widget_size=None):

        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.modify_bg(gtk.STATE_NORMAL,gdk.color_parse('black'))
        window.set_size_request(*test_widget_size)

        align = gtk.Alignment(xalign=0.5, yalign=0.5)
        align.add(test_widget)
        window.move(220, 35)
        window.add(align)
        window.show_all()

        gtk.gdk.pointer_grab(window.window, confine_to=window.window)
        window.connect('key-release-event', self.key_release_callback)
        window.add_events(gdk.KEY_RELEASE_MASK)
	gtk.main()



    def __init__ (self, test_widget_size=(640,480), trigger_set=None):
 
        self.fail = True

        label = gtk.Label("摄像头测试,成功按回车键,失败按Tab键\n")

        label.modify_font(pango.FontDescription('courier new condensed 20'))
        label.modify_fg(gtk.STATE_NORMAL, gdk.color_parse('light green'))
        test_widget = gtk.VBox()
        test_widget.modify_bg(gtk.STATE_NORMAL, gdk.color_parse('black'))
        test_widget.add(label)
        self.test_widget = test_widget

        self.img = None

        dev = v4l2.Device(DEVICE_NAME)

        if not dev.cap.capabilities & v4l2.V4L2_CAP_VIDEO_CAPTURE:
            raise ValueError("%s doesn't support video capture interface"
                             % (DEVICE_NAME, ))
        if not dev.cap.capabilities & v4l2.V4L2_CAP_STREAMING:
            raise ValueError("%s doesn't support streaming I/O"
                             % (DEVICE_NAME, ))
        glib.io_add_watch(dev.fd, glib.IO_IN,
            lambda *x:dev.capture_mmap_shot(self.render) or True,
           priority=glib.PRIORITY_LOW)

        frame_size = self.get_best_frame_size(dev, v4l2.V4L2_PIX_FMT_YUYV,
            PREFERRED_WIDTH, PREFERRED_HEIGHT)
        adj_fmt = dev.capture_set_format(frame_size[0], frame_size[1],
            v4l2.V4L2_PIX_FMT_YUYV, v4l2.V4L2_FIELD_INTERLACED)
	width, height = adj_fmt.fmt.pix.width, adj_fmt.fmt.pix.height
	self.pixbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, False, 8,
            width, height)
	self.pixels = self.pixbuf.get_pixels_array()
        self.img = gtk.image_new_from_pixbuf(self.pixbuf);
        self.test_widget.add(self.img)
	self.img.show()
        
        
        dev.capture_mmap_prepare(PREFERRED_BUFFER_COUNT, 2)

        dev.capture_mmap_start()

        self.run_test_widget(
            test_widget=test_widget,
            test_widget_size=test_widget_size)

	dev.capture_mmap_stop()
        dev.capture_mmap_finish()

def main():
    '''main() do nothing'''

if __name__ == '__main__':
    factory_Camera()
    main()
