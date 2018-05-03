#!/usr/bin/env python

import numpy as np
import os
from PyQt5.QtCore import QDir, Qt
from PyQt5.QtGui import QImage, QPalette, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QLabel,
                             QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy)
from astropy.io import fits
from send2trash import send2trash
from PIL import Image


class ImageViewer(QMainWindow):
    def __init__(self):
        super(ImageViewer, self).__init__()
        self.scaleFactor = 0.0
        self.setup_blank_background()
        self.createActions()
        self.createMenus()
        self.resize(1000, 800)

    def setup_blank_background(self):
        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)
        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.setCentralWidget(self.scrollArea)
        self.setWindowTitle("YAFFV")
        self.current_file = ''

    def next(self):
        '''
        Next image action handler
        :return:
        '''
        self.display(self._navigate_image(1))

    def delete(self):
        '''
        Delete action handler
        :return:
        '''
        next_image = self._navigate_image(1)
        send2trash(self.current_file)
        if os.path.exists(next_image):
            self.display(next_image)
        else:
            self.nextAct.setEnabled(False)
            self.previousAct.setEnabled(False)
            self.deleteAct.setEnabled(False)
            self.setup_blank_background()

    def previous(self):
        '''
        Previous image action handler
        :return:
        '''
        self.display(self._navigate_image(-1))

    def _navigate_image(self, increment):
        '''
        Jump forward or backwards n images from the current_image
        :param increment:
        :return:
        '''
        dir = os.path.dirname(self.current_file)
        files = list(f for f in os.listdir(dir) if f.endswith('fits'))
        files.sort()
        basename = os.path.basename(self.current_file)
        index = files.index(basename) + increment
        if index >= len(files):
            index = 0
        if index < 0:
            index = len(files) - 1
        next = files[index]
        return os.path.join(dir, next)

    def open(self):
        '''
        Open file action handler
        :return:
        '''
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File",
                                                  QDir.currentPath())
        self.display(fileName)

    def display(self, fileName):
        self.current_file = fileName
        if fileName:
            image = None
            try:
                self._save_tmp_jpg_from_fits(fileName)
                image = QImage('/tmp/yaffv-current.jpg')
            except Exception as inst:
                print(inst)
            if not image or image.isNull():
                QMessageBox.information(self, "YAFFV",
                                        "Cannot load %s." % fileName)
                return
            self.imageLabel.setPixmap(QPixmap.fromImage(image))
            self.scaleFactor = 1.0
            self.nextAct.setEnabled(True)
            self.previousAct.setEnabled(True)
            self.deleteAct.setEnabled(True)
            self.fitToWindowAct.setEnabled(True)
            self.updateActions()
            if not self.fitToWindowAct.isChecked():
                self.imageLabel.adjustSize()
            self.setWindowTitle(os.path.basename(fileName))

    def _save_tmp_jpg_from_fits(self, fileName):
        vmax = 8000
        vmin = 400
        with fits.open(fileName) as hdul:
            data = hdul[0].data
            if data is None:
                data = hdul[1].data
            data[data > vmax] = vmax
            data[data < vmin] = vmin
            data = (data - vmin) / (vmax - vmin)
            data = (255 * data).astype(np.uint8)
            image = Image.fromarray(data, 'L')
            image.save('/tmp/yaffv-current.jpg')

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()
        self.updateActions()

    def about(self):
        QMessageBox.about(self, "About YAFFV",
                          "<p><b>YAFFV</b> Yet Another Fits File Viewer</p>"
                          "Navigate to next image using cursor keys"
                          "Delete an image with the delete key</p>")

    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O",
                               triggered=self.open)
        self.nextAct = QAction("&Next...", self, shortcut=Qt.Key_Right,
                               enabled=False, triggered=self.next)
        self.deleteAct = QAction("&Delete...", self, shortcut=Qt.Key_Delete,
                                 enabled=False, triggered=self.delete)
        self.previousAct = QAction("&Previous...", self, shortcut=Qt.Key_Left,
                                   enabled=False, triggered=self.previous)
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                               triggered=self.close)
        self.zoomInAct = QAction("Zoom &In (25%)", self, shortcut="Ctrl++",
                                 enabled=False, triggered=self.zoomIn)
        self.zoomOutAct = QAction("Zoom &Out (25%)", self, shortcut="Ctrl+-",
                                  enabled=False, triggered=self.zoomOut)
        self.normalSizeAct = QAction("&Normal Size", self, shortcut="Ctrl+S",
                                     enabled=False, triggered=self.normalSize)
        self.fitToWindowAct = QAction("&Fit to Window", self, enabled=False,
                                      checkable=True, shortcut="Ctrl+F", triggered=self.fitToWindow)
        self.aboutAct = QAction("&About", self, triggered=self.about)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.nextAct)
        self.fileMenu.addAction(self.previousAct)
        self.fileMenu.addAction(self.deleteAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)
        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())
        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)
        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    imageViewer = ImageViewer()
    imageViewer.show()
    sys.exit(app.exec_())
