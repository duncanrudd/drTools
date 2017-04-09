import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.spine as drSpine
import drTools.systems.systemUtils as systemUtils
import drTools.systems.twistySegment as drTwistySegment
import drTools.systems.head as drHead
import drTools.systems.root as drRoot
import drTools.systems.arm as drArm
import drTools.systems.hoof as drHoof
import drTools.systems.hand as drHand

reload(coreUtils)
reload(systemUtils)
reload(drSpine)
reload(drTwistySegment)
reload(drHead)
reload(drRoot)
reload(drArm)
reload(drHoof)
reload(drHand)


class DrCow(object):
    '''
    builds a default biped based on the default template maya file (assets/rig_templates/dr_defaultRig_template.ma)
    '''

    def __init__(self):
        super(DrCow, self).__init__()
        self.build()

    def build(self):
        ################################################################################################################
        # root
        self.rigSystem = drRoot.DrRig(ctrlSize=5.0)

        ################################################################################################################
        # spine
        self.spineSystem = drSpine.DrSpine(name='spine',
                                           start=pmc.PyNode('hip_GD'),
                                           end=pmc.PyNode('chest_GD'),
                                           rtHip=pmc.PyNode('rt_hip_GD'),
                                           lfHip=pmc.PyNode('lf_hip_GD'),
                                           rtShldr=pmc.PyNode('rt_shldr_GD'),
                                           lfShldr=pmc.PyNode('lf_shldr_GD'),)

        p = systemUtils.plug(self.spineSystem.bodyZero_grp, self.rigSystem.rootSystem.sockets['03'], name='spine')
        p.setParent(self.spineSystem.plugs_grp)

        # Head
        self.headSystem = drHead.DrHead(name='head', start=pmc.PyNode('head_GD'))
        p = systemUtils.plug(self.headSystem.headZero_grp, self.spineSystem.sockets['chest'], plugType='point',
                             name='head')
        p.setParent(self.headSystem.plugs_grp)
        p = systemUtils.multiPlug(self.headSystem.headZero_grp,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'], self.spineSystem.sockets['body'],
                                              self.spineSystem.sockets['chest']],
                                  targetNames=['root', 'body', 'chest'],
                                  settingsNode=self.headSystem.head_ctrl,
                                  plugType='orient',
                                  name='head')
        p.setParent(self.headSystem.plugs_grp)

        ################################################################################################################
        # neck
        self.neckSystem = drTwistySegment.DrTwistySegmentSimple(name='neck',
                                                                start=pmc.PyNode('neck_GD'),
                                                                end=pmc.PyNode('head_GD'),
                                                                numSegs=3,
                                                                axis='y',
                                                                upAxis='x',
                                                                worldUpAxis='x')

        p = systemUtils.plug(self.neckSystem.start_grp, self.spineSystem.sockets['chest'], name='neckStart')
        p.setParent(self.neckSystem.plugs_grp)
        p = systemUtils.plug(self.neckSystem.end_grp, self.headSystem.sockets['ctrl'], name='neckEnd')
        p.setParent(self.neckSystem.plugs_grp)
        self.spineSystem.main_grp.chest_twist.connect(self.neckSystem.twist_pma.input1D[1])
        self.headSystem.main_grp.twist.connect(self.neckSystem.twist_pma.input1D[0])

        ################################################################################################################
        # right arm
        self.rtArmSystem = drArm.DrArm(name='rt_arm',
                                       joints=[pmc.PyNode('rt_shldr_GD'),
                                               pmc.PyNode('rt_elbow_GD'),
                                               pmc.PyNode('rt_wrist_GD'),
                                               pmc.PyNode('rt_wrist_end_GD')],
                                       numTwistSegs=7,
                                       leg=0,
                                       flipTwist=0)
        # connect to body
        p = systemUtils.plug(self.rtArmSystem.fkCtrls_grp, self.spineSystem.sockets['rt_shldr'], plugType='parent',
                             name='shldr')
        p.setParent(self.rtArmSystem.plugs_grp)
        p = systemUtils.multiPlug(self.rtArmSystem.fkCtrlsConst_grp,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'], self.spineSystem.sockets['body'],
                                              self.spineSystem.sockets['chest']],
                                  targetNames=['root', 'body', 'chest'],
                                  settingsNode=self.rtArmSystem.fkTopCtrl,
                                  plugType='orient',
                                  name='rt_arm_shldr')
        p.setParent(self.rtArmSystem.plugs_grp)

        # spaceswitch for ikCtrl
        p = systemUtils.multiPlug(self.rtArmSystem.ikCtrls_grp,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'], self.spineSystem.sockets['body'],
                                              self.spineSystem.sockets['chest'], self.headSystem.sockets['ctrl']],
                                  targetNames=['root', 'body', 'chest', 'head'],
                                  settingsNode=self.rtArmSystem.ikCtrl,
                                  plugType='parent',
                                  name='rt_arm_ikCtrl')
        p.setParent(self.rtArmSystem.plugs_grp)

        # spaceswitch for polevector
        p = systemUtils.multiPlug(self.rtArmSystem.pvZero,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'], self.spineSystem.sockets['body'],
                                              self.spineSystem.sockets['chest'],
                                              self.rtArmSystem.sockets['poleVectorAim']],
                                  targetNames=['root', 'body', 'chest', 'arm'],
                                  settingsNode=self.rtArmSystem.pvCtrl,
                                  plugType='parent',
                                  name='rt_arm_poleVectorCtrl')
        p.setParent(self.rtArmSystem.plugs_grp)

        ################################################################################################################
        # left arm
        self.lfArmSystem = drArm.DrArm(name='lf_arm',
                                       joints=[pmc.PyNode('lf_shldr_GD'),
                                               pmc.PyNode('lf_elbow_GD'),
                                               pmc.PyNode('lf_wrist_GD'),
                                               pmc.PyNode('lf_wrist_end_GD')],
                                       numTwistSegs=7,
                                       leg=0,
                                       flipTwist=1,
                                       colour='blue')
        # connect to body
        p = systemUtils.plug(self.lfArmSystem.fkCtrls_grp, self.spineSystem.sockets['lf_shldr'], plugType='parent',
                             name='shldr')
        p.setParent(self.lfArmSystem.plugs_grp)
        p = systemUtils.multiPlug(self.lfArmSystem.fkCtrlsConst_grp,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'], self.spineSystem.sockets['body'],
                                              self.spineSystem.sockets['chest']],
                                  targetNames=['root', 'body', 'chest'],
                                  settingsNode=self.lfArmSystem.fkTopCtrl,
                                  plugType='orient',
                                  name='lf_arm_shldr')
        p.setParent(self.lfArmSystem.plugs_grp)

        # spaceswitch for ikCtrl
        p = systemUtils.multiPlug(self.lfArmSystem.ikCtrls_grp,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'], self.spineSystem.sockets['body'],
                                              self.spineSystem.sockets['chest'], self.headSystem.sockets['ctrl']],
                                  targetNames=['root', 'body', 'chest', 'head'],
                                  settingsNode=self.lfArmSystem.ikCtrl,
                                  plugType='parent',
                                  name='lf_arm_ikCtrl')
        p.setParent(self.lfArmSystem.plugs_grp)

        # spaceswitch for polevector
        p = systemUtils.multiPlug(self.lfArmSystem.pvZero,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'], self.spineSystem.sockets['body'],
                                              self.spineSystem.sockets['chest'],
                                              self.lfArmSystem.sockets['poleVectorAim']],
                                  targetNames=['root', 'body', 'chest', 'arm'],
                                  settingsNode=self.lfArmSystem.pvCtrl,
                                  plugType='parent',
                                  name='lf_arm_poleVectorCtrl')
        p.setParent(self.lfArmSystem.plugs_grp)

        ################################################################################################################
        # right leg
        self.rtLegSystem = drArm.DrArm(name='rt_leg',
                                       joints=[pmc.PyNode('rt_hip_GD'),
                                               pmc.PyNode('rt_knee_GD'),
                                               pmc.PyNode('rt_ankle_GD'),
                                               pmc.PyNode('rt_ankle_end_GD')],
                                       numTwistSegs=7,
                                       upAxis='z',
                                       flipTwist=0,
                                       leg=0)
        # connect to body
        p = systemUtils.plug(self.rtLegSystem.fkCtrls_grp, self.spineSystem.sockets['rt_hip'], plugType='parent',
                             name='rt_leg_hip')
        p.setParent(self.rtLegSystem.plugs_grp)

        # spaceswitch for ikCtrl
        p = systemUtils.multiPlug(self.rtLegSystem.ikCtrls_grp,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'],
                                              self.spineSystem.sockets['hips']],
                                  targetNames=['root', 'hip'],
                                  settingsNode=self.rtLegSystem.ikCtrl,
                                  plugType='parent',
                                  name='rt_leg_ikCtrl')
        p.setParent(self.rtLegSystem.plugs_grp)

        # spaceswitch for polevector
        p = systemUtils.multiPlug(self.rtLegSystem.pvZero,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'],
                                              self.spineSystem.sockets['hips'],
                                              self.rtLegSystem.sockets['poleVectorAim']],
                                  targetNames=['root', 'hip', 'foot'],
                                  settingsNode=self.rtLegSystem.pvCtrl,
                                  plugType='parent',
                                  name='rt_leg_poleVectorCtrl')
        p.setParent(self.rtLegSystem.plugs_grp)

        ################################################################################################################
        # left leg
        self.lfLegSystem = drArm.DrArm(name='lf_leg',
                                       joints=[pmc.PyNode('lf_hip_GD'),
                                               pmc.PyNode('lf_knee_GD'),
                                               pmc.PyNode('lf_ankle_GD'),
                                               pmc.PyNode('lf_ankle_end_GD')],
                                       numTwistSegs=7,
                                       upAxis='z',
                                       leg=0,
                                       flipTwist=1,
                                       colour='blue')
        # connect to body
        p = systemUtils.plug(self.lfLegSystem.fkCtrls_grp, self.spineSystem.sockets['lf_hip'], plugType='parent',
                             name='hip')
        p.setParent(self.lfLegSystem.plugs_grp)

        # spaceswitch for ikCtrl
        p = systemUtils.multiPlug(self.lfLegSystem.ikCtrls_grp,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'],
                                              self.spineSystem.sockets['hips']],
                                  targetNames=['root', 'hip'],
                                  settingsNode=self.lfLegSystem.ikCtrl,
                                  plugType='parent',
                                  name='lf_leg_ikCtrl')
        p.setParent(self.lfLegSystem.plugs_grp)

        # spaceswitch for polevector
        p = systemUtils.multiPlug(self.lfLegSystem.pvZero,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'],
                                              self.spineSystem.sockets['hips'],
                                              self.lfLegSystem.sockets['poleVectorAim']],
                                  targetNames=['root', 'hip', 'foot'],
                                  settingsNode=self.lfLegSystem.pvCtrl,
                                  plugType='parent',
                                  name='lf_leg_poleVectorCtrl')
        p.setParent(self.lfLegSystem.plugs_grp)

        ################################################################################################################
        
        # right foot
        self.rtFootSystem = drHoof.DrHoof(name='rt_foot',
                                                        ankle=pmc.PyNode('rt_ankle_GD'),
                                                        toe=pmc.PyNode('rt_toe_GD'),
                                                        heel=pmc.PyNode('rt_heel_GD'),
                                                        inner=pmc.PyNode('rt_inner_GD'),
                                                        outer=pmc.PyNode('rt_outer_GD'),
                                                        settingsNode=self.rtLegSystem.ikCtrl,
                                                        blendAttr=self.rtLegSystem.settingsCtrl.ik_fk_blend)

        # connect to body
        p = systemUtils.plug(self.rtFootSystem.ikConstGrp, self.rtLegSystem.sockets['ikCtrl'], name='rt_ikFoot')
        p.setParent(self.rtFootSystem.plugs_grp)
        p = systemUtils.plug(self.rtFootSystem.fkConstGrp, self.rtLegSystem.sockets['fkCtrl'], name='rt_fkFoot')
        p.setParent(self.rtFootSystem.plugs_grp)

        # attach ik leg to foot
        p = systemUtils.plug(self.rtLegSystem.ctrl_loc, self.rtFootSystem.sockets['ankle'], name='rt_leg_ikFoot')
        p.setParent(self.rtLegSystem.plugs_grp)
        
        ################################################################################################################
        # left foot
        self.lfFootSystem = drHoof.DrHoof(name='lf_foot',
                                          ankle=pmc.PyNode('lf_ankle_GD'),
                                          toe=pmc.PyNode('lf_toe_GD'),
                                          heel=pmc.PyNode('lf_heel_GD'),
                                          inner=pmc.PyNode('lf_inner_GD'),
                                          outer=pmc.PyNode('lf_outer_GD'),
                                          settingsNode=self.lfLegSystem.ikCtrl,
                                          blendAttr=self.lfLegSystem.settingsCtrl.ik_fk_blend)

        # connect to body
        p = systemUtils.plug(self.lfFootSystem.ikConstGrp, self.lfLegSystem.sockets['ikCtrl'], name='lf_ikFoot')
        p.setParent(self.lfFootSystem.plugs_grp)
        p = systemUtils.plug(self.lfFootSystem.fkConstGrp, self.lfLegSystem.sockets['fkCtrl'], name='lf_fkFoot')
        p.setParent(self.lfFootSystem.plugs_grp)

        # attach ik leg to foot
        p = systemUtils.plug(self.lfLegSystem.ctrl_loc, self.lfFootSystem.sockets['ankle'], name='lf_leg_ikFoot')
        p.setParent(self.lfLegSystem.plugs_grp)

        ################################################################################################################
        # right hand
        self.rtHandSystem = drHoof.DrHoof(name='rt_hand',
                                            ankle=pmc.PyNode('rt_wrist_GD'),
                                            toe=pmc.PyNode('rt_hand_toe_GD'),
                                            heel=pmc.PyNode('rt_hand_heel_GD'),
                                            inner=pmc.PyNode('rt_hand_inner_GD'),
                                            outer=pmc.PyNode('rt_hand_outer_GD'),
                                            settingsNode=self.rtArmSystem.ikCtrl,
                                            blendAttr=self.rtArmSystem.settingsCtrl.ik_fk_blend)
        
        # connect to body
        p = systemUtils.plug(self.rtHandSystem.ikConstGrp, self.rtArmSystem.sockets['ikCtrl'], name='rt_ikHand')
        p.setParent(self.rtHandSystem.plugs_grp)
        p = systemUtils.plug(self.rtHandSystem.fkConstGrp, self.rtArmSystem.sockets['fkCtrl'], name='rt_fkHand')
        p.setParent(self.rtHandSystem.plugs_grp)

        # attach ik leg to foot
        p = systemUtils.plug(self.rtArmSystem.ctrl_loc, self.rtHandSystem.sockets['ankle'], name='rt_arm_ikHand')
        p.setParent(self.rtArmSystem.plugs_grp)

        ################################################################################################################
        # left hand
        self.lfHandSystem = drHoof.DrHoof(name='lf_hand',
                                            ankle=pmc.PyNode('lf_wrist_GD'),
                                            toe=pmc.PyNode('lf_hand_toe_GD'),
                                            heel=pmc.PyNode('lf_hand_heel_GD'),
                                            inner=pmc.PyNode('lf_hand_inner_GD'),
                                            outer=pmc.PyNode('lf_hand_outer_GD'),
                                            settingsNode=self.lfArmSystem.ikCtrl,
                                            blendAttr=self.lfArmSystem.settingsCtrl.ik_fk_blend)
        
        # connect to body
        p = systemUtils.plug(self.lfHandSystem.ikConstGrp, self.lfArmSystem.sockets['ikCtrl'], name='lf_ikHand')
        p.setParent(self.lfHandSystem.plugs_grp)
        p = systemUtils.plug(self.lfHandSystem.fkConstGrp, self.lfArmSystem.sockets['fkCtrl'], name='lf_fkHand')
        p.setParent(self.lfHandSystem.plugs_grp)

        # attach ik leg to foot
        p = systemUtils.plug(self.lfArmSystem.ctrl_loc, self.lfHandSystem.sockets['ankle'], name='lf_arm_ikHand')
        p.setParent(self.lfArmSystem.plugs_grp)        

        ################################################################################################################
        # Parent to rig_grp and connect globalscales of all systems
        for system in [self.spineSystem,
                       self.headSystem,
                       self.neckSystem,
                       self.rtArmSystem,
                       self.lfArmSystem,
                       self.rtLegSystem,
                       self.lfLegSystem,
                       self.rtFootSystem,
                       self.lfFootSystem,
                       self.rtHandSystem,
                       self.lfHandSystem]:
            system.main_grp.setParent(self.rigSystem.rig_grp)
            self.rigSystem.rootSystem.main_grp.globalScale.connect(system.main_grp.globalScale)

        ################################################################################################################
        # Publish joints
        publishJoints(self.rigSystem, [self.spineSystem,
                                       self.headSystem,
                                       self.neckSystem,
                                       self.rtArmSystem,
                                       self.lfArmSystem,
                                       self.rtLegSystem,
                                       self.lfLegSystem,
                                       self.rtFootSystem,
                                       self.lfFootSystem,
                                       self.rtHandSystem,
                                       self.lfHandSystem])


def publishJoints(rig, systems):
    """
    for each system, makes a group under rig.bind_GRP. Makes a copy of each joint in system.joints and constrains it
    to the corresponding system joint.
    """
    for system in systems:
        grp = coreUtils.addChild(rig.bind_grp, 'group', '%s_bind_GRP' % system.name)
        for joint in system.joints:
            j = coreUtils.addChild(grp, 'joint', joint.name().replace('JNT', 'BND'))
            pmc.parentConstraint(joint, j, mo=0)
            pmc.scaleConstraint(joint, j, mo=0)


############################################
# ROOSTER

'''
import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.spine as drSpine
import drTools.systems.systemUtils as systemUtils
import drTools.systems.twistySegment as drTwistySegment
import drTools.systems.head as drHead
import drTools.systems.root as drRoot
import drTools.systems.arm as drArm
import drTools.systems.hoof as drHoof
import drTools.systems.hand as drHand

reload(coreUtils)
reload(systemUtils)
reload(drSpine)
reload(drTwistySegment)
reload(drHead)
reload(drRoot)
reload(drArm)
reload(drHoof)
reload(drHand)

rigSystem = drRoot.DrRig(ctrlSize=3.0)


# spine
spine = drSpine.DrSpine(name='neck', numJoints=8,
                                   start=pmc.PyNode('hip_GD'),
                                   end=pmc.PyNode('chest_GD'),
                                   rtHip=pmc.PyNode('rt_hip_GD'),
                                   lfHip=pmc.PyNode('lf_hip_GD'),
                                   rtShldr=pmc.PyNode('rt_shldr_GD'),
                                   lfShldr=pmc.PyNode('lf_shldr_GD'),)

p = systemUtils.plug(spine.bodyZero_grp, rigSystem.rootSystem.sockets['03'], name='spine')
p.setParent(spine.plugs_grp)

# right leg
rtLegSystem = drArm.DrArm(name='rt_leg',
                               joints=[pmc.PyNode('rt_hip_GD'),
                                       pmc.PyNode('rt_knee_GD'),
                                       pmc.PyNode('rt_ankle_GD'),
                                       pmc.PyNode('rt_ankle_end_GD')],
                               numTwistSegs=7,
                               upAxis='z',
                               flipTwist=0,
                               leg=0)
# connect to body
p = systemUtils.plug(rtLegSystem.fkCtrls_grp, spine.sockets['rt_hip'], plugType='parent',
                     name='rt_leg_hip')
p.setParent(rtLegSystem.plugs_grp)

# spaceswitch for ikCtrl
p = systemUtils.multiPlug(rtLegSystem.ikCtrls_grp,
                          targetList=[rigSystem.rootSystem.sockets['03'],
                                      spine.sockets['hips']],
                          targetNames=['root', 'hip'],
                          settingsNode=rtLegSystem.ikCtrl,
                          plugType='parent',
                          name='rt_leg_ikCtrl')
p.setParent(rtLegSystem.plugs_grp)

# spaceswitch for polevector
p = systemUtils.multiPlug(rtLegSystem.pvZero,
                          targetList=[rigSystem.rootSystem.sockets['03'],
                                      spine.sockets['hips'],
                                      rtLegSystem.sockets['poleVectorAim']],
                          targetNames=['root', 'hip', 'foot'],
                          settingsNode=rtLegSystem.pvCtrl,
                          plugType='parent',
                          name='rt_leg_poleVectorCtrl')
p.setParent(rtLegSystem.plugs_grp)

# left leg
lfLegSystem = drArm.DrArm(name='lf_leg',
                               joints=[pmc.PyNode('lf_hip_GD'),
                                       pmc.PyNode('lf_knee_GD'),
                                       pmc.PyNode('lf_ankle_GD'),
                                       pmc.PyNode('lf_ankle_end_GD')],
                               numTwistSegs=7,
                               upAxis='z',
                               flipTwist=1,
                               colour='blue',
                               leg=0)
# connect to body
p = systemUtils.plug(lfLegSystem.fkCtrls_grp, spine.sockets['lf_hip'], plugType='parent',
                     name='lf_leg_hip')
p.setParent(lfLegSystem.plugs_grp)

# spaceswitch for ikCtrl
p = systemUtils.multiPlug(lfLegSystem.ikCtrls_grp,
                          targetList=[rigSystem.rootSystem.sockets['03'],
                                      spine.sockets['hips']],
                          targetNames=['root', 'hip'],
                          settingsNode=lfLegSystem.ikCtrl,
                          plugType='parent',
                          name='lf_leg_ikCtrl')
p.setParent(lfLegSystem.plugs_grp)

# spaceswitch for polevector
p = systemUtils.multiPlug(lfLegSystem.pvZero,
                          targetList=[rigSystem.rootSystem.sockets['03'],
                                      spine.sockets['hips'],
                                      lfLegSystem.sockets['poleVectorAim']],
                          targetNames=['root', 'hip', 'foot'],
                          settingsNode=lfLegSystem.pvCtrl,
                          plugType='parent',
                          name='lf_leg_poleVectorCtrl')
p.setParent(lfLegSystem.plugs_grp)

# left arm
lfArmSystem = drArm.DrArm(name='lf_wing',
                               joints=[pmc.PyNode('lf_shldr_GD'),
                                       pmc.PyNode('lf_elbow_GD'),
                                       pmc.PyNode('lf_wrist_GD'),
                                       pmc.PyNode('lf_wrist_end_GD')],
                               numTwistSegs=6,
                               leg=0,
                               flipTwist=1,
                               colour='blue')
# connect to body
p = systemUtils.plug(lfArmSystem.fkCtrls_grp, spine.sockets['lf_shldr'], plugType='parent',
                     name='shldr')
p.setParent(lfArmSystem.plugs_grp)

# spaceswitch for ikCtrl
p = systemUtils.multiPlug(lfArmSystem.ikCtrls_grp,
                          targetList=[rigSystem.rootSystem.sockets['03'], spine.sockets['body']],
                          targetNames=['root', 'body'],
                          settingsNode=lfArmSystem.ikCtrl,
                          plugType='parent',
                          name='lf_wing_ikCtrl')
p.setParent(lfArmSystem.plugs_grp)

# spaceswitch for polevector
p = systemUtils.multiPlug(lfArmSystem.pvZero,
                          targetList=[rigSystem.rootSystem.sockets['03'], spine.sockets['body'],
                                      lfArmSystem.sockets['poleVectorAim']],
                          targetNames=['root', 'body', 'arm'],
                          settingsNode=lfArmSystem.pvCtrl,
                          plugType='parent',
                          name='lf_wing_poleVectorCtrl')
p.setParent(lfArmSystem.plugs_grp)

# right arm
rtArmSystem = drArm.DrArm(name='rt_wing',
                               joints=[pmc.PyNode('rt_shldr_GD'),
                                       pmc.PyNode('rt_elbow_GD'),
                                       pmc.PyNode('rt_wrist_GD'),
                                       pmc.PyNode('rt_wrist_end_GD')],
                               numTwistSegs=6,
                               leg=0,
                               flipTwist=0,
                               colour='red')
# connect to body
p = systemUtils.plug(rtArmSystem.fkCtrls_grp, spine.sockets['rt_shldr'], plugType='parent',
                     name='shldr')
p.setParent(rtArmSystem.plugs_grp)

# spaceswitch for ikCtrl
p = systemUtils.multiPlug(rtArmSystem.ikCtrls_grp,
                          targetList=[rigSystem.rootSystem.sockets['03'], spine.sockets['body']],
                          targetNames=['root', 'body'],
                          settingsNode=rtArmSystem.ikCtrl,
                          plugType='parent',
                          name='rt_wing_ikCtrl')
p.setParent(rtArmSystem.plugs_grp)

# spaceswitch for polevector
p = systemUtils.multiPlug(rtArmSystem.pvZero,
                          targetList=[rigSystem.rootSystem.sockets['03'], spine.sockets['body'],
                                      rtArmSystem.sockets['poleVectorAim']],
                          targetNames=['root', 'body', 'arm'],
                          settingsNode=rtArmSystem.pvCtrl,
                          plugType='parent',
                          name='rt_wing_poleVectorCtrl')
p.setParent(rtArmSystem.plugs_grp)

# right foot
rtFootSystem = drHoof.DrHoof(name='rt_foot',
                                                ankle=pmc.PyNode('rt_ankle_GD'),
                                                toe=pmc.PyNode('rt_toe_GD'),
                                                heel=pmc.PyNode('rt_heel_GD'),
                                                inner=pmc.PyNode('rt_inner_GD'),
                                                outer=pmc.PyNode('rt_outer_GD'),
                                                settingsNode=rtLegSystem.ikCtrl,
                                                blendAttr=rtLegSystem.settingsCtrl.ik_fk_blend)

# connect to body
p = systemUtils.plug(rtFootSystem.ikConstGrp, rtLegSystem.sockets['ikCtrl'], name='rt_ikFoot')
p.setParent(rtFootSystem.plugs_grp)
p = systemUtils.plug(rtFootSystem.fkConstGrp, rtLegSystem.sockets['fkCtrl'], name='rt_fkFoot')
p.setParent(rtFootSystem.plugs_grp)

# attach ik leg to foot
p = systemUtils.plug(rtLegSystem.ctrl_loc, rtFootSystem.sockets['ankle'], name='rt_leg_ikFoot')
p.setParent(rtLegSystem.plugs_grp)

# left foot
lfFootSystem = drHoof.DrHoof(name='lf_foot',
                                                ankle=pmc.PyNode('lf_ankle_GD'),
                                                toe=pmc.PyNode('lf_toe_GD'),
                                                heel=pmc.PyNode('lf_heel_GD'),
                                                inner=pmc.PyNode('lf_inner_GD'),
                                                outer=pmc.PyNode('lf_outer_GD'),
                                                settingsNode=lfLegSystem.ikCtrl,
                                                blendAttr=lfLegSystem.settingsCtrl.ik_fk_blend)

# connect to body
p = systemUtils.plug(lfFootSystem.ikConstGrp, lfLegSystem.sockets['ikCtrl'], name='lf_ikFoot')
p.setParent(lfFootSystem.plugs_grp)
p = systemUtils.plug(lfFootSystem.fkConstGrp, lfLegSystem.sockets['fkCtrl'], name='lf_fkFoot')
p.setParent(lfFootSystem.plugs_grp)

# attach ik leg to foot
p = systemUtils.plug(lfLegSystem.ctrl_loc, lfFootSystem.sockets['ankle'], name='lf_leg_ikFoot')
p.setParent(lfLegSystem.plugs_grp)

# Parent to rig_grp and connect globalscales of all systems
for system in [spine,
               rtArmSystem,
               lfArmSystem,
               rtLegSystem,
               lfLegSystem,
               rtFootSystem,
               lfFootSystem]:
    system.main_grp.setParent(rigSystem.rig_grp)
    rigSystem.rootSystem.main_grp.globalScale.connect(system.main_grp.globalScale)

################################################################################################################
# Publish joints
publishJoints(rigSystem, [spine,
                               rtArmSystem,
                               lfArmSystem,
                               rtLegSystem,
                               lfLegSystem,
                               rtFootSystem,
                               lfFootSystem])
'''

