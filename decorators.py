"""Library of convienence wrappers for OpenCV-functions and operators."""
import cv

#TODO: have configurable resources. Some ops need several images and/or memStorages. 
def make_resources(op):
    """Preallocate resources image operators need"""
    def allocator(image, *args, **kwargs):
        sameSize = True #TODO: make configable
        depth = image.depth
        channels = image.channels
        out = cv.CreateImage(cv.GetSize(image), depth, channels) #TODO: if kwargs already has an image as value for the key "out", use tis image
        op(image, out, *args, **kwargs)
        return out
    return allocator
            

#TODO: yielder must be able to handle *arg- and **kwarg-less functions
def make_filter(op):
    """"Converts a normal image proccing function into a generator"""
    def wrapper(*args,**kwargs):
        while True:
            image = yield
            yield op(image, *args, **kwargs)

    return wrapper

def chain(start, *gens):
    for gen in gens:
        gen.next()
    temp = start
    for gen in gens:
        temp = gen.send(temp)

    return temp

#does the same as make_filter applied to chain.
def pipe(*parts):
    while True:
        for part in parts:
            part.next()
        temp = yield
        for part in parts:
            #print "Next step: %s"%str(part), temp
            temp = part.send(temp)
        yield temp

def split(image):
    out1 = cv.CreateImage(cv.GetSize(image), cv.IPL_DEPTH_8U, 1)
    out2 = cv.CreateImage(cv.GetSize(image), cv.IPL_DEPTH_8U, 1)
    out3 = cv.CreateImage(cv.GetSize(image), cv.IPL_DEPTH_8U, 1)
    if image.nChannels ==4:
        out4 = cv.CreateImage(cv.GetSize(image), cv.IPL_DEPTH_8U, 1)
    else:
        out4 = None

    cv.Split(image, out1, out2, out3, out4)

    return out1, out2, out3, out4

def merge(*channels):
    debug=False
    assert len(channels) > 0

    firstDepth = channels[0].depth
    assert all([channel.depth == firstDepth for channel in channels])

    firstSize = cv.GetSize(channels[0])
    assert all([cv.GetSize(channel) == firstSize for channel in channels])

    chans = 3 if len(channels) == 2 else len(channels) #For filling up the 3rd chan when there are 2 imgs, add room for this 3rd channel
    if debug: print "merging %i channels"%chans
    out = cv.CreateImage(cv.GetSize(channels[0]), channels[0].depth, chans)
    #print out
    
    if len(channels) == 4:
        cv.Merge(channels[0],channels[1],channels[2],channels[3],out)
    elif len(channels) == 3:
        cv.Merge(channels[0],channels[1],channels[2],None,out)
    elif len(channels) == 2:
        filler = cv.CreateImage(cv.GetSize(channels[0]), channels[0].depth, 1)
        cv.Merge(channels[0],channels[1],filler,None,out) #TODO: make pos of filler configable
    elif len(channels) == 1:
        cv.Merge(channels[0],None,None,None,out)
    return out

def apply_to_channels(image, ops, merge_result=False, out=None, debug=False):
    if debug: print "Splitting image.nChannels=%i"%image.nChannels
    channels = split(image)
    
    if debug: print "Applying operation to %s channels"%str(channels)
    parts = [chain(channel, *ops) for channel in channels if channel]

    if debug: print "Merging operated channels"
    result = merge(*parts)
    if debug: print "Done merging"
##    if not out:
##        return result
##    else:
##        return out
    return result

def test1(image):
    smooth = make_resources(cv.Smooth)
    return smooth(image, cv.CV_GAUSSIAN, 11,11)
    

if __name__ == "__main__":
    image = cv.LoadImage("""images\geilo_25.png""")

    out = test1(image)
    cv.NamedWindow("Show")
    cv.ShowImage("Show", out)
    cv.WaitKey()
    cv.DestroyAllWindows()
