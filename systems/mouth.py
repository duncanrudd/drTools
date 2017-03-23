import pymel.core as pmc
import drTools.systems.curveUtils as curveUtils
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls
import drTools.systems.rail as drRail

reload(drRail)
reload(controls)
reload(systemUtils)
reload(curveUtils)
reload(coreUtils)

class DrMouth(systemUtils.DrSystem):
    def __init__(self, name, crv=None, numCtrls=5, numLipJoints=9):
        if not crv and len(pmc.selected()) == 1:
            crv = pmc.selected()[0]
        super(DrMouth, self).__init__(name)
        self.buildMouth(crv, numCtrls, numLipJoints)

    def buildMouth(self, crv, numCtrls, numLipJoints):
        if not crv:
            return 'DrMouth: Please provide a curve for the mouth to ride along'
        self.topLip = drRail.DrRail(name='topLip', crv=crv, numCtrls=numCtrls, numSubCtrls=numLipJoints)
        self.topLip.main_grp.end_uValue.set(1.0)
        self.topLip.main_grp.setParent(self.main_grp)

        self.btmLip = drRail.DrRail(name='btmLip', crv=crv, numCtrls=numCtrls, numSubCtrls=numLipJoints)
        self.btmLip.main_grp.end_uValue.set(1.0)
        self.btmLip.main_grp.setParent(self.main_grp)

        ctrlSize=coreUtils.getDistance(crv.getCV(0), crv.getCV(1)) * .5

        self.rtCtrl = controls.circleBumpCtrl(radius=ctrlSize, name='%s_rt_corner_CTRL' % self.name)
        coreUtils.align(self.rtCtrl, self.topLip.ctrls[0])
        self.rtCtrl.setParent(self.ctrls_grp)
        zero = coreUtils.addParent(self.rtCtrl, 'group', '%s_rt_cornerCtrl_ZERO' % self.name)
        coreUtils.colorize('red', [self.rtCtrl])

        self.lfCtrl = controls.circleBumpCtrl(radius=ctrlSize, name='%s_lf_corner_CTRL' % self.name)
        coreUtils.align(self.lfCtrl, self.topLip.ctrls[-1])
        self.lfCtrl.setParent(self.ctrls_grp)
        zero = coreUtils.addParent(self.lfCtrl, 'group', '%s_lf_cornerCtrl_ZERO' % self.name)
        coreUtils.colorize('blue', [self.lfCtrl])
        zero.sx.set(-1)

        #split into left and right
        for i in range(numCtrls):
            topCtrl = self.topLip.ctrls[i]
            topLoc = self.topLip.locs[i]
            btmCtrl = self.btmLip.ctrls[i]
            btmLoc = self.btmLip.locs[i]
            if i < numCtrls / 2:
                coreUtils.colorize('red', [topCtrl, btmCtrl])
            elif i > numCtrls / 2:
                coreUtils.colorize('blue', [topCtrl, btmCtrl])
                topCtrl.getParent().sx.set(-1)
                topLoc.getParent().sx.set(-1)
                btmCtrl.getParent().sx.set(-1)
                btmLoc.getParent().sx.set(-1)
            else:
                coreUtils.colorize('green', [topCtrl, btmCtrl])
            if i == 0:
                pmc.delete([topCtrl.getParent(), btmCtrl.getParent()])
            if i == (numCtrls-1):
                pmc.delete([topCtrl.getParent(), btmCtrl.getParent()])

        rt_loc = coreUtils.addChild(self.rig_grp, 'locator', '%s_rt_corner_LOC' % self.name)
        coreUtils.align(rt_loc, self.rtCtrl)
        rt_zero = coreUtils.addParent(rt_loc, 'group', '%s_rt_cornerLoc_ZERO' % self.name)
        self.rtCtrl.t.connect(rt_loc.t)
        rtCornerClosestPoint = pmc.createNode('nearestPointOnCurve', name='closestCrvPoint_%s_rt_corner_UTL' % self.name)
        locShape = pmc.listRelatives(rt_loc, s=1, c=1)[0]
        locShape.worldPosition[0].connect(rtCornerClosestPoint.inPosition)
        crvShape = coreUtils.getShape(crv)
        crvShape.worldSpace[0].connect(rtCornerClosestPoint.inputCurve)
        rtCornerClosestPoint.parameter.connect(self.topLip.main_grp.start_uValue)
        rtCornerClosestPoint.parameter.connect(self.btmLip.main_grp.start_uValue)
        pmc.pointConstraint(rt_loc, self.topLip.locs[0].getParent(), mo=0)
        pmc.pointConstraint(rt_loc, self.btmLip.locs[0].getParent(), mo=0)

        lf_loc = coreUtils.addChild(self.rig_grp, 'locator', '%s_lf_corner_LOC' % self.name)
        coreUtils.align(lf_loc, self.lfCtrl)
        lf_zero = coreUtils.addParent(lf_loc, 'group', '%s_lf_cornerLoc_ZERO' % self.name)
        self.lfCtrl.t.connect(lf_loc.t)
        lfCornerClosestPoint = pmc.createNode('nearestPointOnCurve', name='closestCrvPoint_%s_lf_corner_UTL' % self.name)
        locShape = pmc.listRelatives(lf_loc, s=1, c=1)[0]
        locShape.worldPosition[0].connect(lfCornerClosestPoint.inPosition)
        crvShape.worldSpace[0].connect(lfCornerClosestPoint.inputCurve)
        lfCornerClosestPoint.parameter.connect(self.topLip.main_grp.end_uValue)
        lfCornerClosestPoint.parameter.connect(self.btmLip.main_grp.end_uValue)
        pmc.pointConstraint(lf_loc, self.topLip.locs[-1].getParent(), mo=0)
        pmc.pointConstraint(lf_loc, self.btmLip.locs[-1].getParent(), mo=0)

        # Constrain systems
        pmc.parentConstraint(self.ctrls_grp, self.topLip.const_grp)
        pmc.parentConstraint(self.ctrls_grp, self.btmLip.const_grp)




