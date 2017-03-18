import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.systemUtils as systemUtils
import drTools.systems.controls as controls
import drTools.systems.limb as drLimb
import drTools.systems.twistySegment as drTwistySegment

reload(controls)
reload(coreUtils)
reload(systemUtils)
reload(drLimb)
reload(drTwistySegment)

class DrArm(drLimb.DrLimb):
    def __init__(self, name='', joints=None, cleanup=0, colour='red', numTwistSegs=8):
        super(DrArm, self).__init__(name, joints=joints)
        self.buildArm(colour, numTwistSegs)

    def buildArm(self, colour, numTwistSegs):
        # Twisty Segments
        #Upper twist
        self.upperTwist = drTwistySegment.DrTwistySegmentCurve(name='%s_upperTwist' % self.name,
                                                               start=self.tripleChain['resultChain'][0],
                                                               end=self.tripleChain['resultChain'][1],
                                                               numSegs=numTwistSegs,
                                                               numCtrls=2,
                                                               axis='x',
                                                               upAxis='y',
                                                               worldUpAxis='y',
                                                               colour=colour,
                                                               cleanup=0)
        self.upperTwist.main_grp.setParent(self.main_grp)
        p = systemUtils.plug(self.upperTwist.start_grp, self.sockets['start'], name='upperTwistStart')
        p.setParent(self.upperTwist.plugs_grp)
        p = systemUtils.plug(self.upperTwist.end_grp, self.sockets['mid'], name='upperTwistEnd')
        p.setParent(self.upperTwist.plugs_grp)
        self.main_grp.top_twist.connect(self.upperTwist.twist_pma.input1D[0])
        self.main_grp.globalScale.connect(self.upperTwist.main_grp.globalScale)

        #Lower twist
        self.lowerTwist = drTwistySegment.DrTwistySegmentCurve(name='%s_lowerTwist' % self.name,
                                                               start=self.tripleChain['resultChain'][1],
                                                               end=self.tripleChain['resultChain'][2],
                                                               numSegs=numTwistSegs,
                                                               numCtrls=2,
                                                               axis='x',
                                                               upAxis='y',
                                                               worldUpAxis='y',
                                                               colour=colour,
                                                               cleanup=0)
        self.lowerTwist.main_grp.setParent(self.main_grp)
        p = systemUtils.plug(self.lowerTwist.start_grp, self.sockets['mid'], name='lowerTwistStart')
        p.setParent(self.lowerTwist.plugs_grp)
        p = systemUtils.plug(self.lowerTwist.end_grp, self.sockets['end'], name='lowerTwistEnd')
        p.setParent(self.lowerTwist.plugs_grp)
        self.main_grp.btm_twist.connect(self.lowerTwist.twist_pma.input1D[0])
        self.main_grp.globalScale.connect(self.lowerTwist.main_grp.globalScale)








        coreUtils.colorize(colour, self.ctrls)


    def cleanup(self):
        super(DrArm, self).cleanup()
        pass