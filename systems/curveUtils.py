import pymel.core as pmc
import drTools.core.coreUtils as coreUtils

#
#
#

def curveBetweenNodes(start=None, end=None, numCVs=4, name=''):
    '''
    Makes a degree 3 nurbs curve with 4 cvs between two nodes

    '''
    # Validation of args
    startPos, endPos = coreUtils.getStartAndEnd(start, end)

    if not startPos or not endPos:
        return 'curveBetweenNodes: Cannot determine start and end points'

    points = coreUtils.pointsAlongVector(start=startPos, end=endPos, divisions=(numCVs-1))

    # create the curve
    numKnots = 3 + numCVs - 1
    knots = [0,0,0]
    for i in range(numKnots-6):
        knots.append(i+1)
    knotsMax = knots[-1]
    for i in range(3):
        knots.append(knotsMax+1)

    crv = pmc.curve(p=points, k=knots, name='%s_CRV' % name)
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
        l = pmc.spaceLocator(name='%s_%s_LOC' %(crv, cv+1))
        l.t.set(cvs[cv])
        locShape = pmc.listRelatives(l, c=1, s=1)[0]
        locShape.worldPosition[0].connect(crvShape.controlPoints[cv])
        locList.append(l)

    return locList

#
#
#

def nodesAlongCurve(crv=None, numNodes=6, name='', followAxis='x', upAxis='y', upNode=None, upVec=None):
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
        mp.follow.set(1)
        mp.frontAxis.set(axisDict[followAxis])
        if invertFront:
            mp.inverseFront.set(1)
        mp.upAxis.set(axisDict[upAxis])
        if invertFront:
            mp.inverseUp.set(1)
        mp.worldUpVector.set(upDict[upAxis])
        if upNode:
            mp.worldUpType.set(3)
            upNode.worldMatrix[0].connect(mp.worldUpMatrix)
        crv.worldSpace[0].connect(mp.geometryPath)

        # Manually connect up the position
        mp.allCoordinates.connect(n.t)
        mp.rotate.connect(n.r)

        if numNodes != 1:
            mp.uValue.set((1.0 / (numNodes-1))*i)
        else:
            mp.uValue.set(0.5)

        returnDict['mpNodes'].append(mp)
        returnDict['grps'].append(n)

    return returnDict