import pymel.core as pmc
import drTools.core.coreUtils as coreUtils
import drTools.systems.controls as controls

def addCtrlsToLattice(lattice, name=''):
    '''
    Creates a control at each lattice point, creates a constrained joint for each ctrl, skins lattice to joints
    '''
    main_grp = pmc.group(empty=1, name='%s_GRP' % name)
    ctrlsGrp = coreUtils.addChild(main_grp, 'group', name='%s_ctrls_GRP' % name)
    rigGrp = coreUtils.addChild(main_grp, 'group', name='%s_rig_GRP' % name)

    divs = lattice.getDivisions()
    points = []
    for x in range(divs[0]):
        for y in range(divs[1]):
            for z in range(divs[2]):
                points.append(lattice.pt[x][y][z])

    positions = [pmc.pointPosition(p, w=1) for p in points]

    ctrlSize = ((lattice.sx.get() + lattice.sy.get() + lattice.sz.get()) / 3.0) * .25

    joints = []

    for i in range(len(points)):
        num = str(i+1).zfill(2)
        p = points[i]

        c = controls.crossCtrl(name='%s_%s_CTRL' % (name, num), size=ctrlSize)
        c.setParent(ctrlsGrp)
        c.t.set(positions[i])
        coreUtils.addParent(c, 'group', '%s_%sCtrl_ZERO' % (name, num))

        j = coreUtils.createAlignedNode(c, 'joint', '%s_%s_BND' % (name, num))
        j.setParent(rigGrp)
        coreUtils.addParent(j, 'group', '%s_%sCtrl_ZERO' % (name, num))
        joints.append(j)

        c.t.connect(j.t)

    rigGrp.visibility.set(0)

    pmc.skinCluster(joints, lattice, mi=1)

