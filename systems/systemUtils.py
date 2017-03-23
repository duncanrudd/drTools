import pymel.core as pmc
import drTools.core.coreUtils as coreUtils

reload(coreUtils)


#
#
#

class DrSystem(object):
    '''
    Template for rig system components.
    Creates group hierarchy, connections groups and world scale attributes that can be plugged together to create complex rigs.
    '''

    def __init__(self, name):
        # super(DrSystem, self).__init__()
        self.name = name
        self.sockets = {}
        self.joints=[]
        self.build()

    def build(self):
        self.main_grp = pmc.group(empty=1, name='%s_GRP' % self.name)
        self.ctrls_grp = coreUtils.addChild(self.main_grp, 'group', name='%s_ctrls_GRP' % self.name)
        self.rig_grp = coreUtils.addChild(self.main_grp, 'group', name='%s_rig_GRP' % self.name)
        self.conns_grp = coreUtils.addChild(self.main_grp, 'group', name='%s_connections_GRP' % self.name)
        self.plugs_grp = coreUtils.addChild(self.conns_grp, 'group', name='%s_plugs_GRP' % self.name)
        self.sockets_grp = coreUtils.addChild(self.conns_grp, 'group', name='%s_sockets_GRP' % self.name)

        # scale attribute - this can be connected to the rig's global scale
        pmc.addAttr(self.main_grp, longName='globalScale', at='double', k=1, h=0)
        self.main_grp.globalScale.set(1.0)
        self.main_grp.globalScale.connect(self.main_grp.sx)
        self.main_grp.globalScale.connect(self.main_grp.sy)
        self.main_grp.globalScale.connect(self.main_grp.sz)

    def exposeSockets(self, socketDict):
        for socket in socketDict.keys():
            s = coreUtils.addChild(self.sockets_grp, 'group', '%s_%s_socket' % (self.name, socket))
            coreUtils.align(s, socketDict[socket], orient=0)
            pmc.parentConstraint(socketDict[socket], s, mo=1)
            self.sockets[socket] = s
#
#
#

def plug(node=None, socket=None, plugType='parent', name=''):
    if not node or not socket:
        sel = pmc.selected()
        if len(sel) == 2:
            node = sel[0]
            socket = sel[1]
        else:
            return 'Please supply or select node and socket'

    main_grp = pmc.group(empty=1, name='%s_%s_PLUG' % (name, plugType))

    # constrained group
    const_grp = coreUtils.addChild(main_grp, 'group', name='%s_%s_CONST' % (name, plugType))
    coreUtils.align(const_grp, node)
    pmc.parentConstraint(socket, const_grp, mo=1)

    if plugType == 'parent':
        pmc.parentConstraint(const_grp, node, mo=1)
    elif plugType == 'point':
        pmc.pointConstraint(const_grp, node, mo=1)
    else:
        pmc.orientConstraint(const_grp, node, mo=1)

    return main_grp


def multiPlug(node=None, targetList=[], targetNames=[], settingsNode=None, plugType='parent', name=''):
    # Argument validation
    if not node or not targetList:
        sel = pmc.selected()
        if len(sel) > 1:
            node = sel[0]
            targetList = [s for s in sel[1:]]
        else:
            return 'Please supply or select node and targetList'
    if type(targetList) != type([]):
        targetList = [targetList]
    if not settingsNode:
        settingsNode = node
    if not targetNames:
        targetNames = [t.name() for t in targetList]

    # main group
    main_grp = pmc.group(empty=1, name='%s_%s_PLUG' % (name, plugType))

    # constrained group
    const_grp = coreUtils.addChild(main_grp, 'group', name='%s_%s_CONST' % (name, plugType))
    coreUtils.align(const_grp, node)

    if plugType == 'parent':
        pmc.parentConstraint(const_grp, node)
    elif plugType == 'point':
        pmc.pointConstraint(const_grp, node)
    else:
        pmc.orientConstraint(const_grp, node)

    # targets
    targets = []
    for t in range(len(targetList)):
        targ = coreUtils.addChild(main_grp, 'group', name='%s_%s_TGT' % (name, targetNames[t]))
        coreUtils.align(targ, const_grp)
        pmc.parentConstraint(targetList[t], targ, mo=1)
        targets.append(targ)

    parentEnumString = ''
    for t in targetNames:
        parentEnumString += (t + ':')
    par = pmc.parentConstraint(targets, const_grp)
    pmc.addAttr(settingsNode, longName='parent_space', at='enum', enumName=parentEnumString, keyable=True)
    # Set driven keys to drive the weights of the targets in the orient constraint
    parentWeightAliasList = [str(w) for w in pmc.parentConstraint(par, q=True, weightAliasList=True)]
    for spaceIndex in range(len(targetList)):
        rv = pmc.createNode('remapValue', name='remapVal_%s_%s_UTL' % (name, targetNames[spaceIndex]))
        settingsNode.parent_space.connect(rv.inputValue)
        rv.inputMin.set(spaceIndex - 1)
        rv.inputMax.set(spaceIndex + 1)
        rv.value[1].value_FloatValue.set(0)
        rv.value[2].value_Position.set(0.5)
        rv.value[2].value_FloatValue.set(1)
        rv.value[2].value_Interp.set(1)
        rv.outValue.connect(parentWeightAliasList[spaceIndex])

    return main_grp


#
#
#

def tripleChain(name='', joints=None):
    '''
    :param joints: List of hierarchical joints to create a blended chain for
    :param name: base name for the new joint chains
    :return: dictionary with keys for each chain (ik, fk, result) and a key for the blendColors nodes
    '''

    if not joints:
        joints = pmc.selected()

    main_grp = coreUtils.createAlignedNode(joints[0], nodeType='group', name='%s_joints_GRP' % name)

    def _duplicateChain(chainType):
        dupes = []
        for i in range(len(joints)):
            joint = joints[i]
            j = coreUtils.createAlignedNode(joint, nodeType='joint', name='%s_%s_%s' % (name, str(i + 1).zfill(2), chainType))
            dupes.append(j)
            if i > 0:
                j.setParent(dupes[i - 1])
                j.jointOrient.set(joint.jointOrient.get())
                j.r.set((0, 0, 0))
            else:
                j.setParent(main_grp)
                j.jointOrient.set((0, 0, 0))
                j.r.set((0, 0, 0))
        return dupes

    resultChain = _duplicateChain('result_JNT')
    fkChain = _duplicateChain('fk_JNT')
    ikChain = _duplicateChain('ik_JNT')
    blendColors = []

    # Set up ik / fk blending
    for i in range(len(joints)):
        bc = coreUtils.blend(fkChain[i].t, ikChain[i].t, name='bc_%s_%s_translate_UTL' % (name, str(i + 1).zfill(2)))
        bc.output.connect(resultChain[i].t)
        blendColors.append(bc)

        bc = coreUtils.blend(fkChain[i].r, ikChain[i].r, name='bc_%s_%s_rotate_UTL' % (name, str(i + 1).zfill(2)))
        bc.output.connect(resultChain[i].r)
        blendColors.append(bc)

    return {'fkChain': fkChain,
            'ikChain': ikChain,
            'resultChain': resultChain,
            'blendColors': blendColors,
            'main_grp': main_grp}


#
#
#

def placePoleVector(start=None, end=None, axis='x', upAxis='y', worldUpAxis='y', mult=10):
    m = coreUtils.getAimMatrix(start=start, end=end, axis='x', upAxis='y', worldUpAxis='y')
    mList = [row for row in m]
    mList[3] = mList[3] + (mList[2] * mult)
    return pmc.datatypes.Matrix(mList).translate.get()
