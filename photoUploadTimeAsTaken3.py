# -*- coding: utf-8 -*-
import piexif
import sys, os
import glob
import time
import shutil
import cv2
import subprocess

REMOVE_PNG = False

taglist = []
for ifd in ("0th", "Exif", "GPS", "1st"):
    for t in piexif.TAGS[ifd]:
        if piexif.TAGS[ifd][t]["name"].find('DateTime') != -1:
            print(t, 'as', ifd, piexif.TAGS[ifd][t]["name"])
            taglist.append((ifd, t))

def setMTime(imgname, dstring):
    dd = dstring.split(' ')
    tt = dd[1].split(':')
    dd = dd[0].split(':')
    mtstring = "%s%s%s%s%s.%s" % (dd[0], dd[1], dd[2], tt[0], tt[1], tt[2])
    subprocess.call(['touch', '-mt', mtstring, imgname])


def doOne(imgname):
    print(imgname)
    originname = imgname
    iname = os.path.split(imgname)[1]
    if iname.startswith('IMG') or iname.startswith('Screenshot'):
        sp = iname.split('_')
        year = sp[1][:4]
        month = sp[1][4:6]
        day = sp[1][6:8]
        hh = sp[2][:2]
        mm = sp[2][2:4]
        ss = sp[2][4:6]
        dstring = '%s:%s:%s %s:%s:%s' % (year, month, day, hh, mm, ss)
    else:
        ts = int(os.path.splitext(iname)[0]) >> 32
        dstring = time.strftime("%Y:%m:%d %H:%M:%S", time.localtime(ts))

    exifsucc = False
    if imgname.endswith('.mp4') or imgname.endswith('.MP4') or imgname.endswith('.mov') or imgname.endswith('.MOV'):
        # it is a video
        exifsucc = False
    else:
        try:
            exif_dict = piexif.load(imgname)
            exifsucc = True
        except:
            print('not a video but fail loading exif, try converting to jpg')
            img = cv2.imread(imgname)
            if img is None:
                print('fail to convert')
                exifsucc = False
            else:
                nname = os.path.splitext(imgname)[0] + '.jpg'
                cv2.imwrite(nname, img)
                imgname = nname
                try:
                    exif_dict = piexif.load(imgname)
                    exifsucc = True
                except:
                    exifsucc = False
    if not exifsucc:
        print('finally exif load fail, maybe a video or unsupported image type, set MTime instead')
        setMTime(originname, dstring)
        return
    dflag = False
    for ifd in ("0th", "Exif", "GPS", "1st"):
        for tag in exif_dict[ifd]:
            # print piexif.TAGS[ifd][tag]["name"], exif_dict[ifd][tag]
            dname = piexif.TAGS[ifd][tag]["name"]
            if dname.find('DateTime') != -1:
                dflag = True
                dtime = exif_dict[ifd][tag]

    if dflag:
        print('find datetime', dtime)
        if len(dtime) != 19:
            print('dtime not right')
            dflag = False
    if dflag:
        pass
    else:
        print('##################set datetime to', dstring)
        for t in taglist:
            exif_dict[t[0]][t[1]] = dstring
        # imgname1 = imgname + '.e.jpg'
        # shutil.copyfile(imgname, imgname1)
        imgname1 = imgname
        try:
            piexif.insert(piexif.dump(exif_dict), imgname1)
            if REMOVE_PNG and (originname.endswith('.png') or originname.endswith('.PNG')):
                print("@@@@@@@@@@@@@@@@@@@ removing original png")
                os.remove(originname)
        except:
            print('A bad case, can not set, set mtime instead !!!!!!!!!!!!!!')
            setMTime(originname, dstring)


if __name__ == '__main__':
    imgdir = sys.argv[1]
    imglist = glob.glob(imgdir + '/*.jpg') + glob.glob(imgdir + '/*.JPG') + glob.glob(imgdir + '/*.png') + glob.glob(
        imgdir + '/*.PNG') + glob.glob(imgdir + '/*.mp4') + glob.glob(imgdir + '/*.MP4') + glob.glob(
        imgdir + '/*.mov') + glob.glob(imgdir + '/*.MOV')
    for imgname in imglist:
        doOne(imgname)
