import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.spine as drSpine
import drTools.systems.systemUtils as systemUtils
import drTools.systems.twistySegment as drTwistySegment
import drTools.systems.head as drHead
import drTools.systems.root as drRoot
import drTools.systems.arm as drArm
import drTools.systems.reverseFoot as drReverseFoot
import drTools.systems.hand as drHand

reload(coreUtils)
reload(systemUtils)
reload(drSpine)
reload(drTwistySegment)
reload(drHead)
reload(drRoot)
reload(drArm)
reload(drReverseFoot)
reload(drHand)


class DrBiped(object):
    '''
    builds a default biped based on the default template maya file (assets/rig_templates/dr_defaultRig_template.ma)
    '''

    def __init__(self):
        super(DrBiped, self).__init__()
        self.build()

    def build(self):
        ################################################################################################################
        # root
        self.rigSystem = drRoot.DrRig()

        ################################################################################################################
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
                                       joints=[pmc.PyNode('rt_clavEnd_GD'),
                                               pmc.PyNode('rt_elbow_GD'),
                                               pmc.PyNode('rt_wrist_GD'),
                                               pmc.PyNode('rt_wrist_end_GD')],
                                       numTwistSegs=6)
        # connect to body
        p = systemUtils.plug(self.rtArmSystem.fkCtrls_grp, self.spineSystem.sockets['rt_shldr'], plugType='parent',
                             name='shldr')
        p.setParent(self.rtArmSystem.plugs_grp)
        p = systemUtils.multiPlug(self.rtArmSystem.fkCtrlsConst_grp,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'], self.spineSystem.sockets['body'],
                                              self.spineSystem.sockets['chest'], self.spineSystem.sockets['rt_shldr']],
                                  targetNames=['root', 'body', 'chest', 'shldr'],
                                  settingsNode=self.rtArmSystem.fkTopCtrl,
                                  plugType='orient',
                                  name='rt_arm_shldr')
        p.setParent(self.rtArmSystem.plugs_grp)

        # spaceswitch for ikCtrl
        p = systemUtils.multiPlug(self.rtArmSystem.ikCtrls_grp,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'], self.spineSystem.sockets['body'],
                                              self.spineSystem.sockets['chest'], self.headSystem.sockets['ctrl'],
                                              self.spineSystem.sockets['rt_hip']],
                                  targetNames=['root', 'body', 'chest', 'head', 'hip'],
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
                                       joints=[pmc.PyNode('lf_clavEnd_GD'),
                                               pmc.PyNode('lf_elbow_GD'),
                                               pmc.PyNode('lf_wrist_GD'),
                                               pmc.PyNode('lf_wrist_end_GD')],
                                       numTwistSegs=6,
                                       flipTwist=1,
                                       colour='blue')
        # connect to body
        p = systemUtils.plug(self.lfArmSystem.fkCtrls_grp, self.spineSystem.sockets['lf_shldr'], plugType='parent',
                             name='shldr')
        p.setParent(self.lfArmSystem.plugs_grp)
        p = systemUtils.multiPlug(self.lfArmSystem.fkCtrlsConst_grp,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'], self.spineSystem.sockets['body'],
                                              self.spineSystem.sockets['chest'], self.spineSystem.sockets['lf_shldr']],
                                  targetNames=['root', 'body', 'chest', 'shldr'],
                                  settingsNode=self.lfArmSystem.fkTopCtrl,
                                  plugType='orient',
                                  name='lf_arm_shldr')
        p.setParent(self.lfArmSystem.plugs_grp)

        # spaceswitch for ikCtrl
        p = systemUtils.multiPlug(self.lfArmSystem.ikCtrls_grp,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'], self.spineSystem.sockets['body'],
                                              self.spineSystem.sockets['chest'], self.headSystem.sockets['ctrl'],
                                              self.spineSystem.sockets['lf_hip']],
                                  targetNames=['root', 'body', 'chest', 'head', 'hip'],
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
                                       numTwistSegs=6,
                                       upAxis='z',
                                       leg=1)
        # connect to body
        p = systemUtils.plug(self.rtLegSystem.fkCtrls_grp, self.spineSystem.sockets['rt_hip'], plugType='parent',
                             name='rt_leg_hip')
        p.setParent(self.rtLegSystem.plugs_grp)

        # spaceswitch for ikCtrl
        p = systemUtils.multiPlug(self.rtLegSystem.ikCtrls_grp,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'],
                                              self.spineSystem.sockets['rt_hip']],
                                  targetNames=['root', 'hip'],
                                  settingsNode=self.rtLegSystem.ikCtrl,
                                  plugType='parent',
                                  name='rt_leg_ikCtrl')
        p.setParent(self.rtLegSystem.plugs_grp)

        # spaceswitch for polevector
        p = systemUtils.multiPlug(self.rtLegSystem.pvZero,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'],
                                              self.spineSystem.sockets['rt_hip'],
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
                                       numTwistSegs=6,
                                       upAxis='z',
                                       leg=1,
                                       flipTwist=1,
                                       colour='blue')
        # connect to body
        p = systemUtils.plug(self.lfLegSystem.fkCtrls_grp, self.spineSystem.sockets['lf_hip'], plugType='parent',
                             name='hip')
        p.setParent(self.lfLegSystem.plugs_grp)

        # spaceswitch for ikCtrl
        p = systemUtils.multiPlug(self.lfLegSystem.ikCtrls_grp,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'],
                                              self.spineSystem.sockets['lf_hip']],
                                  targetNames=['root', 'hip'],
                                  settingsNode=self.lfLegSystem.ikCtrl,
                                  plugType='parent',
                                  name='lf_leg_ikCtrl')
        p.setParent(self.lfLegSystem.plugs_grp)

        # spaceswitch for polevector
        p = systemUtils.multiPlug(self.lfLegSystem.pvZero,
                                  targetList=[self.rigSystem.rootSystem.sockets['03'],
                                              self.spineSystem.sockets['lf_hip'],
                                              self.lfLegSystem.sockets['poleVectorAim']],
                                  targetNames=['root', 'hip', 'foot'],
                                  settingsNode=self.lfLegSystem.pvCtrl,
                                  plugType='parent',
                                  name='lf_leg_poleVectorCtrl')
        p.setParent(self.lfLegSystem.plugs_grp)

        ################################################################################################################
        # right foot
        self.rtFootSystem = drReverseFoot.DrReverseFoot(name='rt_foot',
                                                        ankle=pmc.PyNode('rt_footStart_GD'),
                                                        foot=pmc.PyNode('rt_foot_GD'),
                                                        ball=pmc.PyNode('rt_ball_GD'),
                                                        toe=pmc.PyNode('rt_toe_GD'),
                                                        heel=pmc.PyNode('rt_heel_GD'),
                                                        inner=pmc.PyNode('rt_footInner_GD'),
                                                        outer=pmc.PyNode('rt_footOuter_GD'),
                                                        blendAttr=self.rtLegSystem.settingsCtrl.ik_fk_blend)
        p = systemUtils.plug(self.rtFootSystem.ikCtrls_grp, self.rtLegSystem.sockets['ikCtrl'], name='rt_ikFoot')
        p.setParent(self.rtFootSystem.plugs_grp)
        p = systemUtils.plug(self.rtFootSystem.fkCtrls_grp, self.rtLegSystem.sockets['fkCtrl'], name='rt_fkFoot')
        p.setParent(self.rtFootSystem.plugs_grp)

        self.rtLegSystem.fkCtrls_grp.visibility.connect(self.rtFootSystem.fkCtrls_grp.visibility)
        self.rtLegSystem.ikCtrls_grp.visibility.connect(self.rtFootSystem.ikCtrls_grp.visibility)

        # attach ik leg to foot
        p = systemUtils.plug(self.rtLegSystem.ctrl_loc, self.rtFootSystem.sockets['ikFoot'], name='rt_leg_ikFoot')
        p.setParent(self.rtFootSystem.plugs_grp)

        ################################################################################################################
        # left foot
        self.lfFootSystem = drReverseFoot.DrReverseFoot(name='lf_foot', colour='blue',
                                                        ankle=pmc.PyNode('lf_footStart_GD'),
                                                        foot=pmc.PyNode('lf_foot_GD'),
                                                        ball=pmc.PyNode('lf_ball_GD'),
                                                        toe=pmc.PyNode('lf_toe_GD'),
                                                        heel=pmc.PyNode('lf_heel_GD'),
                                                        inner=pmc.PyNode('lf_footInner_GD'),
                                                        outer=pmc.PyNode('lf_footOuter_GD'),
                                                        blendAttr=self.lfLegSystem.settingsCtrl.ik_fk_blend)
        p = systemUtils.plug(self.lfFootSystem.ikCtrls_grp, self.lfLegSystem.sockets['ikCtrl'], name='lf_ikFoot')
        p.setParent(self.lfFootSystem.plugs_grp)
        p = systemUtils.plug(self.lfFootSystem.fkCtrls_grp, self.lfLegSystem.sockets['fkCtrl'], name='lf_fkFoot')
        p.setParent(self.lfFootSystem.plugs_grp)

        self.lfLegSystem.fkCtrls_grp.visibility.connect(self.lfFootSystem.fkCtrls_grp.visibility)
        self.lfLegSystem.ikCtrls_grp.visibility.connect(self.lfFootSystem.ikCtrls_grp.visibility)

        # attach ik leg to foot
        p = systemUtils.plug(self.lfLegSystem.ctrl_loc, self.lfFootSystem.sockets['ikFoot'], name='lf_leg_ikFoot')
        p.setParent(self.lfFootSystem.plugs_grp)

        ################################################################################################################
        # right hand
        self.rtHandSystem = drHand.DrHand(name='rt_hand', settingsNode=self.rtArmSystem.settingsCtrl,
                                          fingerDict={
                                              'pinky': [pmc.PyNode(j) for j in ['rt_pinky_1_GD',
                                                                                'rt_pinky_2_GD',
                                                                                'rt_pinky_3_GD',
                                                                                'rt_pinky_4_GD',
                                                                                'rt_pinky_5_GD']],
                                              'mid': [pmc.PyNode(j) for j in ['rt_mid_1_GD',
                                                                              'rt_mid_2_GD',
                                                                              'rt_mid_3_GD',
                                                                              'rt_mid_4_GD',
                                                                              'rt_mid_5_GD']],
                                              'index': [pmc.PyNode(j) for j in ['rt_index_1_GD',
                                                                                'rt_index_2_GD',
                                                                                'rt_index_3_GD',
                                                                                'rt_index_4_GD',
                                                                                'rt_index_5_GD']],
                                              'thumb': [pmc.PyNode(j) for j in ['rt_thumb_1_GD',
                                                                                'rt_thumb_2_GD',
                                                                                'rt_thumb_3_GD',
                                                                                'rt_thumb_4_GD']]})
        p = systemUtils.plug(self.rtHandSystem.ctrls_grp, self.rtArmSystem.sockets['wrist'], name='rt_wrist')
        p.setParent(self.rtHandSystem.plugs_grp)

        ################################################################################################################
        # left hand
        self.lfHandSystem = drHand.DrHand(name='lf_hand', colour='blue', settingsNode=self.lfArmSystem.settingsCtrl,
                                          fingerDict={
                                              'pinky': [pmc.PyNode(j) for j in ['lf_pinky_1_GD',
                                                                                'lf_pinky_2_GD',
                                                                                'lf_pinky_3_GD',
                                                                                'lf_pinky_4_GD',
                                                                                'lf_pinky_5_GD']],
                                              'mid': [pmc.PyNode(j) for j in ['lf_mid_1_GD',
                                                                              'lf_mid_2_GD',
                                                                              'lf_mid_3_GD',
                                                                              'lf_mid_4_GD',
                                                                              'lf_mid_5_GD']],
                                              'index': [pmc.PyNode(j) for j in ['lf_index_1_GD',
                                                                                'lf_index_2_GD',
                                                                                'lf_index_3_GD',
                                                                                'lf_index_4_GD',
                                                                                'lf_index_5_GD']],
                                              'thumb': [pmc.PyNode(j) for j in ['lf_thumb_1_GD',
                                                                                'lf_thumb_2_GD',
                                                                                'lf_thumb_3_GD',
                                                                                'lf_thumb_4_GD']]})
        p = systemUtils.plug(self.lfHandSystem.ctrls_grp, self.lfArmSystem.sockets['wrist'], name='lf_wrist')
        p.setParent(self.lfHandSystem.plugs_grp)

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
    '''
    for each system, makes a group under rig.bind_GRP. Makes a copy of each joint in system.joints and constrains it
    to the corresponding system joint.
    '''
    pmc.select(None)
    bindSet = pmc.sets(name='bind_SET')
    for system in systems:
        pmc.select(system.joints)
        set = pmc.sets(name='%s_bind_SET' % system.name)
