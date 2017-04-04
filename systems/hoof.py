import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls

reload(controls)
reload(coreUtils)
reload(systemUtils)


class DrHoof(systemUtils.DrSystem):
    def __init__(self, name, ankle=None, toe=None, inner=None, outer=None, heel=None,
                 settingsNode=None, colour='red', cleanup=1, blendAttr=None):
        if not ankle and len(pmc.selected()) == 5:
            sel = pmc.selected()
            ankle = sel[0]
            toe = sel[1]
            inner = sel[2]
            outer = sel[3]
            heel = sel[4]
        super(DrHoof, self).__init__(name=name)
        self.ctrls=[]
        self.buildHoof(ankle, toe, inner, outer, heel, settingsNode, colour, cleanup, blendAttr)

    def buildHoof(self, ankle, toe, inner, outer, heel, settingsNode, colour, cleanup, blendAttr):
        if not ankle:
            return 'DrReverseFoot: Please supply or select joints for Ankle, Toe, Inner, Outer and Heel positions.'

        self.innerLoc = coreUtils.createAlignedNode(inner, 'group', '%s_inner_GRP' % self.name)
        self.innerLoc.setParent(self.rig_grp)
        innerZero = coreUtils.addParent(self.innerLoc, 'group', '%s_inner_ZERO' % self.name)

        self.outerLoc = coreUtils.createAlignedNode(outer, 'group', '%s_outer_GRP' % self.name)
        self.outerLoc.setParent(self.innerLoc)
        outerZero = coreUtils.addParent(self.outerLoc, 'group', '%s_outer_ZERO' % self.name)

        self.toeLoc = coreUtils.createAlignedNode(toe, 'group', '%s_toe_GRP' % self.name)
        self.toeLoc.setParent(self.outerLoc)
        toeZero = coreUtils.addParent(self.toeLoc, 'group', '%s_toe_ZERO' % self.name)

        self.heelLoc = coreUtils.createAlignedNode(heel, 'group', '%s_heel_GRP' % self.name)
        self.heelLoc.setParent(self.toeLoc)
        heelZero = coreUtils.addParent(self.heelLoc, 'group', '%s_heel_ZERO' % self.name)

        self.ankleLoc = coreUtils.createAlignedNode(ankle, 'group', '%s_ankle_GRP' % self.name)
        self.ankleLoc.setParent(self.heelLoc)
        ankleZero = coreUtils.addParent(self.ankleLoc, 'group', '%s_ankle_ZERO' % self.name)

        self.ikConstGrp = coreUtils.createAlignedNode(ankle, 'group', '%s_ik_CONST' % self.name)
        self.ikConstGrp.setParent(self.rig_grp)
        innerZero.setParent(self.ikConstGrp)

        self.fkConstGrp = coreUtils.createAlignedNode(ankle, 'group', '%s_fk_CONST' % self.name)
        self.fkConstGrp.setParent(self.rig_grp)

        self.constGrp = coreUtils.createAlignedNode(ankle, 'group', '%s_CONST' % self.name)
        self.constGrp.setParent(self.rig_grp)
        j = coreUtils.addChild(self.constGrp, 'joint', '%s_JNT' % self.name)
        self.joints.append(j)

        if not blendAttr:
            blendAttr = pmc.addAttr(self.main_grp, ln='ik_fk_blend', at='double', k=1, h=0)
            
        if not settingsNode:
            settingsNode = self.main_grp
        pmc.addAttr(settingsNode, longName='heel_toe', at='double', k=1, h=0)
        pmc.addAttr(settingsNode, longName='side_side', at='double', k=1, h=0)
        settingsNode.heel_toe.connect(self.heelLoc.rx)
        settingsNode.heel_toe.connect(self.toeLoc.rx)
        settingsNode.side_side.connect(self.innerLoc.rz)
        settingsNode.side_side.connect(self.outerLoc.rz)

        pmc.transformLimits(self.heelLoc, rx=(-45, 0), erx=(0, 1))
        pmc.transformLimits(self.toeLoc, rx=(0, 45), erx=(1, 0))
        pmc.transformLimits(self.innerLoc, rz=(-45, 0), erz=(0, 1))
        pmc.transformLimits(self.outerLoc, rz=(0, 45), erz=(1, 0))

        con = pmc.parentConstraint(self.ankleLoc, self.fkConstGrp, self.constGrp, mo=0)
        pmc.connectAttr(blendAttr, '%s.%sW1' % (con.name(), self.fkConstGrp))
        rev = coreUtils.reverse(blendAttr, name='rev_%sIkFkBlend_UTL' % self.name)
        rev.outputX.connect('%s.%sW0' % (con.name(), self.ankleLoc))

        # connections
        self.exposeSockets({'ankle': self.ankleLoc})

        if cleanup:
            self.cleanup()

    def cleanup(self):
        self.rig_grp.visibility.set(0)
