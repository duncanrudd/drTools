import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.curveUtils as curveUtils
import drTools.systems.controls as controls

reload(systemUtils)
reload(curveUtils)
reload(coreUtils)
reload(controls)


class DrTwistySegmentCurve(systemUtils.DrSystem):
    '''
    creates a chain of joints along a curve with controls to deform curve.
    x rotation of joints is driven by the twist attribute on the main group

    WISHLIST: Ability to twist chain with falloff at each control
    '''

    def __init__(self, name, start=None, end=None, numSegs=8, numCtrls=2, axis='x', upAxis='y', worldUpAxis='y', colour='yellow', cleanup=1):
        startPos, endPos = coreUtils.getStartAndEnd(start, end)
        if not startPos or not endPos:
            return 'DrTwistySegmentCurve: Unable to determine start and end positions'
        super(DrTwistySegmentCurve, self).__init__(name)
        self.axis = axis
        self.upAxis = upAxis
        self.worldUpAxis = worldUpAxis
        self.ctrls = []
        self.buildTwistySegmentCurve(numSegs, numCtrls, startPos, endPos, colour, cleanup)

    def buildTwistySegmentCurve(self, numSegs, numCtrls, startPos, endPos, colour, cleanup):

        self.noXform_grp = coreUtils.addChild(self.rig_grp, 'group', name='%s_noXform_GRP' % self.name)
        self.noXform_grp.inheritsTransform.set(0)

        # Create curve
        self.crv = curveUtils.curveBetweenNodes(startPos, endPos, numCVs=(numCtrls + 2), name=self.name)
        self.crv.setParent(self.noXform_grp)
        self.crvLocs = curveUtils.connectCurve(self.crv)
        for loc in self.crvLocs:
            loc.setParent(self.rig_grp)

        # start and end groups
        self.start_grp = pmc.group(empty=1, name='%s_start_GRP' % self.name)
        startMatrix = coreUtils.getAimMatrix(startPos, endPos, self.axis, self.upAxis, self.worldUpAxis)
        pmc.xform(self.start_grp, matrix=startMatrix, ws=1)
        self.start_grp.setParent(self.ctrls_grp)
        pmc.parentConstraint(self.start_grp, self.crvLocs[0], mo=0)

        self.end_grp = pmc.group(empty=1, name='%s_end_GRP' % self.name)
        pmc.xform(self.end_grp, matrix=startMatrix, ws=1)
        self.end_grp.t.set(endPos)
        self.end_grp.setParent(self.ctrls_grp)
        pmc.parentConstraint(self.end_grp, self.crvLocs[-1], mo=0)

        ctrlPoints = coreUtils.pointsAlongVector(startPos, endPos, divisions=(numCtrls + 1))[1:-1]

        # controls
        ctrlSize = coreUtils.getDistance(startPos, endPos) * .33
        for i in range(numCtrls):
            c = controls.squareCtrl(axis=self.axis, size=ctrlSize, name='%s_%s_CTRL' % (self.name, str(i + 1).zfill(2)))
            self.ctrls.append(c)
            c.setParent(self.ctrls_grp)
            zero = coreUtils.addParent(c, 'group', c.name().replace('CTRL', 'ZERO'))
            pmc.pointConstraint(self.start_grp, self.end_grp, zero, mo=0)

            startWeight = (1.0 / (numCtrls + 1)) * (i + 1)
            pmc.pointConstraint(self.end_grp, zero, e=1, w=startWeight)
            pmc.pointConstraint(self.start_grp, zero, e=1, w=(1.0 - startWeight))

            axisDict = {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1), '-x': (-1, 0, 0), '-y': (0, -1, 0),
                        '-z': (0, 0, -1)}
            pmc.aimConstraint(self.end_grp, zero, mo=0, wut='objectRotation', wuo=self.start_grp,
                              aimVector=axisDict[self.axis], upVector=axisDict[self.upAxis],
                              worldUpVector=axisDict[self.upAxis])

            pmc.parentConstraint(c, self.crvLocs[i + 1], mo=0)

        # pathNodes
        mps = curveUtils.nodesAlongCurve(crv=self.crv, numNodes=numSegs, name=self.name, followAxis=self.axis,
                                         upAxis=self.upAxis, upVec=self.upAxis)
        pmc.addAttr(self.main_grp, longName='twist', at='double', k=1, h=0)

        for i in range(numSegs):
            grp = mps['grps'][i]
            grp.setParent(self.noXform_grp)
            j = coreUtils.addChild(grp, 'group', name='%s_%s_JNT' % (self.name, str(i + 1).zfill(2)))
            mult = 0.017
            if '-' in self.axis:
                mult = -0.017
            uc = coreUtils.convert(self.main_grp.twist, ((1.0 / (numSegs - 1) * i) * mult),
                                   name='%s_twist_%s_uc' % (self.name, str(i + 1).zfill(2)))
            attrDict = {'x': j.rx, 'y': j.ry, 'z': j.rz, '-x': j.rx, '-y': j.ry, '-z': j.rz}
            uc.output.connect(attrDict[self.axis])

        # colours
        coreUtils.colorize(colour, self.ctrls)

        if cleanup:
            self.cleanup()

    def cleanup(self):
        coreUtils.attrCtrl(nodeList=self.ctrls, attrList=['rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'visibility'])
        self.rig_grp.visibility.set(0)


class DrTwistySegment(systemUtils.DrSystem):
    '''
    creates a chain of joints between two nodes.
    x rotation of joints is driven by the twist attribute on the main group
    '''

    def __init__(self, name, start=None, end=None, numSegs=8, axis='x', upAxis='y', worldUpAxis='y', cleanup=1):
        startPos, endPos = coreUtils.getStartAndEnd(start, end)
        if not startPos or not endPos:
            return 'DrTwistySegment: Unable to determine start and end positions'
        super(DrTwistySegment, self).__init__(name)
        self.axis = axis
        self.upAxis = upAxis
        self.worldUpAxis = worldUpAxis
        self.buildTwistySegment(numSegs, startPos, endPos, cleanup)

    def buildTwistySegment(self, numSegs, startPos, endPos, cleanup):

        # start and end groups
        self.start_grp = pmc.group(empty=1, name='%s_start_GRP' % self.name)
        startMatrix = coreUtils.getAimMatrix(startPos, endPos, self.axis, self.upAxis, self.worldUpAxis)
        pmc.xform(self.start_grp, matrix=startMatrix, ws=1)
        self.start_grp.setParent(self.rig_grp)

        self.end_grp = pmc.group(empty=1, name='%s_end_GRP' % self.name)
        pmc.xform(self.end_grp, matrix=startMatrix, ws=1)
        self.end_grp.t.set(endPos)
        self.end_grp.setParent(self.rig_grp)

        pmc.addAttr(self.main_grp, longName='twist', at='double', k=1, h=0)

        # groups
        for i in range(numSegs):
            g = coreUtils.addChild(self.rig_grp, 'group', name='%s_%s_GRP' % (self.name, str(i + 1).zfill(2)))
            pmc.pointConstraint(self.start_grp, self.end_grp, g, mo=0)

            startWeight = (1.0 / (numSegs - 1)) * i
            pmc.pointConstraint(self.end_grp, g, e=1, w=startWeight)
            pmc.pointConstraint(self.start_grp, g, e=1, w=(1.0 - startWeight))

            axisDict = {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1), '-x': (-1, 0, 0), '-y': (0, -1, 0),
                        '-z': (0, 0, -1)}
            pmc.aimConstraint(self.end_grp, g, mo=0, wut='objectRotation', wuo=self.start_grp,
                              aimVector=axisDict[self.axis], upVector=axisDict[self.upAxis],
                              worldUpVector=axisDict[self.upAxis])

            j = coreUtils.addChild(g, 'joint', name='%s_%s_JNT' % (self.name, str(i + 1).zfill(2)))
            mult = 0.017
            if '-' in self.axis:
                mult = -0.017
            uc = coreUtils.convert(self.main_grp.twist, ((1.0 / (numSegs - 1) * i) * mult),
                                   name='%s_twist_%s_uc' % (self.name, str(i + 1).zfill(2)))
            attrDict = {'x': j.rx, 'y': j.ry, 'z': j.rz, '-x': j.rx, '-y': j.ry, '-z': j.rz}
            uc.output.connect(attrDict[self.axis])

        if cleanup:
            self.cleanup()

    def cleanup(self):
        self.rig_grp.visibility.set(0)
