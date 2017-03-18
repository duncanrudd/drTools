import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls

reload(systemUtils)
reload(coreUtils)
reload(controls)


class DrRoot(systemUtils.DrSystem):
    def __init__(self, name, ctrlSize=20.0, cleanup=1):
        super(DrRoot, self).__init__(name)
        self.ctrls = []
        self.buildRoot(ctrlSize, cleanup)

    def buildRoot(self, ctrlSize, cleanup):
        # controls

        self.root_01_ctrl = controls.circleBumpCtrl(name='root_01_CTRL', axis='y', radius=ctrlSize)
        self.root_01_ctrl.setParent(self.ctrls_grp)
        self.ctrls.append(self.root_01_ctrl)

        self.root_02_ctrl = controls.circleBumpCtrl(name='root_02_CTRL', axis='y', radius=ctrlSize*.85)
        self.root_02_ctrl.setParent(self.root_01_ctrl)
        self.ctrls.append(self.root_02_ctrl)

        self.root_03_ctrl = controls.circleBumpCtrl(name='root_03_CTRL', axis='y', radius=ctrlSize*.7)
        self.root_03_ctrl.setParent(self.root_02_ctrl)
        self.ctrls.append(self.root_03_ctrl)

        coreUtils.colorize('green', self.ctrls)

        # connections
        self.exposeSockets({'03': self.root_03_ctrl})

        if cleanup:
            self.cleanup()

    def cleanup(self):
        coreUtils.attrCtrl(nodeList=[self.root_02_ctrl, self.root_03_ctrl], attrList=['sx', 'sy', 'sz', 'visibility'])
        coreUtils.attrCtrl(nodeList=[self.root_01_ctrl], attrList=['visibility'])
        coreUtils.attrCtrl(nodeList=[self.root_01_ctrl], attrList=['sx', 'sy', 'sz'], lock=0)
        self.rig_grp.visibility.set(0)

class DrRig():
    def __init__(self, ctrlSize=50.0, cleanup=1):
        self.build(ctrlSize, cleanup)

    def build(self, ctrlSize, cleanup):
        self.main_grp = pmc.group(empty=1, name='world_GRP')
        self.rig_grp = coreUtils.addChild(self.main_grp, 'group', name='rig_GRP')
        self.geo_grp = coreUtils.addChild(self.main_grp, 'group', name='geo_GRP')

        self.rootSystem = DrRoot(name='root', ctrlSize=ctrlSize, cleanup=cleanup)
        self.rootSystem.main_grp.setParent(self.rig_grp)

        pmc.addAttr(self.rootSystem.root_01_ctrl, ln='geo_display', at='enum', enumName='normal:template:reference', hidden=0)
        self.geo_grp.overrideEnabled.set(1)
        pmc.setAttr(self.rootSystem.root_01_ctrl.geo_display, keyable=0)
        pmc.setAttr(self.rootSystem.root_01_ctrl.geo_display, channelBox=1)
        self.rootSystem.root_01_ctrl.geo_display.connect(self.geo_grp.overrideDisplayType)

        pmc.addAttr(self.rootSystem.root_01_ctrl, ln='globalScale', at='double', k=1, h=0)
        self.rootSystem.root_01_ctrl.globalScale.set(1)
        self.rootSystem.root_01_ctrl.globalScale.connect(self.rootSystem.main_grp.globalScale)

