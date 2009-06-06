#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QBrush, QDesktopServices, QFont, QImage, QPalette, QPixmap


# Substantially cribbed from Anki (main.py, onOpenPluginFolder):
def openFolder(path):
    import sys
    import subprocess
    
    if sys.platform == "win32":
        subprocess.Popen("explorer", path.encode(sys.getfilesystemencoding()))
    else:
        QDesktopServices.openUrl(QUrl("file://" + path))


# Code to convert from QVariant taken from <http://www.opensubscriber.com/message/pyqt@riverbankcomputing.com/9900124.html>
variant_converter = {
  "QVariantList": lambda v: fromQVariantList(v),
  "QList<QVariant>": lambda v: fromQVariantList(v),
  "int": lambda v: v.toInt()[0],
  "double": lambda v: v.toDouble()[0],
  "char": lambda v: v.toChar(),
  "QByteArray": lambda v: v.toByteArray(),
  "QString": lambda v: unicode(v.toString()),
  "QPoint": lambda v: v.toPoint(),
  "QPointF": lambda v: v.toPointF(),
  "QSize": lambda v: v.toSize(),
  "QLine": lambda v: v.toLine(),
  "QStringList": lambda v: v.toStringList(),
  "QTime": lambda v: v.toTime(),
  "QDateTime": lambda v: v.toDateTime(),
  "QDate": lambda v: v.toDate(),
  "QLocale": lambda v: v.toLocale(),
  "QUrl": lambda v: v.toUrl(),
  "QRect": lambda v: v.toRect(),
  "QBrush": lambda v: QBrush(v),
  "QFont": lambda v: QFont(v),
  "QPalette": lambda v: QPalette(v),
  "QPixmap": lambda v: QPixmap(v),
  "QImage": lambda v: QImage(v),
  "bool": lambda v: v.toBool()
}

"""
Convert QList<QVariant> to a normal Python list.
"""
def fromQVariantList(variantlist):
    return [fromQVariant(variant) for variant in variantlist.toList()]

"""
Convert a QVariant to a Python value.
"""
def fromQVariant(variant):
    typeName = variant.typeName()
    convert = variant_converter.get(typeName)
    if not convert:
        raise ValueError, "Could not convert value to %s" % typeName
    else:
        return convert(variant) 