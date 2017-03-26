import pymel.core as pmc
import drTools.systems.curveUtils as curveUtils
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls

reload(controls)
reload(systemUtils)
reload(curveUtils)
reload(coreUtils)

class DrBrows(systemUtils.DrSystem):
    def __init__(self, name, rtPos=None, lfPos=None, cleanup=1):
        rtPos, lfPos = coreUtils.getStartAndEnd(rtPos, lfPos)
        super(DrBrows, self).__init__(name)
        self.ctrls=[]
        self.buildBrows(rtPos, lfPos)
        if cleanup:
            self.cleanup()

    def buildBrows(self, rtPos, lfPos):

        if not rtPos or not lfPos:
            rtPos, lfPos = (-5, 0, 0), (5, 0, 0)
        ctrlSize = coreUtils.getDistance(rtPos, lfPos)

        rtGrp = coreUtils.addChild(self.rig_grp, 'group', 'rt_brow_GRP')
        rtGrp.t.set(rtPos)

        lfGrp = coreUtils.addChild(self.rig_grp, 'group', 'lf_brow_GRP')
        lfGrp.t.set(lfPos)

        rtBrowZero = coreUtils.addChild(rtGrp, 'group', 'rt_brow_ZERO')

        lfBrowZero = coreUtils.addChild(lfGrp, 'group', 'lf_brow_ZERO')

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
            c.t.connect(g.t)

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
                j.t.set((ctrlSize*subs[i][1], 0, 0))
                self.joints.append(j)

                c.t.connect(g.t)


        subs = {0: ['in', .33], 1: ['mid', 0], 2: ['out', -.33]}
        # rt brow
        c, g = _makeCtrl('rt_brow', 'red', (rtPos[0], rtPos[1]+(ctrlSize * .33), rtPos[2] + ctrlSize), rtBrowZero)
        _makeSubCtrls(c, 'rt_brow', 'red', g)

        subs = {0: ['in', .33], 1: ['mid', 0], 2: ['out', -.33]}

        # lf brow
        c, g = _makeCtrl('lf_brow', 'blue', (lfPos[0], lfPos[1]+(ctrlSize * .33), lfPos[2] + ctrlSize), lfBrowZero)
        c.getParent().sx.set(-1)
        g.getParent().sx.set(-1)
        _makeSubCtrls(c, 'lf_brow', 'blue', g)

        # centre joint
        j = coreUtils.addChild(self.rig_grp, 'joint', name='%s_mid_JNT' % self.name)
        self.joints.append(j)
        zero = coreUtils.addParent(j, 'group', '%s_mid_ZERO' % self.name)
        pmc.parentConstraint(self.joints[0].getParent(), self.joints[3].getParent(), zero, mo=0).interpType.set(2)
        pmc.pointConstraint(self.joints[0], self.joints[3], j, skip=('x', 'z'))



    def cleanup(self):
        self.rig_grp.visibility.set(0)
        coreUtils.attrCtrl(nodeList=self.ctrls, attrList=['tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'visibility'])
