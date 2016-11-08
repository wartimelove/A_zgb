#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import pygtk
pygtk.require('2.0')
import gtk
import sys

def log(message):
    print  >>sys.stderr,message
