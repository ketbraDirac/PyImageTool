import os
import sys
from PyQt5 import QtWidgets, QtGui, QtCore
# from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import numpy as np


# The ImageTool object
# Subclasses QMainWindow

class ImageTool(QtWidgets.QMainWindow):
    def __init__(self, parent=None, data=None):
        super(ImageTool, self).__init__(parent)

        # Window title
        self.setWindowTitle("Image Tool")
        self.setGeometry(50, 50, 800, 600)

        # Menu bar
        file = self.menuBar().addMenu("File")
        view = self.menuBar().addMenu("View")

        load_action = QtWidgets.QAction("&Load File", self)
        load_action.setShortcut("Ctrl+O")
        load_action.setStatusTip('Open a dataset')
        load_action.triggered.connect(self.load_data)
        exit_action = QtWidgets.QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+W")
        exit_action.setStatusTip("Exit")
        exit_action.triggered.connect(self.close)
        autoscale_action = QtWidgets.QAction("&Autoscale All", self)
        autoscale_action.setShortcut("Ctrl+A")
        autoscale_action.setStatusTip('Autoscale all axes')
        autoscale_action.triggered.connect(self.autoscale_all)

        file.addAction(load_action)
        view.addAction(autoscale_action)
        file.addAction(exit_action)

        # Create the main graphics view
        self.view = pg.GraphicsView()
        self.setCentralWidget(self.view)
        self.main_graphics_view = pg.GraphicsLayout(border=[100, 100, 100])
        self.view.setCentralItem(self.main_graphics_view)

        # Start laying out the widgets and info
        # Information bar
        self.posLabel = self.main_graphics_view.addLabel("Pos = [0, 0, 0]")
        self.sizeLabel = self.main_graphics_view.addLabel("[Nx, Ny, Nz] = [0, 0, 0]")
        self.main_graphics_view.nextRow()
        # Layout for the x plot, xz image plot, and z plot
        self.l_xz = self.main_graphics_view.addLayout(border=[100, 100, 100])
        # Make the x cut plot
        self.vb_x_cut = self.l_xz.addViewBox()
        self.x_cut = pg.PlotDataItem()
        self.vb_x_cut.addItem(self.x_cut)
        # Make the xz image plot
        self.l_xz.nextRow()
        self.vb_xz_cut = self.l_xz.addViewBox()
        self.img_xz_cut = pg.ImageItem()
        self.vb_xz_cut.addItem(self.img_xz_cut)
        # Make the z plot
        self.vb_z_cut = self.main_graphics_view.addViewBox()
        self.z_cut = pg.PlotDataItem()
        self.vb_z_cut.addItem(self.z_cut)
        # Make the xy layout
        self.main_graphics_view.nextRow()
        self.l_xy = self.main_graphics_view.addLayout(border=None)
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
        self.l_yz = self.main_graphics_view.addLayout(border=[100, 100, 100])
        # Make the yz image plot
        self.vb_yz_cut = self.l_yz.addViewBox()
        self.img_yz_cut = pg.ImageItem()
        self.vb_yz_cut.addItem(self.img_yz_cut)
        # Make the y plot
        self.vb_y_cut = self.l_yz.addViewBox()
        self.ycut = pg.PlotDataItem()
        self.vb_y_cut.addItem(self.ycut)

        # Make crosshairs
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
        self.vb_x_cut.addItem(self.x_line)
        self.vb_y_cut.addItem(self.y_line)
        self.vb_z_cut.addItem(self.z_line)

        self.xy_y_line.sigPositionChanged.connect(self.xy_y_update)
        self.xy_x_line.sigPositionChanged.connect(self.xy_x_update)
        self.x_line.sigPositionChanged.connect(self.x_update)
        self.y_line.sigPositionChanged.connect(self.y_update)
        self.z_line.sigPositionChanged.connect(self.z_update)

        self.data = None

        # Set data
        if data is None:
            # Make random data
            noise = 0.1 * np.random.random((51, 101, 201))
            x = np.linspace(-1, 1, 51)
            y = np.linspace(-1, 1, 101)
            z = np.linspace(-1, 1, 201)
            x_grid, y_grid, z_grid = np.meshgrid(x, y, z, indexing='ij')
            data = (x_grid - 0.5) ** 2 + (y_grid + 0.5) ** 2 + z_grid ** 2 + noise
            self.set_data(data)
        else:
            self.set_data(data)

        self.update_plots()

    # Control crosshairs with keyboard
    def keyPressEvent(self, event):
        if type(event) == QtGui.QKeyEvent:
            if event.key() == QtCore.Qt.Key_Up:
                new_val = self.xy_x_line.value() + 1
                self.xy_x_line.setValue(new_val)
                self.y_line.setValue(new_val)
            elif event.key() == QtCore.Qt.Key_Left:
                new_val = self.xy_y_line.value() - 1
                self.xy_y_line.setValue(new_val)
                self.x_line.setValue(new_val)
            elif event.key() == QtCore.Qt.Key_Down:
                new_val = self.xy_x_line.value() - 1
                self.xy_x_line.setValue(new_val)
                self.y_line.setValue(new_val)
            elif event.key() == QtCore.Qt.Key_Right:
                new_val = self.xy_y_line.value() + 1
                self.xy_y_line.setValue(new_val)
                self.x_line.setValue(new_val)
            event.accept()
        else:
            super(ImageTool, self).keyPressEvent(event)

    def update_plots(self, force=False):
        if self.pos[0] != self.newPos[0] or force:
            self.img_yz_cut.setImage(self.data[self.newPos[0], :, :])
            self.ycut.setData(x=self.data[self.newPos[0], :, self.newPos[2]],
                              y=np.arange(len(self.data[self.newPos[0], :, self.newPos[2]])))
            self.z_cut.setData(self.data[self.newPos[0], self.newPos[1], :])
            self.pos[0] = self.newPos[0]
        if self.pos[1] != self.newPos[1] or force:
            self.img_xz_cut.setImage(self.data[:, self.newPos[1], :])
            self.x_cut.setData(self.data[:, self.newPos[1], self.newPos[2]])
            self.z_cut.setData(self.data[self.newPos[0], self.newPos[1], :])
            self.pos[1] = self.newPos[1]
        if self.pos[2] != self.newPos[2] or force:
            self.img_xy_cut.setImage(self.data[:, :, self.newPos[2]])
            self.x_cut.setData(self.data[:, self.newPos[1], self.newPos[2]])
            self.ycut.setData(x=self.data[self.newPos[0], :, self.newPos[2]],
                              y=np.arange(len(self.data[self.newPos[0], :, self.newPos[2]])))
            self.pos[2] = self.newPos[2]
        self.posLabel.setText("Pos = " + str(self.pos))

    def xy_x_update(self):
        self.newPos[1] = int(round(self.xy_x_line.value()))
        self.y_line.setValue(self.newPos[1])
        self.update_plots()

    def xy_y_update(self):
        self.newPos[0] = int(round(self.xy_y_line.value()))
        self.x_line.setValue(self.newPos[0])
        self.update_plots()

    def x_update(self):
        self.newPos[0] = int(round(self.x_line.value()))
        self.xy_y_line.setValue(self.newPos[0])
        self.update_plots()

    def y_update(self):
        self.newPos[1] = int(round(self.y_line.value()))
        self.xy_x_line.setValue(self.newPos[1])
        self.update_plots()

    def z_update(self):
        self.newPos[2] = int(round(self.z_line.value()))
        self.update_plots()

    def make2d(self):
        if self.l_xz.getItem(1, 0) is not None:
            self.l_xz.removeItem(self.vb_xz_cut)
            self.l_yz.removeItem(self.vb_yz_cut)
            self.main_graphics_view.removeItem(self.vb_z_cut)

    def make3d(self):
        if self.l_xz.getItem(1, 0) is None:
            self.l_xz.addItem(self.vb_xz_cut, row=1, col=0)
            self.l_yz.addItem(self.vb_yz_cut, row=0, col=0)
            self.main_graphics_view.addItem(self.vb_z_cut, row=1, col=1)

    def set_data(self, new_data):
        if new_data.ndim == 2:
            nx, ny = new_data.shape
            new_data = new_data.reshape((nx, ny, 1))
            self.data = new_data
            self.make2d()
        elif new_data.ndim == 3:
            nx, ny, nz = new_data.shape
            if nx == 1 or ny == 1 or nz == 1:
                self.make2d()
                if nx == 1:
                    new_data = np.transpose(new_data, (1, 2, 0))
                elif ny == 1:
                    new_data = np.transpose(new_data, (0, 2, 1))
            else:
                self.make3d()
            self.data = new_data
        else:
            print("Can't convert data of shape ", str(new_data.shape), " to 3 dimensional data.")

        bounds = self.data.shape
        self.xy_x_line.setBounds([0, bounds[1] - 1])
        self.xy_y_line.setBounds([0, bounds[0] - 1])
        self.x_line.setBounds([0, bounds[0] - 1])
        self.y_line.setBounds([0, bounds[1] - 1])
        self.z_line.setBounds([0, bounds[2] - 1])
        self.pos = np.array([0, 0, 0], dtype='int')
        self.newPos = np.array([0, 0, 0], dtype='int')
        self.update_plots(force=True)
        self.sizeLabel.setText("[Nx, Ny, Nz] = " + str(self.data.shape))

        self.autoscale_all()

    def autoscale_all(self):
        self.vb_x_cut.autoRange()
        self.vb_y_cut.autoRange()
        self.vb_z_cut.autoRange()
        self.vb_xy_cut.autoRange()
        self.vb_xz_cut.autoRange()
        self.vb_yz_cut.autoRange()
        self.hist.setLevels(np.min(np.min(self.data[:, :, self.pos[2]])), np.max(np.max(self.data[:, :, self.pos[2]])))

    def load_data(self):
        dialog = LoadDialog(parent=self)
        dialog.exec_()
        if dialog.result() == QtWidgets.QDialog.Accepted:
            self.set_data(dialog.data)


class LoadDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(LoadDialog, self).__init__(parent)

        v_box = QtWidgets.QVBoxLayout(self)

        self.setWindowTitle("Load File")

        # File type combo box
        combo_layout = QtWidgets.QHBoxLayout()
        filetype_label = QtWidgets.QLabel("File type:", self)
        self.filetype_box = QtWidgets.QComboBox(self)
        self.filetype_box.addItem("Igor (.ibw)")
        self.filetype_box.addItem("HDF5 (.h5)")
        self.filetype_box.addItem("Numpy (.npy)")
        # Index of each file type
        self.IBW = 0
        self.HDF5 = 1
        self.NPY = 2
        self.filetype_box.currentIndexChanged.connect(self.check_file_type)
        self.filetype_box.currentIndexChanged.connect(self.check_file_type)
        combo_layout.addWidget(filetype_label)
        combo_layout.addWidget(self.filetype_box)
        v_box.addLayout(combo_layout)

        # Data shape description
        data_shape_layout = QtWidgets.QHBoxLayout()
        is_int = QtGui.QIntValidator()
        is_int.setBottom(0)
        x_label = QtWidgets.QLabel("Nx:", self)
        self.nx = QtWidgets.QLineEdit(self)
        self.nx.setText("0")
        self.nx.setValidator(is_int)
        y_label = QtWidgets.QLabel("Ny:", self)
        self.ny = QtWidgets.QLineEdit(self)
        self.ny.setText("0")
        self.ny.setValidator(is_int)
        z_label = QtWidgets.QLabel("Nz:", self)
        self.nz = QtWidgets.QLineEdit(self)
        self.nz.setText("0")
        self.nz.setValidator(is_int)
        data_shape_layout.addWidget(x_label)
        data_shape_layout.addWidget(self.nx)
        data_shape_layout.addWidget(y_label)
        data_shape_layout.addWidget(self.ny)
        data_shape_layout.addWidget(z_label)
        data_shape_layout.addWidget(self.nz)
        v_box.addLayout(data_shape_layout)

        # File name and load button
        file_layout = QtWidgets.QHBoxLayout()
        self.filename = QtWidgets.QLineEdit(self)
        selectFile = QtWidgets.QPushButton("...")
        selectFile.clicked.connect(self.getFilename)
        file_layout.addWidget(self.filename)
        file_layout.addWidget(selectFile)
        v_box.addLayout(file_layout)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(self.check_file)
        buttons.rejected.connect(self.reject)
        v_box.addWidget(buttons)

        self.setLayout(v_box)

        self.data = np.array([])

    def display_error(self, error):
        msg = QtWidgets.QMessageBox(parent=self)
        msg.setText(error)
        msg.exec()

    def check_file(self):
        userfile = str(self.filename.text())
        if userfile != "":
            if os.path.isfile(userfile):
                self.data = np.load(userfile)
                self.accept()
            else:
                self.display_error("Could not find the file: " + userfile)
                print("Could not find file ", userfile)
        else:
            self.display_error("Please enter a file name!")

    def getFilename(self, bool):
        ind = self.filetype_box.currentIndex()
        if ind == self.NPY:
            load_filter = "Numpy binary files (*.npy)"
        else:
            load_filter = ""
        userfile, filefilter = QtWidgets.QFileDialog.getOpenFileName(parent=self, caption="Open File", filter=load_filter)
        self.filename.setText(userfile)

    def check_file_type(self, ind):
        palette = QtGui.QPalette()
        if ind != self.NPY:
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
    def get_data(parent=None):
        dialog = LoadDialog(parent)
        dialog.exec_()
        return dialog.data


# Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        app = QtWidgets.QApplication(sys.argv)
        window = ImageTool()
        window.show()
        app.exec()
