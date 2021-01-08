# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SaveAttributes
                                 A QGIS plugin
 This plugin saves the attribute of the selected vector layer as a csv file. 
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-10-30
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Ahmet Fırat Karaoğlu & Metehan Ergen
        email                : Metehan Ergen: metehan.ergenn@gmail.com & Ahmet Fırat Karaoğlu: karaoglu@email.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""


import timeit

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox #
from qgis.core import *
from osgeo import ogr, osr, gdal
import os
from PyQt5.QtCore import QVariant
from qgis.utils import iface

from .great_distance import *


# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .save_attributes_dialog import SaveAttributesDialog
import os.path


class SaveAttributes:
    """
    
        QGIS Plugin Implementation.
    """

    def __init__(self, iface):
        """
            Constructor.

            :param iface: An interface instance that will be passed to this class
                which provides the hook by which you can manipulate the QGIS
                application at run time.
            :type iface: QgsInterface
        
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = iface.mapCanvas()
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SaveAttributes_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Save Attributes')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """

        Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SaveAttributes', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """

        Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """

        Create the menu entries and toolbar icons inside the QGIS GUI.
        
        """

        icon_path = ':/plugins/save_attributes/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u''),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """

        Removes the plugin menu item and icon from QGIS GUI.
        
        """
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Save Attributes'),
                action)
            self.iface.removeToolBarIcon(action)

    def select_output_file(self):
        """"

        Select output file

        """
        filename, _filter = QFileDialog.getSaveFileName(
            self.dlg, 
            "Select output file ",
            "", 
            '*.csv')
        self.dlg.lineEdit.setText(filename)
        
    def error_msg(self,text):
        """

        Required error message for user
        
        """
        QMessageBox.warning(self.dlg.show(), self.tr("Save attributes Message"), self.tr(str(text)),QMessageBox.Ok)
    
    def input_shp_file(self):
        """

        Selecting input shp file
        
        """
        self.shpPath, self._filter = QFileDialog.getOpenFileName(self.dlg, "Select input shp file","", 'ESRI Shapefiles(*.shp *.SHP);; GeoJSON (*.GEOJSON *.geojson);; Geography Markup Language(*.GML)')
        try:
            self.shp = ogr.Open(self.shpPath)
            self.layer = self.shp.GetLayer(0)
            self.name = self.layer.GetName()
            self.layerDef = self.layer.GetLayerDefn()
            self.control = False
            if self.layerDef.GetGeomType() == ogr.wkbLineString:
                self.dlg.lineEdit_input_shp.setText(self.shpPath)
                self.dlg.comboBox_id.clear()
                self.control = True
                self.dlg.label_wrong_input.setText("")
                self.dlg.checkBox.setEnabled(False)
            elif self.layerDef.GetGeomType() == ogr.wkbPoint:
                self.dlg.comboBox_id.clear()
                self.dlg.lineEdit_input_shp.setText(self.shpPath)
                self.fieldNames = [self.layerDef.GetFieldDefn(i).name for i in range(self.layerDef.GetFieldCount())] 
                self.dlg.comboBox_id.addItems(self.fieldNames)
                self.control = True
                self.dlg.checkBox.setEnabled(True)
                self.dlg.label_wrong_input.setText("")

            elif self.layerDef.GetGeomType() == ogr.wkbPolygon:  
                self.dlg.lineEdit_input_shp.setText(self.shpPath)
                self.dlg.comboBox_id.clear()
                self.control = True
                self.dlg.label_wrong_input.setText("")
                self.dlg.checkBox.setEnabled(False)
                
            else:
                self.dlg.label_wrong_input.setText('Input layer could only be "point" or "linestring"') #No need anymore because of the polygon area calculating
        except:
            self.dlg.label_wrong_input.setText("Please enter a suitable input file")

    
    """def poly_area(self,geom):

        llayer = QgsVectorLayer(self.dlg.lineEdit_input_shp.text(), 
                                        self.name, 
                                        "ogr")
        self.fields = llayer.fields().names()
        self.field2Add = ["Area", "Peri"]
                        
        llayer.startEditing()
        dp = llayer.dataProvider()

        for name in self.field2Add:
            if not name in self.fields:
                dp.addAttributes([QgsField(name,QVariant.Double)])

                llayer.updateFields() 
                self.areas = [feat for feat in llayer.getFeatures()]

                if len(self.areas) > 0:
                    sCrs = llayer.sourceCrs()
                    self.measure = QgsDistanceArea()
                    self.measure.setEllipsoid(sCrs.ellipsoidAcronym())

                    for i in self.areas:
                        self.geom = i.geometry()
                        self.attr1 = self.measure.measureArea(self.geom)
                        self.attr2 = self.measure.measurePerimeter(self.geom)

                        i["Area"] = self.attr1
                        #i["Peri"] = self.attr2
                        llayer.updateFeature(i)

                    llayer.updateFields()
                    llayer.commitChanges()

    """

    def transform_to_epsg_4326(self, point):
        if self.canvas.mapSettings().destinationCrs().authid() != 'EPSG:4326':
            crs_src = self.canvas.mapSettings().destinationCrs()
            crs_dest = QgsCoordinateReferenceSystem(4326)
            xform = QgsCoordinateTransform(crs_src, crs_dest, QgsCoordinateTransformContext())
            point.transform(xform)
            return point
        else:
            return point
        
    
    # createShp is supposed to create a new shapefile.
    def createShp(self, input_line, costs, out_shp, sr):

        """

        createShp is supposed to create a new shapefile

        """
        
        driver = ogr.GetDriverByName('Esri Shapefile')
        ds = driver.CreateDataSource(out_shp)
        srs = osr.SpatialReference()
        srs.ImportFromProj4(sr)
        layer = ds.CreateLayer('mst', srs, ogr.wkbLineString)
        layer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
        layer.CreateField(ogr.FieldDefn('cost', ogr.OFTReal))
        defn = layer.GetLayerDefn()
        
        for e,i in enumerate(zip(input_line, costs)):
            feat = ogr.Feature(defn)
            feat.SetField('id', e)
            feat.SetField('cost', i[1])
        
            # Geometry
            feat.SetGeometry(i[0])    
            layer.CreateFeature(feat)
        
        ds = layer = defn = feat = None


    def run(self):
        
        start = timeit.default_timer()
        """

        Run method that performs all the real work
        
        """
        
        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = SaveAttributesDialog()
            #self.dlg.pushButton.clicked.connect(self.select_output_file)
            
            self.dlg.pb_select_layer.clicked.connect(self.input_shp_file)
            

       

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            if self.control == True:
                # Do something useful here - delete the line containing pass and
                # substitute with your code.
                
                file_path = self.dlg.lineEdit_input_shp.text()
                # Open the shp file
                # Second argument tell whether to read (0, default), or to update (1)
                ds = ogr.Open(file_path,0)
                
                if ds is None:
                    sys.exit('Could not open {0}.'.format(file_path))
                
                # Obtain the layer
                lyr = ds.GetLayer()
                
                # Runs, but does not create a new field-------------
                # lyr.CreateField(ogr.FieldDefn('x', ogr.OFTReal))
                # lyr.CreateField(ogr.FieldDefn('y', ogr.OFTReal))
                # # Runs, but does not create a new field-------------
                
                if (lyr.GetGeomType() == ogr.wkbPoint): #wkb: well known binary
                    type_of_layer = "point"
                elif(lyr.GetGeomType() == ogr.wkbLineString):
                    type_of_layer = "line"
                elif(lyr.GetGeomType() == ogr.wkbPolygon):
                    type_of_layer = "polygon"
                    
                       
                vlayer = QgsVectorLayer(self.dlg.lineEdit_input_shp.text(), 
                                        self.name, 
                                        "ogr")
  
                idFieldName = self.dlg.comboBox_id.currentText()

                #num_features = lyr.GetFeatureCount()
                #print("Number of features: ", num_features)
                
                if not vlayer.isValid():
                    print("Layer failed to load!")
                else:
                    QgsProject.instance().addMapLayer(vlayer)

                # If there is a point layer input
                # =======================================================================
                if(type_of_layer == "point"):
                    fields = vlayer.fields().names()
                    field2Add = ["x","y"]
                    
                    vlayer.startEditing()
                    dp = vlayer.dataProvider()

                    for name in field2Add:
                        if not name in fields:
                            dp.addAttributes([QgsField(name,QVariant.Double)])

                    vlayer.updateFields() 
    
                    points = [feat for feat in vlayer.getFeatures()]

                    if len(points) > 1:
                        for feat in points:
                            geom = feat.geometry()
                            x = geom.asPoint().x()
                            y = geom.asPoint().y()

                            feat['x'] = x
                            feat['y'] = y
                            vlayer.updateFeature(feat)
                        vlayer.commitChanges()
                            
                        minDistance = 9999999999
                        maxDistance = 0
                        for x,point in enumerate(points):
                            point_geom = point.geometry() #Input geometry
                            for y,pointSearched in enumerate(points):
                                pointSearched_geom = pointSearched.geometry()
                                if not x == y and not x > y: 
                                    distance = point_geom.distance(pointSearched_geom)
                                    if distance > maxDistance:
                                        maxDistance = distance
                                        maxDistFeatures = [point,pointSearched]
                                    if distance < minDistance and not distance <= 0:
                                        minDistance = distance
                                        minDistFeatures = [point,pointSearched]
                        
                        if len(maxDistFeatures) > 1 and len(minDistFeatures) > 1:
                            
                            if self.dlg.checkBox.isChecked():
                                lineLayer = QgsVectorLayer("MultiLineString", "lines","memory",crs = vlayer.sourceCrs())
                                lineLayer.startEditing()
                                pr = lineLayer.dataProvider()
                                pr.addAttributes([QgsField('length', QVariant.Double)])
                                lineLayer.updateFields()
                                
                                
                                for i in range(len(maxDistFeatures)-1):
                                    lineStart = maxDistFeatures[i].geometry().get()
                                    lineEnd = maxDistFeatures[i+1].geometry().get()
                                    segMax = QgsFeature()
                                    segMax.setGeometry(QgsGeometry.fromPolyline([lineStart, lineEnd]))
                                    segMax.setAttributes([maxDistance])
                                    
                                for i in range(len(minDistFeatures)-1):
                                    lineStart = minDistFeatures[i].geometry().get()
                                    lineEnd = minDistFeatures[i+1].geometry().get()
                                    segMin = QgsFeature()
                                    segMin.setGeometry(QgsGeometry.fromPolyline([lineStart, lineEnd]))
                                    segMin.setAttributes([minDistance])
                                
                                pr.addFeatures( [ segMax,segMin ] )
                                lineLayer.updateFeature(segMax)
                                lineLayer.updateFeature(segMin)
                                

                                lineLayer.updateExtents()
                                QgsProject.instance().addMapLayers([lineLayer])
                                lineLayer.commitChanges()

                                    
                            else:
                                lineLayer = QgsVectorLayer("MultiLineString", "lines","memory",crs = vlayer.sourceCrs())
                                lineLayer.startEditing()
                                pr = lineLayer.dataProvider()
                                pr.addAttributes([QgsField('startPoint_ID', QVariant.String),QgsField('endPoint_ID', QVariant.String),QgsField('length', QVariant.Double)])
                                lineLayer.updateFields()
                                
                                
                                for i in range(len(maxDistFeatures)-1):
                                    lineStart = maxDistFeatures[i].geometry().get()
                                    lineEnd = maxDistFeatures[i+1].geometry().get()
                                    segMax = QgsFeature()
                                    segMax.setGeometry(QgsGeometry.fromPolyline([lineStart, lineEnd]))
                                    segMax.setAttributes([str(int(maxDistFeatures[i][idFieldName])),str(int(maxDistFeatures[i+1][idFieldName])) ,maxDistance])
                                    
                                for i in range(len(minDistFeatures)-1):
                                    lineStart = minDistFeatures[i].geometry().get()
                                    lineEnd = minDistFeatures[i+1].geometry().get()
                                    segMin = QgsFeature()
                                    segMin.setGeometry(QgsGeometry.fromPolyline([lineStart, lineEnd]))
                                    segMin.setAttributes( [str(int(minDistFeatures[i][idFieldName])) ,str(int(minDistFeatures[i+1][idFieldName])),minDistance] )
                                
                                pr.addFeatures( [ segMax,segMin ] )
                                lineLayer.updateFeature(segMax)
                                lineLayer.updateFeature(segMin)
                                

                                lineLayer.updateExtents()
                                QgsProject.instance().addMapLayers([lineLayer])
                                lineLayer.commitChanges()

                        
                    else:
                        self.error_msg("There is no enough features !")
                        self.dlg.label_wrong_input.setText("Please enter a suitable input file")
                        
                # If there is a line layer input
                # =======================================================================
                elif type_of_layer == "line":
                    fields = vlayer.fields().names()
                    fields2add = ["minDist","realDist", "azimuth" , "revAzimuth"]
                    vlayer.startEditing()
                    dp = vlayer.dataProvider()

                    for name in fields2add:
                        if not name in fields:
                            dp.addAttributes([QgsField(name,QVariant.Double)])
                    vlayer.updateFields()
                    lines = [feat for feat in vlayer.getFeatures()]

                    if len(lines) > 0:
                        sCrs = vlayer.sourceCrs()
                        d = QgsDistanceArea()
                        d.setEllipsoid(sCrs.ellipsoidAcronym())
                        for line in lines:
                            geom = line.geometry()
                            realDist = d.measureLine(geom.asMultiPolyline()[0])
                            startPoint = geom.constGet()[0][0]
                            endPoint = geom.constGet()[0][-1]
                            minline = QgsFeature()
                            minline.setGeometry(QgsGeometry.fromPolyline([startPoint,endPoint]))
                            minDist = d.measureLine(minline.geometry().asPolyline())

                            #Azimuth Calculation

                            #sp = self.transform_to_epsg_4326(startPoint)
                            #ep = self.transform_to_epsg_4326(endPoint)
                            calculus = great_distance(
                            start_longitude=startPoint.x(),
                            start_latitude=startPoint.y(),
                            end_longitude=endPoint.x(),
                            end_latitude=endPoint.y())
                            
                            line["minDist"] = minDist
                            line["realDist"] = realDist
                            
                            line["azimuth"] = (calculus[1]) #
                            line["revAzimuth"] = (calculus[2]) #
                            

                            

                            
                            
                            vlayer.updateFeature(line)
                        
                        vlayer.updateFields()
                        vlayer.commitChanges()



                        
                        
                        # Detect Polygons and create a layer from them
                        # =======================================================================
                        exp = QgsExpression( "\"minDist\"=0" )
                        request = QgsFeatureRequest(exp)
                        layer = iface.activeLayer()

                        polyLayer = QgsVectorLayer("Polygon", "polygons","memory",crs = vlayer.sourceCrs())
                        pr = polyLayer.dataProvider()
                        pr.addAttributes([QgsField('id', QVariant.Int)])
                        polyLayer.updateFields()

                        for idx,feature in enumerate(vlayer.getFeatures(request)):
                            points = []
                            geom = feature.geometry().constGet()[0]
                            for point in geom:
                                points.append(QgsPointXY(point))
                            polygonFeature = QgsFeature()
                            polygonFeature.setGeometry(QgsGeometry.fromPolygonXY([points]))
                            polygonFeature.setAttributes([idx])
                            pr.addFeatures([polygonFeature])

                        polyLayer.updateExtents()
                        QgsProject.instance().addMapLayers([polyLayer])
                        polyLayer.commitChanges()

                        #self.poly_area(polyLayer)


                        # Create the shortest line layer and show on QGIS interface
                        # =======================================================================
                        if len(lines) == 1:
                            shortestLineLayer = QgsVectorLayer("MultiLineString", "shortest line","memory",crs = vlayer.sourceCrs())
                            shortestLinePr = shortestLineLayer.dataProvider()
                            shortestLinePr.addAttributes([QgsField('id', QVariant.Int),QgsField('length', QVariant.Double)])
                            shortestLineLayer.updateFields()

                            minline.setAttributes([1,minDist])
                            shortestLinePr.addFeatures([minline])

                            shortestLineLayer.updateExtents()
                            QgsProject.instance().addMapLayers([shortestLineLayer])
                            shortestLineLayer.commitChanges()
    

                # If there is a polygon layer input (area and perimeter calculation)
                # =======================================================================
                elif  type_of_layer == "polygon":

                    fields = vlayer.fields().names()
                    field2Add = ["Area", "Perimeter"]
                    
                    vlayer.startEditing()
                    dp = vlayer.dataProvider()

                    for name in field2Add:
                        if not name in fields:
                            dp.addAttributes([QgsField(name,QVariant.Double)])

                    vlayer.updateFields() 
    
                    areas = [feat for feat in vlayer.getFeatures()]


                    if len(areas) > 0:
                        sCrs = vlayer.sourceCrs()
                        measure = QgsDistanceArea()
                        measure.setEllipsoid(sCrs.ellipsoidAcronym())
                        

                        for i in areas:
                            geom = i.geometry()
                            attr1 = measure.measureArea(geom)
                            attr2 = measure.measurePerimeter(geom)

                            i["Area"] = attr1
                            i["Perimeter"] = attr2
                            vlayer.updateFeature(i)

                        vlayer.updateFields()
                        vlayer.commitChanges()
            else:
                self.error_msg("Please select a valid shapefile location !")

        stop = timeit.default_timer()
        print('Time: ', stop - start)
        