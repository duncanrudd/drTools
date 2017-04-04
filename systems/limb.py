import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls

reload(controls)
reload(coreUtils)
reload(systemUtils)

class DrLimb(systemUtils.DrSystem):
    def __init__(self, name='', joints=None, leg=0, cleanup=1):
        if not joints and len(pmc.selected()) == 4:
            joints = pmc.selected()
        self.ctrls = []
        super(DrLimb, self).__init__(name)
        self.buildLimb(joints, leg, cleanup)

    def buildLimb(self, joints, leg, cleanup):
        if not joints:
            return 'DrLimb: Please supply 4 joints to build limb from'

        # Make duplicate joint chains
        self.tripleChain = systemUtils.tripleChain(joints=joints, name=self.name, flip=1)

        self.tripleChain['main_grp'].setParent(self.rig_grp)
        self.const_grp = coreUtils.addParent(self.tripleChain['main_grp'], 'group', '%s_const_grp' % self.name)

        # Orientation for controls and aim constraints
        axis='x'
        aimVec = (1, 0, 0)
        if self.tripleChain['resultChain'][1].tx.get() < 0.0:
            axis='-x'
            aimVec = (-1, 0, 0)
        ctrlSize = coreUtils.getDistance(self.tripleChain['resultChain'][0], self.tripleChain['resultChain'][1]) * .25

        # CONTROLS
        # settings ctrl
        self.settingsCtrl = controls.crossCtrl(name='%s_settings_CTRL' % self.name, size=ctrlSize)
        self.settingsCtrl.setParent(self.tripleChain['resultChain'][2])
        settingsOffset = ctrlSize * 1.5
        if self.tripleChain['resultChain'][2].tx.get() < 0.0:
            settingsOffset = ctrlSize * -1.5
        if leg:
            settingsOffset = settingsOffset * -1
        self.settingsCtrl.t.set((0, settingsOffset, 0))
        self.settingsCtrl.r.set(0, 0, 0)
        self.settingsCtrl.setParent(self.ctrls_grp)
        pmc.parentConstraint(self.tripleChain['resultChain'][2], self.settingsCtrl, mo=1)
        self.ctrls.append(self.settingsCtrl)
        pmc.addAttr(self.settingsCtrl, ln='ik_fk_blend', at='double', k=1, h=0, minValue=0.0, maxValue=1.0)
        for bc in self.tripleChain['blendColors']:
            self.settingsCtrl.ik_fk_blend.connect(bc.blender)

        # fk top ctrl
        self.fkTopCtrl = controls.circleBumpCtrl(name='%s_top_fk_CTRL' % self.name, axis=axis, radius=ctrlSize)
        coreUtils.align(self.fkTopCtrl, self.tripleChain['fkChain'][0])
        self.fkTopCtrl.setParent(self.ctrls_grp)
        self.fkCtrls_grp = coreUtils.addParent(self.fkTopCtrl, 'group', '%s_fkCtrls_grp' % self.name)
        self.fkCtrlsConst_grp = coreUtils.addParent(self.fkTopCtrl, 'group', '%s_fkConst_grp' % self.name)
        pmc.parentConstraint(self.fkCtrls_grp, self.const_grp)
        self.ctrls.append(self.fkTopCtrl)

        self.settingsCtrl.ik_fk_blend.connect(self.fkCtrls_grp.visibility)

        # fk mid ctrl
        self.fkMidCtrl = controls.circleBumpCtrl(name='%s_mid_fk_CTRL' % self.name, axis=axis, radius=ctrlSize)
        coreUtils.align(self.fkMidCtrl, self.tripleChain['fkChain'][1])
        self.fkMidCtrl.setParent(self.fkTopCtrl)
        coreUtils.addParent(self.fkMidCtrl, 'group', '%s_mid_fkCtrl_ZERO' % self.name)
        self.ctrls.append(self.fkMidCtrl)

        # fk btm ctrl
        self.fkBtmCtrl = controls.circleBumpCtrl(name='%s_btm_fk_CTRL' % self.name, axis=axis, radius=ctrlSize)
        coreUtils.align(self.fkBtmCtrl, self.tripleChain['fkChain'][2])
        self.fkBtmCtrl.setParent(self.fkMidCtrl)
        coreUtils.addParent(self.fkBtmCtrl, 'group', '%s_btm_fkCtrl_ZERO' % self.name)
        self.ctrls.append(self.fkBtmCtrl)


        # rotate order
        for node in [self.fkMidCtrl, self.tripleChain['resultChain'][1], self.tripleChain['ikChain'][1], self.tripleChain['fkChain'][1]]:
            node.rotateOrder.set(3)

        pmc.parentConstraint(self.fkTopCtrl, self.tripleChain['fkChain'][0])
        pmc.parentConstraint(self.fkMidCtrl, self.tripleChain['fkChain'][1]).rotateOrder.set(4)
        pmc.parentConstraint(self.fkBtmCtrl, self.tripleChain['fkChain'][2])

        # IK ctrl
        self.ikCtrl = controls.boxCtrl(name='%s_ik_CTRL' % self.name, size=ctrlSize)
        coreUtils.align(self.ikCtrl, self.tripleChain['ikChain'][2], orient=0)
        self.ikCtrl.setParent(self.ctrls_grp)
        self.ikCtrls_grp = coreUtils.addParent(self.ikCtrl, 'group', '%s_ikCtrls_ZERO' % self.name)
        self.ctrls.append(self.ikCtrl)

        ik_fk_rev = coreUtils.reverse(self.settingsCtrl.ik_fk_blend, 'rev_%s_ik_fk_blend_UTL' % self.name)
        ik_fk_rev.outputX.connect(self.ikCtrls_grp.visibility)

        pmc.addAttr( self.ikCtrl, longName='stretch', at='double', minValue=0, maxValue=1, defaultValue=0, keyable=True )
        pmc.addAttr( self.ikCtrl, longName='twist', at='double', keyable=True )
        pmc.addAttr( self.ikCtrl, longName='soft', at='double', minValue=0, defaultValue=0, keyable=True )
        pmc.addAttr( self.ikCtrl, longName='mid_pin', at='double', keyable=True, minValue=0, maxValue=1 )
        pmc.addAttr( self.ikCtrl, longName='flip_poleVector', at='bool', keyable=True, h=0 )
        pmc.addAttr( self.ikCtrl, longName='force_straight', at='double', keyable=True, h=0, minValue=0.0, maxValue=1.0 )
		
        for bc in self.tripleChain['flipBlendColors']:
            self.ikCtrl.flip_poleVector.connect(bc.blender)
        
        # Soft non-stretchy IK stuff
        ik_grp = coreUtils.addChild(self.rig_grp, 'group', name='%s_ik_GRP' % self.name)
        
        softBlend_loc = coreUtils.createAlignedNode(self.ikCtrl, 'locator', name='%s_ikSoftBlend_LOC' % self.name)
        softBlend_loc.setParent(ik_grp)
    
        self.ctrl_loc = coreUtils.createAlignedNode(self.ikCtrl, 'locator', name='%s_ikCtrl_LOC' % self.name)
        self.ctrl_loc.setParent(ik_grp)
        if not leg:
            pmc.parentConstraint(self.ikCtrl, self.ctrl_loc)
    
        aim_loc = coreUtils.addChild(self.const_grp, 'locator', name='%s_softIkaim_LOC' % self.name)
        pmc.aimConstraint(self.ctrl_loc, aim_loc, upVector=(0, 0, 0))

        btm_loc = coreUtils.createAlignedNode(self.ikCtrl, 'locator', name='%s_ikBtm_LOC' % self.name)
        btm_loc.setParent(aim_loc)

        chainLen = abs(self.tripleChain['ikChain'][1].tx.get() + self.tripleChain['ikChain'][2].tx.get())

        ctrlDist = coreUtils.distanceBetweenNodes(aim_loc, self.ctrl_loc, name='dist_%s_ikCtrl_UTL' % self.name)
        globalScaleDiv = coreUtils.divide(1.0, self.main_grp.globalScale, name='md_%s_globalScaleDiv_UTL' % self.name)
        isStretchedMult = coreUtils.multiply(ctrlDist.distance, globalScaleDiv.outputX, name='md_%s_isStretched_UTL' % self.name)

        softDist = coreUtils.distanceBetweenNodes(btm_loc, softBlend_loc, name='dist_%s_soft_UTL' % self.name)
        stretchDist = coreUtils.distanceBetweenNodes(aim_loc, softBlend_loc, name='dist_%s_stretch_UTL' % self.name)
    
        chainLenMinusSoft = coreUtils.minus([chainLen, self.ikCtrl.soft], name='pma_%s_chainLenMinusSoft_UTL' % self.name)
    
        isStretchedCond = pmc.createNode('condition', name='cond_%s_isStretched_UTL' % self.name)
        isStretchedCond.operation.set(2)
        isStretchedMult.outputX.connect(isStretchedCond.firstTerm)
        chainLenMinusSoft.output1D.connect(isStretchedCond.secondTerm)
        isStretchedMult.outputX.connect(isStretchedCond.colorIfFalseR)
    
        isSoftCond = pmc.createNode('condition', name='cond_%s_isSoft_UTL' % self.name)
        isSoftCond.operation.set(2)
        self.ikCtrl.soft.connect(isSoftCond.firstTerm)
        isSoftCond.colorIfFalseR.set(chainLen)
    
        ctrlDistMinusSoftChain = coreUtils.minus([isStretchedMult.outputX, chainLenMinusSoft.output1D], name='pmc_%s_ctrlDistMinusSoftChain_UTL' % self.name)
    
        divideBySoft = coreUtils.safeDivide(ctrlDistMinusSoftChain.output1D, self.ikCtrl.soft, name='md_%s_divideBySoft_UTL' % self.name)
    
        invert = coreUtils.multiply(divideBySoft.outputX, -1, name='md_%s_invertSoft_UTL' % self.name)
    
        exp = coreUtils.pow(2.718282, invert.outputX, name='md_%s_exponential_UTL' % self.name)
    
        multiplyBySoft = coreUtils.multiply(exp.outputX, self.ikCtrl.soft, name='md_%s_multiplyBySoft_UTL' % self.name)
    
        minusFromChainLen = coreUtils.minus([chainLen, multiplyBySoft.outputX], name='md_%s_minusFromChainLen_UTL' % self.name)
    
        minusFromChainLen.output1D.connect(isSoftCond.colorIfTrueR)
    
        isSoftCond.outColorR.connect(isStretchedCond.colorIfTrueR)
    
        isStretchedCond.outColorR.connect(btm_loc.tx)
    
        # IK Solvers
        ikHandleGrp = coreUtils.createAlignedNode(self.ikCtrl, 'group', name='%s_ikHandle_GRP' % self.name)
        ikHandleGrp.setParent(softBlend_loc)
        pmc.orientConstraint(self.ikCtrl, ikHandleGrp, mo=1)

        ikHandle = pmc.ikHandle(solver='ikRPsolver',
                                name='%s_ikHandle' % self.name,
                                startJoint=self.tripleChain['ikChain'][0],
                                endEffector=self.tripleChain['ikChain'][2],
                                setupForRPsolver=1)[0]
        ikHandle.setParent(ikHandleGrp)
        self.ikCtrl.twist.connect(ikHandle.twist)

        endIkHandle = pmc.ikHandle(solver='ikSCsolver',
                                   name='%s_end_ikHandle' % self.name,
                                   startJoint=self.tripleChain['ikChain'][2],
                                   endEffector=self.tripleChain['ikChain'][3],
                                   setupForRPsolver=1)[0]
        endIkHandle.setParent(ikHandleGrp)
		
        # Flipped solvers
        flip_ikHandle = pmc.ikHandle(solver='ikRPsolver',
                                name='%s_flip_ikHandle' % self.name,
                                startJoint=self.tripleChain['flipChain'][0],
                                endEffector=self.tripleChain['flipChain'][2],
                                setupForRPsolver=1)[0]
        flip_ikHandle.setParent(ikHandleGrp)
        self.ikCtrl.twist.connect(flip_ikHandle.twist)

        flip_endIkHandle = pmc.ikHandle(solver='ikSCsolver',
                                   name='%s_flip_end_ikHandle' % self.name,
                                   startJoint=self.tripleChain['flipChain'][2],
                                   endEffector=self.tripleChain['flipChain'][3],
                                   setupForRPsolver=1)[0]
        flip_endIkHandle.setParent(ikHandleGrp)
		
        self.tripleChain['flipChain'][1].preferredAngleY.set(self.tripleChain['flipChain'][1].preferredAngleY.get() * -1)

        # Pole Vector
        pvAimGrp = coreUtils.addChild(self.const_grp, 'group', name='%s_pvAim_GRP' % self.name)
        if leg:
            pmc.aimConstraint(btm_loc, pvAimGrp, mo=0, u=(0, 1, 0), wu=(1, 0, 0),
                              wut='objectRotation', wuo=self.ctrl_loc, aimVector=aimVec)
        else:
            pmc.aimConstraint(btm_loc, pvAimGrp, mo=0, u=(0, 0, 0), aimVector=aimVec)
        self.pvCtrl = controls.crossCtrl(name='%s_pv_CTRL' % self.name, size=ctrlSize)
        poleOffset = 3
        if '-' in axis:
            poleOffset = -3
        self.pvCtrl.setParent(self.tripleChain['ikChain'][1])
        self.pvCtrl.t.set((0, 0, ctrlSize * poleOffset))
        self.pvCtrl.setParent(self.ikCtrls_grp)
        self.pvZero = coreUtils.addParent(self.pvCtrl, 'group', '%s_pvCtrl_ZERO' % self.name)
        pmc.poleVectorConstraint(self.pvCtrl, ikHandle)
        self.ctrls.append(self.pvCtrl)
        
        self.flipPvCtrl = controls.crossCtrl(name='%s_flip_pv_CTRL' % self.name, size=ctrlSize)
        self.flipPvCtrl.setParent(self.tripleChain['flipChain'][1])
        self.flipPvCtrl.t.set((0, 0, ctrlSize * (poleOffset*-1)))
        self.flipPvCtrl.setParent(self.pvZero)
        self.flipPvZero = coreUtils.addParent(self.flipPvCtrl, 'group', '%s_flipPvCtrl_ZERO' % self.name)
        pmc.poleVectorConstraint(self.flipPvCtrl, flip_ikHandle)
        self.ctrls.append(self.flipPvCtrl)

        
        # stretchy soft IK stuff
        pc = pmc.pointConstraint(btm_loc, self.ctrl_loc, softBlend_loc)
        stretchRev = coreUtils.reverse(self.ikCtrl.stretch, name='rev_%s_stretch_UTL' % self.name)
        stretchRev.outputX.connect('%s.%sW0' % (pc.nodeName(), btm_loc.nodeName()))
        self.ikCtrl.stretch.connect('%s.%sW1' % (pc.nodeName(), self.ctrl_loc.nodeName()))
    
        scaledSoftDist = coreUtils.multiply(globalScaleDiv.outputX, softDist.distance, name='md_%s_scaledSoftDist_UTL' % self.name)
    
        # Stretchy Mid
        midLen = coreUtils.multiply((self.tripleChain['ikChain'][1].tx.get() / chainLen), scaledSoftDist.outputX, name='md_%s_midLen_UTL' % self.name)
    
        stretchMidLen = coreUtils.multiply(self.ikCtrl.stretch, midLen.outputX, name='md_%s_stretchMidLen_UTL' % self.name)
    
        stretchMidLenPlusBoneLen = coreUtils.add([self.tripleChain['ikChain'][1].tx.get(), stretchMidLen.outputX], name='pma_%s_stretchMidLenPlusBoneLen_UTL' % self.name)
    
        pinUpperDist = coreUtils.distanceBetweenNodes(self.const_grp, self.pvCtrl, name='dist_%s_pinUpper_UTL' % self.name)
        pinMult = 1.0
        if '-' in axis:
            pinMult = -1.0
        pinUpper_uc = coreUtils.convert(pinUpperDist.distance, pinMult, name='uc_%s_pinUpperDist_UTL' % self.name)
        pinUpperGlobalScale = coreUtils.multiply(globalScaleDiv.outputX, pinUpper_uc.output, name='md_%s_pinUpperGlobalScale_UTL' % self.name)
        pinUpperBlend = coreUtils.blend(input1=pinUpperGlobalScale.outputX, input2=stretchMidLenPlusBoneLen.output1D, blendAttr=self.ikCtrl.mid_pin, name='bc_%s_pinUpper_UTL' % self.name)
    
        # pinUpperBlend.outputR.connect(self.tripleChain['ikChain'][1].tx)
        # pinUpperBlend.outputR.connect(self.tripleChain['flipChain'][1].tx)
    
        # Stretchy Bot
        botLen = coreUtils.multiply((self.tripleChain['ikChain'][2].tx.get() / chainLen), scaledSoftDist.outputX, name='md_%s_botLen_UTL' % self.name)
    
        stretchBotLen = coreUtils.multiply(self.ikCtrl.stretch, botLen.outputX, name='md_%s_stretchBotLen_UTL' % self.name)
    
        stretchBotLenPlusBoneLen = coreUtils.add([self.tripleChain['ikChain'][2].tx.get(), stretchBotLen.outputX], name='pma_%s_stretchBotLenPlusBoneLen_UTL' % self.name)
    
        pinLowerDist = coreUtils.distanceBetweenNodes(softBlend_loc, self.pvCtrl, name='dist_%s_pinLower_UTL' % self.name)
        pinLower_uc = coreUtils.convert(pinLowerDist.distance, pinMult, name='uc_%s_pinLowerDist_UTL' % self.name)
        pinLowerGlobalScale = coreUtils.multiply(globalScaleDiv.outputX, pinLower_uc.output, name='md_%s_pinLowerGlobalScale_UTL' % self.name)
        pinLowerBlend = coreUtils.blend(input1=pinLowerGlobalScale.outputX, input2=stretchBotLenPlusBoneLen.output1D, blendAttr=self.ikCtrl.mid_pin, name='bc_%s_pinLower_UTL' % self.name)
    
        # pinLowerBlend.outputR.connect(self.tripleChain['ikChain'][2].tx)
        # pinLowerBlend.outputR.connect(self.tripleChain['flipChain'][2].tx)

        # Add ability to force straight arm
        straightUpper_md = coreUtils.multiply(stretchDist.distance, self.tripleChain['ikChain'][1].tx.get() / chainLen, name='md_%s_midLenTimesChainLen_UTL' % self.name)
        straightLower_md = coreUtils.multiply(stretchDist.distance, self.tripleChain['ikChain'][2].tx.get() / chainLen, name='md_%s_botLenTimesChainLen_UTL' % self.name)
        straightUpperBlend = coreUtils.blend(input1=straightUpper_md.outputX, input2=pinUpperBlend.outputR, blendAttr=self.ikCtrl.force_straight, name='bc_%s_straightUpper_UTL' % self.name)
        straightLowerBlend = coreUtils.blend(input1=straightLower_md.outputX, input2=pinLowerBlend.outputR, blendAttr=self.ikCtrl.force_straight, name='bc_%s_straightLower_UTL' % self.name)
        straightUpperBlend.outputR.connect(self.tripleChain['ikChain'][1].tx)
        straightLowerBlend.outputR.connect(self.tripleChain['ikChain'][2].tx)
        straightUpperBlend.outputR.connect(self.tripleChain['flipChain'][1].tx)
        straightLowerBlend.outputR.connect(self.tripleChain['flipChain'][2].tx)
        
        # Extract twist
        self.topTwist = coreUtils.extractAxis(self.tripleChain['resultChain'][0], axis='x', name='%s_top_twist' % self.name, exposeNode=self.main_grp, exposeAttr='top_twist')
        self.topTwist['main_grp'].setParent(self.rig_grp)
        pmc.parentConstraint(self.const_grp, self.topTwist['main_grp'])
        
        self.midTwist = coreUtils.extractAxis(self.tripleChain['resultChain'][1], axis='x', name='%s_mid_twist' % self.name, exposeNode=self.main_grp, exposeAttr='mid_twist')
        self.midTwist['main_grp'].setParent(self.rig_grp)
        pmc.pointConstraint(self.tripleChain['resultChain'][1], self.midTwist['main_grp'])
        pmc.orientConstraint(self.topTwist['nonRoll'], self.midTwist['main_grp'])
        
        btmTwist = coreUtils.extractAxis(self.tripleChain['resultChain'][2], axis='x', name='%s_btm_twist' % self.name, exposeNode=self.main_grp, exposeAttr='btm_twist')
        btmTwist['main_grp'].setParent(self.rig_grp)
        pmc.pointConstraint(self.tripleChain['resultChain'][2], btmTwist['main_grp'])
        pmc.orientConstraint(self.tripleChain['resultChain'][1], btmTwist['main_grp'])

        # connections
        self.exposeSockets({'poleVectorAim': pvAimGrp})
        self.exposeSockets({'ikCtrl': self.ikCtrl, 'fkCtrl': self.fkBtmCtrl})
        self.exposeSockets({'wrist': self.tripleChain['resultChain'][2]})

        if cleanup:
            self.cleanup()

    def cleanup(self):
        print 'cleaning up'
        coreUtils.attrCtrl(nodeList=[self.fkMidCtrl, self.fkBtmCtrl], attrList=['ty', 'tz','sx', 'sy', 'sz', 'visibility'])
        coreUtils.attrCtrl(nodeList=[self.fkTopCtrl], attrList=['tx', 'ty', 'tz','sx', 'sy', 'sz', 'visibility'])
        coreUtils.attrCtrl(nodeList=[self.ikCtrl], attrList=['sx', 'sy', 'sz', 'visibility'])
        coreUtils.attrCtrl(nodeList=[self.pvCtrl], attrList=['rx', 'ry', 'rz','sx', 'sy', 'sz', 'visibility'])
        coreUtils.attrCtrl(nodeList=[self.settingsCtrl], attrList=['tx', 'ty', 'tz',
                                                                   'rx', 'ry', 'rz',
                                                                   'sx', 'sy', 'sz', 'visibility'])
        self.rig_grp.visibility.set(0)



