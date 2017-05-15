import pymel.core as pmc
import drTools.systems.curveUtils as curveUtils
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls

reload(controls)
reload(systemUtils)
reload(curveUtils)
reload(coreUtils)

class DrCockle(object):
    def __init__(self, name='', settingsNode=None):
        super(DrCockle, self).__init__()
        self.name = name
        self.settingsNode = settingsNode
        self.buildGuides()

    def buildGuides(self):
        self.main_GD = pmc.spaceLocator(name='%s_main_GD' % self.name)

        self.fnt_GD = coreUtils.addChild(self.main_GD, 'locator', '%s_fnt_GD' % self.name)
        self.fnt_GD.tz.set(5.0)

        self.bck_GD = coreUtils.addChild(self.main_GD, 'locator', '%s_bck_GD' % self.name)
        self.bck_GD.tz.set(-5.0)

        self.lf_GD = coreUtils.addChild(self.main_GD, 'locator', '%s_lf_GD' % self.name)
        self.lf_GD.tx.set(5.0)

        self.rt_GD = coreUtils.addChild(self.main_GD, 'locator', '%s_rt_GD' % self.name)
        self.rt_GD.tx.set(-5.0)

    def buildCockle(self):
        self.main_grp = pmc.group(empty=1, name='%s_GRP' % self.name)
        if not self.settingsNode:
            self.settingsNode = self.main_grp

        self.lf_grp = coreUtils.addChild(self.main_grp, 'group', name='%s_lf_ZERO' % self.name)
        coreUtils.align(self.lf_grp, self.lf_GD)
        self.lf_drv = coreUtils.addChild(self.lf_grp, 'group', name='%s_lf_DRV' % self.name)
        pmc.transformLimits(self.lf_drv, rz=(0, 0), erz=(0, 1))

        self.rt_grp = coreUtils.addChild(self.lf_drv, 'group', name='%s_rt_ZERO' % self.name)
        coreUtils.align(self.rt_grp, self.rt_GD)
        self.rt_drv = coreUtils.addChild(self.rt_grp, 'group', name='%s_rt_DRV' % self.name)
        pmc.transformLimits(self.rt_drv, rz=(0, 0), erz=(1, 0))

        self.fnt_grp = coreUtils.addChild(self.rt_drv, 'group', name='%s_fnt_ZERO' % self.name)
        coreUtils.align(self.fnt_grp, self.fnt_GD)
        self.fnt_drv = coreUtils.addChild(self.fnt_grp, 'group', name='%s_fnt_DRV' % self.name)
        pmc.transformLimits(self.fnt_drv, rx=(0, 0), erx=(1, 0))

        self.bck_grp = coreUtils.addChild(self.fnt_drv, 'group', name='%s_bck_ZERO' % self.name)
        coreUtils.align(self.bck_grp, self.bck_GD)
        self.bck_drv = coreUtils.addChild(self.bck_grp, 'group', name='%s_bck_DRV' % self.name)
        pmc.transformLimits(self.bck_drv, rx=(0, 0), erx=(0, 1))

        pmc.addAttr(self.settingsNode, ln='side_tilt', at='double', k=1, h=0)
        pmc.addAttr(self.settingsNode, ln='front_tilt', at='double', k=1, h=0)

        self.settingsNode.side_tilt.connect(self.lf_drv.rz)
        self.settingsNode.side_tilt.connect(self.rt_drv.rz)
        self.settingsNode.front_tilt.connect(self.fnt_drv.rx)
        self.settingsNode.front_tilt.connect(self.bck_drv.rx)

        pmc.delete([self.lf_GD, self.rt_GD, self.fnt_GD, self.bck_GD])



