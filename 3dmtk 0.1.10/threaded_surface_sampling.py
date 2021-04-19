from PyQt5 import QtCore, QtWidgets
import sys
import random
import pyvista as pv
import torch
import dgl
import trimesh
import os
import time
import math


#sampling Pointclouds in a Background Thread
class SurfaceCloudsampler(QtCore.QObject):
    signalStatus = QtCore.pyqtSignal(str)
    signaloutput = QtCore.pyqtSignal(pv.PolyData)
    signal_full_pc_out = QtCore.pyqtSignal(pv.PolyData)
    signal_full_mesh_out = QtCore.pyqtSignal(str)
    signal_progpercent_out = QtCore.pyqtSignal(int)

    sampsize = 1000
    plotfile = 'test_objects/stl/chair.stl'
    plotdir = ''
    mesh = trimesh.load_mesh(plotfile)

    num_persps_per_obj = 1
    #sample = ((trimesh.sample.sample_surface_even(mesh, sampsize, radius = None))[0]) 

    
    sampcloud = []
    sampcl = pv.PolyData()

    file_paths = []


    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)

    @QtCore.pyqtSlot()        
    def startWork(self):
        ''' Test if GUI free while in permanent loop
        while True:
            print('stuck in loop')
        '''
        self.sampcloud = ((trimesh.sample.sample_surface_even(self.mesh, self.sampsize, radius = None))[0])
        self.sampcl = pv.PolyData(self.sampcloud)
        self.signaloutput.emit(self.sampcl)
        self.signal_full_pc_out.emit(self.sampcl)
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
        print(nodepostens)
        print(len(nodepostens))
        knn_g_edges = dgl.knn_graph(nodepostens, k = 20)
        print(knn_g_edges)
        torch.save(nodepostens.clone(), 'nodepostens.pt')
        torch.save(knn_g_edges.clone(), 'knn_g_edges.pt')
        self.signalStatus.emit('Tensor files saved')

        
    def fixfile(self):
        self.mesh = trimesh.load_mesh(self.plotfile)
        #self.sampcloud = pv.PolyData(self.mesh_points)


    def fixfilelist(self):
        self.file_paths = []
        filenames = [f for f in os.listdir(self.plotdir) if (f.endswith('.off') or f.endswith('.stl'))]
        for each in filenames:
            self.file_paths.append(self.plotdir + '/' + each)
        print(self.file_paths)
        #self.dofordir()


    def dofordir(self):
        savedir = 'converted/'
        currprogress = 0
        tsf_nr = 0
        perspectives_per_object = self.num_persps_per_obj
        for filepath in self.file_paths:
            for countvar in range(0,perspectives_per_object):
                currprogress += 1
                outprog = int(((currprogress / len(self.file_paths))*100) / perspectives_per_object)
                initialsize = 2048
                mesh = trimesh.load_mesh(filepath) 
                sample = ((trimesh.sample.sample_surface_even(mesh, initialsize, radius = None))[0])

                if len(sample) != 2048:
                    fstmul = (2048 / len(sample)) * 0.92
                    initialsize = int(initialsize * fstmul)
                    sample = ((trimesh.sample.sample_surface_even(mesh, initialsize, radius = None))[0])
                
                while len(sample) < 2048:
                    initialsize = int(initialsize * 1.02)
                    sample = ((trimesh.sample.sample_surface_even(mesh, initialsize, radius = None))[0])

                i = 0
                indices = []
                rightlensample = []
                
                if len(sample) != 2048:
                    while i < 2048:
                        rand_pt_idx = random.randint(0, len(sample)-1)
                        if rand_pt_idx not in indices:
                            indices.append(rand_pt_idx)
                            i += 1
                        elif rand_pt_idx in indices:
                            pass
                    for each in indices:
                        rightlensample.append(sample[each])       
                elif len(sample) == 2048:
                    rightlensample = sample

                cloud = trimesh.points.PointCloud(rightlensample)
                pccenter = cloud.centroid
                for each in rightlensample:
                    each[0] = each[0] - pccenter[0]
                    each[1] = each[1] - pccenter[1]
                    each[2] = each[2] - pccenter[2]


                maxdist = 0
                for each in rightlensample:
                    dist = math.sqrt((each[0]**2)+(each[1]**2)+(each[2]**2))
                    if dist >= maxdist:
                        maxdist = dist
                print('old pointcloudsize (maxdist): ', maxdist)

                for each in rightlensample:
                    each[0] = each[0] / maxdist
                    each[1] = each[1] / maxdist
                    each[2] = each[2] / maxdist

                cloud2 = trimesh.points.PointCloud(rightlensample)
                pccenter2 = cloud2.centroid
                print('new pointcloud center: ', pccenter2)

                maxdist = 0
                for each in rightlensample:
                    dist = math.sqrt((each[0]**2)+(each[1]**2)+(each[2]**2))
                    if dist >= maxdist:
                        maxdist = dist
                print('new pointcloudsize (maxdist): ', maxdist)
                #print(rightlensample)

                ###### 90 DEGREE STEP Z ROTATION ###################################################
                '''
                possible_transforms = [[[0,-1,0,0],[1,0,0,0],[0,0,1,0],[0,0,0,1]],
                                       [[-1,0,0,0],[0,-1,0,0],[0,0,1,0],[0,0,0,1]],
                                       [[0,1,0,0],[-1,0,0,0],[0,0,1,0],[0,0,0,1]],
                                       [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]]
                tsf_nr += 1
                tsf_nr = tsf_nr % 4
                print(tsf_nr)
                '''

                ###### 1 DEGREE STEP Z ROTATION ###################################################
                radmul = 0.017453293
                yaw = random.randint(0,360)
                rotzmat = [[round(math.cos(yaw * radmul),4), round(-(math.sin(yaw * radmul)),4), 0, 0],
                           [round(math.sin(yaw * radmul),4), round(math.cos(yaw * radmul),4), 0, 0],
                           [0,  0,  1,  0],
                           [0,  0,  0,  1]]
                print(rotzmat)

                

                cloud2.apply_transform(rotzmat)

                
                pccenter2 = cloud2.centroid
                print('new pointcloud center: ', pccenter2)

                rightlensample2 = []
                for each in cloud2:
                    rightlensample2.append(each)
                    #print(each)

                



                point_cloud = pv.PolyData(sample)
                point_cloud_rls = pv.PolyData(rightlensample2)

                self.signal_full_mesh_out.emit(filepath)
                self.signal_full_pc_out.emit(point_cloud)
                self.signaloutput.emit(point_cloud_rls)
                self.signalStatus.emit('Done Sampling')
                self.signal_progpercent_out.emit(outprog)

                converted = torch.FloatTensor(rightlensample2)
                filename = os.path.splitext(os.path.basename(str(filepath)))[0]
                print('filename: ', filename, '\noriginal sampsize: ', len(sample), '\nnum of points: ', len(converted), '\n')
                saveat = savedir + filename + '_' + str(countvar) + '.pt'
                torch.save(converted.clone(), saveat)

        
            

    
    
