import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls
import drTools.systems.limb as drLimb
import drTools.systems.twistySegment as drTwistySegment

reload(controls)
reload(coreUtils)
reload(systemUtils)
reload(drLimb)
reload(drTwistySegment)

class DrArm(drLimb.DrLimb):
    def __init__(self, name='', joints=None, cleanup=0, colour='red', numTwistSegs=8, upAxis='y', leg=0, flipTwist=0, alignIkToJoints=0):
        super(DrArm, self).__init__(name, joints=joints, leg=leg, alignIkToJoints=alignIkToJoints)
        self.buildArm(colour, numTwistSegs, flipTwist, upAxis)

    def buildArm(self, colour, numTwistSegs, flipTwist, upAxis):
        self.bendyCtrls_grp = coreUtils.addChild(self.main_grp, 'group', name='%s_bendyCtrls_GRP' % self.name)
        pmc.addAttr(self.settingsCtrl, longName='bendy_ctrls_vis', at='bool', k=1, h=0)
        pmc.setAttr(self.settingsCtrl.bendy_ctrls_vis, k=0, channelBox=1)
        self.settingsCtrl.bendy_ctrls_vis.connect(self.bendyCtrls_grp.visibility)

        # Elbow ctr
        aimVec = (1, 0, 0)
        if flipTwist:
            aimVec = (-1, 0, 0)
        elbowAim = coreUtils.addChild(self.const_grp, 'locator', '%s_elbowOrient_LOC' % self.name)
        pmc.aimConstraint(self.tripleChain['resultChain'][2], elbowAim, mo=0, wut='objectRotation',
                          wuo=self.topTwist['nonRoll'], aimVector=aimVec)
        ctrlSize = coreUtils.getDistance(self.tripleChain['resultChain'][0], self.tripleChain['resultChain'][1]) * .25
        self.elbowCtrl = controls.squareCtrl(axis='x', size=ctrlSize, name='%s_elbow_CTRL' % self.name)
        self.elbowCtrl.setParent(self.bendyCtrls_grp)
        elbowZero = coreUtils.addParent(self.elbowCtrl, 'group', '%s_elbowCtrl_ZERO' % self.name)
        pmc.pointConstraint(self.tripleChain['resultChain'][1], elbowZero, mo=0)
        pmc.orientConstraint(elbowAim, elbowZero, mo=0)
        self.ctrls.append(self.elbowCtrl)

        # Twisty Segments
        # Upper twist
        twistAxis = 'x'
        if flipTwist:
            twistAxis = '-x'

        self.upperTwist = drTwistySegment.DrTwistySegmentCurve(name='%s_upperTwist' % self.name,
                                                               start=self.tripleChain['resultChain'][0],
                                                               end=self.tripleChain['resultChain'][1],
                                                               numSegs=numTwistSegs,
                                                               numCtrls=2,
                                                               axis=twistAxis,
                                                               upAxis=upAxis,
                                                               worldUpAxis=upAxis,
                                                               colour=colour,
                                                               flipTwist=flipTwist,
                                                               upNode=self.tripleChain['resultChain'][0],
                                                               cleanup=1)
        self.upperTwist.main_grp.setParent(self.bendyCtrls_grp)
        self.upperTwist.main_grp.inheritsTransform.set(0)
        pmc.parentConstraint(self.topTwist['nonRoll'], self.upperTwist.start_grp, mo=0)
        pmc.pointConstraint(self.elbowCtrl, self.upperTwist.end_grp, mo=0)
        self.main_grp.mid_twist.connect(self.upperTwist.twist_pma.input1D[0])
        elbowTwist_inv = coreUtils.convert(self.elbowCtrl.rx, -57.2958, name='uc_%s_elbowTwistInvert_UTL' % self.name)
        elbowTwist_inv.output.connect(self.upperTwist.twist_pma.input1D[1])
        '''
        if flipTwist:
            self.elbowCtrl.rx.connect(self.upperTwist.twist_pma.input1D[1])
        else:
            elbowTwist_inv.output.connect(self.upperTwist.twist_pma.input1D[1])
        '''
        pmc.parentConstraint(self.elbowCtrl, self.upperTwist.bendyTargs[-1], mo=1)

        self.main_grp.globalScale.connect(self.upperTwist.main_grp.globalScale)

        # Lower twist
        self.lowerTwist = drTwistySegment.DrTwistySegmentCurve(name='%s_lowerTwist' % self.name,
                                                               start=self.tripleChain['resultChain'][1],
                                                               end=self.tripleChain['resultChain'][2],
                                                               numSegs=numTwistSegs,
                                                               numCtrls=2,
                                                               axis=twistAxis,
                                                               upAxis=upAxis,
                                                               worldUpAxis=upAxis,
                                                               colour=colour,
                                                               flipTwist=flipTwist,
                                                               upNode=self.tripleChain['resultChain'][1],
                                                               cleanup=1)
        self.lowerTwist.main_grp.setParent(self.bendyCtrls_grp)
        self.lowerTwist.main_grp.inheritsTransform.set(0)
        p = pmc.parentConstraint(self.elbowCtrl, self.lowerTwist.start_grp, mo=0)
        self.main_grp.mid_twist.connect(p.target[0].targetOffsetRotate.targetOffsetRotateX)
        self.elbowCtrl.rx.connect(self.lowerTwist.twist_pma.input1D[1])
        '''
        if flipTwist:
            uc = coreUtils.convert(self.main_grp.mid_twist, -.017, name='uc_%s_midTwistInvert_UTL' % self.name)
            uc.output.connect(p.target[0].targetOffsetRotate.targetOffsetRotateX)
            elbowTwist_inv.output.connect(self.lowerTwist.twist_pma.input1D[1])
        else:
            self.main_grp.mid_twist.connect(p.target[0].targetOffsetRotate.targetOffsetRotateX)
            self.elbowCtrl.rx.connect(self.lowerTwist.twist_pma.input1D[1])
        '''
        pmc.parentConstraint(self.tripleChain['resultChain'][2], self.lowerTwist.end_grp, mo=0)
        self.main_grp.btm_twist.connect(self.lowerTwist.twist_pma.input1D[0])
        self.main_grp.globalScale.connect(self.lowerTwist.main_grp.globalScale)
        pmc.parentConstraint(self.elbowCtrl, self.lowerTwist.bendyTargs[0], mo=1)

        # Average joints
        startAvgJnt = coreUtils.addChild(self.rig_grp, 'joint', '%s_startAvg_JNT' % self.name)
        pmc.parentConstraint(self.const_grp, self.topTwist['nonRoll'], startAvgJnt, mo=0).interpType.set(2)

        elbowAvgJnt = coreUtils.addChild(self.rig_grp, 'joint', '%s_midAvg_JNT' % self.name)
        pmc.parentConstraint(self.upperTwist.joints[-1], self.lowerTwist.joints[0], elbowAvgJnt, mo=0).interpType.set(2)

        wristAvgJnt = coreUtils.addChild(self.rig_grp, 'joint', '%s_endAvg_JNT' % self.name)
        pmc.parentConstraint(self.lowerTwist.joints[-1], self.tripleChain['resultChain'][2], wristAvgJnt, mo=0).interpType.set(2)

        # add joints for publishing
        self.joints.append(startAvgJnt)
        for joint in self.upperTwist.joints:
            self.joints.append(joint)
        self.joints.append(elbowAvgJnt)
        for joint in self.lowerTwist.joints:
            self.joints.append(joint)
        self.joints.append(wristAvgJnt)

        coreUtils.colorize(colour, self.ctrls)


    def cleanup(self):
        super(DrArm, self).cleanup()
