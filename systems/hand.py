import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls

reload(controls)
reload(coreUtils)
reload(systemUtils)


class DrHand(systemUtils.DrSystem):
    def __init__(self, name, fingerDict=None, settingsNode=None, colour='red', cleanup=1):
        super(DrHand, self).__init__(name=name)
        self.ctrls=[]
        self.buildHand(settingsNode, fingerDict, colour, cleanup)

    def buildHand(self, settingsNode, fingerDict, colour, cleanup):
        ctrlSize=None
        for finger in fingerDict.keys():
            for i in range(len(fingerDict[finger])):
                if not ctrlSize:
                        ctrlSize = coreUtils.getDistance(fingerDict[finger][0], fingerDict[finger][1]) * .25
                if i > 0:
                    j2 = coreUtils.createAlignedNode(fingerDict[finger][i], 'joint',
                                                     '%s_%s_%s_translate_JNT' % (self.name, finger, str(i+1).zfill(2)))
                    j2.setParent(self.joints[-1])
                    j2.jointOrient.set(fingerDict[finger][i].jointOrient.get())
                    j2.r.set((0, 0, 0))
                    coreUtils.addParent(j2, 'group',
                                        '%s_%s_%s_translateJnt_ZERO' % (self.name, finger, str(i+1).zfill(2)))
                    self.joints.append(j2)
                j = coreUtils.createAlignedNode(fingerDict[finger][i], 'joint',
                                                '%s_%s_%s_JNT' % (self.name, finger, str(i+1).zfill(2)))

                c = controls.squareCtrl(axis='x', name='%s_%s_%s_CTRL' % (self.name, finger, str(i+1).zfill(2)),
                                        size=ctrlSize)
                coreUtils.align(c, j)
                pmc.select('%s.cv[*]' % c.name())
                pmc.scale(5.0, scaleY=1)

                if i == 0:
                    j.setParent(self.rig_grp)
                    jGrp = coreUtils.addParent(j, 'group', '%s_%s_joints_GRP' % (self.name, finger))
                    j.jointOrient.set((0, 0, 0))
                    j.r.set((0, 0, 0))
                    c.setParent(self.ctrls_grp)
                    cGrp = coreUtils.addParent(c, 'group', '%s_%s_ctrls_GRP' % (self.name, finger))
                    c.t.connect(j.t)
                    c.r.connect(j.r)
                    pmc.parentConstraint(cGrp, jGrp)
                else:
                    j.setParent(self.joints[-1])
                    j.jointOrient.set((0, 0, 0))
                    j.r.set((0, 0, 0))
                    c.setParent(self.ctrls[-1])
                    coreUtils.addParent(c, 'group', '%s_%s_%s_ZERO' % (self.name, finger, str(i+1).zfill(2)))
                    c.t.connect(j2.t)
                    c.r.connect(j.r)
                self.joints.append(j)
                self.ctrls.append(c)

        coreUtils.colorize(colour, self.ctrls)

        if settingsNode:
            pmc.addAttr(settingsNode, longName='finger_ctrls_vis', at='bool', k=0, h=0)
            pmc.setAttr(settingsNode.finger_ctrls_vis, channelBox=1)
            settingsNode.finger_ctrls_vis.connect(self.ctrls_grp.visibility)

        if cleanup:
            self.cleanup()

    def cleanup(self):
        coreUtils.attrCtrl(nodeList=self.ctrls, attrList=['sx', 'sy', 'sz', 'visibility'])
        self.rig_grp.visibility.set(0)
