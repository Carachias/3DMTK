from PyQt5 import QtCore, QtWidgets
import sys
import random
import pyvista as pv
import torch
import dgl



#sampling Pointclouds in a Background Thread
class Cloudsampler(QtCore.QObject):
    signalStatus = QtCore.pyqtSignal(str)
    signaloutput = QtCore.pyqtSignal(pv.PolyData)
    signal_full_pc_out = QtCore.pyqtSignal(pv.PolyData)

    plotfile = 'test_objects/stl/chair.stl'
    mesh = pv.read(plotfile)
    mesh_points = mesh.points
    point_cloud = pv.PolyData(mesh_points)
    sampsize = 1000


    sampcloud = []
    sampcl = pv.PolyData()


    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)

    @QtCore.pyqtSlot()        
    def startWork(self):
        ''' Test if GUI free while in permanent loop
        while True:
            print('stuck in loop')
        '''
        i = 0
        indices = []
        self.sampcloud = []
        sampcl = pv.PolyData()

        while i < self.sampsize:
            rand_pt_idx = random.randint(0, len(self.mesh_points)-1)
            if rand_pt_idx not in indices:
                indices.append(rand_pt_idx)
                i += 1
            elif rand_pt_idx in indices:
                pass

        for each in indices:
            self.sampcloud.append(self.mesh_points[each])
        print(self.sampcloud)
        self.sampcl = pv.PolyData(self.sampcloud)
        self.signaloutput.emit(self.sampcl)
        self.signal_full_pc_out.emit(self.point_cloud)
        self.signalStatus.emit('Done Sampling')


    def savetotensfile(self):
        listtenstosave = []
        for each in self.sampcloud:
            vertex = []
            vertex.append(float(each[0]))
            vertex.append(float(each[1]))
            vertex.append(float(each[2]))
            listtenstosave.append(vertex)
        nodepostens = torch.tensor(listtenstosave)
        #print(nodepostens)
        print(len(nodepostens))
        knn_g_edges = dgl.knn_graph(nodepostens, k = 20)
        print(knn_g_edges)
        torch.save(nodepostens.clone(), 'nodepostens.pt')
        torch.save(knn_g_edges.clone(), 'knn_g_edges.pt')
        self.signalStatus.emit('Tensor files saved')

        



    def fixfile(self):
        self.mesh = pv.read(self.plotfile)
        self.mesh_points = self.mesh.points
        self.point_cloud = pv.PolyData(self.mesh_points)
        

    
    
