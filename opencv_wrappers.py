"""decorators around OpenCV functions to make them more pythonic and
automatically allocate resources functions need"""

import cv
import decorators
from decorators import chain, split, merge

def show(**images):
    for name, im in images.iteritems():
        cv.NamedWindow(name)
        cv.ShowImage(name, im)

    cv.WaitKey(0)
    for name in images.keys():
        cv.DestroyWindow(name)

def show_stream(name, wait=10):
    cv.NamedWindow(name)

    while True:
        image = yield

        if image: #TODO: check for StopIteration
            cv.ShowImage(name, image)
            cv.WaitKey(wait)
        else:
            cv.WaitKey(0)
            cv.DestroyWindow(name)
            yield StopIteration

@decorators.make_filter
def gauss(im, size=(11,11), method=cv.CV_GAUSSIAN, out=None):
    assert (size[0] % 2 == 1) and (size[1] % 2 == 1)

    if not out: out = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, im.channels)

    assert cv.GetSize(im) == cv.GetSize(out)
    assert im.depth == out.depth
    assert im.channels == out.channels
    cv.Smooth(im, out, method, size[0],size[1])

    return out

@decorators.make_filter
def scale(im, scale=2, imfilter=cv.CV_GAUSSIAN_5x5, out=None):
    assert im.width%scale == 0 and im.height%scale == 0
    
    if not out: out = cv.CreateImage((im.width/scale, im.height/scale), im.depth, im.channels)

    cv.PyrDown(im, out)

    return out

@decorators.make_filter
def doCanny_3(im, low, high, aperture, out=None):
    in1 = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)
    in2 = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)
    in3 = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)

    cv.Split(im, in1, in2, in3, None)

    out1 = canny(in1, low, high, aperture)
    out2 = canny(in2, low, high, aperture)
    out3 = canny(in3, low, high, aperture)

    if not out: out = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 3)
    cv.Merge(out1, out2, out3, None, out)

    return out

@decorators.make_filter
def canny(im, low, high, aperture):
    assert im.channels == 1

    out = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)

    cv.Canny(im, out, low, high, aperture)
    return out

def find_contours(image):
    assert image.channels == 1
    storage = cv.CreateMemStorage(0)
    seq = cv.FindContours(image, storage)
    return seq

erode = decorators.make_resources(cv.Erode)
dilate = decorators.make_resources(cv.Dilate)
morph = decorators.make_resources(cv.MorphologyEx)
threshold = decorators.make_resources(cv.Threshold)
adaptive_threshold = decorators.make_resources(cv.AdaptiveThreshold) #TODO: appley to all channels?
#TODO: do this for much more of course!

############# TESTS #############
def test1(image, show=False):
    gaussed = decorators.chain(image, gauss())
    if show: show(gaussed=gaussed, orig=image)

def test2(image, do_show=False):
    pipe2 = decorators.pipe(gauss(), scale())
    #print "pipe2 created"
    pipe2.next()
    #print "Initialized"
    out2 = pipe2.send(image)
    #print "Called, showing output:"
    if do_show: show(out2=out2)

def test3(image, do_show=False):
    cannied = decorators.apply_to_channels(image, (gauss(), scale(), canny(0,255,3)))
    if do_show: show(cannied=cannied)

def test_show_stream(image, name="Stream"):
    ss = show_stream(name)
    ss.next()
    ss.send(image)
    import time
    time.sleep(2)
    ss.send(None)

def test_erode(image, do_show=False):
    element = cv.CreateStructuringElementEx(3,3,2,2,cv.CV_SHAPE_RECT)
    eroded = erode(image, element)
    if do_show: show(eroded=eroded)

def test_dilate(image, do_show=False):
    element = cv.CreateStructuringElementEx(3,3,2,2,cv.CV_SHAPE_RECT)
    dilated = dilate(image, element)
    if do_show: show(dilated=dilated)

def test_morph(image, do_show=False):
    element = cv.CreateStructuringElementEx(30,30,15,15,cv.CV_SHAPE_RECT)

    temp = cv.CreateImage(cv.GetSize(image), image.depth, image.channels)
    morphed = morph(image, temp, element, cv.CV_MOP_OPEN)
    if do_show: show(morphed=morphed)

def test_thres(image, do_show=False):
    thresholded = threshold(image, 100, 255, cv.CV_THRESH_BINARY_INV)
    if do_show: show(thresholded=thresholded)

def test_adaptivethres(image, do_show=False):
    thresholded = adaptive_threshold(image, 255, cv.CV_ADAPTIVE_THRESH_MEAN_C, cv.CV_THRESH_BINARY, 3, 5)
    if do_show: show(thresholded=thresholded)

def test_contours(image, do_show=False):
    copy = cv.CloneImage(image)
    seq = find_contours(copy) #TODO: find all contours, instead of just one

    color = 128
    #show(im=image)
    out = cv.CloneImage(image)
    for i in range(len(seq)-2): #dont get the last one
        p1 = seq[i]
        p2 = seq[i+1]
        if do_show: print (p1,p2)
        cv.Line(out, p1, p2, color, 2)

    #print (seq[-1:][0], seq[0])
    cv.Line(out, seq[-1:][0], seq[0], color, 2)

    if do_show: show(contours=out)
        
    
if __name__ == "__main__":
    station = cv.LoadImage("""images\geilo_25.png""")
    blue, green, red, _ = split(station)

    laser = cv.LoadImage("""images\Object0.bmp""")
    bl, gl, rl, _ = split(laser)

    contours = cv.LoadImage("""images\contour_test.png""")
    cb, cg, cr, _ = split(contours)
    
    #show(blue=b_chan)
    test1(station)
    test2(station)
    test3(station)
    #test_show_stream(station)
    test_erode(station)
    test_dilate(station)
    test_morph(station)    
    test_thres(station)
    test_adaptivethres(blue)
    test_contours(threshold(cb, 100,255, cv.CV_THRESH_BINARY), True) #make a blobbed image first! (or watershed?)
