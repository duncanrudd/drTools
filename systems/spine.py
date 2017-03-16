import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.curveUtils as curveUtils
import drTools.systems.controls as controls
reload(systemUtils)
reload(curveUtils)
reload(coreUtils)
reload(controls)

class DrSpine(systemUtils.DrSystem):

    def __init__(self, name, start=None, end=None, rtHip=None, lfHip=None, rtShldr=None, rtClav=None, lfShldr=None, lfClav=None, numJoints=8, cleanup=1):
        startPos, endPos = coreUtils.getStartAndEnd(start, end)
        if not startPos or not endPos:
            return 'DrSpine: Unable to determine start and end positions'

        super(DrSpine, self).__init__(name)
        self.ctrls = []
        self.jnts = []
        self.buildSpine(startPos, endPos, rtHip, lfHip, rtShldr, rtClav, lfShldr, lfClav, numJoints, cleanup)

    def buildSpine(self, startPos, endPos, rtHip, lfHip, rtShldr, rtClav, lfShldr, lfClav, numJoints, cleanup):
        self.noXform_grp = coreUtils.addChild(self.rig_grp, 'group', name='%s_noXform_GRP' % self.name)
        self.noXform_grp.inheritsTransform.set(0)

        # Create curve
        self.crv = curveUtils.curveBetweenNodes(startPos, endPos, numCVs=5, name=self.name)
        self.crv.setParent(self.noXform_grp)
        self.crvLocs = curveUtils.connectCurve(self.crv)

        # controls
        ctrlSize = coreUtils.getDistance(startPos, endPos) * .33

        #Body
        self.body_ctrl = controls.circleBumpCtrl(name='%s_body_CTRL' % self.name, axis='y', radius=ctrlSize)
        self.body_ctrl.setParent(self.ctrls_grp)
        coreUtils.align(self.body_ctrl, self.crvLocs[0])
        self.bodyZero_grp = coreUtils.addParent(self.body_ctrl, 'group', name='%s_body_ZERO' % self.name)
        self.ctrls.append(self.body_ctrl)

        self.bodySub_ctrl = controls.circleBumpCtrl(name='%s_bodySub_CTRL' % self.name, axis='y', radius=ctrlSize*.8)
        self.bodySub_ctrl.setParent(self.body_ctrl)
        coreUtils.align(self.bodySub_ctrl, self.crvLocs[0])
        self.ctrls.append(self.bodySub_ctrl)

        #FK
        self.fk1_ctrl = controls.circleBumpCtrl(name='%s_fk01_CTRL' % self.name, axis='y', radius=ctrlSize*.5)
        self.fk1_ctrl.setParent(self.bodySub_ctrl)
        coreUtils.align(self.fk1_ctrl, self.crvLocs[1])
        fk1Zero_grp = coreUtils.addParent(self.fk1_ctrl, 'group', name='%s_fk01_ZERO' % self.name)
        self.ctrls.append(self.fk1_ctrl)

        self.fk2_ctrl = controls.circleBumpCtrl(name='%s_fk02_CTRL' % self.name, axis='y', radius=ctrlSize*.5)
        self.fk2_ctrl.setParent(self.fk1_ctrl)
        coreUtils.align(self.fk2_ctrl, self.crvLocs[2])
        fk2Zero_grp = coreUtils.addParent(self.fk2_ctrl, 'group', name='%s_fk02_ZERO' % self.name)
        self.ctrls.append(self.fk2_ctrl)

        self.fk3_ctrl = controls.circleBumpCtrl(name='%s_fk03_CTRL' % self.name, axis='y', radius=ctrlSize*.5)
        self.fk3_ctrl.setParent(self.fk2_ctrl)
        coreUtils.align(self.fk3_ctrl, self.crvLocs[3])
        fk3Zero_grp = coreUtils.addParent(self.fk3_ctrl, 'group', name='%s_fk03_ZERO' % self.name)
        self.ctrls.append(self.fk3_ctrl)

        # hip
        self.hips_ctrl = controls.squareCtrl(name='%s_hips_CTRL' % self.name, axis='y', size=ctrlSize)
        coreUtils.align(self.hips_ctrl, self.crvLocs[0])
        self.hips_ctrl.setParent(self.bodySub_ctrl)
        hipsZero_grp = coreUtils.addParent(self.hips_ctrl, 'group', name='%s_hipsCtrl_ZERO' % self.name)
        self.ctrls.append(self.hips_ctrl)

        # chest
        self.chest_ctrl = controls.squareCtrl(name='%s_chest_CTRL' % self.name, axis='y', size=ctrlSize)
        coreUtils.align(self.chest_ctrl, self.crvLocs[-1])
        self.chest_ctrl.setParent(self.fk3_ctrl)
        chestZero_grp = coreUtils.addParent(self.chest_ctrl, 'group', name='%s_chestCtrl_ZERO' % self.name)
        self.ctrls.append(self.chest_ctrl)

        # mid
        self.mid_ctrl = controls.squareCtrl(name='%s_mid_CTRL' % self.name, axis='y', size=(ctrlSize*.75))
        coreUtils.align(self.mid_ctrl, self.crvLocs[2])
        self.mid_ctrl.setParent(self.fk2_ctrl)
        midCtrlZero = coreUtils.addParent(self.mid_ctrl, 'group', name='%s_midCtrl_ZERO' % self.name)
        self.ctrls.append(self.mid_ctrl)

        # crvInfo
        crvInfo = pmc.createNode('curveInfo', name='%s_crvInfo' % self.name)
        crvShape = coreUtils.getShape(self.crv)
        crvShape.worldSpace[0].connect(crvInfo.inputCurve)

        # stretch
        pmc.addAttr(self.main_grp, longName='stretch', at='double', k=1, h=0)
        restLenMD = coreUtils.multiply(crvInfo.arcLength.get(), self.main_grp.globalScale, name='md_%s_restLength_UTL' % self.name)
        stretchMD = coreUtils.divide(restLenMD.outputX, crvInfo.arcLength, name='md_%s_stretch_UTL' % self.name)
        stretchMD.outputX.connect(self.main_grp.stretch)

        # pathNodes
        mps = curveUtils.nodesAlongCurve(crv=self.crv, numNodes=numJoints, name=self.name, followAxis='y', upAxis='z', upVec='z')
        for grp in mps['grps']:
            grp.setParent(self.noXform_grp)

        # constrain to controls
        hipsConst = coreUtils.addParent(self.crvLocs[0], 'group', name='%s_hips_CONST' % self.name)
        hipsConst.setParent(self.rig_grp)
        hipsPar = pmc.parentConstraint(self.hips_ctrl, hipsConst, mo=0)
        self.crvLocs[1].setParent(hipsConst)
        hipDist = coreUtils.distanceBetweenNodes(self.hips_ctrl, self.mid_ctrl, name='dist_%s_hipTangent_UTL')
        hipDistMD = coreUtils.divide(hipDist.distance, self.main_grp.globalScale, name='md_%s_hipTangent_UTL')
        hipDistUC = coreUtils.convert(hipDistMD.outputX, 0.5, name='uc_%s_hipTangent_UTL')
        hipDistUC.output.connect(self.crvLocs[1].ty)

        chestConst = coreUtils.addParent(self.crvLocs[-1], 'group', name='%s_chest_CONST' % self.name)
        chestConst.setParent(self.rig_grp)
        chestPar = pmc.parentConstraint(self.chest_ctrl, chestConst, mo=0)
        self.crvLocs[-2].setParent(chestConst)
        chestDist = coreUtils.distanceBetweenNodes(self.chest_ctrl, self.mid_ctrl, name='dist_%s_chestTangent_UTL')
        chestDistMD = coreUtils.divide(chestDist.distance, self.main_grp.globalScale, name='md_%s_chestTangent_UTL')
        chestDistUC = coreUtils.convert(chestDistMD.outputX, -0.5, name='uc_%s_chestTangent_UTL')
        chestDistUC.output.connect(self.crvLocs[-2].ty)

        midConst = coreUtils.addParent(self.crvLocs[2], 'group', name='%s_mid_CONST' % self.name)
        midConst.setParent(self.rig_grp)
        midPar = pmc.parentConstraint(self.mid_ctrl, midConst, mo=0)

        # twisting
        self.twistReader = coreUtils.addChild(mps['grps'][(numJoints / 2)-1], 'locator', '%s_twistReader_LOC' % self.name)
        twistPar = pmc.orientConstraint(mps['grps'][(numJoints / 2)+1], self.twistReader)

        for i in range(numJoints / 2):
            mp = mps['mpNodes'][i]
            grp = mps['grps'][i]
            mp.worldUpType.set(2)
            self.hips_ctrl.worldMatrix[0].connect(mp.worldUpMatrix)
            j = coreUtils.addChild(grp, 'joint', grp.name().replace('GRP', 'JNT'))
            self.main_grp.s.connect(j.s)
            self.jnts.append(j)
            uc = coreUtils.convert(self.twistReader.ry, (1.0 / (numJoints-1))*i, name=j.name().replace('JNT', 'twist_UC'))
            uc.output.connect(j.ry)
        for i in range(numJoints - (numJoints / 2)):
            index = i + (numJoints / 2)
            mp = mps['mpNodes'][index]
            grp = mps['grps'][index]
            mp.worldUpType.set(2)
            self.chest_ctrl.worldMatrix[0].connect(mp.worldUpMatrix)
            j = coreUtils.addChild(grp, 'joint', grp.name().replace('GRP', 'JNT'))
            self.main_grp.s.connect(j.s)
            self.jnts.append(j)
            uc = coreUtils.convert(self.twistReader.ry, (-1.0 / (numJoints-1))*((numJoints - (numJoints / 2)-i)-1), name=j.name().replace('JNT', 'twist_UC'))
            uc.output.connect(j.ry)

        # squetch
        for i in range(numJoints):
            attr = pmc.addAttr(self.main_grp, longName='squetch_%s_amount' % str(i+1).zfill(2), at='double', k=1, h=0)
            blend = coreUtils.blend(self.main_grp.stretch, 1.0, name='blend_%s_squetch_%s_UTL' % (self.name, str(i+1).zfill(2)), blendAttr=self.main_grp.attr('squetch_%s_amount' % str(i+1).zfill(2)))
            blend.outputR.connect(mps['grps'][i].sx)
            blend.outputR.connect(mps['grps'][i].sz)

        # rotate order
        for node in self.ctrls:
            print node
            node.rotateOrder.set(4)

        for node in mps['grps']:
            node.rotateOrder.set(4)

        for node in [hipsPar, chestPar, midPar, twistPar, hipsConst, chestConst, midConst, self.twistReader]:
            node.rotateOrder.set(4)

        # Hips - must be passed as PyNodes
        if rtHip and lfHip:
            self.rt_hip_ctrl = controls.pinCtrl(name='rt_hip_CTRL', radius=ctrlSize, axis='-x')
            self.rt_hip_ctrl.setParent(self.hips_ctrl)
            coreUtils.align(self.rt_hip_ctrl, rtHip, orient=0)
            coreUtils.addParent(self.rt_hip_ctrl, 'group', 'rt_hip_ZERO')

            hipNegScale = pmc.group(empty=1, name='lf_hip_NEG')
            hipNegScale.setParent(self.hips_ctrl)

            self.lf_hip_ctrl = controls.pinCtrl(name='lf_hip_CTRL', radius=ctrlSize, axis='-x')
            self.lf_hip_ctrl.setParent(hipNegScale)
            coreUtils.align(self.lf_hip_ctrl, lfHip, orient=0)
            lfHipZero = coreUtils.addParent(self.lf_hip_ctrl, 'group', 'lf_hip_ZERO')
            hipNegScale.sx.set(-1)
            lfHipZero.sx.set(1)
            lfHipZero.tx.set(lfHipZero.tx.get()*-1)

        # shoulders - must be passed as PyNodes
        if rtShldr and lfShldr and rtClav and lfClav:
            # right
            self.rt_shldr_ctrl = controls.boxCtrl(size=ctrlSize*.5, name='rt_shldr_CTRL')
            self.rt_shldr_ctrl.setParent(self.chest_ctrl)
            coreUtils.align(self.rt_shldr_ctrl, rtShldr, orient=0)
            rtShldrRotInv_grp = coreUtils.addParent(self.rt_shldr_ctrl, 'group', 'rt_shldrRot_INV')
            rtShldrPosInv_grp = coreUtils.addParent(self.rt_shldr_ctrl, 'group', 'rt_shldrPos_INV')
            rtShldrZero_grp = coreUtils.addParent(rtShldrRotInv_grp, 'group', 'rt_shldr_ZERO')
            rtClavDriven_grp = pmc.group(empty=1, name='rt_clav_DRV')
            coreUtils.align(rtClavDriven_grp, rtClav, orient=0)
            rtClavZero_grp = coreUtils.addParent(rtClavDriven_grp, 'group', 'rt_clav_ZERO')
            rtShldrZero_grp.setParent(rtClavDriven_grp)
            rtClavZero_grp.setParent(self.chest_ctrl)

            self.rt_shldr_ctrl.r.connect(rtClavDriven_grp.r)
            self.rt_shldr_ctrl.t.connect(rtClavDriven_grp.t)

            rtShldrRotInv_uc = coreUtils.convert(self.rt_shldr_ctrl.r, -1, name='uc_rt_shldrRotInv_UTL')
            rtShldrPosInv_uc = coreUtils.convert(self.rt_shldr_ctrl.t, -1, name='uc_rt_shldrPosInv_UTL')

            rtShldrRotInv_uc.output.connect(rtShldrRotInv_grp.r)
            rtShldrPosInv_uc.output.connect(rtShldrPosInv_grp.t)

            rtShldrRotInv_grp.rotateOrder.set(5)

            rtShldrConst = coreUtils.addChild(self.rig_grp, 'group', name='rt_shldr_CONST')
            pmc.parentConstraint(self.rt_shldr_ctrl, rtShldrConst, mo=0)
            j = coreUtils.addChild(rtShldrConst, 'joint', name='rt_shldr_JNT')

            # left
            clavNegScale = pmc.group(empty=1, name='lf_clav_NEG')
            clavNegScale.setParent(self.chest_ctrl)

            self.lf_shldr_ctrl = controls.boxCtrl(size=ctrlSize*.5, name='lf_shldr_CTRL')
            self.lf_shldr_ctrl.setParent(self.chest_ctrl)
            coreUtils.align(self.lf_shldr_ctrl, lfShldr, orient=0)
            lfShldrRotInv_grp = coreUtils.addParent(self.lf_shldr_ctrl, 'group', 'lf_shldrRot_INV')
            lfShldrPosInv_grp = coreUtils.addParent(self.lf_shldr_ctrl, 'group', 'lf_shldrPos_INV')
            lfShldrZero_grp = coreUtils.addParent(lfShldrRotInv_grp, 'group', 'lf_shldr_ZERO')
            lfClavDriven_grp = pmc.group(empty=1, name='lf_clav_DRV')
            coreUtils.align(lfClavDriven_grp, lfClav, orient=0)
            lfClavZero_grp = coreUtils.addParent(lfClavDriven_grp, 'group', 'lf_clav_ZERO')
            lfShldrZero_grp.setParent(lfClavDriven_grp)
            lfClavZero_grp.setParent(clavNegScale)

            self.lf_shldr_ctrl.r.connect(lfClavDriven_grp.r)
            self.lf_shldr_ctrl.t.connect(lfClavDriven_grp.t)

            lfShldrRotInv_uc = coreUtils.convert(self.lf_shldr_ctrl.r, -1, name='uc_lf_shldrRotInv_UTL')
            lfShldrPosInv_uc = coreUtils.convert(self.lf_shldr_ctrl.t, -1, name='uc_lf_shldrPosInv_UTL')

            lfShldrRotInv_uc.output.connect(lfShldrRotInv_grp.r)
            lfShldrPosInv_uc.output.connect(lfShldrPosInv_grp.t)

            lfShldrRotInv_grp.rotateOrder.set(5)

            clavNegScale.sx.set(-1)
            lfShldrZero_grp.tx.set(lfShldrZero_grp.tx.get()*-1)

            lfShldrConst = coreUtils.addChild(self.rig_grp, 'group', name='lf_shldr_CONST')
            pmc.parentConstraint(self.lf_shldr_ctrl, lfShldrConst, mo=0)
            j = coreUtils.addChild(lfShldrConst, 'joint', name='lf_shldr_JNT')


        # colours
        coreUtils.colorize('green', [self.body_ctrl, self.bodySub_ctrl, self.fk1_ctrl, self.fk2_ctrl, self.fk3_ctrl])
        coreUtils.colorize('yellow', [self.hips_ctrl, self.chest_ctrl, self.mid_ctrl])
        coreUtils.colorize('red', [self.rt_hip_ctrl, self.rt_shldr_ctrl])
        coreUtils.colorize('blue', [self.lf_hip_ctrl, self.lf_shldr_ctrl])

        # connections
        self.exposeSockets({'rt_hip':self.rt_hip_ctrl,
                            'lf_hip':self.lf_hip_ctrl,
                            'rt_shldr':self.rt_shldr_ctrl,
                            'lf_shldr':self.lf_shldr_ctrl,
                            'chest':self.chest_ctrl,
                            'body':self.bodySub_ctrl})

        if cleanup:
            self.cleanup()

    def cleanup(self):
        coreUtils.attrCtrl(nodeList=[self.body_ctrl,
                                     self.bodySub_ctrl,
                                     self.hips_ctrl,
                                     self.chest_ctrl,
                                     self.fk1_ctrl,
                                     self.fk2_ctrl,
                                     self.fk3_ctrl,
                                     self.rt_hip_ctrl,
                                     self.rt_shldr_ctrl,
                                     self.lf_hip_ctrl,
                                     self.lf_shldr_ctrl],
                           attrList=['sx', 'sy', 'sz', 'visibility'])

        coreUtils.attrCtrl(nodeList=[self.mid_ctrl], attrList=['rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'visibility'])
        self.rig_grp.visibility.set(0)




