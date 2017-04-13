import sys
import maya.OpenMaya as om
import maya.OpenMayaMPx as omMPx
import math

nodeName = 'RippleDeformer'
nodeID = om.MTypeId(0x102fff)

class Ripple(omMPx.MPxDeformerNode):
    mObj_Amplitude = om.MObject()
    mObj_Displace = om.MObject()
    def __init__(self):
        omMPx.MPxDeformerNode.__init__(self)

    def deform(self, dataBlock, geoIterator, matrix, geometryIndex):

        input = omMPx.cvar.MPxGeometryFilter_input

        # Attach handle to input array attribute
        dataHandleInputArray = dataBlock.inputArrayValue(input)
        #
        dataHandleInputArray.jumpToElement(geometryIndex)
        #
        dataHandleInputElement = dataHandleInputArray.inputValue()
        # attach to the child - inputGeom
        inputGeom = omMPx.cvar.MPxGeometryFilter_inputGeom
        dataHandleInputGeom = dataHandleInputElement.child(inputGeom)
        inMesh = dataHandleInputGeom.asMesh()

        envelope = omMPx.cvar.MPxGeometryFilter_envelope
        dataHandleEnvelope = dataBlock.inputValue(envelope)
        envelopeValue = dataHandleEnvelope.asFloat()

        dataHandleAmplitude = dataBlock.inputValue(Ripple.mObj_Amplitude)
        amplitudeValue = dataHandleAmplitude.asFloat()

        dataHandleDisplace = dataBlock.inputValue(Ripple.mObj_Displace)
        displaceValue = dataHandleDisplace.asFloat()

        # normals
        mFloatVectorArray_normal = om.MFloatVectorArray()
        mFnMesh = om.MFnMesh(inMesh)
        mFnMesh.getVertexNormals(False, mFloatVectorArray_normal, om.MSpace.kObject)

        while(not geoIterator.isDone()):
            pointPosition = geoIterator.position()
            pointPosition.x = pointPosition.x + math.sin(geoIterator.index() + displaceValue) * amplitudeValue * mFloatVectorArray_normal[geoIterator.index()].x * envelopeValue
            pointPosition.y = pointPosition.y + math.sin(geoIterator.index() + displaceValue) * amplitudeValue * mFloatVectorArray_normal[geoIterator.index()].y * envelopeValue
            pointPosition.z = pointPosition.z + math.sin(geoIterator.index() + displaceValue) * amplitudeValue * mFloatVectorArray_normal[geoIterator.index()].z * envelopeValue

            geoIterator.setPosition(pointPosition)

            geoIterator.next()


def deformerCreator():
    nodePtr = omMPx.asMPxPtr(Ripple())
    return nodePtr

def nodeInitializer():
    '''
    create attributes
    attach attributes to node
    design circuitry
    '''
    mFnAttr = om.MFnNumericAttribute()
    Ripple.mObj_Amplitude = mFnAttr.create('AmplitudeValue', 'AmpVal', om.MFnNumericData.kFloat, 0.0)
    mFnAttr.setKeyable(1)
    mFnAttr.setMin(0.0)
    mFnAttr.setMax(1.0)

    Ripple.mObj_Displace = mFnAttr.create('DisplaceValue', 'DispVal', om.MFnNumericData.kFloat, 0.0)
    mFnAttr.setKeyable(1)
    mFnAttr.setMin(0.0)
    mFnAttr.setMax(10.0)

    Ripple.addAttribute(Ripple.mObj_Amplitude)
    Ripple.addAttribute(Ripple.mObj_Displace)

    outputGeom = omMPx.cvar.MPxGeometryFilter_outputGeom
    Ripple.attributeAffects(Ripple.mObj_Amplitude, outputGeom)
    Ripple.attributeAffects(Ripple.mObj_Displace, outputGeom)

def initializePlugin(mobject):
    mplugin = omMPx.MFnPlugin(mobject, 'Duncan Rudd', '1.0')
    try:
        mplugin.registerNode(nodeName, nodeID, deformerCreator, nodeInitializer, omMPx.MPxNode.kDeformerNode)
    except:
        sys.stderr.write('Failed to register node: %s' % nodeName)
        raise

def uninitializePlugin(mobject):
    mplugin = omMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(nodeID)
    except:
        sys.stderr.write('Failed to deregister node: %s' % nodeName)
        raise