from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QPalette, QColor
import PyQt5

from pyvistaqt import QtInteractor
import pyvista as pv


import sys  # We need sys so that we can pass argv to QApplication
import os
os.environ["QT_API"] = "pyqt5"
import numpy as np
import random


from threaded_sampling import Cloudsampler
from threaded_surface_sampling import SurfaceCloudsampler



class ThreadManager(QtCore.QObject):
    #gui render instance
    plotfile = 'test_objects/stl/chair.stl'
    plotdir = 'C:/'
    mode = 0

    #signals
    signalStatus = QtCore.pyqtSignal(str)
    signalfiledir = QtCore.pyqtSignal(str)
    signalprogress = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)

        # Create a gui object.
        self.gui = MainGUIWindow()

        # sample point clouds in extra thread to free up gui
        # during heavy computational work
        self.csampler = Cloudsampler()
        self.csampler_thread = QtCore.QThread()
        self.csampler.moveToThread(self.csampler_thread)
        self.csampler_thread.start()

        # sample point clouds in extra thread to free up gui
        # during heavy computational work (surfacesamples)
        self.surfsampler = SurfaceCloudsampler()
        self.surfsampler_thread = QtCore.QThread()
        self.surfsampler.moveToThread(self.surfsampler_thread)
        self.surfsampler_thread.start()

        # Make any cross object connections.
        self._connectSignals()

        # show MainGUIWindow instance
        self.gui.show()

    def _connectSignals(self):
        #button select file connection
        self.gui.button_sel_file.clicked.connect(self.loadsinglefile)
        self.signalfiledir.connect(self.gui.plotmesh)

        #button select directory connection
        self.gui.button_sel_folder.clicked.connect(self.loaddir)
        self.gui.button_save_folder.clicked.connect(self.surfsampler.dofordir)

        #button_set_sampsize connection
        self.gui.button_set_sampsize.clicked.connect(self.setsampsize)

        # button_plot_samp starts sampling in another thread.
        # preparation to sample thousands of objects and
        # prepare for AI use while maintaining a working GUI
        #self.gui.button_plot_samp.clicked.connect(self.csampler.startWork)
        self.gui.button_save_sample.clicked.connect(self.csampler.savetotensfile)
        self.gui.button_plot_samp_cancel.clicked.connect(self.forcecsamplerReset)

        self.signalStatus.connect(self.gui.updateStatus)

        self.csampler.signalStatus.connect(self.gui.updateStatus)
        self.csampler.signaloutput.connect(self.gui.plotcloudsamp)
        self.csampler.signal_full_pc_out.connect(self.gui.plotcloud)
        
        self.parent().aboutToQuit.connect(self.forcecsamplerQuit)


        #button_plot_surf_samp test
        #self.gui.button_plot_surf_samp.clicked.connect(self.surfsampler.startWork)
        self.gui.button_plot_samp_cancel.clicked.connect(self.forcesurfsamplerReset)

        self.surfsampler.signalStatus.connect(self.gui.updateStatus)
        self.surfsampler.signaloutput.connect(self.gui.plotcloudsamp)
        self.surfsampler.signal_full_pc_out.connect(self.gui.plotcloud)
        self.surfsampler.signal_full_mesh_out.connect(self.gui.plotmesh)
        self.surfsampler.signal_progpercent_out.connect(self.gui.updateProgress)

        self.parent().aboutToQuit.connect(self.forcesurfsamplerQuit)


        #button_testmode
        self.gui.button_testmode.clicked.connect(self.setsampsize)
        

    def setsampsize(self):
        self.csampler.sampsize = int(self.gui.input_sampsize.text())
        self.surfsampler.sampsize = int(self.gui.input_sampsize.text())

        self.gui.button_testmode.clicked.disconnect()   
        if self.gui.box_vertexcloud.isChecked():
            self.mode = 0
        if self.gui.box_surfacecloud.isChecked():
            self.mode = 1
        if self.mode == 0:
            #self.gui.button_testmode.clicked.disconnect(self.surfsampler.startWork)
            self.gui.button_testmode.clicked.connect(self.csampler.startWork)
        elif self.mode == 1:
            #self.gui.button_testmode.clicked.disconnect(self.csampler.startWork)
            self.gui.button_testmode.clicked.connect(self.surfsampler.startWork)
        print(self.mode)

    def loadsinglefile(self):
        fname = QtWidgets.QFileDialog.getOpenFileNames(self.gui, 'open file')
        self.plotfile = str(fname[0][0])
        self.signalfiledir.emit(self.plotfile)
        self.csampler.plotfile = self.plotfile
        self.csampler.fixfile()
        self.surfsampler.plotfile = self.plotfile
        self.surfsampler.fixfile()

    def loaddir(self):
        folderpath = str(QtWidgets.QFileDialog.getExistingDirectory(self.gui, "Select Directory"))
        self.plotdir = folderpath #+ '/'
        self.surfsampler.plotdir = self.plotdir
        self.surfsampler.num_persps_per_obj = int(self.gui.input_perspnum.text())
        self.surfsampler.fixfilelist()
        #self.surfsampler.dofordir()
        #print(self.plotdir)

    # handle Vertex pointsampling thread
    def forcecsamplerReset(self):
        if self.csampler_thread.isRunning():
            self.csampler_thread.terminate()
            self.csampler_thread.wait()

            self.signalStatus.emit('force Reset')
            self.csampler_thread.start()

    def forcecsamplerQuit(self):
        if self.csampler_thread.isRunning():
            self.csampler_thread.terminate()
            self.csampler_thread.wait()

    # handle Surface pointsampling thread
    def forcesurfsamplerReset(self):
        if self.surfsampler_thread.isRunning():
            self.surfsampler_thread.terminate()
            self.surfsampler_thread.wait()

            self.signalStatus.emit('force Reset')
            self.surfsampler_thread.start()

    def forcesurfsamplerQuit(self):
        if self.surfsampler_thread.isRunning():
            self.surfsampler_thread.terminate()
            self.surfsampler_thread.wait()
    
        

        
        
class MainGUIWindow(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        # main/ real usable GUI

        #set windowsize
        self.setFixedSize(1000, 900)

        #meshplot frame with interactor
        self.frame_mp = QtWidgets.QFrame(self)
        self.frame_mp.setGeometry(100,20,500,250)
        vlayout_mp = QtWidgets.QVBoxLayout()
        self.plotter_mp = QtInteractor(self.frame_mp)
        vlayout_mp.addWidget(self.plotter_mp.interactor)
        vlayout_mp.setContentsMargins(0, 0, 0, 0)
        self.frame_mp.setLayout(vlayout_mp)

        #full PCplot frame with all points
        self.frame_pc = QtWidgets.QFrame(self)
        self.frame_pc.setGeometry(100,320,500,250)
        vlayout_pc = QtWidgets.QVBoxLayout()
        self.plotter_pc = QtInteractor(self.frame_pc)
        vlayout_pc.addWidget(self.plotter_pc.interactor)
        vlayout_pc.setContentsMargins(0, 0, 0, 0)
        self.frame_pc.setLayout(vlayout_pc)

        #sample PCplot frame with variable k
        self.frame_spc = QtWidgets.QFrame(self)
        self.frame_spc.setGeometry(100,620,500,250)
        vlayout_spc = QtWidgets.QVBoxLayout()
        self.plotter_spc = QtInteractor(self.frame_spc)
        vlayout_spc.addWidget(self.plotter_spc.interactor)
        vlayout_spc.setContentsMargins(0, 0, 0, 0)
        self.frame_spc.setLayout(vlayout_spc)

        #GUI Functions / Buttons
        #Plot and Inspect single files
        self.lab_inspectorlab = QtWidgets.QLabel('Display Mesh:', self)
        self.lab_inspectorlab.setGeometry(630,20,200,20)

        self.button_sel_file = QtWidgets.QPushButton('Select File', self)
        self.button_sel_file.setGeometry(650,70,100,25)
  
        
        #select sampletype of PointCloud
        self.lab_inspectorlab = QtWidgets.QLabel('Model Sampler Settings:', self)
        self.lab_inspectorlab.setGeometry(630,170,200,20)
        
        self.lab_sampkind = QtWidgets.QLabel('sampletype:', self)
        self.lab_sampkind.setGeometry(650,220,100,20)

        self.lab_vertexcloud = QtWidgets.QLabel('Vertices', self)
        self.lab_vertexcloud.setGeometry(750,220,100,20)
        
        self.box_vertexcloud = QtWidgets.QCheckBox(self)
        self.box_vertexcloud.setGeometry(800,220,100,20)

        self.lab_surfacecloud = QtWidgets.QLabel('Surface', self)
        self.lab_surfacecloud.setGeometry(850,220,100,20)

        self.box_surfacecloud = QtWidgets.QCheckBox(self)
        self.box_surfacecloud.setGeometry(900,220,100,20)


        #samplesize Option config
        self.lab_sampsize = QtWidgets.QLabel('samplesize:', self)
        self.lab_sampsize.setGeometry(650,270,100,20)
        
        self.input_sampsize = QtWidgets.QLineEdit(self)
        self.input_sampsize.setGeometry(750,270,70,20)

        self.button_set_sampsize = QtWidgets.QPushButton('Apply Settings', self)
        self.button_set_sampsize.setGeometry(850,268,100,25)
        

        #plot PointCloud Sample (also plots full pointcloud)
        self.lab_plotsth = QtWidgets.QLabel('Start / Stop Plot:', self)
        self.lab_plotsth.setGeometry(630,350,100,20)

        self.button_plot_samp_cancel = QtWidgets.QPushButton('STOP PLOTS', self)
        self.button_plot_samp_cancel.setGeometry(650,400,100,25)

        self.button_testmode = QtWidgets.QPushButton('PLOT', self)
        self.button_testmode.setGeometry(800,400,100,25)


        #save sample as pytorch tensor object
        self.lab_savesth = QtWidgets.QLabel('Save the Sampled Pointcloud as Tensor:', self)
        self.lab_savesth.setGeometry(630,450,200,20)
        
        self.button_save_sample = QtWidgets.QPushButton('Save', self)
        self.button_save_sample.setGeometry(650,500,100,25)


        #Conversion of Folders to Surfacesamples
        self.lab_conversionlab = QtWidgets.QLabel('Convert Folder to Dataset-Ready Surfaceasamples:', self)
        self.lab_conversionlab.setGeometry(630,620,250,20)

        self.lab_perspnumlab = QtWidgets.QLabel('Num of Perspectives:', self)
        self.lab_perspnumlab.setGeometry(650,670,210,20)
        
        self.input_perspnum = QtWidgets.QLineEdit(self)
        self.input_perspnum.setGeometry(800,670,70,20)
        self.input_perspnum.setText("1")

        self.button_sel_folder = QtWidgets.QPushButton('Select Folder', self)
        self.button_sel_folder.setGeometry(650,720,100,25)

        self.button_save_folder = QtWidgets.QPushButton('Convert', self)
        self.button_save_folder.setGeometry(800,720,100,25)

        self.lab_conversionlab = QtWidgets.QLabel('Progress:', self)
        self.lab_conversionlab.setGeometry(650,770,250,20)

        self.progbar_folderconv = QtWidgets.QProgressBar(self)
        self.progbar_folderconv.setGeometry(720,770,180,20)

       

        #status label
        self.lab_label_status = QtWidgets.QLabel('Status:', self)
        self.lab_label_status.setGeometry(650,850,100,20)
        
        self.label_status = QtWidgets.QLabel('', self)
        self.label_status.setGeometry(750,850,200,20)


    #update GUI functions, triggered by signals
    @QtCore.pyqtSlot(str)
    def updateStatus(self, status):
        self.label_status.setText(status)

    def updateProgress(self, value):
        self.progbar_folderconv.setValue(value)

    def plotmesh(self, filestr):
        self.plotter_mp.clear()
        self.plotter_mp.add_text("Mesh View", font_size=10)
        mesh = pv.read(filestr)
        self.plotter_mp.add_mesh(mesh, show_edges=True, color="#8cfaab")
        self.plotter_mp.reset_camera()

    def plotcloud(self, point_cloud):
        self.plotter_pc.clear()
        self.plotter_pc.add_text("PointCloud View", font_size=10)
        self.plotter_pc.add_mesh(point_cloud, render_points_as_spheres=True, color="#8cfaab")
        self.plotter_pc.reset_camera()

    def plotcloudsamp(self, point_cloud):
        self.plotter_spc.clear()
        self.plotter_spc.add_text("PointCloud Sample", font_size=10)
        self.plotter_spc.add_mesh(point_cloud, render_points_as_spheres=True, color="#8cfaab")
        self.plotter_spc.reset_camera()
    


if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')

    dark_palette = QPalette()

    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Base, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Button, QColor(70, 70, 70))
    dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(50, 200, 100))
    dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

    app.setPalette(dark_palette)

    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")


    example = ThreadManager(app)
    sys.exit(app.exec_())
