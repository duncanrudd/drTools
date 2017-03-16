import pymel.core as pmc
import maya.OpenMaya as om
import math

#
#
#

def addChild(parent, childType, name, zero=1):
    '''
    adds a new node of type childType. Parents it to the parent node.
    :param childType: 'group', 'joint', 'locator'
    :return: newly created child node
    '''
    node = None
    if childType == 'group':
        node = pmc.group(empty=1, name=name)
        node.setParent(parent)
    elif childType == 'locator':
        node = pmc.spaceLocator(name=name)
        node.setParent(parent)
    elif childType == 'joint':
        node = pmc.joint(name=name)
        if not node.getParent() == parent:
            node.setParent(parent)

    if node:
        if zero:
            align(node, parent)
        return node
    else:
        return 'addChild: node not created'
#
#
#

def addParent(child, parentType, name, zero=1):
    '''
    adds a new node of type parentType. Parents node to it.
    :param childType: 'group', 'joint', 'locator'
    :return: newly created parent node
    '''
    node = None
    if not child:
        child = pmc.selected()[0]

    parent = pmc.listRelatives(child, p=1, fullPath=1)

    if parentType == 'group':
        node = pmc.group(empty=1, name=name)
    elif parentType == 'locator':
        node = pmc.spaceLocator(name=name)

    if node:
        if zero:
            align(node, child)
        node.setParent(parent)
        child.setParent(node)
        return node
    else:
        return 'addParent: node not created'
#
#
#

def align( node=None, target=None, translate=True, orient=True, scale=False ):
    '''
    sets the translation and / or orientation of node to match target
    '''

    # Validate that the correct arguments have been supplied
    if not node or not target:
        # If node and target aren't explicitly supplied, check for a valid selection to use
        sel = pmc.selected()
        if len(sel) == 2:
            node, target = sel[0], sel[1]
        else:
            return 'Align: Cannot determine nodes to align'

    targetMatrix = pmc.xform( target, q=True, ws=1, matrix=True )
    nodeMatrix = pmc.xform( node, q=True, ws=1, matrix=True )

    nodeScale = node.s.get()

    if translate and orient:
        pmc.xform(node, ws=1, matrix=targetMatrix)
    elif translate:
        # set row4 x y z to row4 of targetMatrix
        nodeMatrix[12:-1] = targetMatrix[ 12:-1]
        pmc.xform(node, ws=1, matrix=nodeMatrix)
    elif orient:
        # set rows 1-3 to rows 1-3 of nodeMatrix
        targetMatrix[12:-1] = nodeMatrix[12:-1]
        pmc.xform(node, ws=1, matrix=targetMatrix)

    if not scale:
        node.s.set(nodeScale)

#
#
#

def pointsAlongVector( start='', end='', divisions=2 ):
    '''
    returns a list of points that lie on a line between start and end
    'divisions' specifies the number of points to return.
    divisions = 2 (default) will return the start and end points with one intermediate point: [ p1(start), p2, p3(end) ]

    start and end can be supplied as lists, tuples or nodes. If they are not supplied, and 2 scene nodes are selected
    will attempt to use their world space positions as start and end

    creates a vector by subtracting end from start
    stores length of vector
    normalizes vector
    multiplies normalized vector by length / divisions

    '''
    startPos, endPos = getStartAndEnd(start, end)

    if not startPos or not endPos:
        return 'pointsAlongVector: Cannot determine start and end points'

    startVec = om.MVector(startPos[0], startPos[1], startPos[2])
    endVec = om.MVector(endPos[0], endPos[1], endPos[2])
    newVec = endVec - startVec
    segLength = newVec.length() / divisions
    newVec.normalize()
    points = []
    points.append(tuple(startPos))

    for p in range( 1, divisions ):
        point = newVec * segLength * p + startVec
        points.append((point.x, point.y, point.z))

    points.append(tuple(endPos))

    return points

#
#
#

def getShape(transform=None):
    '''
    returns the first shape of the specified transform

    '''
    shape = pmc.listRelatives(transform, children=1, shapes=1)[0]
    return shape
#
#
#

def getDistance( start, end ):
    '''
    Calculates distance between two Transforms using magnitude
    '''

    def mag(numbers):
        num = 0
        for eachNumber in numbers:
            num += math.pow(eachNumber, 2)

        mag = math.sqrt(num)
        return mag

    startPos, endPos = getStartAndEnd(start, end)

    if not startPos or not endPos:
        return 'pointsAlongVector: Cannot determine start and end points'

    calc = []
    calc.append(startPos[0] - endPos[0])
    calc.append(startPos[1] - endPos[1])
    calc.append(startPos[2] - endPos[2])

    return mag(calc)

#
#
#

def getStartAndEnd(start=None, end=None):
    '''
    Takes either two pynodes, two vectors or two selected nodes and returns their positions
    '''
    startPos, endPos = None, None
    if not start or not end and len(pmc.selected()) == 2:
        startPos = pmc.xform(pmc.selected()[0], translation=True, query=True, ws=True)
        endPos = pmc.xform(pmc.selected()[1], translation=True, query=True, ws=True)
    else:
        if pmc.nodetypes.Transform in type(start).__mro__:
            startPos = pmc.xform(start, translation=True, query=True, ws=True)
        else:
            startPos = start

        if pmc.nodetypes.Transform in type(end).__mro__:
            endPos = pmc.xform(end, translation=True, query=True, ws=True)
        else:
            endPos = end

    if not startPos or not endPos:
        return (None, None)
    else:
        return startPos, endPos

#
#
#

def multiply(input1, input2, name, operation=1):
    '''
    creates a multiplyDivide node with the given inputs
    returns the newly created node

    if inputs are attributes, a connection to the attribute is made
    if inputs are values, initial md values are set accordingly

    '''
    md = pmc.createNode('multiplyDivide', name=name)
    md.operation.set(operation)

    val = 0.0
    connect=False

    if type(input1) == pmc.general.Attribute:
        val = input1.get()
        connect=True
    else:
        val = input1
        connect=False

    if type(val) == pmc.datatypes.Vector:
        if connect:
            input1.connect(md.input1)
        else:
            md.input1.set(input1)
    else:
        if connect:
            input1.connect(md.input1X)
        else:
            md.input1X.set(input1)

    if type(input2) == pmc.general.Attribute:
        val = input2.get()
        connect=True
    else:
        val = input2
        connect=False

    if type(val) == pmc.datatypes.Vector:
        if connect:
            input2.connect(md.input2)
        else:
            md.input2.set(input2)
    else:
        if connect:
            input2.connect(md.input2X)
        else:
            md.input2X.set(input2)

    return md

def divide(input1, input2, name):
    md = multiply(input1, input2, name, operation=2)
    return md

def pow(input1, input2, name):
    md = multiply(input1, input2, name, operation=3)
    return md

def add(inputs, name, operation=1):
    '''
    creates a plusMinusAverage node with the given inputs
    returns the newly created node

    if inputs are attributes, a connection to the attribute is made
    if inputs are values, initial md values are set accordingly
    '''
    pma = pmc.createNode('plusMinusAverage', name=name)
    pma.operation.set(operation)

    val = 0.0
    connect=False

    for i in range(len(inputs)):
        if type(inputs[i]) == pmc.general.Attribute:
            val = inputs[i].get()
            connect=True
        else:
            val = inputs[i]
            connect=False

        if type(val) == pmc.datatypes.Vector:
            if connect:
                inputs[i].connect('%s.input3D[%s]' % (pma, i))
            else:
                pmc.setAttr('%s.input3D[%s]' % (pma, i), inputs[i])
        else:
            if connect:
                inputs[i].connect('%s.input1D[%s]' % (pma, i))
            else:
                pmc.setAttr('%s.input1D[%s]' % (pma, i), inputs[i])

    return pma

def minus(inputs, name):
    pma = add(inputs, name, operation=2)
    return pma

def average(inputs, name):
    pma = add(inputs, name, operation=3)
    return pma

def distanceBetweenNodes(node1, node2, name):
    dist = pmc.createNode('distanceBetween', name=name)
    node1.worldMatrix[0].connect(dist.inMatrix1)
    node2.worldMatrix[0].connect(dist.inMatrix2)
    return dist

def convert(input, factor, name):
    '''
    creates a unit conversion node with input connected to input
    '''
    uc = pmc.createNode('unitConversion', name=name)
    input.connect(uc.input)
    uc.conversionFactor.set(factor)
    return uc

def blend(input1, input2, name, blendAttr=None):
    '''
    sets up blending of input1 and input2
    If a blendAttr is supplied, this is connected to the blender value

    '''
    val = 0.0
    connect=False

    blend = pmc.createNode('blendColors', name=name)

    if type(input1) == pmc.general.Attribute:
        val = input1.get()
        connect=True
    else:
        val = input1
        connect=False

    if type(val) == pmc.datatypes.Vector:
        if connect:
            input1.connect(blend.color1)
        else:
            blend.color1.set(input1)
    else:
        if connect:
            input1.connect(blend.color1R)
        else:
            blend.color1R.set(input1)

    if type(input2) == pmc.general.Attribute:
        val = input2.get()
        connect=True
    else:
        val = input2
        connect=False

    if type(val) == pmc.datatypes.Vector:
        if connect:
            input2.connect(blend.color2)
        else:
            blend.color2.set(input2)
    else:
        if connect:
            input2.connect(blend.color2R)
        else:
            blend.color2R.set(input2)

    if blendAttr:
        blendAttr.connect(blend.blender)

    return blend

#
#
#

def attrCtrl(lock=True, keyable=False, channelBox=False, nodeList=[], attrList=[]):
    '''
    Takes a list of nodes and sets locks/unlocks shows/hides attributes in attrList

    '''
    if nodeList:
        for node in nodeList:
            if attrList:
                for a in attrList:
                    if node.hasAttr(a):
                        pmc.setAttr('%s.%s' % (node, a), lock=lock, keyable=keyable, channelBox=channelBox)
            else:
                return 'attrCtrl: No nodes supplied for attribute control'
    else:
        return 'attrCtrl: No nodes supplied for attribute control'
#
#
#

def colorize( color=None, nodeList=[] ):
    '''
    takes a node ( or list or nodes ) and enables the drawing overrides.
    'Color' specifies either an integer for the required color or a string corresponding to a key in colorDict
    if nodelist is not supplied, will attempt to work on selected nodes.

    '''
    if not color:
        raise RuntimeError, 'color not specified. You must supply either a string or integer.'

    colorDict = {
                   'center':14, # green
                   'right':13, # red
                   'left':6, # blue
                   'red':13,
                   'blue':6,
                   'yellow':17,
                   'green':14,
                   'purple':9,
                   'cn':14, # green
                   'rt':13, # red
                   'lf':6, # blue
                  }

    if type(color) == type('hello') or type(color) == type(u'hello'):
        color = colorDict[color]

    if not nodeList:
        nodeList = pmc.selected()
    else:
        if type(nodeList) == type('hello') or type(nodeList) == type(u'hello'):
            nodeList = [pmc.PyNode(nodeList)]

    for n in nodeList:
        n.overrideEnabled.set(1)
        n.overrideColor.set(color)

#
#
#

def extractAxis(node, axis, name, exposeNode=None, exposeAttr='twist'):
    '''
    isolates a single rotational axis as in the twist of a forearm
    Creates a lookat locator which is constrained to 'node' and offset by one unit along 'axis'
    A second locator is aim constrained to the first with the upVector set to (0,0,0)
    the angle between lookat's second axis and the aim locator's second axis gives the extracted value
    '''
    axisDict={'x':(1,0,0), 'y':(0,1,0), 'z':(0,0,1), '-x':(-1,0,0), '-y':(0,-1,0), '-z':(0,0,-1)}
    secondAxis='x'
    if 'x' in axis:
        secondAxis='y'

    main_grp = pmc.group(empty=1, name='%s_GRP' % name)
    align(main_grp, node)
    targetLoc = addChild(main_grp, 'locator', '%s_TARG' % name)
    targetLoc.t.set(axisDict[axis])
    pmc.parentConstraint(node, targetLoc, mo=1)
    readerLoc = addChild(main_grp, 'locator', '%s_READ' % name)
    pmc.aimConstraint(targetLoc, readerLoc, aimVector=axisDict[axis], upVector=(0,0,0))
    infoLoc = addChild(readerLoc, 'locator', '%s_INFO' % name)
    pmc.parentConstraint(targetLoc, infoLoc, mo=0)

    rotateOrderDict = {'x': 0, 'y': 1, 'z': 2}

    for node in [targetLoc, readerLoc, infoLoc]:
        node.rotateOrder.set(rotateOrderDict[axis[-1]])

    if not exposeNode:
        exposeNode = main_grp

    pmc.addAttr(exposeNode, longName=exposeAttr, at='double', k=1, h=0)
    pmc.connectAttr('%s.r%s' % (infoLoc, axis), '%s.%s' % (exposeNode.name(), exposeAttr))

    return main_grp

def getAimMatrix(start=None, end=None, axis='x', upAxis='y', worldUpAxis='y'):
    '''
    Given two nodes or two points, returns a matrix positioned at start, aiming at end along axis
    '''
    startPos, endPos = getStartAndEnd(start, end)
    if not startPos or not endPos:
        return 'getAimMatrix: Unable to determine start and end positions'

    axisDict={'x':(1,0,0), 'y':(0,1,0), 'z':(0,0,1), '-x':(-1,0,0), '-y':(0,-1,0), '-z':(0,0,-1)}
    orderDict={'x':0, 'y':1, 'z':2, '-x':0, '-y':1, '-z':2}

    # Aim vector
    startVec = pmc.datatypes.Vector(startPos[0], startPos[1], startPos[2])
    endVec = pmc.datatypes.Vector(endPos[0], endPos[1], endPos[2])
    upVec = pmc.datatypes.Vector(axisDict[worldUpAxis])
    aimVec = None
    if '-' in axis:
        aimVec = startVec - endVec
    else:
        aimVec = endVec - startVec
    aimVec.normalize()
    normalVec = aimVec.cross(upVec)
    tangentVec = normalVec.cross(aimVec)

    matrixList = ['', '', '', startPos]
    matrixList[orderDict[axis]] = aimVec
    matrixList[orderDict[upAxis]] = tangentVec
    matrixList[matrixList.index('')] = normalVec

    outMatrix = pmc.datatypes.Matrix(matrixList)

    return outMatrix









