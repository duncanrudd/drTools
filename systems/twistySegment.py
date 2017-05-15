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

    def __init__(self, name, start=None, end=None, numSegs=8, numCtrls=2, axis='x', upAxis='y', worldUpAxis='y',
                 colour='yellow', flipTwist=0, upNode=None, cleanup=1):
        startPos, endPos = coreUtils.getStartAndEnd(start, end)
        if not startPos or not endPos:
            return 'DrTwistySegmentCurve: Unable to determine start and end positions'
        super(DrTwistySegmentCurve, self).__init__(name)
        self.axis = axis
        self.upAxis = upAxis
        self.worldUpAxis = worldUpAxis
        self.upNode = upNode
        self.ctrls = []
        self.bendyTargs = []
        self.buildTwistySegmentCurve(numSegs, numCtrls, startPos, endPos, colour, flipTwist, cleanup)

    def buildTwistySegmentCurve(self, numSegs, numCtrls, startPos, endPos, colour, flipTwist, cleanup):

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
        startMatrix = coreUtils.getAimMatrix(startPos, endPos, self.axis, self.upAxis, self.worldUpAxis, upNode=self.upNode)
        pmc.xform(self.start_grp, matrix=startMatrix, ws=1)
        self.start_grp.setParent(self.ctrls_grp)
        pmc.parentConstraint(self.start_grp, self.crvLocs[0], mo=1)

        self.end_grp = pmc.group(empty=1, name='%s_end_GRP' % self.name)
        pmc.xform(self.end_grp, matrix=startMatrix, ws=1)
        self.end_grp.t.set(endPos)
        self.end_grp.setParent(self.ctrls_grp)
        pmc.parentConstraint(self.end_grp, self.crvLocs[-1], mo=1)

        ctrlPoints = coreUtils.pointsAlongVector(startPos, endPos, divisions=(numCtrls + 1))[1:-1]

        # controls
        ctrlSize = coreUtils.getDistance(startPos, endPos) * .33
        for i in range(numCtrls):
            num = str(i + 1).zfill(2)
            c = controls.squareCtrl(axis=self.axis, size=ctrlSize, name='%s_%s_CTRL' % (self.name, num))
            self.ctrls.append(c)
            c.setParent(self.ctrls_grp)
            zero = coreUtils.addParent(c, 'group', c.name().replace('CTRL', 'ZERO'))
            coreUtils.align(zero, self.start_grp)
            
            linearTarg = coreUtils.createAlignedNode(zero, 'group', '%s_%s_linear_TGT' % (self.name, num))
            linearTarg.setParent(self.rig_grp)
            pmc.pointConstraint(self.start_grp, self.end_grp, linearTarg, mo=0)
            startWeight = (1.0 / (numCtrls + 1)) * (i + 1)
            pmc.pointConstraint(self.end_grp, linearTarg, e=1, w=startWeight)
            pmc.pointConstraint(self.start_grp, linearTarg, e=1, w=(1.0 - startWeight))
            
            bendTarg = coreUtils.createAlignedNode(linearTarg, 'group', '%s_%s_bend_TGT' % (self.name, num))
            bendTarg.setParent(self.rig_grp)
            self.bendyTargs.append(bendTarg)
            p = pmc.pointConstraint(linearTarg, bendTarg, zero)
            pmc.addAttr(c, ln='auto_bend', at='double', minValue=0, maxValue=1, k=1, h=0)
            pmc.connectAttr('%s.auto_bend' % c, '%s.%sW1' % (p.name(), bendTarg))
            rev = coreUtils.reverse(c.auto_bend, name='rev_%sAutoBend_UTL' % c.name())
            rev.outputX.connect('%s.%sW0' % (p, linearTarg))

            

            axisDict = {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1), '-x': (-1, 0, 0), '-y': (0, -1, 0),
                        '-z': (0, 0, -1)}
            if i < numCtrls / 2:
                aimVector = (axisDict[self.axis][0] * -1, axisDict[self.axis][1] * -1, axisDict[self.axis][2] * -1)
                pmc.aimConstraint(self.start_grp, zero, mo=0, wut='objectRotation', wuo=self.start_grp,
                                  aimVector=aimVector, upVector=axisDict[self.upAxis],
                                  worldUpVector=axisDict[self.upAxis])
            else:
                pmc.aimConstraint(self.end_grp, zero, mo=0, wut='objectRotation', wuo=self.start_grp,
                                  aimVector=axisDict[self.axis], upVector=axisDict[self.upAxis],
                                  worldUpVector=axisDict[self.upAxis])

            pmc.parentConstraint(c, self.crvLocs[i + 1], mo=0)

        # pathNodes
        mps = curveUtils.nodesAlongCurve(crv=self.crv, numNodes=numSegs, name=self.name, followAxis=self.axis,
                                         upAxis=self.upAxis, upVec=self.upAxis, upNode=self.start_grp)
        pmc.addAttr(self.main_grp, longName='twist', at='double', k=1, h=0)
        self.twist_pma = pmc.createNode('plusMinusAverage', name='pma_%s_twistTotal_UTL' % self.name)

        if not flipTwist:
            self.twist_pma.output1D.connect(self.main_grp.twist)
        else:
            flipTwist_uc = coreUtils.convert(self.twist_pma.output1D, -1, 'uc_%s_twistInv_UTL' % self.name)
            flipTwist_uc.output.connect(self.main_grp.twist)

        self.twist_pma.operation.set(2)

        for i in range(numSegs):
            grp = mps['grps'][i]
            grp.setParent(self.noXform_grp)
            j = coreUtils.addChild(grp, 'joint', name='%s_%s_JNT' % (self.name, str(i + 1).zfill(2)))
            self.joints.append(j)
            self.main_grp.globalScale.connect(j.sx)
            self.main_grp.globalScale.connect(j.sy)
            self.main_grp.globalScale.connect(j.sz)
            mult = 0.0174533
            if '-' in self.axis:
                mult = -0.0174533
            uc = coreUtils.convert(self.main_grp.twist, ((1.0 / (numSegs - 1) * i) * mult),
                                   name='%s_twist_%s_uc' % (self.name, str(i + 1).zfill(2)))
            attrDict = {'x': j.rx, 'y': j.ry, 'z': j.rz, '-x': j.rx, '-y': j.ry, '-z': j.rz}
            uc.output.connect(attrDict[self.axis])

        # crvInfo
        crvInfo = pmc.createNode('curveInfo', name='%s_crvInfo' % self.name)
        crvShape = coreUtils.getShape(self.crv)
        crvShape.worldSpace[0].connect(crvInfo.inputCurve)

        # stretch
        pmc.addAttr(self.main_grp, longName='stretch', at='double', k=1, h=0)
        restLenMD = coreUtils.multiply(crvInfo.arcLength.get(), self.main_grp.globalScale, name='md_%s_restLength_UTL' % self.name)
        stretchMD = coreUtils.divide(restLenMD.outputX, crvInfo.arcLength, name='md_%s_stretch_UTL' % self.name)
        stretchMD.outputX.connect(self.main_grp.stretch)

        # squetch
        secondAxis = [axis for axis in ['x', 'y', 'z'] if not axis in [self.axis, self.upAxis]][0]
        for i in range(numSegs):
            num = str(i + 1).zfill(2)
            attr = pmc.addAttr(self.main_grp, longName='squetch_%s_amount' % str(i+1).zfill(2), at='double', k=1, h=0)
            blend = coreUtils.blend(self.main_grp.stretch, 1.0, name='blend_%s_squetch_%s_UTL' % (self.name, num), blendAttr=self.main_grp.attr('squetch_%s_amount' % num))
            blend.outputR.connect('%s.s%s' % (mps['grps'][i], secondAxis))
            blend.outputR.connect('%s.s%s' % (mps['grps'][i], self.upAxis[-1]))

        # colours
        coreUtils.colorize(colour, self.ctrls)

        if cleanup:
            self.cleanup()

    def cleanup(self):
        coreUtils.attrCtrl(nodeList=self.ctrls, attrList=['rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'visibility'])
        self.rig_grp.visibility.set(0)

        
class DrTwistySegmentSimple(systemUtils.DrSystem):
    '''
    creates a chain of joints along a 1 degree curve.
    x rotation of joints is driven by the twist attribute on the main group
    '''

    def __init__(self, name, start=None, end=None, numSegs=8, axis='x', upAxis='y', worldUpAxis='y', cleanup=1):
        startPos, endPos = coreUtils.getStartAndEnd(start, end)
        if not startPos or not endPos:
            return 'DrTwistySegmentSimple: Unable to determine start and end positions'
        super(DrTwistySegmentSimple, self).__init__(name)
        self.axis = axis
        self.upAxis = upAxis
        self.worldUpAxis = worldUpAxis
        self.buildTwistySegmentSimple(numSegs, startPos, endPos, cleanup)

    def buildTwistySegmentSimple(self, numSegs, startPos, endPos, cleanup):

        self.noXform_grp = coreUtils.addChild(self.rig_grp, 'group', name='%s_noXform_GRP' % self.name)
        self.noXform_grp.inheritsTransform.set(0)

        # Create curve
        self.crv = curveUtils.curveBetweenNodes(startPos, endPos, numCVs=(2), degree=1, name=self.name)
        self.crv.setParent(self.noXform_grp)
        self.crvLocs = curveUtils.connectCurve(self.crv)
        for loc in self.crvLocs:
            loc.setParent(self.rig_grp)

        # start and end groups
        self.start_grp = pmc.group(empty=1, name='%s_start_GRP' % self.name)
        startMatrix = coreUtils.getAimMatrix(startPos, endPos, self.axis, self.upAxis, self.worldUpAxis)
        pmc.xform(self.start_grp, matrix=startMatrix, ws=1)
        self.start_grp.setParent(self.rig_grp)
        pmc.parentConstraint(self.start_grp, self.crvLocs[0], mo=0)

        self.end_grp = pmc.group(empty=1, name='%s_end_GRP' % self.name)
        pmc.xform(self.end_grp, matrix=startMatrix, ws=1)
        self.end_grp.t.set(endPos)
        self.end_grp.setParent(self.rig_grp)
        pmc.parentConstraint(self.end_grp, self.crvLocs[-1], mo=0)

        # pathNodes
        mps = curveUtils.nodesAlongCurve(crv=self.crv, numNodes=numSegs, name=self.name, followAxis=self.axis,
                                         upAxis=self.upAxis, upVec=self.upAxis)
        pmc.addAttr(self.main_grp, longName='twist', at='double', k=1, h=0)
        self.twist_pma = pmc.createNode('plusMinusAverage', name='pma_%s_twistTotal_UTL' % self.name)
        self.twist_pma.output1D.connect(self.main_grp.twist)
        self.twist_pma.operation.set(2)

        for i in range(numSegs):
            grp = mps['grps'][i]
            mp = mps['mpNodes'][i]
            grp.setParent(self.noXform_grp)
            j = coreUtils.addChild(grp, 'joint', name='%s_%s_JNT' % (self.name, str(i + 1).zfill(2)))
            self.joints.append(j)
            self.main_grp.globalScale.connect(j.sx)
            self.main_grp.globalScale.connect(j.sy)
            self.main_grp.globalScale.connect(j.sz)
            if i == 0:
                mp.worldUpType.set(2)
                self.start_grp.worldMatrix[0].connect(mp.worldUpMatrix)
            elif i == (numSegs-1):
                mp.worldUpType.set(2)
                self.end_grp.worldMatrix[0].connect(mp.worldUpMatrix)
            else:
                startWeight = (1.0 / (numSegs-1)) * i
                o = pmc.orientConstraint(mps['grps'][0], mps['grps'][-1], j, mo=0)
                o.interpType.set(2)
                pmc.orientConstraint(mps['grps'][0], j, e=1, w=startWeight)
                pmc.orientConstraint(mps['grps'][-1], j, e=1, w=(1.0-startWeight))

        # crvInfo
        crvInfo = pmc.createNode('curveInfo', name='%s_crvInfo' % self.name)
        crvShape = coreUtils.getShape(self.crv)
        crvShape.worldSpace[0].connect(crvInfo.inputCurve)

        # stretch
        pmc.addAttr(self.main_grp, longName='stretch', at='double', k=1, h=0)
        restLenMD = coreUtils.multiply(crvInfo.arcLength.get(), self.main_grp.globalScale, name='md_%s_restLength_UTL' % self.name)
        stretchMD = coreUtils.divide(restLenMD.outputX, crvInfo.arcLength, name='md_%s_stretch_UTL' % self.name)
        stretchMD.outputX.connect(self.main_grp.stretch)

        # squetch
        for i in range(numSegs):
            num = str(i + 1).zfill(2)
            attr = pmc.addAttr(self.main_grp, longName='squetch_%s_amount' % str(i+1).zfill(2), at='double', k=1, h=0)
            blend = coreUtils.blend(self.main_grp.stretch, 1.0, name='blend_%s_squetch_%s_UTL' % (self.name, num), blendAttr=self.main_grp.attr('squetch_%s_amount' % num))
            blend.outputR.connect(mps['grps'][i].sx)
            blend.outputR.connect(mps['grps'][i].sz)

        if cleanup:
            self.cleanup()

    def cleanup(self):
        self.rig_grp.visibility.set(0)