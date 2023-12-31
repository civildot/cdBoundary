# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_fileio.ipynb.

# %% auto 0
__all__ = ['FileIO']

# %% ../nbs/01_fileio.ipynb 3
import os
import pathlib

import fiona
from fiona import Geometry, Feature, Properties
from shapely.geometry import shape, mapping

from .boundary import ConcaveHull

# %% ../nbs/01_fileio.ipynb 7
class FileIO(ConcaveHull):

    def __init__(self):

        self.triangles = dict()
        self.tedges = list()
        self.elengths = list()
        self.maxtriangles = 0
        self.points = list()
        self.crs = None
        self.driver = None
        self.schema = None
        self.hull = None
        

    def file2points(self, infile:str, inlayer: str=None):

        ''' 
        Reads a file with a format supported by Fiona. Extracts all the points
        and add it to the point list.

            Parameters:
                infile (str)  : The file name
                inlayer (str) : The layer in the file where applicable
    
            Returns:
                None
        
        Todo: Provide option to breakdown LineStrings and Polygon
              to points. Do I need to check for point duplication?
              Easy, but will require a new dependency, `rtree`. 
                  
               def file2points(self, infile:str, inlayer: str=None, 
                               allgeometries: bool=False):
        '''
        
        self.infile = infile
        
        with fiona.open(infile, layer=inlayer) as source:
            self.crs = source.crs
            self.driver = source.driver
            self.schema = source.schema
            for feat in source:
                pt = shape(feat.geometry)
                if pt.geom_type == 'Point':
                    if pt.has_z:
                        self.points.append([pt.x, pt.y, pt.z])
                    else:
                        self.points.append([pt.x, pt.y])
                elif pt.geom_type == 'MultiPoint':
                    for item in list(pt.geoms):
                        if item.has_z:
                            self.points.append([item.x, item.y, item.z])
                        else:
                            self.points.append([item.x, item.y])
                    

    def write2file(self, outfile: str=None, outlayer: str=None, 
                   driver:str = None, crs: str=None, 
                   perc: float=None, tol: float=None):
                       
        '''
         Write the concave hull polygon to a file. 
        
                Parameters:
                    outfile (str) : The file name of the output file. If not specified
                                    it will be named `concave_hull`  
                    outlayer (str): The name of the layer in the output file where
                                    applicable  
                    driver (str)  : See table above on possible driver options
                                    Only drivers with `w` in the mode can be used.
                                    Drivers other than the 'mainstream' my vary in
                                    success.  
                    crs (str)     : the coordinate reference system in WKT format.
                                    Not essential  
                    perc (float)  : Will calculate the concave hull using this
                                    percentile on the triangle edges. See the
                                    `estimate` method in `ConcaveHull`.  
                    tol (float)   : Will calculate the concave hull using this
                                    length tolerance. See the `calculatehull` method
                                    in `ConcaveHull`.  
    
                Returns:
                     None
        '''

        if perc is not None:
            self.calculatehull(tol=fch.estimate(perc=perc))
        elif tol is not None:
            self.calculatehull(tol=tol)
        elif self.hull is None and perc is None and tol is None:
            self.calculatehull(tol=fch.estimate())

        if driver is not None and driver != self.driver:
            drvchange = True
            self.driver = driver
        else:
            drvchange = False

        if crs is not None:
            self.crs = crs

        # Any other drivers to ad?
        gisdrivers = ['ESRI Shapefile',
                      'GPKG',
                      'GeoJSON',
                      'OpenFileGDB']
                       
        geom = Geometry.from_dict(mapping(self.hull))              
        if self.driver in gisdrivers:
            self.schema = {'geometry': 'Polygon', 
                           'properties': {'id': 'int',
                                          'Area': 'float',
                                          'Perimeter': 'float',
                                          'Vertices': 'int'}}
            props = dict()
            props['id'] = 1
            props['Area'] = round(self.hull.area, 3)
            props['Perimeter'] = round(self.hull.length, 3)
            props['Vertices'] = len(self.boundary_points())
        else:
            self.schema['geometry'] = 'Polygon'
            props = dict()
            for key, item in self.schema['properties'].items():
                props[key] = None
        rec = Feature(geometry=geom, properties=Properties.from_dict(props))

        if outfile is None and drvchange:
            print('Please provide an output file name.')
        elif outfile is None:
            path = os.path.abspath(self.infile)
            (dirname, filename) = os.path.split(path)
            # Get extension from the infile name
            fext = pathlib.Path(filename).suffix
            outname = 'concave_hull'+fext
            outfile = os.path.join(dirname, outname)

        if outlayer is None:
            outlayer = 'concave_hull'

        with fiona.open(outfile, 'w', layer=outlayer, schema=self.schema,
                        driver=self.driver, crs=self.crs) as sink:
            sink.write(rec)

