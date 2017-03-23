import pymel.core as pmc
import drTools.systems.curveUtils as curveUtils
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls

reload(controls)
reload(systemUtils)
reload(curveUtils)
reload(coreUtils)

class DrRail(systemUtils.DrSystem):
    '''
    Takes a nurbs curve as input.
    Creates a new curve which slides along the input curve sampling a section of it.
    Controls at each end specify the start and end points for the sub curve
    Also provides sub controls for each point on the sub curve to offset it from the parent curve.
    Example usage - lips
    '''
    def __init__(self, name, crv=None, numCtrls=5, numSubCtrls=9):
        if not crv and len(pmc.selected()) == 1:
            crv = pmc.selected()[0]
        super(DrRail, self).__init__(name)
        self.ctrls=[]
        self.subCtrls = []
        self.buildRail(crv, numCtrls, numSubCtrls)

    def buildRail(self, crv, numCtrls, numSubCtrls):
        if not crv:
            return 'Please provide a curve on which to build your rail'

        ctrlSize=coreUtils.getDistance(crv.getCV(0), crv.getCV(1)) * .25

        self.noXform_grp = coreUtils.addChild(self.rig_grp, 'group', '%s_noXform_GRP' % self.name)
        self.noXform_grp.inheritsTransform.set(0)

        self.const_grp = coreUtils.addChild(self.rig_grp, 'group', '%s_CONST' % self.name)

        self.upLoc = coreUtils.addChild(self.rig_grp, 'locator', '%s_up_LOC' % self.name)
        up_vp = pmc.createNode('vectorProduct', name='vecProd_%s_up_UTL' % self.name)
        self.upLoc.worldMatrix[0].connect(up_vp.matrix)
        up_vp.operation.set(3)
        up_vp.input1.set((0, 1, 0))

        infos = curveUtils.sampleCurve(crv, numSamples=numCtrls, name=self.name)
        subPoints = [inf.result.position.get() for inf in infos]

        for i in range(numCtrls):
            inf = infos[i]
            num = str(i+1).zfill(2)

            d = curveUtils.curveTangentMatrix(inf, up_vp, '%s_%s' % (self.name, num))

            g = coreUtils.addChild(self.const_grp, 'group', '%s_rail_%s_GRP' % (self.name, num))
            d.outputTranslate.connect(g.t)
            d.outputRotate.connect(g.r)

            c = controls.circleBumpCtrl(axis='z', radius=ctrlSize, name='%s_%s_CTRL' % (self.name, num))
            coreUtils.align(c, g)
            c.setParent(self.ctrls_grp)
            zero = coreUtils.addParent(c, 'group', '%s_%sCtrl_ZERO' % (self.name, num))
            const = coreUtils.addParent(zero, 'group', '%s_%sCtrl_CONST' % (self.name, num))
            pmc.parentConstraint(g, const, mo=0)
            self.ctrls.append(c)

        pmc.addAttr(self.main_grp, ln='start_uValue', at='double', k=1, h=0, minValue=0.0, maxValue=1.0)
        pmc.addAttr(self.main_grp, ln='end_uValue', at='double', k=1, h=0, minValue=0.0, maxValue=1.0)

        self.main_grp.start_uValue.connect(infos[0].parameter)
        self.main_grp.end_uValue.connect(infos[-1].parameter)

        # Set up blending of sub curveInfo nodes between start and end
        for i in range(1, numCtrls-1):
            inf = infos[i]
            bc = coreUtils.blend(infos[-1].parameter, infos[0].parameter,
                                 name='blend_%s_%s_uValue_UTL' % (self.name, str(i+1).zfill(2)))
            bc.blender.set((1.0 / (numCtrls-1))*i)
            bc.outputR.connect(inf.parameter)

        # Build sub curve
        locs_grp = coreUtils.addChild(self.rig_grp, 'group', '%s_subCrvLocs_GRP' % self.name)
        self.subCrv = curveUtils.curveThroughPoints(positions=subPoints, name='%s_sub' % self.name)
        pmc.rebuildCurve(self.subCrv, kcp=1, kr=0, rpo=1, end=1)
        self.subCrv.setParent(self.noXform_grp)
        self.locs = curveUtils.connectCurve(self.subCrv)
        for i in range(numCtrls):
            loc = self.locs[i]
            loc.setParent(locs_grp)
            zero = coreUtils.addParent(loc, 'group', loc.name().replace('_LOC', 'Loc_ZERO'))
            infos[i].result.position.connect(zero.t)
            self.ctrls[i].t.connect(loc.t)

        # Create joints and subCtrls
        subInfos = curveUtils.sampleCurve(self.subCrv, numSamples=numSubCtrls, name='%s_Sub' % self.name)
        for i in range(numSubCtrls):
            num = str(i+1).zfill(2)
            inf = subInfos[i]
            d = curveUtils.curveTangentMatrix(inf, up_vp, '%sSub_%s' % (self.name, num))

            g = coreUtils.addChild(self.const_grp, 'group', '%s_subRail_%s_GRP' % (self.name, num))
            d.outputTranslate.connect(g.t)
            d.outputRotate.connect(g.r)

            c = controls.circleCtrl(axis='z', radius=ctrlSize*.33, name='%s_%s_sub_CTRL' % (self.name, num))
            coreUtils.align(c, g)
            c.setParent(self.ctrls_grp)
            zero = coreUtils.addParent(c, 'group', '%s_%sSubCtrl_ZERO' % (self.name, num))
            const = coreUtils.addParent(zero, 'group', '%s_%sSubCtrl_CONST' % (self.name, num))
            pmc.parentConstraint(g, const, mo=0)
            self.subCtrls.append(c)



