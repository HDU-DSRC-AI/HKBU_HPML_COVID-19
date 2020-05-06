import numpy as np
from skimage import morphology
from skimage import measure
from sklearn.cluster import KMeans
from skimage.transform import resize
from glob import glob
import sys
import os
from scipy.ndimage.morphology import binary_dilation,generate_binary_structure
from skimage.morphology import convex_hull_image




def process_mask(mask):
    convex_mask = np.copy(mask)
    for i_layer in range(convex_mask.shape[0]):
        mask1  = np.ascontiguousarray(mask[i_layer])
        if np.sum(mask1)>0:
            mask2 = convex_hull_image(mask1)
            if np.sum(mask2)>2*np.sum(mask1):
                mask2 = mask1
        else:
            mask2 = mask1
        convex_mask[i_layer] = mask2
    struct = generate_binary_structure(3,1)
    dilatedMask = binary_dilation(convex_mask,structure=struct,iterations=10)
    return dilatedMask

def lumTrans(img):
    lungwin = np.array([-1200.,600.])
    newimg = (img-lungwin[0])/(lungwin[1]-lungwin[0])
    newimg[newimg<0]=0
    newimg[newimg>1]=1
    newimg = (newimg*255).astype('uint8')
    return newimg





def lungSeg(imgs_to_process,output,name):

    if os.path.exists(output+'/'+name+'_clean.npy') : return

    imgs_to_process = lumTrans(imgs_to_process)    
    x,y,z = imgs_to_process.shape 
    #if y!=512 : continue
  
    img_array = imgs_to_process.copy()  
    A1 = int(y/(512./100))
    A2 = int(y/(512./400))

    A3 = int(y/(512./475))
    A4 = int(y/(512./40))
    A5 = int(y/(512./470))
    #print "on image", img_file
    for i in range(len(imgs_to_process)):
        img = imgs_to_process[i]
	x,y = img.shape
        #Standardize the pixel values
        mean = np.mean(img)
        std = np.std(img)
        img = img-mean
        img = img/std
        # Find the average pixel value near the lungs
        # to renormalize washed out images
        middle = img[A1:A2,A1:A2] 
        mean = np.mean(middle)  
        max = np.max(img)
        min = np.min(img)
        # To improve threshold finding, I'm moving the 
        # underflow and overflow on the pixel spectrum
        img[img==max]=mean
        img[img==min]=mean
        #
        # Using Kmeans to separate foreground (radio-opaque tissue)
        # and background (radio transparent tissue ie lungs)
        # Doing this only on the center of the image to avoid 
        # the non-tissue parts of the image as much as possible
        #
        kmeans = KMeans(n_clusters=2).fit(np.reshape(middle,[np.prod(middle.shape),1]))
        centers = sorted(kmeans.cluster_centers_.flatten())
        threshold = np.mean(centers)
        thresh_img = np.where(img<threshold,1.0,0.0)  # threshold the image
        #
        # I found an initial erosion helful for removing graininess from some of the regions
        # and then large dialation is used to make the lung region 
        # engulf the vessels and incursions into the lung cavity by 
        # radio opaque tissue
        #
        eroded = morphology.erosion(thresh_img,np.ones([4,4]))
        dilation = morphology.dilation(eroded,np.ones([10,10]))
        #
        #  Label each region and obtain the region properties
        #  The background region is removed by removing regions 
        #  with a bbox that is to large in either dimnsion
        #  Also, the lungs are generally far away from the top 
        #  and bottom of the image, so any regions that are too
        #  close to the top and bottom are removed
        #  This does not produce a perfect segmentation of the lungs
        #  from the image, but it is surprisingly good considering its
        #  simplicity. 
        #
        labels = measure.label(dilation)
        label_vals = np.unique(labels)
        regions = measure.regionprops(labels)
        good_labels = []
        for prop in regions:
            B = prop.bbox
            if B[2]-B[0]<A3 and B[3]-B[1]<A3 and B[0]>A4 and B[2]<A5:
                good_labels.append(prop.label)
        mask = np.ndarray([x,y],dtype=np.int8)
        mask[:] = 0
        #
        #  The mask here is the mask for the lungs--not the nodes
        #  After just the lungs are left, we do another large dilation
        #  in order to fill in and out the lung mask 
        #
        for N in good_labels:
            mask = mask + np.where(labels==N,1,0)
        mask = morphology.dilation(mask,np.ones([10,10])) # one last dilation
        imgs_to_process[i] = mask

    m1 = imgs_to_process
    
    convex_mask = m1
    dm1 = process_mask(m1)
    dilatedMask = dm1
    Mask = m1
    extramask = dilatedMask ^ Mask
    bone_thresh = 210
    pad_value = 170

    img_array[np.isnan(img_array)]=-2000
    sliceim = img_array
    sliceim = sliceim*dilatedMask+pad_value*(1-dilatedMask).astype('uint8')
    bones = sliceim*extramask>bone_thresh
    sliceim[bones] = pad_value

    #sliceim = img_array*imgs_to_process

    x,y,z = sliceim.shape
    np.save(os.path.join(output,name+'_clean.npy'),sliceim.reshape(1,x,y,z))
    np.save(os.path.join(output,name+'_label.npy'),np.array([[0,0,0,0]]))


