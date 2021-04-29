from scipy.spatial import distance as dist
from math import fabs, radians, cos, sin
from modules import dbcontroller
from PyQt5 import QtCore
from modules import asift_module
#from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans

#from modules import frcnn_module
#test!
from PyQt5.QtCore import *
from statistics import median
import cv2
import random
import numpy as np
import ast
import sys, traceback
import glob
import pickle
import time


class IMG_PROCESSOR_CLASS(object):

	def __init__(self):
		self.proxyObject_PLC = None
		self.proxyObject_CAM = None
		self.proxyObject_CALIBRATION_BTTN = None
		self.makeCALIBRATION_BTTN = None

		self.dataFromPlc = None
		self.dataFromCam = None
		self.plug = np.zeros((512,512), np.uint8)

		self.GLOBAL_mtx = None
		self.GLOBAL_dist = None
		self.GLOBAL_newcameramtx = None

		self.imgProcessorParams = { 'GUI_logger': None,					# ok
									'log_ui_object': None,				# ok
									'Error_handler': None,

									# INIT STAGE
									'lockFrame': False,					# ok | flag for imageprocessor ready state
									'lockFrame_count': 0,				# ok | count for image lock

									# INFO STAGE
									'status': 'READY',					# ok | state flag for UI
									'currentOperation': "Init",			# ok | state flag for UI
									'currentProgress': 0,				# ok | state progress bar for UI

									# FRAME LOCK STAGE
									'lockedFrameRaw': None,				# ok
									'lockedFrameCropped': None,			# ok
									'lockedFrameRingDrawed': self.plug,	# ok | need refactoring
									'lockedFrameReady_center': None,	

									#FIND CIRCLES STAGE
									'cathcedLugPoints':[],				# ok
									'cathcedLugPoints_session':[],		# ok
									'catchedLugFrame': None,			# ok
									'filteredLugPoints': None,
									'filteredByLugs_centr': None }

#===========================================================================================================================================================================================|
#| INIT FUNCTIONS	|																																					| INIT FUNCTIONS	|
#===========================================================================================================================================================================================|
	def attach_PLC_OBJ(self, name_link): 
		try:
			self.proxyObject_PLC = name_link
			self.write_log('Proxy PLC attached!')
		except:
			print('Error Sync Thread PLC!')

	def attach_CAM_OBJ(self, name_link): 
		try:
			self.proxyObject_CAM = name_link
			self.write_log('Proxy CAMERA attached!')
		except:
			print('Error Sync Thread CAMERA!')

	def attach_CALIBRATION_BTTN(self, name_link): 
		try:
			self.proxyObject_CALIBRATION_BTTN = name_link
		except:
			print('Error Sync CALIBRATION BUTTN')

	def attach_makeCALIBRATION_BTTN(self, name_link): 
		try:
			self.makeCALIBRATION_BTTN = name_link
		except:
			print('Error Sync makeCALIBRATION BUTTN')

	def setGUI_logger(self, proxy_link): 						   					 
		self.imgProcessorParams['GUI_logger'] = proxy_link[0]
		self.imgProcessorParams['log_ui_object'] = proxy_link[1]

	def write_log(self, message):								    				
		self.imgProcessorParams['GUI_logger'].emit([message, self.imgProcessorParams['log_ui_object']])

	def reloadCalibrationParams(self):
		f = open('calibration/store-mtx.pckl', 'rb')
		self.GLOBAL_mtx = pickle.load(f)
		f.close() 
		f = open('calibration/store-dist.pckl', 'rb')
		self.GLOBAL_dist = pickle.load(f)
		f.close()
		f = open('calibration/store-newcameramtx.pckl', 'rb')
		self.GLOBAL_newcameramtx = pickle.load(f)
		f.close()


#===========================================================================================================================================================================================|
#| LOOP FUNCTIONS	|																																					| LOOP FUNCTIONS	|
#===========================================================================================================================================================================================|
	def getDataFrom_other_workers(self):
		self.imgProcessorParams['currentOperation'] = 'getDataFrom_other_workers'
		self.dataFromPlc = self.proxyObject_PLC.getDataFromPlc()
		self.dataFromCam = self.proxyObject_CAM.getDataFromCam()

	def getDataFromIMGProcessor(self): 												# Геттер для извлечения всех переменных камеры
		self.imgProcessorParams['currentOperation'] = 'getDataFromIMGProcessor'	
		return self.imgProcessorParams

	def checkForLockFrame(self):
		self.imgProcessorParams['currentOperation'] = 'checkForLockFrame'
		
		if self.dataFromCam['online'] == True and self.dataFromPlc['online'] == True and self.dataFromPlc['wheelAvailable'] == True:
			self.imgProcessorParams['lockFrame'] = True								# Поднимаем флаг о блокировке кадра от промышленной камеры, далее проверяем счетчик блокировок
			self.imgProcessorParams['status'] = 'LOCKED FRAME..'
			if self.imgProcessorParams['lockFrame_count'] > 1:
				pass
			else:
				self.imgProcessorParams['lockFrame_count'] += 1
				if self.imgProcessorParams['lockFrame_count'] == 1:
					self.imgProcessorParams['currentProgress'] = 10
					self.write_log(' ')
					self.write_log('Поступила команда анализировать изделие, делаем захват кадра..')
					self.imgProcessorParams['cathcedLugPoints_session'] = []
		else: 
			#print("OOOPPSS! WTF!? self.imgProcessorParams['lockFrame_count']: ", self.imgProcessorParams['lockFrame_count'])
			self.imgProcessorParams['lockFrame'] = False
			self.imgProcessorParams['status'] = 'READY'
			self.imgProcessorParams['currentProgress'] = 0
			self.imgProcessorParams['lockFrame_count'] = 0
			self.dataFromPlc['CameraDone'] = False
			#self.imgProcessorParams['verificationSolution'] = False
		return self.imgProcessorParams['lockFrame'], self.imgProcessorParams['lockFrame_count']

#===========================================================================================================================================================================================|
#| CALIBRATION FUNCTION	|																																			| CALIBRATION FUNCTION	|
#===========================================================================================================================================================================================|
	def checkMakeLensCalibration(self):
		makeCALIBRATION_BTTN_state = self.makeCALIBRATION_BTTN.isChecked()
		if makeCALIBRATION_BTTN_state is True:
			self.write_log('Производится корректировка абберации изображения..')

			# termination criteria
			criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
			# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
			objp = np.zeros((6*9,3), np.float32)
			objp[:,:2] = np.mgrid[0:9,0:6].T.reshape(-1,2)
			# Arrays to store object points and image points from all the images.
			objpoints = [] # 3d point in real world space
			imgpoints = [] # 2d points in image plane.
			images = glob.glob('calibration/*.png')
			for fname in images:
				img = cv2.imread(fname)
				gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
				# Find the chess board corners
				ret, corners = cv2.findChessboardCorners(gray, (9,6),None)
				# If found, add object points, image points (after refining them)
				if ret == True:
					objpoints.append(objp)
					corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
					imgpoints.append(corners2)
			ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
			h,  w = img.shape[:2]
			newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))

			f = open('calibration/store-mtx.pckl', 'wb')
			pickle.dump(mtx, f)
			f.close()

			f = open('calibration/store-dist.pckl', 'wb')
			pickle.dump(dist, f)
			f.close()

			f = open('calibration/store-newcameramtx.pckl', 'wb')
			pickle.dump(newcameramtx, f)
			f.close()

			self.reloadCalibrationParams()

			self.imgProcessorParams['currentOperation'] = 'Корректировка абберации завершена!'
			self.write_log('Корректировка успешно завершена!')
			self.makeCALIBRATION_BTTN.setStyleSheet('background-color: rgb(115, 210, 22);')
			self.makeCALIBRATION_BTTN.setText('ГОТОВО')
			time.sleep(1)
			self.makeCALIBRATION_BTTN.setStyleSheet('background-color: rgb(52, 59, 72);')
			self.makeCALIBRATION_BTTN.setChecked(False)

#===========================================================================================================================================================================================|
#| ASIFT FUNCTIONS	|																																					| ASIFT FUNCTIONS	|
#===========================================================================================================================================================================================|	
	def prepare_all_versions_of_image(self):
		try:
			self.imgProcessorParams['currentOperation'] = 'prepare_all_versions_of_image'
			self.imgProcessorParams['currentProgress'] = 30
			self.imgProcessorParams['lockedFrameRaw'] = self.dataFromCam['currentRawFrame'].copy()

			preparing_image = self.imgProcessorParams['lockedFrameRaw'].copy()	# делаем рабочую копию снимка полученного от промышленной камеры

			# CHECK CALIBRATION MODE:
			turnCALLIBRATIONstate = self.proxyObject_CALIBRATION_BTTN.isChecked()
			if turnCALLIBRATIONstate is True:
				preparing_image = cv2.undistort(preparing_image, self.GLOBAL_mtx, self.GLOBAL_dist, None, self.GLOBAL_newcameramtx)

			#preparing_image = cv2.cvtColor(preparing_image, cv2.COLOR_BGR2RGB )	# меняем цветовое пространство на стандартное RGB
			preparing_image_gray = cv2.cvtColor(preparing_image, cv2.COLOR_BGR2GRAY )	# меняем цветовое пространство на черно-белое

			ROI_FRAME_X = dbcontroller.read_settings_FromDB(params = {'setting':'ROI_FRAME_X'}) # read roi frame for first time!
			ROI_FRAME_Y = dbcontroller.read_settings_FromDB(params = {'setting':'ROI_FRAME_Y'})
			ROI_FRAME_SIZE = dbcontroller.read_settings_FromDB(params = {'setting':'ROI_FRAME_SIZE'})

			preparing_image_gray_cropped = preparing_image_gray[ROI_FRAME_Y : ROI_FRAME_SIZE+ROI_FRAME_Y, ROI_FRAME_X : ROI_FRAME_SIZE+ROI_FRAME_X]
			self.imgProcessorParams['lockedFrameCropped'] = preparing_image_gray_cropped.copy()
			#preparing_image_gray_cropped_backup = preparing_image_gray_cropped.copy()

			BLUR = dbcontroller.read_settings_FromDB(params = {'setting':'BLUR_RATE'})

			preparing_image_gray_cropped_blured = cv2.medianBlur(preparing_image_gray_cropped,BLUR)	# ЗДЕСЬ В КАЧЕСТВЕ АРГУМЕНТА ДЛЯ БЛЮРА ДОЛЖНА БЫТЬ ВЕЛИЧИНА ВЗЯТАЯ ИЗ БД! @DEBUG
			self.imgProcessorParams['lockedFrameBlurred'] = preparing_image_gray_cropped_blured.copy()
			self.write_log('Изображение подготовлено для обработки')
			return False	# return Error
		except:
			return True		#return Error
		
#===================================================================================================================================================|
# 																								| Функция поиска габаритных окружностей на изделии	|
#===================================================================================================================================================|
	# def findGroundsOfRingByHough(self, mode):
	# 	self.mode = mode
	# 	inputImage = self.imgProcessorParams['lockedFrameBlurred'].copy()
	# 	# https://www.pyimagesearch.com/2014/07/21/detecting-circles-images-using-opencv-hough-circles/ 
	# 	# => image, method, dp accum resolution, minDist: Minimum distance between the center (x, y) coordinates of detected circles,
	# 	# param1: Gradient value used to handle edge detection in the Yuen et al. method.
	# 	# param2: Accumulator threshold value for the cv2.HOUGH_GRADIENT method. The smaller the threshold is, the more circles will be detected (including false circles).
	# 	# minRadius: Minimum size of the radius (in pixels).
	# 	# maxRadius: Maximum size of the radius (in pixels).
	# 	DP = dbcontroller.read_settings_FromDB(params = {'setting':'DP'})
	# 	MINDIST = dbcontroller.read_settings_FromDB(params = {'setting':'MINDIST'})
	# 	PARAM1 = dbcontroller.read_settings_FromDB(params = {'setting':'PARAM1'})
	# 	PARAM2 = dbcontroller.read_settings_FromDB(params = {'setting':'PARAM2'})
	# 	MINRAD = dbcontroller.read_settings_FromDB(params = {'setting':'MINRAD'})
	# 	MAXRAD = dbcontroller.read_settings_FromDB(params = {'setting':'MAXRAD'})
	# 	DELTAD = dbcontroller.read_settings_FromDB(params = {'setting':'DELTAD'})

	# 	if self.mode == 'IN':
	# 		MINRAD = MINRAD - DELTAD
	# 		MAXRAD = MAXRAD - DELTAD
	# 		print("MIN AND MAX: " + str(MINRAD) + ' ' + str(MAXRAD))

	# 	try:
	# 		foundedCircles = cv2.HoughCircles(inputImage,cv2.HOUGH_GRADIENT,DP,MINDIST,
	# 		param1=PARAM1,
	# 		param2=PARAM2,
	# 		minRadius=MINRAD,
	# 		maxRadius=MAXRAD) 
		
	# 		foundedCircles = np.uint16(np.around(foundedCircles))
	# 		if len(inputImage.shape) == 2:
	# 			height,width = inputImage.shape
	# 		else: 
	# 			height,width,z = inputImage.shape
	# 		#emptyTemplate = np.zeros((height,width), np.uint8)
	# 		if self.mode == 'IN':
	# 			drawImage_color = self.imgProcessorParams['lockedFrameRingDrawed'].copy()
	# 		if self.mode == 'OUT':
	# 			drawImage = self.imgProcessorParams['lockedFrameCropped'].copy()
	# 			drawImage_color = cv2.cvtColor(drawImage, cv2.COLOR_GRAY2RGB )	# меняем цветовое пространство на стандартное RGB если это первый запуск и мод Аут

	# 		if self.mode == 'IN':
	# 			crossColor = (0,0,0)	
	# 			circleColor = (255, 0, 0)
	# 		if self.mode == 'OUT':
	# 			crossColor = (0,140,255)	# Orange crosshair
	# 			circleColor = ((0, 255, 0))

	# 		cv2.circle(drawImage_color,(foundedCircles[0][0][0], foundedCircles[0][0][1]), foundedCircles[0][0][2], circleColor, thickness =2)
	# 		#mask = cv2.bitwise_and(preparing_image_clear, preparing_image_clear, mask=emptyTemplate)
	# 		cv2.line(drawImage_color,( foundedCircles[0][0][0]-20, foundedCircles[0][0][1] ),
	# 			(foundedCircles[0][0][0]+20, foundedCircles[0][0][1]),crossColor,2) # cross in the center of wheel
	# 		cv2.line(drawImage_color,(foundedCircles[0][0][0], foundedCircles[0][0][1]-20),
	# 			(foundedCircles[0][0][0], foundedCircles[0][0][1]+20),crossColor,2) # cross in the center of wheel

	# 		if self.mode == 'IN':
	# 			cv2.putText(drawImage_color, "Diametr I:" + str(foundedCircles[0][0][2]),  
	# 				(foundedCircles[0][0][0]-110, foundedCircles[0][0][1]+55),  
	# 				fontFace=cv2.FONT_HERSHEY_DUPLEX,  
	# 				fontScale=1,  
	# 				color=(255, 255, 255))  
	# 		if self.mode == 'OUT':
	# 			cv2.putText(drawImage_color, "Diametr O:" + str(foundedCircles[0][0][2]),  
	# 				(foundedCircles[0][0][0]-110, foundedCircles[0][0][1]-40),  
	# 				fontFace=cv2.FONT_HERSHEY_DUPLEX,  
	# 				fontScale=1,  
	# 				color=(255, 255, 255))  			
			
	# 		self.imgProcessorParams['lockedFrameRingDrawed'] = drawImage_color
	# 		self.imgProcessorParams['currentOperation'] = 'prepare_all_versions_of_image'
	# 		self.imgProcessorParams['currentProgress'] = 40

	# 		if self.mode == 'IN':
	# 			self.write_log('Внутренний контур изделия обнаружен успешно!')
	# 		if self.mode == 'OUT':
	# 			self.write_log('Внешний контур изделия обнаружен успешно!')

	# 		return False

	# 	except Exception as e:
	# 		self.write_log('Не удалось определить контур изделия!')
	# 		print("Exception in user code:")
	# 		print("-"*60)
	# 		traceback.print_exc(file=sys.stdout)
	# 		print("-"*60)
	# 		#self.write_log(str(e))
	# 		return True

#===================================================================================================================================================|
# 																								| Функция поиска габаритных окружностей на изделии	|
#===================================================================================================================================================|
	def findGroundsOfLugsByHough(self):
		self.imgProcessorParams['cathcedLugPoints'] = []
		self.imgProcessorParams['catchedLugFrame'] = self.imgProcessorParams['lockedFrameBlurred'].copy()
		DP = dbcontroller.read_settings_FromDB(params = {'setting':'DP'})
		MINDIST = dbcontroller.read_settings_FromDB(params = {'setting':'MINDIST'})
		PARAM1 = dbcontroller.read_settings_FromDB(params = {'setting':'PARAM1'})
		PARAM2 = dbcontroller.read_settings_FromDB(params = {'setting':'PARAM2'})
		MINRAD = dbcontroller.read_settings_FromDB(params = {'setting':'MINRAD'})
		MAXRAD = dbcontroller.read_settings_FromDB(params = {'setting':'MAXRAD'})
		DELTAD = dbcontroller.read_settings_FromDB(params = {'setting':'DELTAD'})
		try:
			for i in range(3):
				inputImage = self.imgProcessorParams['catchedLugFrame']
				foundedCircles = cv2.HoughCircles(inputImage,cv2.HOUGH_GRADIENT,DP,MINDIST,	# Поиск окружности
				param1=PARAM1,
				param2=PARAM2,
				minRadius=MINRAD,
				maxRadius=MAXRAD) 
				foundedCircles = np.uint16(np.around(foundedCircles))						# Сохраняем найденную окружность
				self.imgProcessorParams['catchedLugFrame'] = cv2.rectangle(inputImage, (foundedCircles[0][0][0]-MAXRAD, foundedCircles[0][0][1]-MAXRAD), (foundedCircles[0][0][0]+MAXRAD, foundedCircles[0][0][1]+MAXRAD), (255,255,255), -1) 
				self.write_log('Обнаружен контур бобышки №' + str(i+1))
				self.imgProcessorParams['cathcedLugPoints'].append([foundedCircles[0][0][0], foundedCircles[0][0][1], foundedCircles[0][0][2]])


			drawImage = self.imgProcessorParams['lockedFrameCropped'].copy()
			drawImage_color = cv2.cvtColor(drawImage, cv2.COLOR_GRAY2RGB )
			#crossColor = (0,140,255)	# Orange crosshair
			#circleColor = ((0, 255, 0))
			for circle in self.imgProcessorParams['cathcedLugPoints']:
				cv2.putText(drawImage_color, "Diametr:" + str(circle[2]),  
						(circle[0]-100, circle[1]+140),  
						fontFace=cv2.FONT_HERSHEY_DUPLEX,  
						fontScale=1,  
						color=(255, 255, 255))

			self.imgProcessorParams['lockedFrameRingDrawed'] = drawImage_color
			self.imgProcessorParams['currentProgress'] = 40
			for point in self.imgProcessorParams['cathcedLugPoints']:
				self.imgProcessorParams['cathcedLugPoints_session'].append(point)
			return False

		except Exception as e:
			self.write_log('Не удалось определить контур изделия!')
			print("Exception in user code:")
			print("-"*60)
			traceback.print_exc(file=sys.stdout)
			print("-"*60)
			#self.write_log(str(e))
			return True


	def getMidleErrorWithLugPoints(self):
		nonzero_pred_sub = self.imgProcessorParams['cathcedLugPoints_session']
		num_clusters = 3
		km = KMeans(n_clusters=num_clusters)
		km_fit = km.fit(nonzero_pred_sub)
		crossColor = (0,140,255)
		filtered_points = []

		for point in km_fit.cluster_centers_:
			
			x = int(point[0])
			y = int(point[1])
			z = int(point[2])
			filtered_points.append([x,y,z])

			# Отрисовка границы одной из трех бобышек
			cv2.circle(self.imgProcessorParams['lockedFrameRingDrawed'],(x, y), z, (0,255,0), thickness =1)
			# Отрисовка центра одной из трех бобышек
			cv2.line(self.imgProcessorParams['lockedFrameRingDrawed'],( x-20, y ),
							(x+20, y),crossColor,2) # cross in the center of wheel
			cv2.line(self.imgProcessorParams['lockedFrameRingDrawed'],(x, y-20),
							(x, y+20),crossColor,2) # cross in the center of wheel

		# Рассчет центра масс найденных бобышек
		filtered_centr = self.centroid(filtered_points)
		self.imgProcessorParams['filteredByLugs_centr'] = filtered_centr
		self.imgProcessorParams['filteredLugPoints'] = filtered_points

		# Отрисовка контура границы изделия
		cv2.circle(self.imgProcessorParams['lockedFrameRingDrawed'],(filtered_centr[0], filtered_centr[1]), 460, (0,255,0), thickness =1)

		# Отрисовка центра масс найденных бобышек в виде черно-белого перекрестия:
		cv2.line(self.imgProcessorParams['lockedFrameRingDrawed'],( filtered_centr[0]-20, filtered_centr[1] ),
							(filtered_centr[0]+20, filtered_centr[1]),(255,255,255),5) # cross in the center of wheel
		cv2.line(self.imgProcessorParams['lockedFrameRingDrawed'],(filtered_centr[0], filtered_centr[1]-20),
							(filtered_centr[0], filtered_centr[1]+20),(255,255,255),5) # cross in the center of wheel

		cv2.line(self.imgProcessorParams['lockedFrameRingDrawed'],( filtered_centr[0]-20, filtered_centr[1] ),
							(filtered_centr[0]+20, filtered_centr[1]),(0,0,0),2) # cross in the center of wheel
		cv2.line(self.imgProcessorParams['lockedFrameRingDrawed'],(filtered_centr[0], filtered_centr[1]-20),
							(filtered_centr[0], filtered_centr[1]+20),(0,0,0),2) # cross in the center of wheel

	# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ РАССЧЕТА ГЕОМЕТРИИ
	def centroid(self, vertexes):
				_x_list = [vertex[0] for vertex in vertexes]
				_y_list = [vertex[1] for vertex in vertexes]
				_len = len(vertexes)
				_x = int(sum(_x_list) / _len)
				_y = int(sum(_y_list) / _len)
				return(_x, _y)


	def calculateAngleByLugs(self):
		# Сортировка самой высокой бобышки как точки рассчета угла
		mostUpLug = min(self.imgProcessorParams['filteredLugPoints'], key=lambda x: (x[1]))

		# Отрисовка центра самой высокой бобышки
		cv2.circle(self.imgProcessorParams['lockedFrameRingDrawed'],(mostUpLug[0], mostUpLug[1]), 50, (0,255,0), thickness =3)

		# Берем размерность изображения с lockedFrameCropped
		x, y = (self.imgProcessorParams['lockedFrameCropped']).shape
		mostUpLug_x = mostUpLug[0]
		mostUpLug_y = mostUpLug[1]

		# (self, asift_checkpoint_source, asift_checkpoint_target, centr_coordinates)
		lugAngle_precision = self.calculate_delta_angle((self.imgProcessorParams['filteredByLugs_centr'][0], 0), (mostUpLug_x, mostUpLug_y),  self.imgProcessorParams['filteredByLugs_centr']) 	
		lugAngle = int(lugAngle_precision)
		distanceBetweenTargetAndCenter = dist.euclidean(self.imgProcessorParams['filteredByLugs_centr'], (mostUpLug_x, mostUpLug_y) )

		radius=int(distanceBetweenTargetAndCenter) # 280
		axes = (radius,radius)
		drawAngle=270;
		startAngle=0;
		endAngle=lugAngle;
		color=(0, 255, 255)

		cv2.ellipse(self.imgProcessorParams['lockedFrameRingDrawed'], self.imgProcessorParams['filteredByLugs_centr'], axes, drawAngle, startAngle, endAngle, color, thickness= 2)
		cv2.putText(self.imgProcessorParams['lockedFrameRingDrawed'], "Angle:" + str(lugAngle),  
						(mostUpLug_x-75, mostUpLug_y-150),  
						fontFace=cv2.FONT_HERSHEY_DUPLEX,  
						fontScale=1,  
						color=(255, 255, 255))

		line_startOffset = radius + 80
		line_endOffset = radius - 200
		cv2.line(self.imgProcessorParams['lockedFrameRingDrawed'],(self.imgProcessorParams['filteredByLugs_centr'][0], self.imgProcessorParams['filteredByLugs_centr'][1]-line_startOffset),
							(self.imgProcessorParams['filteredByLugs_centr'][0], self.imgProcessorParams['filteredByLugs_centr'][1]- line_endOffset),(0, 255, 255),2) # Vertical line in center of wheel

		# DEBUG:
		#cv2.line(self.imgProcessorParams['lockedFrameRingDrawed'],(self.imgProcessorParams['filteredByLugs_centr'][0], self.imgProcessorParams['filteredByLugs_centr'][1]),
		#					(mostUpLug_x, mostUpLug_y),(0,140,255),2) # Vertical line in center of wheel

		# Send results to PLC:
		self.write_log('Угол ориентации изделия: ' + str(lugAngle_precision))
		self.dataFromPlc['shiftXmm'] = float('{:.2f}'.format(lugAngle_precision))
		self.dataFromPlc['CameraDone'] = True
		self.dataFromPlc['shotTrigger'] = True

#===================================================================================================================================================|
# 															| Преобразование кейпоинтов после поиска БЛОБ-объектов на изображении в X-Y координаты	|
#===================================================================================================================================================|
	def translate_blob_keyponts_to_normal(self, list_of_keypoints):
		coordinates = []
		for i, key_point in enumerate(list_of_keypoints):
			translate = key_point.pt
			translate = [int(translate[0]), int(translate[1])]
			coordinates.append(translate) #key_pont.pt
		
		return coordinates

#===================================================================================================================================================|
# 																| Функция фильтрации БЛОБ-объектов => отбор объекта только по центру изображения	|
#===================================================================================================================================================|
	def filtr_coordinates_to_centr_only(self, source_image ,coordinates):
		if len(source_image.shape) == 2:
			shape_x, shape_y = source_image.shape
		else: 
			shape_x, shape_y, z = source_image.shape
		middle_x = int(shape_x/2)
		middle_y = int(shape_y/2)
		list_of_delta = []
		for i, coordinate in enumerate(coordinates):
			delta_x = middle_x - coordinate[0]
			delta_y = middle_y - coordinate[1]
			list_of_delta.append(fabs(delta_x)+fabs(delta_y))
		minimal_delta = list_of_delta.index(min(list_of_delta))
		
		return coordinates[minimal_delta]

#===================================================================================================================================================|
# 																											| Поиск центрального отверстия диска	|
#===================================================================================================================================================|
	def find_centroid(self, source_image):
		detector =cv2.SimpleBlobDetector_create()
		keypoints_blob = detector.detect(source_image)
		if len(keypoints_blob) == 0:
			coordinates = keypoints_blob = None
		else:
			#output_detector = cv2.drawKeypoints(source_image, keypoints_blob, np.array([]), (0,0,255),
															#cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
			coordinates = self.translate_blob_keyponts_to_normal(keypoints_blob)
			coordinates = self.filtr_coordinates_to_centr_only(source_image, coordinates)
		
		return keypoints_blob, coordinates #output_detector

#===================================================================================================================================================|
# 																					| Преобразование кейпоинтов полученных ASIFT в X-Y координаты	|
#===================================================================================================================================================|
	def translate_asift_keyponts_to_normal(self, list_of_keypoints):
		source_coordinates = []
		target_coordinates = []
		for i, pair_key_point in enumerate(list_of_keypoints):
			translate_source = pair_key_point[0].pt
			translate_source = [int(translate_source[0]), int(translate_source[1])]
			translate_target = pair_key_point[1].pt
			translate_target = [int(translate_target[0]), int(translate_target[1])]
			source_coordinates.append(translate_source)
			target_coordinates.append(translate_target)
		
		return source_coordinates, target_coordinates

#===================================================================================================================================================|
# 																	| Расчет угла рассогласования между кейпоинтами шаблона и  целевого изображения	|
#===================================================================================================================================================|
	def calculate_delta_angle(self, asift_checkpoint_source, asift_checkpoint_target, centr_coordinates):
		p0 = asift_checkpoint_source
		p1 = centr_coordinates
		p2 = asift_checkpoint_target
		v0 = np.array(p0) - np.array(p1)
		v1 = np.array(p2) - np.array(p1)
		angle = np.math.atan2(np.linalg.det([v0,v1]),np.dot(v0,v1))
		degrees_angle = float(np.degrees(angle))
		
		return degrees_angle

#===================================================================================================================================================|
# 																									| Функции отрисовки HUD на изображениях дисков	|
#===================================================================================================================================================|
	#1. Отрисовка небольшой окружности в центре диска (изображение шаблона и обозреваемого диска)
	def draw_centroid_circle(self, imgProcessorParams, version):
		if version == 1:
			cv2.circle(imgProcessorParams['output_template_image'],(imgProcessorParams['center_coordinates_template'][0],imgProcessorParams['center_coordinates_template'][1]), 15, (220,220,220), 1)
			cv2.circle(imgProcessorParams['output_target_image'],(imgProcessorParams['center_coordinates_target'][0],imgProcessorParams['center_coordinates_target'][1]), 15, (220,220,220), 1)
			return imgProcessorParams['output_template_image'], imgProcessorParams['output_target_image']
		if version == 2:
			pass

	def draw_cross_inCenterOfWheel(self, imgProcessorParams, version):
		if version == 1:
			cv2.line(imgProcessorParams['rotated_image'],(imgProcessorParams['center_coordinates_target'][0]-20, imgProcessorParams['center_coordinates_target'][1]),
				(imgProcessorParams['center_coordinates_target'][0]+20, imgProcessorParams['center_coordinates_target'][1]),(255,0,0),1) # cross in the center of wheel
			cv2.line(imgProcessorParams['rotated_image'],(imgProcessorParams['center_coordinates_target'][0], imgProcessorParams['center_coordinates_target'][1]-20),
				(imgProcessorParams['center_coordinates_target'][0], imgProcessorParams['center_coordinates_target'][1]+20),(255,0,0),1) # cross in the center of wheel
			return imgProcessorParams['rotated_image']
		if version == 2:
			cv2.line(imgProcessorParams['rotated_image'],(imgProcessorParams['center_coordinates_target'][0]-20, imgProcessorParams['center_coordinates_target'][1]),
				(imgProcessorParams['center_coordinates_target'][0]+20, imgProcessorParams['center_coordinates_target'][1]),(255,0,0),1) # cross in the center of wheel
			cv2.line(imgProcessorParams['rotated_image'],(imgProcessorParams['center_coordinates_target'][0], imgProcessorParams['center_coordinates_target'][1]-20),
				(imgProcessorParams['center_coordinates_target'][0], imgProcessorParams['center_coordinates_target'][1]+20),(255,0,0),1) # cross in the center of wheel
			return imgProcessorParams['rotated_image']

	def draw_cross_inWholeOfWheel(self, imgProcessorParams):
		dimensions = imgProcessorParams['rotated_image'].shape
		if len(dimensions) > 2:
			w, h, z = dimensions
		else:
			w, h = dimensions
		cv2.line(imgProcessorParams['rotated_image'],(imgProcessorParams['center_coordinates_target'][0]-30, imgProcessorParams['center_coordinates_target'][1]),
											(0, imgProcessorParams['center_coordinates_target'][1]),(255,140,0),1)
		cv2.line(imgProcessorParams['rotated_image'],(imgProcessorParams['center_coordinates_target'][0]+30, imgProcessorParams['center_coordinates_target'][1]),
											(w, imgProcessorParams['center_coordinates_target'][1]),(255,140,0),1)
		#-----------------------------------------------------------------------------------------------------------------------------------------------------------
		cv2.line(imgProcessorParams['rotated_image'],(imgProcessorParams['center_coordinates_target'][0], imgProcessorParams['center_coordinates_target'][1]-30),
											(imgProcessorParams['center_coordinates_target'][0], 0),(255,140,0),1)
		cv2.line(imgProcessorParams['rotated_image'],(imgProcessorParams['center_coordinates_target'][0], imgProcessorParams['center_coordinates_target'][1]+30),
											(imgProcessorParams['center_coordinates_target'][0], h),(255,140,0),1)
		return imgProcessorParams['rotated_image']

	def draw_control_zones_circleType(self, polygons_list, img):
		for points_list in polygons_list:
			#print(points_list)
			if len(points_list) == 2:
				cv2.circle(img,(int(points_list[0]), int(points_list[1])), 30, (0,0,255), 2)
		return img


#===================================================================================================================================================|
# 																		| Функция для удобного обеспечения итераций цикла высчитывания дельты угла	|
#===================================================================================================================================================|
	#  Решение таска №1, создание функции для удобного обеспечения итераций цикла высчитывания дельты угла:
	def full_calculateDeltaAngle(self, imgProcessorParams, iterations, template_coordinates, target_coordinates): # Составная функция. Высчитывает угол рассогласования между шаблоном и текущим диском 
		iterations_ = iterations
		template_coordinates_ = template_coordinates
		target_coordinates_ = target_coordinates
		def generate_checkIndexLists(iterations_): # Сгенерируем индекс срезов для выбора случайной контрольной точки из списка уникальных точек Asift
			checkIndexList = []
			for index in range(iterations_):
				check_index = random.randrange(0, len(template_coordinates), 1)
				checkIndexList.append(check_index)
			#print('[Стадия-1] Сгенерированно индексов срезов: ', len(checkIndexList))
			imgProcessorParams['checkIndexList'] = len(checkIndexList)
			
			return checkIndexList # Вывод - список индексов для срезов точек

		def generate_checkpointsList(checkIndexList, template_coordinates_, target_coordinates_): # Выберем контрольную точку шаблона и соответствующую точку цели, сделаем список
			asiftCheckpointTemplateList = []
			asiftCheckpointTargetList = []
			for index in checkIndexList:
				asift_checkpoint_template = template_coordinates_[index]
				asift_checkpoint_target = target_coordinates_[index]
				asiftCheckpointTemplateList.append(asift_checkpoint_template)
				asiftCheckpointTargetList.append(asift_checkpoint_target)
			#print('[Стадия-2] Сгенерированно пар точек: ', len(asiftCheckpointTemplateList), len(asiftCheckpointTargetList))
			
			return asiftCheckpointTemplateList, asiftCheckpointTargetList # Вывод - список рандомных точек для расчетов
		
		def calculateDistanse(asiftCheckpointTemplateList, asiftCheckpointTargetList, center_coordinates_template, center_coordinates_target): # Считаем дистанцию между центром диска и точкой для шаблона и цели
			distanceListTemplate = []
			distanceListTarget = []
			for asift_checkpoint_template in asiftCheckpointTemplateList:
				Distance_control_template = dist.euclidean((center_coordinates_template[0],center_coordinates_template[1]), 
																			(asift_checkpoint_template[0], asift_checkpoint_template[1]))
				distanceListTemplate.append(Distance_control_template)
			for asift_checkpoint_target in asiftCheckpointTargetList:
				Distance_control_target = dist.euclidean((center_coordinates_target[0],center_coordinates_target[1]), 
																			(asift_checkpoint_target[0], asift_checkpoint_target[1]))
				distanceListTarget.append(Distance_control_target)
			#print('[Стадия-3] Дистанции между центром дисков и уникальными точками рассчитаны, сгенерированны списки!')
			
			return distanceListTemplate, distanceListTarget
		
		def calculateDeltaAngle_Finally(asiftCheckpointTemplateList, asiftCheckpointTargetList, center_coordinates_template): # Собираем все в кучу и наконец считаем углы в список
			deltaAngleList = []
			for counter , asift_checkpoint_template in enumerate(asiftCheckpointTemplateList):
				delta_angle = self.calculate_delta_angle(asift_checkpoint_template, asiftCheckpointTargetList[counter], center_coordinates_template)
				deltaAngleList.append(delta_angle)
			#print('[Стадия-4] Сгенерирован список рассогласований углов!')
			
			return deltaAngleList

		checkIndexList = generate_checkIndexLists(iterations_)
		asiftCheckpointTemplateList, asiftCheckpointTargetList = generate_checkpointsList(checkIndexList, template_coordinates_, target_coordinates_)
		distanceListTemplate, distanceListTarget = calculateDistanse(asiftCheckpointTemplateList, asiftCheckpointTargetList, imgProcessorParams['center_coordinates_template'], imgProcessorParams['center_coordinates_target'])
		deltaAngleList = calculateDeltaAngle_Finally(asiftCheckpointTemplateList, asiftCheckpointTargetList, imgProcessorParams['center_coordinates_template'])
		
		return deltaAngleList, imgProcessorParams['checkIndexList'], imgProcessorParams['center_coordinates_template'], imgProcessorParams['center_coordinates_target']
