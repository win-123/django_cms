#! /usr/bin/env python
# -*- coding:utf-8 -*-

from django import conf


for app in conf.settings.INSTALLED_APPS:
    try:
        admin_module = __import__("%s.kingadmin" % app)
        # print("admin_module:",admin_module.kingadmin)
    except ImportError:
        pass

