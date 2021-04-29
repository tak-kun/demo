#from __future__ import division
import os
import cv2
import sys
import time
import glob
import io

import itertools as it
import numpy as np

from optparse import OptionParser
from threading import Thread
from modules.common import Timer
from modules.find_obj import init_feature, filter_matches, explore_match

from multiprocessing.pool import ThreadPool

feature_name = 'brisk-flann'                                # инициализация Алгортма поиска ключевых точек
detector, matcher = init_feature(feature_name)              # инициализация детектора
pool=ThreadPool(processes = cv2.getNumberOfCPUs())          # Инициализация пула ядер процессора

def affine_skew(tilt, phi, img, mask=None):                 # Функция Афинных преобразований
    '''
    Ai - is an affine transform matrix from skew_img to img
    '''
    h, w = img.shape[:2]
    if mask is None:
        mask = np.zeros((h, w), np.uint8)
        mask[:] = 255
    A = np.float32([[1, 0, 0], [0, 1, 0]])
    if phi != 0.0:
        phi = np.deg2rad(phi)
        s, c = np.sin(phi), np.cos(phi)
        A = np.float32([[c,-s], [ s, c]])
        corners = [[0, 0], [w, 0], [w, h], [0, h]]
        tcorners = np.int32( np.dot(corners, A.T) )
        x, y, w, h = cv2.boundingRect(tcorners.reshape(1,-1,2))
        A = np.hstack([A, [[-x], [-y]]])
        img = cv2.warpAffine(img, A, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    if tilt != 1.0:
        s = 0.8*np.sqrt(tilt*tilt-1)
        img = cv2.GaussianBlur(img, (0, 0), sigmaX=s, sigmaY=0.01)
        img = cv2.resize(img, (0, 0), fx=1.0/tilt, fy=1.0, interpolation=cv2.INTER_NEAREST)
        A[0] /= tilt
    if phi != 0.0 or tilt != 1.0:
        h, w = img.shape[:2]
        mask = cv2.warpAffine(mask, A, (w, h), flags=cv2.INTER_NEAREST)
    Ai = cv2.invertAffineTransform(A)
    return img, mask, Ai


def affine_detect(detector, img, mask=None, pool=None):     # Детектирование Афинных смещений
    '''
    affine_detect(detector, img, mask=None, pool=None) -> keypoints, descrs
    '''
    params = [(1.0, 0.0)]
    for t in 2**(0.5*np.arange(1,6)):
        for phi in np.arange(0, 180, 72.0 / t):
            params.append((t, phi))

    def f(p):
        t, phi = p
        timg, tmask, Ai = affine_skew(t, phi, img)
        keypoints, descrs = detector.detectAndCompute(timg, tmask)
        for kp in keypoints:
            x, y = kp.pt
            kp.pt = tuple( np.dot(Ai, (x, y, 1)) )
        if descrs is None:
            descrs = []
        return keypoints, descrs

    keypoints, descrs = [], []
    if pool is None:
        ires = it.imap(f, params)
    else:
        ires = pool.imap(f, params)

    for i, (k, d) in enumerate(ires):
        #print('affine sampling: %d / %d\r' % (i+1, len(params)), end='')
        keypoints.extend(k)
        descrs.extend(d)

    return keypoints, np.array(descrs)

def start(review_img, template_img):
    img2 = review_img
    img1 = template_img
    feature_name = 'brisk-flann'
    #detector, matcher = init_feature(feature_name)
    #print('using', feature_name)

    if img1 is not None and img2 is not None:

        kp1, desc1 = affine_detect(detector, img1, pool=pool)
        kp2, desc2 = affine_detect(detector, img2, pool=pool)
        #print('img1 - %d features, img2 - %d features' % (len(kp1), len(kp2)))

        def match_and_draw(win):
            global answer_asift, res
            with Timer('matching'):
                raw_matches = matcher.knnMatch(desc1, trainDescriptors = desc2, k = 2) #2
            p1, p2, kp_pairs = filter_matches(kp1, kp2, raw_matches)
            if len(p1) >= 4:
                H, status = cv2.findHomography(p1, p2, cv2.RANSAC, 5.0)
                #print('%d / %d  inliers/matched' % (np.sum(status), len(status)))
                kp_pairs = [kpp for kpp, flag in zip(kp_pairs, status) if flag]
                if (np.sum(status)) >= 51:
                    answer_asift = True
                else:   
                    answer_asift = False
                points = (np.sum(status))
                #----------------------------------------------- ALL IS FINE! |
                res = [answer_asift, points, len(status), kp_pairs]
                #-------------------------------------------------------------|
            else:
                H, status = None, None
                #print('%d matches found, not enough for homography estimation' % len(p1))
                answer_asift = False
                res = answer_asift
            vis = explore_match(win, img1, img2, kp_pairs, None, H)
            res.append(vis)

        
        match_and_draw('affine find_obj')
        return res
    else:
        #print('assift error')
        #print(img1)
        return ['Ошибка: Шаблон изображения отсутствует!', 0, 0, None]

        # СТРУКТУРА ОТВЕТА ОТ АЛГОРИТМА:
        # [ANSWER ASIFT]; [POINTS]; [KP_PAIRS]; [VIS IMAGE];

