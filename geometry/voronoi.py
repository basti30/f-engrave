import openvoronoi as ovd
# import ngc_writer
from math import (sqrt)

import time


def insert_polygon_points(vd, polygon):
    pts = []
    for p in polygon:
        pts.append(ovd.Point(p[0], p[1]))
    id_list = []
    print("inserting %d point-sites:" % len(pts))
    m = 0
    for p in pts:
        id_list.append(vd.addVertexSite(p))
        # print " ", m, " added vertex ", id_list[len(id_list) - 1]
        m += 1
    return id_list


def insert_polygon_segments(vd, id_list):
    j = 0
    print("inserting %d line-segments:" % len(id_list))
    for n in range(len(id_list)):
        n_nxt = n + 1
        if n == (len(id_list) - 1):
            n_nxt = 0
        # print " ", j, "inserting segment ", id_list[n], " - ", id_list[n_nxt]
        vd.addLineSite(id_list[n], id_list[n_nxt])
        j += 1


def modify_segments(segs):
    segs_mod = []
    for seg in segs:
        first = seg[0]
        last = seg[len(seg) - 1]
        assert (first[0] == last[0] and first[1] == last[1])
        seg.pop()
        seg.reverse()  # to get interior or exterior offsets
        segs_mod.append(seg)
        # drawSegment(myscreen, seg)
    return segs_mod


def insert_many_polygons(vd, segs):
    polygon_ids = []
    t_before = time.time()
    for poly in segs:
        poly_id = insert_polygon_points(vd, poly)
        polygon_ids.append(poly_id)
    t_after = time.time()
    pt_time = t_after - t_before

    t_before = time.time()
    for ids in polygon_ids:
        insert_polygon_segments(vd, ids)

    t_after = time.time()
    seg_time = t_after - t_before

    return [pt_time, seg_time]


def translate(segs, x, y):
    out = []
    for seg in segs:
        seg2 = []
        for p in seg:
            p2 = []
            p2.append(p[0] + x)
            p2.append(p[1] + y)
            seg2.append(p2)
        out.append(seg2)
    return out


class NgcWriter:
    """A basic G-Code writer, for testing purpose"""
    clearance_height = 20
    feed_height = 10
    feed = 200
    plunge_feed = 100
    metric = True
    scale = 1

    def __init__(self, filename="output.ngc"):
        self.filename = filename
        self.out = open(filename, 'w')

    def write(self, cmd):
        self.out.write("{}\n".format(cmd))

    def pen_up(self):
        self.write("G0 Z{}".format(self.feed_height))

    def xy_rapid_to(self, x, y):
        self.write("G0 X{} Y{}".format(x, y))

    def pen_down(self, z):
        self.write("G0 Z{}".format(z))

    def line_to(self, x, y, z):
        self.write("G1 X{} Y{} Z{} F{}".format(x, y, z, self.feed))


def printMedial(vd, scale):
    maw = ovd.MedialAxisWalk(vd.getGraph())
    toolpath = maw.walk()
    ngc = NgcWriter()
    for chain in toolpath:
        n = 0
        for move in chain:
            for point in move:
                if n == 0:  # don't draw anything on the first iteration
                    p = point[0]
                    zdepth = scale * point[1]
                    ngc.pen_up()
                    ngc.xy_rapid_to(scale * p.x, scale * p.y)
                    ngc.pen_down(z=-zdepth)
                else:
                    p = point[0]
                    z = point[1]
                    ngc.line_to(scale * p.x, scale * p.y, scale * (-z))
                n += 1
    return


def medial_axis(segs, clean=False):
    import sys

    # svg = "../samples/Hello_flattened2_rev.svg" if len(sys.argv) < 2 else sys.argv[1]
    # svgr = SvgReader(svg, error_threshold=.6)
    # svgr.parse()
    # svgr.centerPolys()

    # far = svgr.radius * 1.2
    far = 100.0
    n_bins = int(sqrt(1200))  # approx. sqrt(nr of sites)
    vd = ovd.VoronoiDiagram(far, n_bins)

    times = insert_many_polygons(vd, segs)
    print("all sites inserted: %d " % len(times))
    # print("all sites inserted.")
    print("VD check: %s" % vd.check())

    pi = ovd.PolygonInterior(True)
    vd.filter_graph(pi)
    ma = ovd.MedialAxis()
    vd.filter_graph(ma)

    printMedial(vd, 1)  # write ngc to output.ngc

    # vod.setVDText2(times)
    # vod.setAll()
