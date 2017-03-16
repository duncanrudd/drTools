import pymel.core as pmc
import drTools.systems.spine as drSpine
import drTools.systems.systemUtils as systemUtils
import drTools.systems.twistySegment as drTwistySegment
import drTools.systems.head as drHead
import drTools.systems.root as drRoot

reload(systemUtils)
reload(drSpine)
reload(drTwistySegment)
reload(drHead)
reload(drRoot)

class DrBiped(object):
    '''
    builds a default biped based on the default template maya file (assets/rig_templates/dr_defaultRig_template.ma)
    '''

    def __init__(self):
        super(DrBiped, self).__init__()
        self.build()

    def build(self):
        # root
        self.rootSystem = drRoot.DrRig()

        # spine
        self.spineSystem = drSpine.DrSpine(name='spine',
                                           start=pmc.PyNode('hip_GD'),
                                           end=pmc.PyNode('chest_GD'),
                                           rtHip=pmc.PyNode('rt_hip_GD'),
                                           lfHip=pmc.PyNode('lf_hip_GD'),
                                           rtShldr=pmc.PyNode('rt_clavEnd_GD'),
                                           rtClav=pmc.PyNode('rt_clavStart_GD'),
                                           lfShldr=pmc.PyNode('lf_clavEnd_GD'),
                                           lfClav=pmc.PyNode('lf_clavStart_GD'))

        p = systemUtils.plug(self.spineSystem.bodyZero_grp, self.rootSystem.rootSystem.sockets['03'], name='spine')
        p.setParent(self.spineSystem.plugs_grp)

        # Head
        self.headSystem = drHead.DrHead(name='head', start=pmc.PyNode('head_GD'))
        p = systemUtils.plug(self.headSystem.headZero_grp, self.spineSystem.sockets['chest'], plugType='point', name='head')
        p.setParent(self.headSystem.plugs_grp)
        p = systemUtils.multiPlug(self.headSystem.headZero_grp,
                                  targetList=[self.spineSystem.sockets['body'], self.spineSystem.sockets['chest']],
                                  targetNames=['body', 'chest'],
                                  settingsNode=self.headSystem.head_ctrl,
                                  plugType='orient',
                                  name='head')
        p.setParent(self.headSystem.plugs_grp)


        # neck
        self.neckSystem = drTwistySegment.DrTwistySegment(name='neck',
                                                          start=pmc.PyNode('neck_GD'),
                                                          end=pmc.PyNode('head_GD'),
                                                          numSegs=3,
                                                          axis='y',
                                                          upAxis='x',
                                                          worldUpAxis='x')

        p = systemUtils.plug(self.neckSystem.start_grp, self.spineSystem.sockets['chest'], name='neckStart')
        p.setParent(self.neckSystem.plugs_grp)
        p = systemUtils.plug(self.neckSystem.end_grp, self.headSystem.sockets['base'], name='neckEnd')
        p.setParent(self.neckSystem.plugs_grp)
        self.headSystem.head_ctrl.twist.connect(self.neckSystem.main_grp.twist)


        # Parent to rig_grp and connect globalscales of all systems
        for system in [self.spineSystem, self.headSystem, self.neckSystem]:
            system.main_grp.setParent(self.rootSystem.rig_grp)
            self.rootSystem.rootSystem.main_grp.globalScale.connect(system.main_grp.globalScale)