import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls

reload(controls)
reload(coreUtils)
reload(systemUtils)


class DrReverseFoot(systemUtils.DrSystem):
    def __init__(self, name, ankle=None, foot=None, ball=None, toe=None, inner=None, outer=None, heel=None,
                 settingsNode=None, blendAttr=None, colour='red', cleanup=1):
        self.ctrls=[]
        if not ankle and len(pmc.selected()) == 7:
            sel = pmc.selected()
            ankle = sel[0]
            foot = sel[1]
            ball = sel[2]
            toe = sel[3]
            inner = sel[4]
            outer = sel[5]
            heel = sel[6]
        if not ankle:
            return 'DrReverseFoot: Please supply or select joints for Ankle, Foot, Ball, Toe, Inner, Outer and Heel positions.'
        super(DrReverseFoot, self).__init__(name=name)
        self.buildFoot(ankle, foot, ball, toe, inner, outer, heel, settingsNode, blendAttr, colour, cleanup)

    def buildFoot(self, ankle, foot, ball, toe, inner, outer, heel, settingsNode, blendAttr, colour, cleanup):

        # Make duplicate joint chains
        self.tripleChain = systemUtils.tripleChain(joints=[ankle, foot, ball, toe], name=self.name, flip=0)
        ikConst_grp = coreUtils.addParent(self.tripleChain['ikChain'][0], 'group', '%s_ikConst_GRP' % self.name)
        fkConst_grp = coreUtils.addParent(self.tripleChain['fkChain'][0], 'group', '%s_fkConst_GRP' % self.name)
        resultConst_grp = coreUtils.addParent(self.tripleChain['resultChain'][0], 'group', '%s_resultConst_GRP' % self.name)

        self.tripleChain['main_grp'].setParent(self.rig_grp)

        if blendAttr:
            par = pmc.parentConstraint(ikConst_grp, fkConst_grp, resultConst_grp, mo=0)
            attr = pmc.Attribute('%s.%sW1' % (par.name(), fkConst_grp.name()))
            blendAttr.connect(attr)
            attr = pmc.Attribute('%s.%sW0' % (par.name(), ikConst_grp.name()))
            blend_rev = coreUtils.reverse(blendAttr, 'reverse_%s_blend, UTL' % self.name)
            blend_rev.outputX.connect(attr)

            for bc in self.tripleChain['blendColors']:
                blendAttr.connect(bc.blender)

        # Orientation for controls
        axis = 'x'
        if self.tripleChain['resultChain'][1].tx.get() < 0.0:
            axis = '-x'
        ctrlSize = coreUtils.getDistance(self.tripleChain['resultChain'][0], self.tripleChain['resultChain'][1]) * .5

        # ikHandles
        footIkHandle = pmc.ikHandle(solver='ikRPsolver',
                                    name='%s_foot_ikHandle' % self.name,
                                    startJoint=self.tripleChain['ikChain'][0],
                                    endEffector=self.tripleChain['ikChain'][1],
                                    setupForRPsolver=1)[0]
        footIkHandle.setParent(self.rig_grp)
        footIkHandleConst = coreUtils.addParent(footIkHandle, 'group', '%s_footIkHandle_CONST' % self.name)

        ballIkHandle = pmc.ikHandle(solver='ikRPsolver',
                                    name='%s_ball_ikHandle' % self.name,
                                    startJoint=self.tripleChain['ikChain'][1],
                                    endEffector=self.tripleChain['ikChain'][2],
                                    setupForRPsolver=1)[0]
        ballIkHandle.setParent(self.rig_grp)
        ballIkHandleConst = coreUtils.addParent(ballIkHandle, 'group', '%s_ballIkHandle_CONST' % self.name)

        toeIkHandle = pmc.ikHandle(solver='ikRPsolver',
                                   name='%s_toe_ikHandle' % self.name,
                                   startJoint=self.tripleChain['ikChain'][2],
                                   endEffector=self.tripleChain['ikChain'][3],
                                   setupForRPsolver=1)[0]
        toeIkHandle.setParent(self.rig_grp)
        toeIkHandleConst = coreUtils.addParent(toeIkHandle, 'group', '%s_toeIkHandle_CONST' % self.name)

        # ikCtrls
        self.heelIkCtrl = controls.squareCtrl(name='%s_heel_ik_CTRL' % self.name, axis=axis, size=ctrlSize)
        coreUtils.align(self.heelIkCtrl, heel)
        self.heelIkCtrl.setParent(self.ctrls_grp)
        self.ikCtrls_grp = coreUtils.addParent(self.heelIkCtrl, 'group', '%s_ikCtrls_GRP' % self.name)
        coreUtils.addParent(self.heelIkCtrl, 'group', '%s_heelIkCtrl_ZERO' % self.name)
        self.ctrls.append(self.heelIkCtrl)

        self.toeIkCtrl = controls.squareCtrl(name='%s_toe_ik_CTRL' % self.name, axis=axis, size=ctrlSize)
        coreUtils.align(self.toeIkCtrl, self.tripleChain['ikChain'][3])
        self.toeIkCtrl.setParent(self.heelIkCtrl)
        coreUtils.addParent(self.toeIkCtrl, 'group', '%s_toeIkCtrl_ZERO' % self.name)
        self.ctrls.append(self.toeIkCtrl)

        self.innerLoc = coreUtils.createAlignedNode(inner, 'group', '%s_inner_GRP' % self.name)
        self.innerLoc.setParent(self.toeIkCtrl)
        innerZero = coreUtils.addParent(self.innerLoc, 'group', '%s_inner_ZERO' % self.name)

        self.outerLoc = coreUtils.createAlignedNode(outer, 'group', '%s_outer_GRP' % self.name)
        self.outerLoc.setParent(self.innerLoc)
        outerZero = coreUtils.addParent(self.outerLoc, 'group', '%s_outer_ZERO' % self.name)

        self.ballPivotIkCtrl = controls.squareCtrl(name='%s_ballPivot_ik_CTRL' % self.name, axis=axis, size=ctrlSize)
        coreUtils.align(self.ballPivotIkCtrl, self.tripleChain['ikChain'][2])
        self.ballPivotIkCtrl.setParent(self.outerLoc)
        coreUtils.addParent(self.ballPivotIkCtrl, 'group', '%s_ballPivotIkCtrl_ZERO' % self.name)
        inv_grp = coreUtils.addParent(self.ballPivotIkCtrl, 'group', '%s_ballPivotIkCtrlRotX_INV' % self.name)
        inv_uc = coreUtils.convert(self.ballPivotIkCtrl.rx, -1.0, name='uc_%s_ballPivotIkCtrlRotX_UTL' % self.name)
        inv_uc.output.connect(inv_grp.rx)

        pmc.parentConstraint(self.ballPivotIkCtrl, toeIkHandleConst, mo=1)
        self.ctrls.append(self.ballPivotIkCtrl)

        self.ballPivotIkCtrl.rx.connect(self.outerLoc.rx)
        pmc.transformLimits(self.innerLoc, rx=(-45, 0), erx=(0, 1))

        self.ballPivotIkCtrl.rx.connect(self.innerLoc.rx)
        pmc.transformLimits(self.outerLoc, rx=(0, 45), erx=(1, 0))

        self.ballIkCtrl = controls.squareCtrl(name='%s_ball_ik_CTRL' % self.name, axis=axis, size=ctrlSize)
        coreUtils.align(self.ballIkCtrl, self.tripleChain['ikChain'][2])
        self.ballIkCtrl.setParent(self.ballPivotIkCtrl)
        coreUtils.addParent(self.ballIkCtrl, 'group', '%s_ballIkCtrl_ZERO' % self.name)
        pmc.parentConstraint(self.ballIkCtrl, ballIkHandleConst, mo=1)
        self.ctrls.append(self.ballIkCtrl)

        self.footIkCtrl = controls.squareCtrl(name='%s_foot_ik_CTRL' % self.name, axis=axis, size=ctrlSize)
        coreUtils.align(self.footIkCtrl, self.tripleChain['ikChain'][1])
        self.footIkCtrl.setParent(self.ballIkCtrl)
        coreUtils.addParent(self.footIkCtrl, 'group', '%s_footIkCtrl_ZERO' % self.name)
        pmc.parentConstraint(self.footIkCtrl, footIkHandleConst, mo=1)
        pmc.parentConstraint(self.footIkCtrl, ikConst_grp, mo=1)
        self.ctrls.append(self.footIkCtrl)

        # fkCtrls
        self.footFkCtrl = controls.squareCtrl(name='%s_foot_fk_CTRL' % self.name, axis=axis, size=ctrlSize)
        coreUtils.align(self.footFkCtrl, self.tripleChain['fkChain'][1])
        self.footFkCtrl.setParent(self.ctrls_grp)
        self.fkCtrls_grp = coreUtils.addParent(self.footFkCtrl, 'group', '%s_fkCtrls_GRP' % self.name)
        coreUtils.addParent(self.footFkCtrl, 'group', '%s_footFkCtrl_ZERO' % self.name)
        pmc.parentConstraint(self.footFkCtrl, self.tripleChain['fkChain'][1])
        self.ctrls.append(self.footFkCtrl)

        self.ballFkCtrl = controls.squareCtrl(name='%s_ball_fk_CTRL' % self.name, axis=axis, size=ctrlSize)
        coreUtils.align(self.ballFkCtrl, self.tripleChain['fkChain'][2])
        self.ballFkCtrl.setParent(self.footFkCtrl)
        coreUtils.addParent(self.ballFkCtrl, 'group', '%s_ballFkCtrl_ZERO' % self.name)
        pmc.parentConstraint(self.ballFkCtrl, self.tripleChain['fkChain'][2])
        self.ctrls.append(self.ballFkCtrl)

        coreUtils.colorize(colour, self.ctrls)

        for ctrl in self.ctrls:
            pmc.select('%s.cv[*]' % ctrl.name())
            if ctrl != self.ballPivotIkCtrl:
                pmc.scale(3.0, scaleZ=1)
            else:
                pmc.scale(3.0, scaleY=1)

        pmc.parentConstraint(self.fkCtrls_grp, fkConst_grp, mo=1)

        for joint in self.tripleChain['resultChain']:
            self.joints.append(joint)

        # connections
        self.exposeSockets({'ikFoot': self.tripleChain['ikChain'][0]})

        if cleanup:
            self.cleanup()

    def cleanup(self):
        coreUtils.attrCtrl(nodeList=self.ctrls, attrList=['tx', 'ty', 'tz', 'sx', 'sy', 'sz', 'visibility'])
        coreUtils.attrCtrl(nodeList=[self.ballPivotIkCtrl], attrList=['ry'])
        self.rig_grp.visibility.set(0)

class DrReverseFootAttrs(systemUtils.DrSystem):
    def __init__(self, name, ankle=None, foot=None, ball=None, toe=None, inner=None, outer=None, heel=None,
                 settingsNode=None, blendAttr=None, colour='red', cleanup=1):
        self.ctrls=[]
        if not ankle and len(pmc.selected()) == 7:
            sel = pmc.selected()
            ankle = sel[0]
            foot = sel[1]
            ball = sel[2]
            toe = sel[3]
            inner = sel[4]
            outer = sel[5]
            heel = sel[6]
        if not ankle:
            return 'DrReverseFoot: Please supply or select joints for Ankle, Foot, Ball, Toe, Inner, Outer and Heel positions.'
        super(DrReverseFootAttrs, self).__init__(name=name)
        self.buildFoot(ankle, foot, ball, toe, inner, outer, heel, settingsNode, blendAttr, colour, cleanup)

    def buildFoot(self, ankle, foot, ball, toe, inner, outer, heel, settingsNode, blendAttr, colour, cleanup):

        # Make duplicate joint chains
        self.tripleChain = systemUtils.tripleChain(joints=[ankle, foot, toe], name=self.name, flip=0)
        ikConst_grp = coreUtils.addParent(self.tripleChain['ikChain'][0], 'group', '%s_ikConst_GRP' % self.name)
        fkConst_grp = coreUtils.addParent(self.tripleChain['fkChain'][0], 'group', '%s_fkConst_GRP' % self.name)
        resultConst_grp = coreUtils.addParent(self.tripleChain['resultChain'][0], 'group', '%s_resultConst_GRP' % self.name)

        self.tripleChain['main_grp'].setParent(self.rig_grp)

        if blendAttr:
            par = pmc.parentConstraint(ikConst_grp, fkConst_grp, resultConst_grp, mo=0)
            attr = pmc.Attribute('%s.%sW1' % (par.name(), fkConst_grp.name()))
            blendAttr.connect(attr)
            attr = pmc.Attribute('%s.%sW0' % (par.name(), ikConst_grp.name()))
            blend_rev = coreUtils.reverse(blendAttr, 'reverse_%s_blend, UTL' % self.name)
            blend_rev.outputX.connect(attr)

            for bc in self.tripleChain['blendColors']:
                blendAttr.connect(bc.blender)

        # Orientation for controls
        axis = 'x'
        if self.tripleChain['resultChain'][1].tx.get() < 0.0:
            axis = '-x'
        ctrlSize = coreUtils.getDistance(self.tripleChain['resultChain'][0], self.tripleChain['resultChain'][1]) * .5

        # ikHandles
        ballIkHandle = pmc.ikHandle(solver='ikRPsolver',
                                    name='%s_ball_ikHandle' % self.name,
                                    startJoint=self.tripleChain['ikChain'][0],
                                    endEffector=self.tripleChain['ikChain'][1],
                                    setupForRPsolver=1)[0]
        ballIkHandle.setParent(self.rig_grp)
        ballIkHandleConst = coreUtils.addParent(ballIkHandle, 'group', '%s_ballIkHandle_CONST' % self.name)

        toeIkHandle = pmc.ikHandle(solver='ikRPsolver',
                                   name='%s_toe_ikHandle' % self.name,
                                   startJoint=self.tripleChain['ikChain'][1],
                                   endEffector=self.tripleChain['ikChain'][2],
                                   setupForRPsolver=1)[0]
        toeIkHandle.setParent(self.rig_grp)
        toeIkHandleConst = coreUtils.addParent(toeIkHandle, 'group', '%s_toeIkHandle_CONST' % self.name)

        # ikCtrls
        self.heelLoc = coreUtils.createAlignedNode(heel, 'group', '%s_heel_GRP' % self.name)
        self.heelLoc.setParent(self.rig_grp)
        self.ikRig_grp = coreUtils.addParent(self.heelLoc, 'group', '%s_heel_ZERO' % self.name)

        self.toeLoc = coreUtils.createAlignedNode(toe, 'group', '%s_toe_GRP' % self.name)
        self.toeLoc.setParent(self.heelLoc)

        self.innerLoc = coreUtils.createAlignedNode(inner, 'group', '%s_inner_GRP' % self.name)
        self.innerLoc.setParent(self.toeLoc)
        innerZero = coreUtils.addParent(self.innerLoc, 'group', '%s_inner_ZERO' % self.name)

        self.outerLoc = coreUtils.createAlignedNode(outer, 'group', '%s_outer_GRP' % self.name)
        self.outerLoc.setParent(self.innerLoc)
        outerZero = coreUtils.addParent(self.outerLoc, 'group', '%s_outer_ZERO' % self.name)

        self.ballPivotLoc = coreUtils.createAlignedNode(ball, 'group', '%s_ballPivot_GRP' % self.name)
        self.ballPivotLoc.setParent(self.outerLoc)
        coreUtils.addParent(self.ballPivotLoc, 'group', '%s_ballPivot_ZERO' % self.name)

        pmc.transformLimits(self.innerLoc, rx=(-45, 0), erx=(0, 1))

        pmc.transformLimits(self.outerLoc, rx=(0, 45), erx=(1, 0))

        self.ballLoc = coreUtils.createAlignedNode(foot, 'group', '%s_ball_GRP' % self.name)
        self.ballLoc.setParent(self.ballPivotLoc)
        self.ballZero = coreUtils.addParent(self.ballLoc, 'group', '%s_ball_ZERO' % self.name)
        self.toeWiggleLoc = coreUtils.addChild(self.ballZero, 'group', '%s_toeWiggle_GRP' % self.name)
        pmc.parentConstraint(self.ballLoc, ballIkHandleConst, mo=1)
        pmc.parentConstraint(self.toeWiggleLoc, toeIkHandleConst, mo=1)

        # driver attributes
        for attrName in ['roll_heel', 'roll_ball', 'roll_toe', 'pivot_heel', 'pivot_ball', 'pivot_toe', 'tilt_side', 'lean_ankle', 'wiggle_toe', 'lean_toe']:
            pmc.addAttr(settingsNode, ln=attrName, at='double', k=1, h=0)

        attr = pmc.Attribute('%s.roll_heel' % settingsNode.name())
        attr.connect(self.heelLoc.ry)

        attr = pmc.Attribute('%s.roll_ball' % settingsNode.name())
        attr.connect(self.ballLoc.ry)

        attr = pmc.Attribute('%s.roll_toe' % settingsNode.name())
        attr.connect(self.toeLoc.ry)

        attr = pmc.Attribute('%s.pivot_heel' % settingsNode.name())
        attr.connect(self.heelLoc.rz)

        attr = pmc.Attribute('%s.pivot_ball' % settingsNode.name())
        attr.connect(self.ballPivotLoc.rz)

        attr = pmc.Attribute('%s.pivot_toe' % settingsNode.name())
        attr.connect(self.toeLoc.rz)

        attr = pmc.Attribute('%s.tilt_side' % settingsNode.name())
        attr.connect(self.innerLoc.rx)
        attr.connect(self.outerLoc.rx)

        attr = pmc.Attribute('%s.lean_ankle' % settingsNode.name())
        attr.connect(self.ballLoc.rx)

        attr = pmc.Attribute('%s.wiggle_toe' % settingsNode.name())
        attr.connect(self.toeWiggleLoc.ry)

        attr = pmc.Attribute('%s.lean_toe' % settingsNode.name())
        attr.connect(self.toeWiggleLoc.rx)


        # fkCtrl
        self.ballFkCtrl = controls.pinCtrl(name='%s_ball_fk_CTRL' % self.name, axis=axis, radius=ctrlSize)
        coreUtils.align(self.ballFkCtrl, self.tripleChain['fkChain'][1])
        self.ballFkCtrl.setParent(self.ctrls_grp)
        self.ballFkCtrlZero = coreUtils.addParent(self.ballFkCtrl, 'group', '%s_ballFkCtrl_ZERO' % self.name)
        pmc.parentConstraint(self.ballFkCtrl, self.tripleChain['fkChain'][1])

        coreUtils.colorize(colour, [self.ballFkCtrl])

        pmc.parentConstraint(self.ballFkCtrlZero, fkConst_grp, mo=1)

        for joint in self.tripleChain['resultChain']:
            self.joints.append(joint)

        # connections
        self.exposeSockets({'ikFoot': self.tripleChain['ikChain'][0]})

        if cleanup:
            self.cleanup()

    def cleanup(self):
        coreUtils.attrCtrl(nodeList=self.ctrls, attrList=['tx', 'ty', 'tz', 'sx', 'sy', 'sz', 'visibility'])
        self.rig_grp.visibility.set(0)
