from mxnet import nd,gluon
import mxnet as mx
import numpy as np
import skimage as ski
from numpy.lib import stride_tricks as st
import warnings
from PIL import Image
from numba import jit


def load_img(path):
    x = np.array(Image.open(path).convert('L'))  
    return x

def load_MXNet(homedir,ctx,sUnet3,sUnet5=None):   
    with warnings.catch_warnings():
       warnings.simplefilter("ignore")
       netMask = gluon.nn.SymbolBlock.imports(homedir+"UNetL3_V"+sUnet3+"-symbol.json",['data'],homedir+"UNetL3_V"+sUnet3+"-0000.params",ctx=ctx)
       if sUnet5 is not None:
            netInter = gluon.nn.SymbolBlock.imports(homedir+"UNetL5_V"+sUnet5+"-symbol.json",['data'],homedir+"UNetL5_V"+sUnet5+"-0000.params",ctx=ctx)
       else:
            netInter=None
    return netMask,netInter

def createSubs(img,SizeX,SizeY,CropSize,divNum):
    StartX=0
    EndX=CropSize
    SubsX=list()
    StartCoordsX=list()
    while(EndX<=SizeX):
        SubsX.append(fixed_crop_new(img,StartX,0,CropSize,SizeY))
        StartCoordsX.append(StartX)
        StartX+=int(CropSize/divNum)
        EndX+=int(CropSize/divNum)
    if (EndX<(SizeX+CropSize)):
        StartX=SizeX-CropSize
        if StartX < 0: StartX = 0
        EndX=SizeX
        SubsX.append(fixed_crop_new(img,StartX,0,CropSize,SizeY))
        StartCoordsX.append(StartX)
    Subs=list()
    EndY=CropSize
    StartY=0
    StartCoords=list()  
    if (EndY>=SizeY):
        Subs.extend(SubsX)
        for StX in StartCoordsX:
            StartCoords.append((StX,0))
    else:
        while(EndY<=SizeY):
            iCounterX=0
            for sub in SubsX:
                Subs.append(fixed_crop_new(sub,0,StartY,CropSize,CropSize))
                StartCoords.append((StartCoordsX[iCounterX],StartY))
                iCounterX+=1
            StartY+=int(CropSize/divNum)
            EndY+=int(CropSize/divNum)
        if (EndY<(SizeY+CropSize)):
            StartY=SizeY-CropSize
            if StartY < 0: StartY = 0
            EndY=SizeY
            iCounterX=0
            for sub in SubsX:
                Subs.append(fixed_crop_new(sub,0,StartY,CropSize,CropSize))
                StartCoords.append((StartCoordsX[iCounterX],StartY))
                iCounterX+=1
    return Subs,StartCoords

def fixed_crop_new(src, x0, y0, w, h, size=None, interp=2):
    out = src[y0:y0+h, x0:x0+w]
    if size is not None and (w, h) != size:
        sizes = (h, w, size[1], size[0])
        out = mx.image.imresize(out, *size, interp=mx.image._get_interp_method(interp, sizes))
    return out

def predictionResize(sub,net,SizeX,SizeY,ctx):
    sub=sub.as_in_context(ctx)
    imgPred = net(nd.expand_dims(sub, 0))
    imgPred = nd.softmax(imgPred, axis=1)
    imgPred = nd.argmax(data=imgPred, axis=1)       
    imgPred= nd.transpose(imgPred, axes=(1, 2, 0))
    imgPred=imgPred.as_in_context(mx.cpu(0))
    imgResize=mx.img.imresize(imgPred,SizeX,SizeY)
    imgOut = imgResize.asnumpy() 
    if imgOut.ndim>2:
        imgOut=imgOut[...,0]
    return imgOut

def combineSubs(Subs,SizeX,SizeY,StartCoords,SubSizeX,SubSizeY):
    NewIm=np.zeros((SizeY,SizeX))
    iCounter=0
    for sub in Subs:
        StartY=StartCoords[iCounter][1]
        StartX=StartCoords[iCounter][0]
        NewIm[StartY:StartY+SubSizeY,StartX:StartX+SubSizeX]=np.where(sub>0,1,NewIm[StartY:StartY+SubSizeY,StartX:StartX+SubSizeX])
        iCounter+=1
    return NewIm.astype(np.uint8)

def fillSmallHoles(img, size, Value,connectivity):
    labels = ski.measure.label(img, connectivity=connectivity)
    props = ski.measure.regionprops_table(
        labels, img, properties=['label', 'area'])
    for count, a in zip(props.get('label'), props.get('area')):
        if (a < size):
            img = np.where(labels == count, Value, img)
    return img

def createLabelUNet(img,divNum,netMask,CropSize,fillsize,ctxMask=mx.cpu(0),ctxInter=mx.cpu(0),netInter=None):
    SizeY=len(img)
    SizeX=len(img[0])
    Subs,StartCoords=createSubs(img,SizeX,SizeY,CropSize,divNum)
    IntersectionSubs=list()
    DetectionSubs=list()
    for sub in Subs:
        OrgSizeX=len(sub[0])
        OrgSizeY=len(sub)
        # Convert to NDArray and add channel dimension (H, W) -> (H, W, 1)
        sub_nd = mx.nd.array(sub)
        if sub_nd.ndim == 2:
            sub_nd = nd.expand_dims(sub_nd, axis=2)
            
        if (sub_nd.shape[0] != CropSize) or (sub_nd.shape[1] != CropSize):
            sub_nd = mx.img.imresize(sub_nd, CropSize, CropSize)
            
        # Transpose to Channel First (C, H, W) -> (1, 512, 512)
        sub_nd = nd.transpose(sub_nd, (2, 0, 1))
        
        DetectionSubs.append(predictionResize(sub_nd,netMask,OrgSizeX,OrgSizeY,ctxMask))
        if netInter!=None:
            IntersectionSubs.append(predictionResize(sub_nd,netInter,OrgSizeX,OrgSizeY,ctxInter))
                
    imgMask = combineSubs(DetectionSubs,SizeX,SizeY,StartCoords,OrgSizeX,OrgSizeY)
    if netInter!=None:
        imgIntersec = combineSubs(IntersectionSubs,SizeX,SizeY,StartCoords,OrgSizeX,OrgSizeY)
    else:
        imgIntersec=np.zeros(imgMask.shape)
    imgMask=fillSmallHoles(imgMask,fillsize,1,1)
    return imgMask,imgIntersec

def checkLabelsforMask(labelsSD,imgMask):
    for i in range(1,np.max(labelsSD)+1):
        points=np.argwhere(labelsSD==i)
        if np.count_nonzero(imgMask[points[:,0],points[:,1]])==0:
            labelsSD[points[:,0],points[:,1]]=0

try:
    from numpy.lib.stride_tricks import sliding_window_view as _swv
    def _sliding_window_view(a, win): return _swv(a, win)
except Exception:
    from numpy.lib.stride_tricks import as_strided
    def _sliding_window_view(a, win):
        h, w = a.shape
        wh, ww = win
        out_shape = (h - wh + 1, w - ww + 1, wh, ww)
        out_strides = a.strides + a.strides
        return as_strided(a, shape=out_shape, strides=out_strides, writeable=False)

# @jit(nopython=True)
# def controlled_dilation(labels, LabelsNeighbors, imgMask, imgIntersec):
#     labels_copy = labels.copy()
#     dilated = False
#     for i in range(len(labels)):
#         for j in range(len(labels[0])):
#             if (labels[i, j] > 0) and (np.count_nonzero(LabelsNeighbors[i, j]) < 9):
#                 for e in range(3):
#                     for ee in range(3):
#                         if (i+e-1 >= 0) and (j+ee-1 >= 0) and (i+e-1 < len(labels)) and (j+ee-1 < len(labels[0])):
#                             if (LabelsNeighbors[i, j, e, ee] == 0) and (imgMask[i+e-1, j+ee-1] > 0) and (imgIntersec[i+e-1, j+ee-1] == 0):
#                                 labels_copy[i+e-1, j+ee-1] = labels[i, j]
#                                 dilated = True
#     return labels_copy, dilated
def controlled_dilation(labels, LabelsNeighbors, imgMask, imgIntersec):
     # Pure NumPy/Python version (no numba)
     H, W = labels.shape
     labels_copy = labels.copy()
     dilated = False
     for i in range(H):
         for j in range(W):
             if labels[i, j] > 0 and (np.count_nonzero(LabelsNeighbors[i, j]) < 9):
                 for e in range(3):
                     for ee in range(3):
                         ni, nj = i + e - 1, j + ee - 1
                         if 0 <= ni < H and 0 <= nj < W:
                             if (LabelsNeighbors[i, j, e, ee] == 0) and (imgMask[ni, nj] > 0) and (imgIntersec[ni, nj] == 0):
                                 labels_copy[ni, nj] = labels[i, j]
                                 dilated = True
     return labels_copy, dilated

def dilateToMask(labels,imgMask,imgIntersec):
    # Cast all arrays to int32 for numba compatibility
    # labels = np.ascontiguousarray(labels, dtype=np.int32)
    # imgMask = np.ascontiguousarray(imgMask, dtype=np.int32)
    # imgIntersec = np.ascontiguousarray(imgIntersec, dtype=np.int32)

    # LabelsNeighbors = st.sliding_window_view(np.pad(labels, 1), (3, 3))
    # LabelsNeighbors = np.ascontiguousarray(LabelsNeighbors, dtype=np.int32)

    # Keep original dtypes; just ensure C-contiguous
    labels = np.ascontiguousarray(labels)
    imgMask = np.ascontiguousarray(imgMask)
    imgIntersec = np.ascontiguousarray(imgIntersec)

    LabelsNeighbors = _sliding_window_view(np.pad(labels, 1), (3, 3))

    labels_copy, dilated = controlled_dilation(
        labels, LabelsNeighbors, imgMask, imgIntersec)
    while(dilated):
        # LabelsNeighbors = st.sliding_window_view(
        #     np.pad(labels_copy, 1), (3, 3))
        # LabelsNeighbors = np.ascontiguousarray(LabelsNeighbors, dtype=np.int32)
        LabelsNeighbors = _sliding_window_view(np.pad(labels_copy, 1), (3, 3))
        labels_copy, dilated = controlled_dilation(
            labels_copy, LabelsNeighbors, imgMask, imgIntersec)
    return labels_copy  

def combinedPrediction(X,modelSD,imgMask,imgIntersec):
    labelsSD=modelSD.predict_instances(X)[0]
    checkLabelsforMask(labelsSD,imgMask)
    labels=dilateToMask(labelsSD,imgMask,imgIntersec)
    return labels,labelsSD