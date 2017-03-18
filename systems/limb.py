import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls

reload(controls)
reload(coreUtils)
reload(systemUtils)

class DrLimb(systemUtils.DrSystem):
    def __init__(self, name='', joints=None, cleanup=1):
        if not joints and len(pmc.selected()) == 4:
            joints = pmc.selected()
        if not joints:
            return 'DrLimb: Please supply 4 joints to build limb from'
        self.ctrls = []
        super(DrLimb, self).__init__(name)
        self.buildLimb(joints, cleanup)

    def buildLimb(self, joints, cleanup):

        # Make duplicate joint chains
        self.tripleChain = systemUtils.tripleChain(joints=joints, name=self.name)

        pmc.addAttr(self.main_grp, ln='ik_fk_blend', at='double', k=1, h=0, minValue=0.0, maxValue=1.0)
        for bc in self.tripleChain['blendColors']:
            self.main_grp.ik_fk_blend.connect(bc.blender)

        self.tripleChain['main_grp'].setParent(self.rig_grp)
        const_grp = coreUtils.addParent(self.tripleChain['main_grp'], 'group', '%s_const_GRP' % self.name)

        # Orientation for controls and aim constraints
        axis='x'
        aimVec = (1, 0, 0)
        if self.tripleChain['resultChain'][1].tx.get() < 0.0:
            axis='-x'
            aimVec = (-1, 0, 0)
        ctrlSize = coreUtils.getDistance(self.tripleChain['resultChain'][0], self.tripleChain['resultChain'][1]) * .25

        # CONTROLS
        # fk top ctrl
        self.fkTopCtrl = controls.circleBumpCtrl(name='%s_top_fk_CTRL' % self.name, axis=axis, radius=ctrlSize)
        coreUtils.align(self.fkTopCtrl, self.tripleChain['fkChain'][0])
        self.fkTopCtrl.setParent(self.ctrls_grp)
        fkCtrls_grp = coreUtils.addParent(self.fkTopCtrl, 'group', '%s_fkCtrls_GRP' % self.name)
        self.ctrls.append(self.fkTopCtrl)

        self.main_grp.ik_fk_blend.connect(fkCtrls_grp.visibility)

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

        pmc.parentConstraint(self.fkTopCtrl, self.tripleChain['fkChain'][0])
        pmc.parentConstraint(self.fkMidCtrl, self.tripleChain['fkChain'][1])
        pmc.parentConstraint(self.fkBtmCtrl, self.tripleChain['fkChain'][2])

        # IK ctrl
        self.ikCtrl = controls.boxCtrl(name='%s_ik_CTRL' % self.name, size=ctrlSize)
        coreUtils.align(self.ikCtrl, self.tripleChain['ikChain'][2])
        self.ikCtrl.setParent(self.ctrls_grp)
        self.ikCtrls_grp = coreUtils.addParent(self.ikCtrl, 'group', '%s_self.ikCtrls_GRP' % self.name)
        self.ctrls.append(self.ikCtrl)

        ik_fk_rev = coreUtils.reverse(self.main_grp.ik_fk_blend, 'rev_%s_ik_fk_blend_UTL' % self.name)
        ik_fk_rev.outputX.connect(self.ikCtrls_grp.visibility)

        pmc.addAttr( self.ikCtrl, longName='stretch', at='double', minValue=0, maxValue=1, defaultValue=0, keyable=True )
        pmc.addAttr( self.ikCtrl, longName='twist', at='double', keyable=True )
        pmc.addAttr( self.ikCtrl, longName='soft', at='double', minValue=0, defaultValue=0, keyable=True )
        pmc.addAttr( self.ikCtrl, longName='mid_pin', at='double', keyable=True, minValue=0, maxValue=1 )
        
        # Soft non-stretchy IK stuff
        ik_grp = coreUtils.addChild(self.rig_grp, 'group', name='%s_ik_GRP' % self.name)
        
        softBlend_loc = coreUtils.createAlignedNode(self.ikCtrl, 'locator', name='%s_ikSoftBlend_LOC' % self.name)
        softBlend_loc.setParent(ik_grp)
    
        ctrl_loc = coreUtils.createAlignedNode(self.ikCtrl, 'locator', name='%s_self.ikCtrl_LOC' % self.name)
        ctrl_loc.setParent(ik_grp)
        pmc.parentConstraint(self.ikCtrl, ctrl_loc)
    
        aim_loc = coreUtils.addChild(const_grp, 'locator', name='%s_softIkaim_LOC' % self.name)
        pmc.aimConstraint(ctrl_loc, aim_loc, upVector=(0, 0, 0))
    
        btm_loc = coreUtils.createAlignedNode(self.ikCtrl, 'locator', name='%s_ikBtm_LOC' % self.name)
        btm_loc.setParent(aim_loc)
        
        chainLen = abs(self.tripleChain['ikChain'][1].tx.get() + self.tripleChain['ikChain'][2].tx.get())
    
        ctrlDist = coreUtils.distanceBetweenNodes(aim_loc, ctrl_loc, name='dist_%s_self.ikCtrl_UTL' % self.name)
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

        # Pole Vector
        pvAimGrp = coreUtils.addChild(const_grp, 'group', name='%s_pvAim_GRP' % self.name)
        pmc.aimConstraint(btm_loc, pvAimGrp, mo=0, u=(0, 0, 0), aimVector=aimVec)
        self.pvCtrl = controls.crossCtrl(name='%s_pv_CTRL' % self.name, size=ctrlSize)
        poleOffset = 1
        if '-' in axis:
            poleOffset = -1
        self.pvCtrl.setParent(self.tripleChain['ikChain'][1])
        self.pvCtrl.t.set((0, 0, ctrlSize * poleOffset))
        self.pvCtrl.setParent(pvAimGrp)
        pvZero = coreUtils.addParent(self.pvCtrl, 'group', '%s_pvCtrl_ZERO' % self.name)
        pmc.poleVectorConstraint(self.pvCtrl, ikHandle)
        self.ctrls.append(self.pvCtrl)

        
        # stretchy soft IK stuff
        pc = pmc.pointConstraint(btm_loc, ctrl_loc, softBlend_loc)
        stretchRev = coreUtils.reverse(self.ikCtrl.stretch, name='rev_%s_stretch_UTL' % self.name)
        stretchRev.outputX.connect('%s.%sW0' % (pc.nodeName(), btm_loc.nodeName()))
        self.ikCtrl.stretch.connect('%s.%sW1' % (pc.nodeName(), ctrl_loc.nodeName()))
    
        scaledSoftDist = coreUtils.multiply(globalScaleDiv.outputX, softDist.distance, name='md_%s_scaledSoftDist_UTL' % self.name)
    
        # Stretchy Mid
        midLen = coreUtils.multiply((self.tripleChain['ikChain'][1].tx.get() / chainLen), scaledSoftDist.outputX, name='md_%s_midLen_UTL' % self.name)
    
        stretchMidLen = coreUtils.multiply(self.ikCtrl.stretch, midLen.outputX, name='md_%s_stretchMidLen_UTL' % self.name)
    
        stretchMidLenPlusBoneLen = coreUtils.add([self.tripleChain['ikChain'][1].tx.get(), stretchMidLen.outputX], name='pma_%s_stretchMidLenPlusBoneLen_UTL' % self.name)
    
        pinUpperDist = coreUtils.distanceBetweenNodes(const_grp, self.pvCtrl, name='dist_%s_pinUpper_UTL' % self.name)
        pinMult = 1.0
        if '-' in axis:
            pinMult = -1.0
        pinUpper_uc = coreUtils.convert(pinUpperDist.distance, pinMult, name='uc_%s_pinUpperDist_UTL' % self.name)
        pinUpperGlobalScale = coreUtils.multiply(globalScaleDiv.outputX, pinUpper_uc.output, name='md_%s_pinUpperGlobalScale_UTL' % self.name)
        pinUpperBlend = coreUtils.blend(input1=pinUpperGlobalScale.outputX, input2=stretchMidLenPlusBoneLen.output1D, blendAttr=self.ikCtrl.mid_pin, name='bc_%s_pinUpper_UTL')
    
        pinUpperBlend.outputR.connect(self.tripleChain['ikChain'][1].tx)
    
        # Stretchy Bot
        botLen = coreUtils.multiply((self.tripleChain['ikChain'][2].tx.get() / chainLen), scaledSoftDist.outputX, name='md_%s_botLen_UTL' % self.name)
    
        stretchBotLen = coreUtils.multiply(self.ikCtrl.stretch, botLen.outputX, name='md_%s_stretchBotLen_UTL' % self.name)
    
        stretchBotLenPlusBoneLen = coreUtils.add([self.tripleChain['ikChain'][2].tx.get(), stretchBotLen.outputX], name='pma_%s_stretchBotLenPlusBoneLen_UTL' % self.name)
    
        pinLowerDist = coreUtils.distanceBetweenNodes(softBlend_loc, self.pvCtrl, name='dist_%s_pinLower_UTL' % self.name)
        pinLower_uc = coreUtils.convert(pinLowerDist.distance, pinMult, name='uc_%s_pinLowerDist_UTL' % self.name)
        pinLowerGlobalScale = coreUtils.multiply(globalScaleDiv.outputX, pinLower_uc.output, name='md_%s_pinLowerGlobalScale_UTL' % self.name)
        pinLowerBlend = coreUtils.blend(input1=pinLowerGlobalScale.outputX, input2=stretchBotLenPlusBoneLen.output1D, blendAttr=self.ikCtrl.mid_pin, name='bc_%s_pinLower_UTL')
    
        pinLowerBlend.outputR.connect(self.tripleChain['ikChain'][2].tx)
        
        # Extract twist
        topTwist = coreUtils.extractAxis(self.tripleChain['resultChain'][0], axis='x', name='%s_top_twist' % self.name, exposeNode=self.main_grp, exposeAttr='top_twist')
        topTwist['main_grp'].setParent(self.rig_grp)
        pmc.parentConstraint(const_grp, topTwist['main_grp'])
        
        midTwist = coreUtils.extractAxis(self.tripleChain['resultChain'][1], axis='x', name='%s_mid_twist' % self.name, exposeNode=self.main_grp, exposeAttr='mid_twist')
        midTwist['main_grp'].setParent(self.rig_grp)
        pmc.pointConstraint(self.tripleChain['resultChain'][1], midTwist['main_grp'])
        pmc.orientConstraint(self.tripleChain['resultChain'][0], midTwist['main_grp'])
        
        btmTwist = coreUtils.extractAxis(self.tripleChain['resultChain'][2], axis='x', name='%s_btm_twist' % self.name, exposeNode=self.main_grp, exposeAttr='btm_twist')
        btmTwist['main_grp'].setParent(self.rig_grp)
        pmc.pointConstraint(self.tripleChain['resultChain'][2], btmTwist['main_grp'])
        pmc.orientConstraint(self.tripleChain['resultChain'][1], btmTwist['main_grp'])

        # connections
        self.exposeSockets({'start': topTwist['nonRoll'],
                            'mid': midTwist['nonRoll'],
                            'end': self.tripleChain['resultChain'][2]})

        if cleanup:
            self.cleanup()

    def cleanup(self):
        print 'cleaning up'
        coreUtils.attrCtrl(nodeList=[self.fkMidCtrl, self.fkBtmCtrl], attrList=['ty', 'tz','sx', 'sy', 'sz', 'visibility'])
        coreUtils.attrCtrl(nodeList=[self.fkTopCtrl], attrList=['tx', 'ty', 'tz','sx', 'sy', 'sz', 'visibility'])
        coreUtils.attrCtrl(nodeList=[self.ikCtrl], attrList=['sx', 'sy', 'sz', 'visibility'])
        coreUtils.attrCtrl(nodeList=[self.pvCtrl], attrList=['rx', 'ry', 'rz','sx', 'sy', 'sz', 'visibility'])
        self.rig_grp.visibility.set(0)



