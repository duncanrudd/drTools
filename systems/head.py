import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls


reload(systemUtils)
reload(coreUtils)
reload(controls)


class DrHead(systemUtils.DrSystem):
    def __init__(self, name, start=None, cleanup=1):
        startPos = None
        if not start and len(pmc.selected()) == 1:
            startPos = pmc.xform(pmc.selected()[0], translation=True, query=True, ws=True)
        else:
            if pmc.nodetypes.Transform in type(start).__mro__:
                startPos = pmc.xform(start, translation=True, query=True, ws=True)
            else:
                startPos = start

        if not startPos:
            return 'DrHead: Please provide start'

        super(DrHead, self).__init__(name)
        self.ctrls = []
        self.buildHead(startPos, cleanup)

    def buildHead(self, startPos, cleanup):
        # controls
        ctrlSize = startPos[1] * .1

        self.head_ctrl = controls.circleBumpCtrl(name='head_CTRL', axis='y', radius=ctrlSize)
        self.head_ctrl.setParent(self.ctrls_grp)
        self.head_ctrl.t.set(startPos)
        self.headZero_grp = coreUtils.addParent(self.head_ctrl, 'group', name='head_ZERO')
        self.ctrls.append(self.head_ctrl)

        self.head_ctrl.rotateOrder.set(4)

        # Extract twist
        twist = coreUtils.extractAxis(self.head_ctrl, axis='y', name='head_twist', exposeNode=self.main_grp, exposeAttr='twist')
        twist['main_grp'].setParent(self.rig_grp)
        pmc.parentConstraint(self.headZero_grp, twist['main_grp'])

        # colours
        coreUtils.colorize('green', [self.head_ctrl])

        # connections
        self.exposeSockets({'ctrl': self.head_ctrl})

        if cleanup:
            self.cleanup()

    def cleanup(self):
        coreUtils.attrCtrl(nodeList=[self.head_ctrl], attrList=['sx', 'sy', 'sz', 'visibility'])
        self.rig_grp.visibility.set(0)
