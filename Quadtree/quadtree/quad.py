"""
    Quadtree implementation.
    
    Every Quad Node has four children, partitioning space accordingly based on NE, NW, 
    SW, SE quadrants. Each Node evenly divides quadrants and stores circles that are 
    wholly contained by its rectangular region. 
    
    Two or more identical circles can exist.
    
    Because the circles are two-dimensional, they may intersect two (or more) of the 
    subregions in the quadtree. Therefore, each circle is stored in the highest node in 
    the tree whose associated region fully encloses the circle.
    
    When the circles are large, this means the resulting quadtree might be skewed with 
    far too many circles stored in upper nodes. 
   
"""

import math
from adk.region import Region, X, Y

# each point (X,Y,RADIUS) represents a circle.
RADIUS=2

# Associated tuple position that declares whether circle cuts over multiple nodes.
MULTIPLE=4

# Each node can be subdivided into four quadrants.
NE = 0
NW = 1
SW = 2
SE = 3

def distance(p, pt):
    """Compute distance from p to pt."""
    if pt:
        return ((p[X] - pt[X])**2 + (p[Y] - pt[Y])**2) ** 0.5

def smaller2k(n):
    """
    Returns power of 2 which is smaller than n. Handles negative numbers.
    """
    if n == 0: return 0
    if n < 0:
        return -2**math.ceil(math.log2(-n))
    else:
        return 2**math.floor(math.log2(n))
    
def larger2k(n):
    """
    Returns power of 2 which is larger than n. Handles negative numbers.
    """
    if n == 0: return 0
    if n < 0:
        return -2**math.floor(math.log2(-n))
    else:
        return 2**math.ceil(math.log2(n))

def completelyContains(region, circle):
    """Determine if region completely contains circle, closed on min, open on max."""
    if circle[X] - circle[RADIUS] <  region.x_max: return False
    if circle[X] + circle[RADIUS] >= region.x_max: return False
    if circle[Y] - circle[RADIUS] <  region.y_min: return False
    if circle[Y] + circle[RADIUS] >= region.y_max: return False

    return True

def intersectsCircle(region, circle):
    """Returns True if circle intersects region, based on geometry. Be careful of open-ended regions."""
    rectOrigin = [ (region.x_min + region.x_max)//2, (region.y_min + region.y_max)//2]
    halfSize = [ (region.x_max - region.x_min)//2, (region.y_max - region.y_min)//2]
    distCenter = [ abs(circle[X] - rectOrigin[X]), abs(circle[Y] - rectOrigin[Y])]
    
    if distCenter[X] > circle[RADIUS] + halfSize[X] or distCenter[Y] > circle[RADIUS] + halfSize[Y]:
        return False 
    if distCenter[X] <= halfSize[X] or distCenter[Y] <= halfSize[Y]:
        return True 
    
    corner = [ distCenter[X] - halfSize[X], distCenter[Y] - halfSize[Y]]
    
    return (corner[X] ** 2 + corner[Y] ** 2) <= circle[RADIUS] ** 2
    # http://www.reddit.com/r/pygame/comments/2pxiha/rectanglar_circle_hit_detection
    

def defaultCollision(c1, c2):
    """Two circles intersect if distance between centers is between the sum and the difference of radii."""
    centerDistance = (c1[X] - c2[X])**2 + (c1[Y] - c2[Y])**2
    sumSquared = (c1[RADIUS]+c2[RADIUS])**2
    if centerDistance > sumSquared: return False
    return True
    

class QuadNode:
    
    def __init__(self, region):
        """Create QuadNode centered on origin of given region."""
        self.region = region
        self.origin = (region.x_min + (region.x_max - region.x_min)//2, region.y_min + (region.y_max - region.y_min)//2) 
        self.children = [None]*4
        self.circles = []
    
    def collide(self, circle):
        """Yield circles in leaf that intersect with circle."""
        
        # Circle must intersect
        if intersectsCircle (self.region, circle):
            # if we have circles, must check them
            for c in self.circles:
                if QuadTree.collision(c, circle):
                    yield c
            
            # If subquadrants, find quadrant(s) into which to check further 
            if self.children[NE] == None: return
            
            for q in self.quadrants(circle):
                for s in self.children[q].collide(circle):
                    yield s
 
    def add(self, circle):
        """Add circle to the QuadNode, subdividing as needed."""
        node = self
        while node:
            # Not part of this region
            if not intersectsCircle (node.region, circle):
                return False
        
            # Not yet subdivided? Then add to circles, subdividing once > 4
            if node.children[NE] == None:
                node.circles.append(circle)
                if len(node.circles) > 4:
                    node.subdivide()
                return True
            
            # Find quadrant(s) into which to add; if intersects two or more
            # then this node keeps it, otherwise we add to that child.
            quads = node.quadrants (circle)
            if len(quads) == 1:
                node = node.children[quads[0]]
            else:
                node.circles.append(circle)
                return True
            
        return False

    def remove(self, circle):
        """Remove circle from QuadNode. Does not adjust structure. Return True if updated information."""
        if self.circles != None:
            if circle in self.circles:
                idx = self.circles.index(circle)
                del self.circles[idx]
                return True
            
        return False

    def subdivide(self):
        """Add four children nodes to node and reassign existing points."""
        r = self.region
        self.children[NE] = QuadNode(Region(self.origin[X], self.origin[Y], r.x_max,        r.y_max))
        self.children[NW] = QuadNode(Region(r.x_min,        self.origin[Y], self.origin[X], r.y_max))
        self.children[SW] = QuadNode(Region(r.x_min,        r.y_min,        self.origin[X], self.origin[Y]))
        self.children[SE] = QuadNode(Region(self.origin[X], r.y_min,        r.x_max,        self.origin[Y]))
        
        # go through completely contained circles and try to push to lowest 
        # children. If intersect 2 or more quadrants then we must keep.
        update = self.circles
        self.circles = []
        for circle in update:
            quads = self.quadrants(circle)
            
            # If circle intersects multiple quadrants, must add to self, and mark
            # as MULTIPLE, otherwise only add to that individual quadrant 
            if len(quads) == 1:
                self.children[quads[0]].add(circle)
                circle[MULTIPLE] = False
            else:
                self.circles.append(circle)
                circle[MULTIPLE] = True 
    
    
    def quadrants(self, circle):
        """Determine quadrant(s) in which point exists."""
        quads = []
        if intersectsCircle(self.children[NE].region, circle): quads.append(NE)
        if intersectsCircle(self.children[NW].region, circle): quads.append(NW)
        if intersectsCircle(self.children[SW].region, circle): quads.append(SW)
        if intersectsCircle(self.children[SE].region, circle): quads.append(SE)
        return quads
    
    def quadrant(self, pt):
        """Determine quadrant in which point exists."""
        if pt[X] >= self.origin[X]:
            if pt[Y] >= self.origin[Y]:
                return NE
            else:
                return SE
        else:
            if pt[Y] >= self.origin[Y]:
                return NW
            else:
                return SW
     
    def preorder(self):
        """Pre-order traversal of tree rooted at given node."""
        yield self

        for node in self.children:
            if node:
                for n in node.preorder():
                    yield n

    def __str__(self):
        """toString representation."""
        return "[{} ({}): {},{},{},{}]".format(self.region, self.circles, self.children[NE], self.children[NW], self.children[SW], self.children[SE])

class QuadTree:

    # define default collision which can be replaced. Affects all QuadTree objects
    collision = defaultCollision

    def __init__(self, region):
        """
        Create QuadTree defined over existing rectangular region. Assume that (0,0) is
        the lower left coordinate and the half-length side of any square in quadtree
        is power of 2. If incoming region is too small, this expands accordingly.    
        """
        self.root = None
        self.region = region.copy()
        
        xmin2k = smaller2k(self.region.x_min)
        ymin2k = smaller2k(self.region.y_min)
        xmax2k = larger2k(self.region.x_max)
        ymax2k = larger2k(self.region.y_max)
        
        self.region.x_min = self.region.y_min = min(xmin2k, ymin2k)
        self.region.x_max = self.region.y_max = max(xmax2k, ymax2k)
        
    def add(self, circle):
        """Add circle to QuadTree."""
        if self.root is None:
            self.root = QuadNode(self.region)
            self.root.add(circle)
            return True
        
        return self.root.add (circle)
    
    def collide(self, circle):
        """Return collisions to circle within QuadTree."""
        if self.root is None:
            return iter([])
        
        return self.root.collide (circle)
    
    def remove(self, circle):
        """Remove circle should it exist in QuadTree."""
        node = self.root
        while node:
            quads = node.quadrants (circle)
            if len(quads) == 1:
                node = node.children[quads[0]]
            else:
                for i in range(len(node.circles)):
                    if node.circles[i] == circle:
                        del node.circles[i]
                        return True
    
        return False
    
    def __iter__(self):
        """Traverse elements in the tree."""
        if self.root:
            for e in self.root.preorder():
                yield e