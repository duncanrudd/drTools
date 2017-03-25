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
        if len(cmds.ls(sl=1)) == 1:
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
        if invertFront:
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