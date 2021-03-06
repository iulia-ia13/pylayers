import pylayers.util.geomutil as geu
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
#from imposm.parser import OSMParser
import networkx as nx
import numpy as np
import pdb

# classes that handle the OSM data file format.
class Way(object):
    """ 
    
    A Way is a polyline or a Polycon (if closed)

    typ : 0 Polygon
          1 LineString

    """
    def __init__(self,refs,tags,coords):
        self.refs  = refs
        self.tags = tags
        N = len(refs)
        p = np.zeros((2, N))
        self.valid = True
        for k, nid in enumerate(refs):
            try: 
                p[0, k] = coords.xy[nid][0]
                p[1, k] = coords.xy[nid][1]
            except:
                self.valid=False
                break
        # closed way of open way
        if self.valid:
            if (N>=4) & (refs[0]==refs[-1]):
                self.shp = geu.Polygon(p)
                self.typ = 0
            else:
                self.shp = geu.LineString(p)
                self.typ = 1

    def __repr__(self):
        st = ''
        st = st + str(self.tags) + ':' + str(self.refs) 
        return(st)

    def show(self,fig=[],ax=[]):
        """
        """
        fig,ax = self.shp.plot(fig=fig,ax=ax)
        return(fig,ax)

class Coords(object):
    """
    """
    cpt = 0
    latlon = {}
    xy = {}
    minlon = 1000
    maxlon = -1000
    minlat = 1000
    maxlat = -1000

    def __repr__(self):
        st = ''
        for k in self.xy:
            st = st + str(k)+ ':' + str(self.xy[k])+'\n' 
        st = st+ 'Ncoords = '+ str(len(self.xy))+'\n'
        return(st)

    def clean(self):
        self.cpt = 0 
        self.latlon={}
        self.xy = {}
        self.minlon =1000
        self.maxlon =-1000
        self.minlat =1000
        self.maxlat =-1000

    def coords(self, coords):
        # callback method for coords
        for osmid, lon, lat in coords:
            self.latlon[osmid] = np.array([lon, lat])
            # find extrema
            self.minlon = min(lon,self.minlon)
            self.maxlon = max(lon,self.maxlon)
            self.minlat = min(lat,self.minlat)
            self.maxlat = max(lat,self.maxlat)

            self.cpt += 1
        self.boundary=np.array([self.minlat,self.minlon,self.maxlat,self.maxlon])

    def cartesian(self):
        """ Convert Latitude/Longitude in cartesian 
        
        Returns
        -------

        m : Basemap converter


        Notes
        -----

        The transformation is centered on the mean of latitude and longitude 

        """
        bd = self.boundary
        lon_0 = (bd[1]+bd[3])/2.
        lat_0 = (bd[0]+bd[2])/2.

        m = Basemap(llcrnrlon=bd[1]-0.01, llcrnrlat=bd[0]-0.01,
                    urcrnrlon=bd[3]+0.01, urcrnrlat=bd[2]+0.01,
                resolution='i', projection='cass', lon_0=lon_0, lat_0=lat_0)

        for id in self.latlon:
            x, y = m(self.latlon[id][0], self.latlon[id][1])
            self.xy[id]  = np.array([x,y])
        
        return(m)

class Nodes(object):
    """
    """

    node = {}
    cpt = 0

    def nodes(self,nodes):
        """  parse tagged nodes
        """
        for osmid,tags,coords in nodes:
            self.node[osmid] = {}
            self.node[osmid]['tags'] = tags
            self.node[osmid]['lonlat'] = coords
            lon = coords[0]
            lat = coords[1]
            self.cpt += 1

    def clean(self):       
        self.node= {}
        self.cpt = 0

class Ways(object):
    """

    Attributes
    ----------

    w
    way
    cpt 

    Methods
    -------

    ways
    eval
    show

    """
    w = {}
    way = {}
    cpt = 0

    def ways(self, ways):
        """ 
            general callback function 
        """
        for osmid, tags, refs in ways:
                self.w[osmid] = (refs,tags)
                self.cpt += 1

    def clean(self):
        self.w = {}
        self.way = {}
        self.cpt = 0

    def building(self, ways):
        """ 
            building callback function 
        """
        for osmid, tags, refs in ways:
            if 'building' in tags:
                self.w[osmid] = (refs,tags)
                self.cpt += 1
    
    def eval(self,coords):
        """
            convert into a Way object 
        """
        for osmid in self.w:
            refs = self.w[osmid][0]
            tags = self.w[osmid][1]
            away =  Way(refs,tags,coords)
            if away.valid:
                self.way[osmid] = away
    
    def show(self,fig=[],ax=[],typ=2):
        """ show all way

        Parameters
        ----------

        fig : figure
        ax  : axe
        typ : 0|1|2 (default)

        """
        if fig==[]:
            fig = plt.figure()
        elif ax==[]:
            ax = fig.gca()

        for b in self.way:
            if typ==0:
                if self.way.typ==0:
                    fig,ax = self.way[b].shp.plot(fig=fig,ax=ax)
            if typ==1:
                if self.way.typ==1:
                    fig,ax = self.way[b].shp.plot(fig=fig,ax=ax)
            if typ==2:
                fig,ax = self.way[b].shp.plot(fig=fig,ax=ax)

        plt.axis('scaled')
        return(fig,ax)

    def showold(self,fig=[],ax=[]):
        """ show ways
        """
        if fig==[]:
            fig = plt.figure()
        elif ax==[]:
            ax = fig.gca()

        for b in self.way:
            tags  = self.way[b].tags
            if ('building' in tags) | ('buildingpart' in tags):
                print "buildingpart found"
                try:
                    poly  = self.way[b].shp
                    if 'building:roof:colour' in tags:
                        col = '#'+tags['building:roof:colour']
                    else:
                        col = '#abcdef'
                    fig, ax = poly.plot(fig=fig, ax=ax,color=col)
                except:
                    print "building: ",b," is not a polygon"
        plt.axis('scaled')
        return(fig,ax)

class Relations(object):
    relation = {}
    cpt = 0
    def relations(self,rels):
        for osmid,tags,member in rels:
                self.relation[osmid]={}
                self.relation[osmid]['tags']=tags
                self.relation[osmid]['members']=member
                self.cpt = self.cpt+1
    def clean(self):       
        self.relation= {}
        self.cpt = 0

class FloorPlan(nx.DiGraph):
    """
    FloorPlan class

    """

    def __init__(self,rootid,coords,nodes,ways,relations):
        nx.DiGraph.__init__(self)
        self.rootid=rootid
        self.coords = coords
        self.nodes = nodes
        self.ways = ways
        self.relations = relations

    def __repr__(self):

        st = str(self.rootid)+'\n'
        levels = nx.neighbors(self,self.rootid)
        st = st + '---'+'\n' 
        for l in levels:
            nw = len(nx.neighbors(self,l))
            st = st + str(l)+' : '+ str(nw) + '\n'
        return(st)



    def build(self,typ,eid):
        """
        
        Notes : recursive construction 

        """
        if typ=='relation':
            tags = self.relations.relation[eid]['tags']
            members  =  self.relations.relation[eid]['members']
        if typ=='way':
            tags = self.ways.way[eid].tags
            members  =  self.ways.way[eid].refs
        if typ=='node':
            try:
                tags = self.nodes.node[eid]['tags']
            except:
                tags = None
            members = None

        self.add_node(eid,tags=tags,type=typ)
        if members is not None:
            for m in members:
                if typ=='relation':
                    eidn = m[0]
                    typn = m[1]
                if typ=='way':
                    eidn = m
                    typn = 'node'

                self.add_edge(eid,eidn)
                #self = self.build(typ=typn,eid=eidn)
                self.build(typ=typn,eid=eidn)


    def show(self,nid=None,fig=[],ax=[]):
        """
        show the floorplan
        """
        if fig==[]:
            fig = plt.figure()
        elif ax==[]:
            ax = fig.gca()

        if nid ==None:
            nid = self.rootid
        nb = nx.neighbors(self,nid)
        for k in nb:
            #print k,self.node[k]['type'],self.node[k]['tags']
            if self.node[k]['type']=='way':
                fig,ax = self.ways.way[k].show(fig=fig,ax=ax)
            else:
                fig,ax = self.show(k,fig=fig,ax=ax)
        return fig,ax

def osmparse(filename,typ='floorplan',verbose=False,c=True,n=True,w=True,r=True):
    """

    Parameters
    ----------

    typ : string 
        floorplan | building 
    verbose : boolean
        default : False
    c : boolean 
    n : boolean
    w : boolean 
    r : boolean 

    Returns
    -------

    coords : 
    nodes  : 
    ways   : 
    relations :

    """

    if c: 
        coords = Coords()
        coords.clean()
        coords_parser = OSMParser(concurrency=4, coords_callback=coords.coords)
        if verbose:
            print "parsing coords"

        coords_parser.parse(filename)
        m = coords.cartesian()

        if verbose:
            print str(coords.cpt)
    else:
        coords = None

    if n:    
        nodes = Nodes()
        nodes.clean()
        nodes_parser = OSMParser(concurrency=4, nodes_callback=nodes.nodes)

        if verbose:
            print "parsing nodes"

        nodes_parser.parse(filename)

        if verbose:
            print str(nodes.cpt)
    else:
        nodes = None

    if w:    
        ways = Ways()
        ways.clean()
        if typ=='building':
            ways_parser = OSMParser(concurrency=4, ways_callback=ways.building)
        if typ=='floorplan':    
            ways_parser = OSMParser(concurrency=4, ways_callback=ways.ways)
        if verbose:
            print "parsing ways"
        ways_parser.parse(filename)
    
        if verbose:
            print str(ways.cpt)
    
        # convert lat,lon in cartesian  
        ways.eval(coords)
    else:
        ways = None


    if r:    
        relations = Relations()
        relations.clean()
        relations_parser = OSMParser(concurrency=4,relations_callback=relations.relations)

        if verbose:
            print "parsing relations"
        relations_parser.parse(filename)
        
        if verbose:
            print str(relations.cpt)
    else:
        relations = None

    return coords,nodes,ways,relations,m


def extract(alat,alon,fileosm,fileout):
    """

    Parameters
    ----------
    alat : array of latitude (1xn)
    alon : array of longitude (1xn)
    fileosm : source osm file 
    filout  : output osm file  

    Returns
    -------

    m : Basemap oject for coordinates conversion

    """
    latmax = alat.max()
    latmin = alat.min()
    lonmax = alon.max()
    lonmin = alon.min()
    lon_0=(lonmax+lonmin)/2
    lat_0=(latmax+latmin)/2

    command = 'osmconvert -b='+str(lonmin)+','\
            + str(latmin)+','+str(lonmax)+','\
            + str(latmax)+' '+fileosm +' > '+ fileout+'.osm'
    print command
    os.system(command)

    m = Basemap(llcrnrlon=lonmin,llcrnrlat=latmin,urcrnrlon=lonmax,urcrnrlat=latmax,
            resolution='i',projection='cass',lon_0=lon_0,lat_0=lat_0)

    return(m) 

def getbdg(fileosm,m):
    """ get building from osm file 

    Parameters 
    ----------

    fileosm : string 
    m : Basemap object 

    Returns
    -------

    zone : list of Polygon  

    """

    coords,nodes,ways,relation,m = osmparse(fileosm,typ='building')
    zone = []
    for w in ways.way:
        zone.append(Polygon(p))
    return(zone)

def buildingsparse(filename):
    """
    """
    coords,nodes,ways,relations,m = osmparse(filename)
    for bid in relations.relation:
        tags = relations.relation[bid]['tags']
        if tags['type']=='building':
            print "Constructing Indoor building ", bid
            bdg = FloorPlan(bid,coords,nodes,ways,relations)
            bdg.build(typ='relation',eid=bid)
    return bdg,m

