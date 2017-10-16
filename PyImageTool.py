"""
Image Tool v2

TODO
+ Load Igor binary waves
+ Load HDF5 files
+ Button for transposing data
+ Axes on plots
+ StartX and DeltaX
"""

import os
import sys
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import numpy as np


# The ImageTool object
# Subclasses QMainWindow
class ImageTool(QtGui.QMainWindow):
    def __init__(self, parent=None, data=None):
        super(ImageTool, self).__init__(parent)

        # Window title
        self.setWindowTitle("Image Tool v2")
        self.setGeometry(50, 50, 800, 600)

        # Menu bar
        file = self.menuBar().addMenu("File")
        view = self.menuBar().addMenu("View")
        
        loadAction = QtGui.QAction("&Load File", self)
        loadAction.setShortcut("Ctrl+O")
        loadAction.setStatusTip('Open a dataset')
        loadAction.triggered.connect(self.loadData)
        exitAction = QtGui.QAction("&Exit", self)
        exitAction.setShortcut("Ctrl+W")
        exitAction.setStatusTip("Exit")
        exitAction.triggered.connect(self.close)
        autoscaleAction = QtGui.QAction("&Autoscale All", self)
        autoscaleAction.setShortcut("Ctrl+A")
        autoscaleAction.setStatusTip('Autoscale all axes')
        autoscaleAction.triggered.connect(self.autoscaleAll)
        
        file.addAction(loadAction)
        view.addAction(autoscaleAction)
        file.addAction(exitAction)

        ## Create the main graphics view
        self.view = pg.GraphicsView()
        self.setCentralWidget(self.view)
        self.l = pg.GraphicsLayout(border=[100, 100, 100])
        self.view.setCentralItem(self.l)

        ## Start laying out the widgets and info
        # Information bar
        self.posLabel = self.l.addLabel("Pos = [0, 0, 0]")
        self.sizeLabel = self.l.addLabel("[Nx, Ny, Nz] = [0, 0, 0]")
        self.l.nextRow()
        # Layout for the x plot, xz image plot, and z plot
        self.l_xz = self.l.addLayout(border=[100, 100, 100])
        # Make the x cut plot
        self.vb_xcut = self.l_xz.addViewBox()
        self.xcut = pg.PlotDataItem()
        self.vb_xcut.addItem(self.xcut)
        # Make the xz image plot
        self.l_xz.nextRow()
        self.vb_xz_cut = self.l_xz.addViewBox()
        self.img_xz_cut = pg.ImageItem()
        self.vb_xz_cut.addItem(self.img_xz_cut)
        # Make the z plot
        self.vb_zcut = self.l.addViewBox()
        self.zcut = pg.PlotDataItem()
        self.vb_zcut.addItem(self.zcut)
        # Make the xy layout
        self.l.nextRow()
        self.l_xy = self.l.addLayout(border=None)
        self.l_xy.setContentsMargins(1, 1, 1, 1)
        self.l_xy.setSpacing(0)
        # Make the xy image and axes
        self.x_axis = pg.AxisItem(orientation='bottom')
        self.y_axis = pg.AxisItem(orientation='left')
        self.hist = pg.HistogramLUTItem()
        self.hist.autoHistogramRange()
        self.vb_xy_cut = self.l_xy.addViewBox()
        self.img_xy_cut = pg.ImageItem()
        self.vb_xy_cut.addItem(self.img_xy_cut)
        self.l_xy.addItem(self.y_axis)
        self.l_xy.addItem(self.vb_xy_cut)
        self.l_xy.addItem(self.hist, rowspan=2)
        self.l_xy.nextRow()
        self.l_xy.addItem(self.x_axis, col=2)
        # Link axes to viewbox
        self.x_axis.linkToView(self.vb_xy_cut)
        self.y_axis.linkToView(self.vb_xy_cut)
        self.hist.setImageItem(self.img_xy_cut)
        # Layout for the y plot and yz image plot
        self.l_yz = self.l.addLayout(border=[100, 100, 100])
        # Make the yz image plot
        self.vb_yz_cut = self.l_yz.addViewBox()
        self.img_yz_cut = pg.ImageItem()
        self.vb_yz_cut.addItem(self.img_yz_cut)
        # Make the y plot
        self.vb_ycut = self.l_yz.addViewBox()
        self.ycut = pg.PlotDataItem()
        self.vb_ycut.addItem(self.ycut)

        ## Make crosshairs
        self.pos = np.array([0, 0, 0], dtype='int')
        self.newPos = np.copy(self.pos)
        bounds = (1, 1, 1)
        self.xy_x_line = pg.InfiniteLine(pos=self.pos[1], movable=True, angle=0, bounds=[0, bounds[1] - 1])
        self.xy_y_line = pg.InfiniteLine(pos=self.pos[0], movable=True, bounds=[0, bounds[0] - 1])
        self.x_line = pg.InfiniteLine(pos=self.pos[0], movable=True, bounds=[0, bounds[0] - 1])
        self.y_line = pg.InfiniteLine(pos=self.pos[0], movable=True, angle=0, bounds=[0, bounds[1] - 1])
        self.z_line = pg.InfiniteLine(pos=self.pos[0], movable=True, bounds=[0, bounds[2] - 1])
        self.vb_xy_cut.addItem(self.xy_x_line)
        self.vb_xy_cut.addItem(self.xy_y_line)
        self.vb_xcut.addItem(self.x_line)
        self.vb_ycut.addItem(self.y_line)
        self.vb_zcut.addItem(self.z_line)

        self.xy_y_line.sigPositionChanged.connect(self.xy_y_update)
        self.xy_x_line.sigPositionChanged.connect(self.xy_x_update)
        self.x_line.sigPositionChanged.connect(self.x_update)
        self.y_line.sigPositionChanged.connect(self.y_update)
        self.z_line.sigPositionChanged.connect(self.z_update)

        ## Set data
        if (data is None):
            ## Make random data
            noise = 0.1*np.random.random((51, 101, 201))
            x = np.linspace(-1, 1, 51)
            y = np.linspace(-1, 1, 101)
            z = np.linspace(-1, 1, 201)
            X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
            data = (X-0.5)**2 + (Y+0.5)**2 + Z**2 + noise
            self.setData(data)
        else:
            self.setData(data)

        self.updatePlots()

    # Control crosshairs with keyboard
    def keyPressEvent(self, event):
        if type(event) == QtGui.QKeyEvent:
            if (event.key() == QtCore.Qt.Key_Up):
                newVal = self.xy_x_line.value() + 1
                self.xy_x_line.setValue(newVal)
                self.y_line.setValue(newVal)
            elif (event.key() == QtCore.Qt.Key_Left):
                newVal = self.xy_y_line.value() - 1
                self.xy_y_line.setValue(newVal)
                self.x_line.setValue(newVal)
            elif (event.key() == QtCore.Qt.Key_Down):
                newVal = self.xy_x_line.value() - 1
                self.xy_x_line.setValue(newVal)
                self.y_line.setValue(newVal)
            elif (event.key() == QtCore.Qt.Key_Right):
                newVal = self.xy_y_line.value() + 1
                self.xy_y_line.setValue(newVal)
                self.x_line.setValue(newVal)
            event.accept()
        else:
            super(ImageTool, self).keyPressEvent(event)

    def updatePlots(self, force=False):
        if (self.pos[0] != self.newPos[0] or force):
            self.img_yz_cut.setImage(self.data[self.newPos[0], :, :])
            self.ycut.setData(x=self.data[self.newPos[0], :, self.newPos[2]],
                              y=np.arange(len(self.data[self.newPos[0], :, self.newPos[2]])))
            self.zcut.setData(self.data[self.newPos[0], self.newPos[1], :])
            self.pos[0] = self.newPos[0]
        if (self.pos[1] != self.newPos[1] or force):
            self.img_xz_cut.setImage(self.data[:, self.newPos[1], :])
            self.xcut.setData(self.data[:, self.newPos[1], self.newPos[2]])
            self.zcut.setData(self.data[self.newPos[0], self.newPos[1], :])
            self.pos[1] = self.newPos[1]
        if (self.pos[2] != self.newPos[2] or force):
            self.img_xy_cut.setImage(self.data[:, :, self.newPos[2]])
            self.xcut.setData(self.data[:, self.newPos[1], self.newPos[2]])
            self.ycut.setData(x=self.data[self.newPos[0], :, self.newPos[2]],
                              y=np.arange(len(self.data[self.newPos[0], :, self.newPos[2]])))
            self.pos[2] = self.newPos[2]
        self.posLabel.setText("Pos = " + str(self.pos))

    def xy_x_update(self):
        self.newPos[1] = int(round(self.xy_x_line.value()))
        self.y_line.setValue(self.newPos[1])
        self.updatePlots()

    def xy_y_update(self):
        self.newPos[0] = int(round(self.xy_y_line.value()))
        self.x_line.setValue(self.newPos[0])
        self.updatePlots()

    def x_update(self):
        self.newPos[0] = int(round(self.x_line.value()))
        self.xy_y_line.setValue(self.newPos[0])
        self.updatePlots()

    def y_update(self):
        self.newPos[1] = int(round(self.y_line.value()))
        self.xy_x_line.setValue(self.newPos[1])
        self.updatePlots()

    def z_update(self):
        self.newPos[2] = int(round(self.z_line.value()))
        self.updatePlots()

    def make2d(self):
        if (self.l_xz.getItem(1, 0) is not None):
            self.l_xz.removeItem(self.vb_xz_cut)
            self.l_yz.removeItem(self.vb_yz_cut)
            self.l.removeItem(self.vb_zcut)

    def make3d(self):
        if (self.l_xz.getItem(1, 0) is None):
            self.l_xz.addItem(self.vb_xz_cut, row=1, col=0)
            self.l_yz.addItem(self.vb_yz_cut, row=0, col=0)
            self.l.addItem(self.vb_zcut, row=1, col=1)

    def setData(self, newData):
        if (newData.ndim == 2):
            nx, ny = newData.shape
            newData = newData.reshape((nx, ny, 1))
            self.data = newData
            self.make2d()
        elif (newData.ndim == 3):
            nx, ny, nz = newData.shape
            if (nx == 1 or ny == 1 or nz == 1):
                self.make2d()
                if (nx == 1):
                    newData = np.transpose(newData, (1, 2, 0))
                elif (ny == 1):
                    newData = np.transpose(newData, (0, 2, 1))
            else:
                self.make3d()
            self.data = newData
        else:
            print("Can't convert data of shape ", str(newData.shape), " to 3 dimensional data.")
        
        bounds = self.data.shape
        self.xy_x_line.setBounds([0, bounds[1] - 1])
        self.xy_y_line.setBounds([0, bounds[0] - 1])
        self.x_line.setBounds([0, bounds[0] - 1])
        self.y_line.setBounds([0, bounds[1] - 1])
        self.z_line.setBounds([0, bounds[2] - 1])
        self.pos = np.array([0, 0, 0], dtype='int')
        self.newPos = np.array([0, 0, 0], dtype='int')
        self.updatePlots(force=True)
        self.sizeLabel.setText("[Nx, Ny, Nz] = " + str(self.data.shape))
        
        self.autoscaleAll()

    def autoscaleAll(self):
        self.vb_xcut.autoRange()
        self.vb_ycut.autoRange()
        self.vb_zcut.autoRange()
        self.vb_xy_cut.autoRange()
        self.vb_xz_cut.autoRange()
        self.vb_yz_cut.autoRange()
        self.hist.setLevels(np.min(np.min(self.data[:, :, self.pos[2]])), np.max(np.max(self.data[:, :, self.pos[2]])))
        
    def loadData(self):
        dialog = LoadDialog(parent=self)
        dialog.exec_()
        if (dialog.result() == QtGui.QDialog.Accepted):
            self.setData(dialog.data)


class LoadDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(LoadDialog, self).__init__(parent)

        vbox = QtGui.QVBoxLayout(self)
        
        self.setWindowTitle("Load File")

        ## File type combo box
        comboLayout = QtGui.QHBoxLayout()
        filetypeLabel = QtGui.QLabel("File type:", self)
        self.filetypeBox = QtGui.QComboBox(self)
        self.filetypeBox.addItem("Igor (.ibw)")
        self.filetypeBox.addItem("HDF5 (.h5)")
        self.filetypeBox.addItem("Numpy (.npy)")
        # Index of each file type
        self.IBW = 0
        self.HDF5 = 1
        self.NPY = 2
        self.filetypeBox.currentIndexChanged.connect(self.checkFileType)
        comboLayout.addWidget(filetypeLabel)
        comboLayout.addWidget(self.filetypeBox)
        vbox.addLayout(comboLayout)

        ## Data shape description
        dataShapeLayout = QtGui.QHBoxLayout()
        isInt = QtGui.QIntValidator()
        isInt.setBottom(0)
        xLabel = QtGui.QLabel("Nx:", self)
        self.nx = QtGui.QLineEdit(self)
        self.nx.setText("0")
        self.nx.setValidator(isInt)
        yLabel = QtGui.QLabel("Ny:", self)
        self.ny = QtGui.QLineEdit(self)
        self.ny.setText("0")
        self.ny.setValidator(isInt)
        zLabel = QtGui.QLabel("Nz:", self)
        self.nz = QtGui.QLineEdit(self)
        self.nz.setText("0")
        self.nz.setValidator(isInt)
        dataShapeLayout.addWidget(xLabel)
        dataShapeLayout.addWidget(self.nx)
        dataShapeLayout.addWidget(yLabel)
        dataShapeLayout.addWidget(self.ny)
        dataShapeLayout.addWidget(zLabel)
        dataShapeLayout.addWidget(self.nz)
        vbox.addLayout(dataShapeLayout)

        ## File name and load button
        fileLayout = QtGui.QHBoxLayout()
        self.filename = QtGui.QLineEdit(self)
        selectFile = QtGui.QPushButton("...")
        selectFile.clicked.connect(self.getFilename)
        fileLayout.addWidget(self.filename)
        fileLayout.addWidget(selectFile)
        vbox.addLayout(fileLayout)

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(self.checkFile)
        buttons.rejected.connect(self.reject)
        vbox.addWidget(buttons)

        self.setLayout(vbox)

        self.data = np.array([])

    def displayError(self, error):
        msg = QtWidgets.QMessageBox(parent=self)
        msg.setText(error)
        msg.exec()

    def checkFile(self):
        userfile = str(self.filename.text())
        if userfile != "":
            if os.path.isfile(userfile):
                self.data = np.load(userfile)
                self.accept()
            else:
                self.displayError("Could not find the file: " + userfile)
                print("Could not find file ", userfile)
        else:
            self.displayError("Please enter a file name!")

    def getFilename(self, bool):
        ind = self.filetypeBox.currentIndex()
        if (ind == self.NPY):
            loadFilter = "Numpy binary files (*.npy)"
        else:
            loadFilter = ""
        userfile, filefilter = QtGui.QFileDialog.getOpenFileName(parent=self, caption="Open File", filter=loadFilter)
        self.filename.setText(userfile)

    def checkFileType(self, ind):
        palette = QtGui.QPalette()
        if (ind != self.NPY):
            palette.setColor(QtGui.QPalette.Base, QtCore.Qt.white)
            palette.setColor(QtGui.QPalette.Text, QtCore.Qt.black)
            self.nx.setPalette(palette)
            self.ny.setPalette(palette)
            self.nz.setPalette(palette)
            self.nx.setEnabled(True)
            self.ny.setEnabled(True)
            self.nz.setEnabled(True)
        else:
            palette.setColor(QtGui.QPalette.Base, QtCore.Qt.lightGray)
            palette.setColor(QtGui.QPalette.Text, QtCore.Qt.darkGray)
            self.nx.setPalette(palette)
            self.ny.setPalette(palette)
            self.nz.setPalette(palette)
            self.nx.setEnabled(False)
            self.ny.setEnabled(False)
            self.nz.setEnabled(False)

    @staticmethod
    def getData(parent=None):
        dialog = LoadDialog(parent)
        dialog.exec_()
        return dialog.data

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        app = QtGui.QApplication(sys.argv)
        window = ImageTool()
        window.show()
        app.exec()
