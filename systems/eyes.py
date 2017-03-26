import pymel.core as pmc
import drTools.systems.curveUtils as curveUtils
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls

reload(controls)
reload(systemUtils)
reload(curveUtils)
reload(coreUtils)

class DrEyes(systemUtils.DrSystem):
    def __init__(self, name, rtPos=None, lfPos=None, cleanup=1):
        rtPos, lfPos = coreUtils.getStartAndEnd(rtPos, lfPos)
        super(DrEyes, self).__init__(name)
        self.ctrls=[]
        self.buildEyes(rtPos, lfPos)
        if cleanup:
            self.cleanup()

    def buildEyes(self, rtPos, lfPos):
        if not rtPos or not lfPos:
            return 'DrEyes: Please supply and right and left location for your eye rig'
        # Make Ctrls
        ctrlSize = coreUtils.getDistance(rtPos, lfPos)
        self.mainCtrl = controls.squareCtrl(axis='z', name='%s_CTRL' % self.name, size=ctrlSize)
        pmc.select('%s.cv[ * ]' % coreUtils.getShape(self.mainCtrl))
        pmc.scale(2.5, scaleX=1)
        pmc.scale(1.25, scaleY=1)
        self.ctrls.append(self.mainCtrl)
        ctrlZero = coreUtils.addParent(self.mainCtrl, 'group', '%s_ctrl_ZERO' % self.name)
        ctrlZero.setParent(self.ctrls_grp)
        midPos = coreUtils.pointsAlongVector(lfPos, rtPos)[1]
        ctrlZero.t.set((midPos[0], midPos[1], midPos[2] + (ctrlSize * 10)))

        self.rtCtrl = controls.circleCtrl(radius=ctrlSize*.25, name='rt_eye_CTRL')
        self.ctrls.append(self.rtCtrl)
        coreUtils.align(self.rtCtrl, self.mainCtrl, parent=1)
        rtCtrlZero = coreUtils.addParent(self.rtCtrl, 'group', 'rt_eyeCtrl_ZERO')
        rtCtrlZero.tx.set(rtPos[0])


        self.lfCtrl = controls.circleCtrl(radius=ctrlSize*.25, name='lf_eye_CTRL')
        self.ctrls.append(self.lfCtrl)
        coreUtils.align(self.lfCtrl, self.mainCtrl, parent=1)
        lfCtrlZero = coreUtils.addParent(self.lfCtrl, 'group', 'lf_eyeCtrl_ZERO')
        lfCtrlZero.tx.set(lfPos[0])
        lfCtrlZero.sx.set(-1)

        coreUtils.colorize('green', [self.mainCtrl])
        coreUtils.colorize('red', [self.rtCtrl])
        coreUtils.colorize('blue', [self.lfCtrl])

        # Set up aims
        rtGrp = coreUtils.addChild(self.rig_grp, 'group', 'rt_eye_GRP')
        rtGrp.t.set(rtPos)
        pmc.parentConstraint(self.ctrls_grp, rtGrp, mo=1)
        pmc.scaleConstraint(self.ctrls_grp, rtGrp, mo=1)

        rtAimGrp = coreUtils.addChild(rtGrp, 'group', 'rt_eyeAim_GRP')
        pmc.aimConstraint(self.rtCtrl, rtAimGrp, aim=(0, 0, 1), wut='objectrotation', wuo=rtGrp)
        rtJnt = coreUtils.addChild(rtAimGrp, 'joint', 'rt_eyeAim_JNT')
        self.joints.append(rtJnt)

        lfGrp = coreUtils.addChild(self.rig_grp, 'group', 'lf_eye_GRP')
        lfGrp.t.set(lfPos)
        pmc.parentConstraint(self.ctrls_grp, lfGrp, mo=1)
        pmc.scaleConstraint(self.ctrls_grp, lfGrp, mo=1)

        lfAimGrp = coreUtils.addChild(lfGrp, 'group', 'lf_eyeAim_GRP')
        pmc.aimConstraint(self.lfCtrl, lfAimGrp, aim=(0, 0, 1), wut='objectrotation', wuo=lfGrp)
        lfJnt = coreUtils.addChild(lfAimGrp, 'joint', 'lf_eyeAim_JNT')
        self.joints.append(lfJnt)

        # softness
        pmc.addAttr(self.main_grp, longName='eye_pull', minValue=0.0, maxValue=1.0, at='double', k=1, h=0)
        eyePullRev = coreUtils.reverse(self.main_grp.eye_pull, name='rev_eyePull_UTL')

        rtSoftGrp = coreUtils.addChild(rtGrp, 'group', 'rt_eyeSoft_GRP')
        rtSoftJnt = coreUtils.addChild(rtSoftGrp, 'joint', 'rt_soft_JNT')
        self.joints.append(rtSoftJnt)
        con = pmc.orientConstraint(rtGrp, rtAimGrp, rtSoftGrp)
        con.interpType.set(2)
        w0 = pmc.Attribute('%s.%sW0' % (con.name(), rtGrp.name()))
        w1 = pmc.Attribute('%s.%sW1' % (con.name(), rtAimGrp.name()))
        self.main_grp.eye_pull.connect(w1)
        eyePullRev.outputX.connect(w0)

        lfSoftGrp = coreUtils.addChild(lfGrp, 'group', 'lf_eyeSoft_GRP')
        lfSoftJnt = coreUtils.addChild(lfSoftGrp, 'joint', 'lf_soft_JNT')
        self.joints.append(lfSoftJnt)
        con = pmc.orientConstraint(lfGrp, lfAimGrp, lfSoftGrp)
        con.interpType.set(2)
        w0 = pmc.Attribute('%s.%sW0' % (con.name(), lfGrp.name()))
        w1 = pmc.Attribute('%s.%sW1' % (con.name(), lfAimGrp.name()))
        self.main_grp.eye_pull.connect(w1)
        eyePullRev.outputX.connect(w0)

        #############################################################################################################
        # Lids

        pmc.addAttr(self.main_grp, ln='lids_rotate_factor', at='double', k=0, h=0)
        pmc.setAttr(self.main_grp.lids_rotate_factor, channelBox=1)
        self.main_grp.lids_rotate_factor.set(-10)
        pmc.addAttr(self.main_grp, ln='lids_auto', at='double', k=0, h=0, minValue=0.0, maxValue=1.0)
        self.main_grp.lids_auto.set(1.0)

        rtLidGrp = coreUtils.addChild(self.rig_grp, 'group', 'rt_lids_GRP')
        coreUtils.align(rtLidGrp, rtGrp)

        # rt_top
        rtTopLidZero = coreUtils.addChild(rtLidGrp, 'group', 'rt_topLid_ZERO')
        rtTopLidAutoGrp = coreUtils.addChild(rtTopLidZero, 'group', 'rt_topLidAuto_GRP')
        md = coreUtils.multiply(rtAimGrp.rx, self.main_grp.lids_auto, name='md_rtLidsAuto_UTL')
        md.outputX.connect(rtTopLidAutoGrp.rx)

        # rt_btm
        rtBtmLidZero = coreUtils.addChild(rtLidGrp, 'group', 'rt_btmLid_ZERO')
        rtBtmLidAutoGrp = coreUtils.addChild(rtBtmLidZero, 'group', 'rt_btmLidAuto_GRP')
        md.outputX.connect(rtBtmLidAutoGrp.rx)

        # lf_top
        lfLidGrp = coreUtils.addChild(self.rig_grp, 'group', 'lf_lids_GRP')
        coreUtils.align(lfLidGrp, lfGrp)

        lfTopLidZero = coreUtils.addChild(lfLidGrp, 'group', 'lf_topLid_ZERO')
        lfTopLidAutoGrp = coreUtils.addChild(lfTopLidZero, 'group', 'lf_topLidAuto_GRP')
        md = coreUtils.multiply(lfAimGrp.rx, self.main_grp.lids_auto, name='md_lfLidsAuto_UTL')
        md.outputX.connect(lfTopLidAutoGrp.rx)

        # lf_btm
        lfBtmLidZero = coreUtils.addChild(lfLidGrp, 'group', 'lf_btmLid_ZERO')
        lfBtmLidAutoGrp = coreUtils.addChild(lfBtmLidZero, 'group', 'lf_btmLidAuto_GRP')
        md.outputX.connect(lfBtmLidAutoGrp.rx)

        def _addControl(slave, driver):
            md = coreUtils.multiply(driver.ty, self.main_grp.lids_rotate_factor,
                                    name='md_%s_UTL' % driver.name().replace('_CTRL', ''))
            md.outputX.connect(slave.rx)

        # CTRLS
        def _makeCtrl(prefix='', colour='red', pos=(0, 0, 0), grpParent=None):
            c = controls.squareCtrl(size=ctrlSize, name='%s_CTRL' % prefix, axis='z')
            c.t.set(pos)
            zero = coreUtils.addParent(c, 'group', '%sCtrl_ZERO' % prefix)
            zero.setParent(self.ctrls_grp)
            pmc.select('%s.cv[ * ]' % coreUtils.getShape(c))
            pmc.scale(.33, scaleY=1)
            coreUtils.colorize(colour, [c])
            self.ctrls.append(c)

            g = coreUtils.addChild(grpParent, 'group', '%s_DRV' % prefix)
            _addControl(g, c)

            return c, g

        def _makeSubCtrls(parent, prefix='', colour='red', grpParent=None):
            for i in range(len(subs.keys())):
                c = controls.squareCtrl(size=ctrlSize*.15, name='%s_%s_CTRL' % (prefix, subs[i][0]), axis='z')
                coreUtils.align(c, parent, parent=1)
                c.tx.set(ctrlSize * subs[i][1])
                coreUtils.addParent(c, 'group', c.name().replace('_CTRL', 'Ctrl_ZERO'))
                coreUtils.colorize(colour, [c])
                self.ctrls.append(c)

                g = coreUtils.addChild(grpParent, 'group', '%s_%s_DRV' % (prefix, subs[i][0]))
                j = coreUtils.addChild(g, 'joint', '%s_%s_JNT' % (prefix, subs[i][0]))
                jEnd = coreUtils.addChild(j, 'joint', '%s_%sEnd_JNT' % (prefix, subs[i][0]))
                jEnd.t.set((ctrlSize*subs[i][1], 0, ctrlSize*.33))
                self.joints.append(jEnd)

                _addControl(g, c)

        subs = {0: ['in', .33], 1: ['mid', 0], 2: ['out', -.33]}
        # rt top lid
        c, g = _makeCtrl('rt_topLid', 'red', (rtPos[0], rtPos[1]+(ctrlSize * .33), rtPos[2] + ctrlSize), rtTopLidAutoGrp)
        _makeSubCtrls(c, 'rt_topLid', 'red', g)

        # rt btm lid
        c, g = _makeCtrl('rt_btmLid', 'red', (rtPos[0], rtPos[1]+(ctrlSize * -.33), rtPos[2] + ctrlSize), rtBtmLidAutoGrp)
        _makeSubCtrls(c, 'rt_btmLid', 'red', g)

        subs = {0: ['in', -.33], 1: ['mid', 0], 2: ['out', .33]}

        # lf top lid
        c, g = _makeCtrl('lf_topLid', 'blue', (lfPos[0], lfPos[1]+(ctrlSize * .33), lfPos[2] + ctrlSize), lfTopLidAutoGrp)
        _makeSubCtrls(c, 'lf_topLid', 'blue', g)

        #lf btm lid
        c, g = _makeCtrl('lf_btmLid', 'blue', (lfPos[0], lfPos[1]+(ctrlSize * -.33), lfPos[2] + ctrlSize), lfBtmLidAutoGrp)
        _makeSubCtrls(c, 'lf_btmLid', 'blue', g)

    def cleanup(self):
        self.rig_grp.visibility.set(0)
        coreUtils.attrCtrl(nodeList=self.ctrls, attrList=['rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'visibility'])
        coreUtils.attrCtrl(nodeList=[c for c in self.ctrls if 'LID' in c.name().upper()], attrList=['tx', 'tz'])
