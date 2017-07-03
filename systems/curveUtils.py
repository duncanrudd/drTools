import pymel.core as pmc
import drTools.core.coreUtils as coreUtils

#
#
#

def curveBetweenNodes(start=None, end=None, numCVs=4, name='', degree=3):
    '''
    Makes a  nurbs curve between two nodes

    '''
    # Validation of args
    startPos, endPos = coreUtils.getStartAndEnd(start, end)

    if not startPos or not endPos:
        return 'curveBetweenNodes: Cannot determine start and end points'

    points = coreUtils.pointsAlongVector(start=startPos, end=endPos, divisions=(numCVs-1))

    crv = curveThroughPoints(positions=points, name=name, degree=degree)

    return crv
#
#
#

def curveThroughPoints(positions=None, name='', degree=3, bezier=0):
    if not positions:
        positions = [pmc.xform(p, q=1, ws=1, t=1) for p in pmc.selected()]

    if len(positions) < (degree+1):
        return 'Please supply at least 4 points'

    # create the curve
    numKnots = degree + len(positions) - 1
    knots = [0 for i in range(degree)]
    for i in range(numKnots-(degree*2)):
        knots.append(i+1)
    knotsMax = knots[-1]
    for i in range(degree):
        knots.append(knotsMax+1)

    crv = pmc.curve(p=positions, k=knots, d=degree, name='%s_CRV' % name)
    return crv
#
#
#

def bindCurve(crv=None):
    '''
    Creates a joint for each cv in the supplied or selected curve
    performs a smooth bind on the curve to the joints
    returns a list of the newly created joints

    '''
    # Validation of args
    if not crv:
        if len(pmc.selected()) == 1:
            crv = pmc.selected()[0]
        else:
            return 'bindCurve: Please supply or select a nurbs curve'

    jointList = []

    cvs = crv.getCVs(space='world')

    for cv in range(len(cvs)):
        pmc.select(None)
        j = pmc.joint(p=cvs[cv], name='%s_%s_JNT' %(crv, cv+1))
        jointList.append(j)

    pmc.skinCluster(jointList, crv, tsb=1, name='%s_SKN' % crv)

    return jointList

#
#
#

def connectCurve(crv=None):
    '''
    Creates a locator for each CV in crv
    connects the position of each CV to the worldPosition of its corresponding locatorShape
    returns a list of the newly created locators
    '''
    # Validation of args
    if not crv:
        if len(pmc.selected()) == 1:
            crv = pmc.selected()[0]
        else:
            return 'connectCurve: Please supply or select a nurbs curve'

    locList = []

    cvs = crv.getCVs(space='world')
    crvShape = pmc.listRelatives(crv, c=1, s=1)[0]

    for cv in range(len(cvs)):
        l = pmc.spaceLocator(name='%s_%s_LOC' %(crv.name(), cv+1))
        l.t.set(cvs[cv])
        locShape = pmc.listRelatives(l, c=1, s=1)[0]
        locShape.worldPosition[0].connect(crvShape.controlPoints[cv])
        locList.append(l)

    return locList

#
#
#

def nodesAlongCurve(crv=None, numNodes=6, name='', followAxis='x', upAxis='y', upNode=None, upVec=None, follow=1):
    '''
    creates a motionPath node for each in numNodes and connects its parameter to the supplied curve
    attaches an empty group to each motionpath node
    returns a dictionary with keys for the motionPath nodes and the groups along the curve as well as the rootGrp
    upVec can be passed as an attribute eg translation which worldUpVector of motionpath node can be connected to
    '''
    # Validation of args
    if not crv:
        if len(pmc.selected()) == 1:
            crv = pmc.selected()[0]
        else:
            return 'nodesAlongCurve: Please supply or select a nurbs curve'

    invertFront, invertUp = 0, 0
    if '-' in followAxis:
        invertFront = 1
        followAxis = followAxis[-1]
    if '-' in upAxis:
        invertUp = 1
        upAxis = upAxis[-1]

    axisDict = {'x': 0, 'y': 1, 'z': 2}
    upDict = {'x': (1.0, 0.0, 0.0), 'y': (0.0, 1.0, 0.0), 'z': (0.0, 0.0, 1.0)}

    returnDict={'mpNodes':[], 'grps':[]}

    for i in range( numNodes ):
        num = str(i+1).zfill(2)
        n = pmc.group(empty=1, name='%s_%s_GRP' % (name, num))

        mp = pmc.createNode('motionPath', name='%s_%s_MP' % (name, num))
        mp.fractionMode.set(1)
        mp.follow.set(follow)
        mp.frontAxis.set(axisDict[followAxis])
        if invertFront:
            mp.inverseFront.set(1)
        mp.upAxis.set(axisDict[upAxis])
        if invertUp:
            mp.inverseUp.set(1)
        mp.worldUpVector.set(upDict[upAxis])
        if upNode:
            mp.worldUpType.set(2)
            upNode.worldMatrix[0].connect(mp.worldUpMatrix)
        crv.worldSpace[0].connect(mp.geometryPath)

        # Manually connect up the position
        mp.allCoordinates.connect(n.t)
        if follow:
            mp.rotate.connect(n.r)

        if numNodes != 1:
            mp.uValue.set((1.0 / (numNodes-1))*i)
        else:
            mp.uValue.set(0.5)

        returnDict['mpNodes'].append(mp)
        returnDict['grps'].append(n)

    return returnDict
#
#
#

def nodesAtCurvePoints(crv=None, name='', followAxis='x', upAxis='y', upNode=None, upVec=None, follow=1):
    if not crv and len(pmc.selected()) == 1:
        crv = pmc.selected()[0]
        cvs = crv.getCVs(space='world')
        print cvs
    else:
        return 'nodesAtCurvePoints: please provide a curve'
    
    invertFront, invertUp = 0, 0
    if '-' in followAxis:
        invertFront = 1
        followAxis = followAxis[-1]
    if '-' in upAxis:
        invertUp = 1
        upAxis = upAxis[-1]

    axisDict = {'x': 0, 'y': 1, 'z': 2}
    upDict = {'x': (1.0, 0.0, 0.0), 'y': (0.0, 1.0, 0.0), 'z': (0.0, 0.0, 1.0)}

    returnDict={'mpNodes':[], 'grps':[]}
    for i in range(len(cvs)):
        cv = cvs[i]
        num = str(i+1).zfill(2)
        uParam = getClosestPointOnCurve(crv, point=cv)
        mp = pmc.createNode('motionPath', name='mp_%s_%s_UTL' % (name, num))
        mp.uValue.set(uParam)
        mp.follow.set(follow)
        mp.frontAxis.set(axisDict[followAxis])
        if invertFront:
            mp.inverseFront.set(1)
        mp.upAxis.set(axisDict[upAxis])
        if invertFront:
            mp.inverseUp.set(1)
        mp.worldUpVector.set(upDict[upAxis])
        if upNode:
            mp.worldUpType.set(2)
            upNode.worldMatrix[0].connect(mp.worldUpMatrix)
        crv.worldSpace[0].connect(mp.geometryPath)

        n = pmc.group(empty=1, name='%s_%s_GRP' % (name, num))
        # Manually connect up the position
        mp.allCoordinates.connect(n.t)
        if follow:
            mp.rotate.connect(n.r)

#
#
#

def getClosestPointOnCurve(crv, point=None, obj=None):
    '''
    returns the uParam of the curve at the closest point to point or obj
    '''
    if point:
        pass
    elif obj:
        point = pmc.xform(obj, q=1, ws=1, t=1)
    else:
        return 'Incorrect paramters passed in'

    npoc = pmc.createNode('nearestPointOnCurve')
    crv.worldSpace[0].connect(npoc.inputCurve)
    npoc.inPosition.set(point)
    result = npoc.parameter.get()
    pmc.delete(npoc)
    return result

#
#
#

def sampleCurve(crv=None, numSamples=6, name=''):
    '''
    creates a pointOnCurveInfo node for each in numSamples and connects its parameter to the supplied curve
    returns a list of the created nodes
    '''
    nodes=[]
    for i in range(numSamples):
        num = str(i+1).zfill(2)

        inf = pmc.createNode('pointOnCurveInfo', name='crvInfo_%s_%s_UTL' % (name, num))
        inf.turnOnPercentage.set(1)
        crv.worldSpace[0].connect(inf.inputCurve)

        if numSamples != 1:
            inf.parameter.set((1.0 / (numSamples-1))*i)
        else:
            inf.parameter.set(0.5)
        nodes.append(inf)

    return nodes
#
#
#

def curveTangentMatrix(mp, up_vp, name):
    '''
    constructs a matrix based on the tangent of a curve - for use in mouth rigs
    '''
    tangent_vp = pmc.createNode('vectorProduct', name='vecProd_%s_tangent_UTL' % name)
    tangent_vp.operation.set(3)
    mp.worldMatrix[0].connect(tangent_vp.matrix)
    tangent_vp.input1.set((1, 0, 0))

    z_vp = pmc.createNode('vectorProduct', name='vecProd_%s_z_UTL' % name)
    z_vp.operation.set(2)
    tangent_vp.output.connect(z_vp.input1)
    up_vp.output.connect(z_vp.input2)

    x_vp = pmc.createNode('vectorProduct', name='vecProd_%s_x_UTL' % name)
    x_vp.operation.set(2)
    up_vp.output.connect(x_vp.input1)
    z_vp.output.connect(x_vp.input2)

    m = pmc.createNode('fourByFourMatrix', name='mat44_%s_UTL' % name)
    x_vp.outputX.connect(m.in00)
    x_vp.outputY.connect(m.in01)
    x_vp.outputZ.connect(m.in02)

    up_vp.outputX.connect(m.in10)
    up_vp.outputY.connect(m.in11)
    up_vp.outputZ.connect(m.in12)

    z_vp.outputX.connect(m.in20)
    z_vp.outputY.connect(m.in21)
    z_vp.outputZ.connect(m.in22)

    mp.tx.connect(m.in30)
    mp.ty.connect(m.in31)
    mp.tz.connect(m.in32)

    d = pmc.createNode('decomposeMatrix', name='decompMat_%s_UTL' % name)
    m.output.connect(d.inputMatrix)

    return d

#
#
#

class TangentCurve(object):
    '''
    Creates a bezier curve which automatically adjusts its tangents to maintain clean curvature.
    Creates a control at each point in points with a weight attribute to control tangent lengths
    If closed == true. Creates a closed curve.
    '''
    def __init__(self, points=None, name='', closed=False):
        super(TangentCurve, self).__init__()
        if points:
            self.points = points
        else:
            self.points = pmc.selected()
        if not self.points:
            return 'please supply or select at least 3 points to create a tangentCurve'
        self.name = name
        self.closed = closed
        self.build()

    def buildSpan(self, points, index):
        num = str(index + 1).zfill(2)
        main_grp = pmc.group(empty=1, name='%s_span_%s_GRP' % (self.name, num))

        # Create curve and connect curve points
        crv = curveBetweenNodes(points[0], points[2], name='%s_span_%s' % (self.name, num))
        crv.setParent(main_grp)
        locs = connectCurve(crv)
        pmc.pointConstraint(points[0], points[1], locs[1], mo=0)
        pmc.pointConstraint(points[1], points[2], locs[2], mo=0)
        locs[0].setParent(points[0])
        locs[1].setParent(main_grp)
        locs[2].setParent(main_grp)
        locs[3].setParent(points[2])


        # Motionpath node
        mp = nodesAlongCurve(crv, numNodes=1, name='%s_span_%s' % (self.name, str(index)), upNode=points[1])
        npc = pmc.createNode('nearestPointOnCurve', name='%s_span_%s' % (self.name, num))
        points[1].worldPosition[0].connect(npc.inPosition)
        crv.worldSpace[0].connect(npc.inputCurve)
        npc.parameter.connect(mp['mpNodes'][0].uValue)
        mp['mpNodes'][0].fractionMode.set(0)
        mp['grps'][0].setParent(main_grp)

        # Tangents
        tanGrp = coreUtils.addChild(points[1], 'group', '%s_span_%s_tangent_GRP' % (self.name, num))
        pmc.orientConstraint(mp['grps'][0], tanGrp)

        tanDrv = coreUtils.addChild(tanGrp, 'group', '%s_span_%s_tangent_DRV' % (self.name, num))
        points[1].r.connect(tanDrv.r)
        points[1].s.connect(tanDrv.s)

        inTan_grp = coreUtils.addChild(tanDrv, 'group', '%s_span_%s_inTangent_GRP' % (self.name, num))
        inTan_loc = coreUtils.addChild(inTan_grp, 'locator', '%s_span_%s_inTangent_LOC' % (self.name, num))
        inDist = coreUtils.distanceBetweenNodes(points[0], points[1], '%s_span_%s_in_dist' % (self.name, num))

        outTan_grp = coreUtils.addChild(tanDrv, 'group', '%s_span_%s_outTangent_GRP' % (self.name, num))
        outTan_loc = coreUtils.addChild(outTan_grp, 'locator', '%s_span_%s_outTangent_LOC' % (self.name, num))
        outDist = coreUtils.distanceBetweenNodes(points[1], points[2], '%s_span_%s_out_dist' % (self.name, num))

        pmc.addAttr(points[1], ln='tangentWeight', at="float", minValue=0.0, maxValue=1.0, keyable=1, hidden=0, defaultValue=0.25)

        inWeight_md = coreUtils.multiply(inDist.distance, points[1].tangentWeight, 'md_%s_span_%s_inWeight_UTL' % (self.name, num))
        outWeight_md = coreUtils.multiply(outDist.distance, points[1].tangentWeight, 'md_%s_span_%s_outWeight_UTL' % (self.name, num))
        weight_uc = coreUtils.convert(inWeight_md.outputX, -1, 'uc_%s_span_%s_weightInvert_UTL' % (self.name, num))

        outWeight_md.outputX.connect(outTan_grp.tx)
        weight_uc.output.connect(inTan_grp.tx)

        return{
            'inTan':inTan_loc,
            'outTan':outTan_loc,
            'inDist':inDist,
            'outDist':outDist,
            #'weight_md':weight_md,
            'main_grp':main_grp,
        }

    def build(self):
        self.dnt_grp = pmc.group(empty=1, name='%s_doNotTouch' % self.name)
        self.dnt_grp.inheritsTransform.set(0)
        numSpans = len(self.points)-2
        self.cv_locs = []
        self.spans = []
        for i in range(len(self.points)):
            num = str(i + 1).zfill(2)
            loc = coreUtils.createAlignedNode(self.points[i], 'locator', '%s_cv_%s_loc' % (self.name, num))
            self.cv_locs.append(loc)
        for i in range(numSpans):
            span = self.buildSpan(self.cv_locs[i:i+3], i)
            span['main_grp'].setParent(self.dnt_grp)
            self.spans.append(span)

        if not self.closed:
            # Build start tangent
            tanGrp = coreUtils.addChild(self.cv_locs[0], 'group', '%s_startTangent_GRP' % self.name)
            pmc.aimConstraint(self.spans[0]['inTan'], tanGrp, wut='objectrotation', wuo=self.cv_locs[0])

            outTan_loc = coreUtils.addChild(tanGrp, 'locator', '%s_outTangent_LOC' % self.name)

            pmc.addAttr(self.cv_locs[0], ln='tangentWeight', at="float", minValue=0.0, maxValue=1.0, keyable=1, hidden=0, defaultValue=0.25)

            weight_md = coreUtils.multiply(self.spans[0]['inDist'].distance, self.cv_locs[0].tangentWeight, 'md_%s_start_weight_UTL' % self.name)
            weight_md.outputX.connect(outTan_loc.tx)

            # Build end tangent
            tanGrp = coreUtils.addChild(self.cv_locs[-1], 'group', '%s_endTangent_GRP' % self.name)
            pmc.aimConstraint(self.spans[-1]['outTan'], tanGrp, wut='objectrotation', wuo=self.cv_locs[-1])

            inTan_loc = coreUtils.addChild(tanGrp, 'locator', '%s_inTangent_LOC' % self.name)

            pmc.addAttr(self.cv_locs[-1], ln='tangentWeight', at="float", minValue=0.0, maxValue=1.0, keyable=1, hidden=0, defaultValue=0.25)

            weight_md = coreUtils.multiply(self.spans[-1]['outDist'].distance, self.cv_locs[-1].tangentWeight, 'md_%s_end_weight_UTL' % self.name)
            weight_md.outputX.connect(inTan_loc.tx)

            self.spans.append({
                'endTan':inTan_loc,
                'startTan':outTan_loc,
            })

            # Collect points for curve
            self.crv_points = [self.cv_locs[0], self.spans[-1]['startTan']]
            for i in range(len(self.spans)-1):
                self.crv_points.append(self.spans[i]['inTan'])
                #self.crv_points.append(self.cv_locs[i+1])
                self.crv_points.append(self.spans[i]['outTan'])
            self.crv_points.append(self.spans[-1]['endTan'])
            self.crv_points.append(self.cv_locs[-1])

            # Create curve and connect points
            self.crv = curveThroughPoints(positions=[p.worldPosition[0].get() for p in self.crv_points], name=self.name)
            self.crv.setParent(self.dnt_grp)


            for i in range(len(self.crv_points)):
                self.crv_points[i].worldPosition[0].connect(self.crv.controlPoints[i])

        else:
            self.spans.append(self.buildSpan([self.cv_locs[-2], self.cv_locs[-1], self.cv_locs[0]], numSpans + 1))
            self.spans.append(self.buildSpan([self.cv_locs[-2], self.cv_locs[-1], self.cv_locs[0]], numSpans + 2))