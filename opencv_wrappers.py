"""decorators around OpenCV functions to make them more pythonic and
automatically allocate resources functions need"""

import cv
import decorators

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
def doCanny(im, low, high, aperture, out=None):
    in1 = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)
    in2 = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)
    in3 = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)

    cv.Split(im, in1, in2, in3, None)

    out1 = doCanny_single(in1, low, high, aperture)
    out2 = doCanny_single(in2, low, high, aperture)
    out3 = doCanny_single(in3, low, high, aperture)

    if not out: out = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 3)
    cv.Merge(out1, out2, out3, None, out)

    return out

@decorators.make_filter
def doCanny_single(im, low, high, aperture):
    assert im.channels == 1

    out = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)

    cv.Canny(im, out, low, high, aperture)
    return out

############# TESTS #############
def test1(image):
    pipe = decorators.chain(gauss(), scale())
    pipe.next()
    out = pipe.send(image)
    #gaussed = decorators.chain(image, gauss())
    show(gaussed=out, orig=image)

def test2(image):
    pipe2 = decorators.pipe(gauss(), scale())
    print "pipe2 created"
    pipe2.next()
    print "Initialized"
    out2 = pipe2.send(image)
    print "Called, showing output:"
    show(out2=out2)

def test3(image):
    canny = decorators.apply_to_channels(image, (gauss(), doCanny_single(0,255,3)))
    show(cannied=canny)

def test_show_stream(image, name="Stream"):
    ss = show_stream(name)
    ss.next()
    ss.send(image)
    import time
    time.sleep(2)
    ss.send(None)

if __name__ == "__main__":
    image = cv.LoadImage("""images\geilo_25.png""")

##    test1(image)
##    test2(image)
##    test3(image)
    test_show_stream(image)
