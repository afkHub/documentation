GMT456 GROUP 2 INTRO
======================
Authors
--------
Ahmet Fırat Karaoğlu : karaoglu@email.com  
Metehan Ergen : metehan.ergenn@gmail.com  

Hello everyone! We have contributed new features to a QGIS plugin called "save_attributes". You may find a brief information about the plugin below,  

Interface
----------   
.. figure:: /image/GUI.png

You could select the shapefile from the interface (Input layer part). And there will be 3 main cases,

Case 1
^^^^^^^^
  If the input layer geometry is line; the plugin will compute the shortest and real distance among features, azimuth and reverse azimuth between lines' start points and end points. And also draw the shortest line with its length. See below,  
.. figure:: /image/line_1feat.jfif
.. figure:: /image/lines_attr.jfif
|br| 
  If there is more than one feature on layer. It will also show the features which could possibly be a polygon.    
.. figure:: /image/line_mult.jfif
.. figure:: /image/azimuth.png

Case 2
^^^^^^^^^^
  If the input layer is point. It will check whether feature number is greater than 2. If it is the case, it  will calculate the minimum and maxiumum distannce among all points and draw the lines related to them. See below,      
.. figure:: /image/minmax.jfif
.. figure:: /image/point_attr.jfif

Case 3
^^^^^^^^^^^^^
  If the input layer is polygon, the plugin computes the area and perimeter of the poligons and show in the table with inserting.
.. figure:: /image/area-peri.png



|br| 
|br| 
|br| 
Note: We used this to be able to add our university logo to the GUI: https://gis.stackexchange.com/questions/381661/image-adding-problem-to-qgis-plugin-gui-with-qt-designer (You may need to run the "compile.bat" file in the folder according to you for the logo.)


			 
.. |br| raw:: html

  <br/>
