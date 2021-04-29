import numpy as np
import time
from modules import TIS
from PyQt5 import QtCore
from modules import dbcontroller

class CAMERA_CLASS():
	def __init__(self):
		self.CAM = None
		self.cameraParams = {   'id' : None, 					    # уникальный номер камеры
								'name' : None, 					    # имя камеры
								'online': None,					    # флаг состояния соединения с камерой
								'GUI_logger': None,				    # ссылка на объект логгера
								'log_ui_object': None,
								'update_settings_counter': 0,
								'gain_autoMode': False,
								'gain_level': None,
								'exposure_autoMode': False,
								'exposure_level': None,
								'currentRawFrame': None  } 		    # последняя полученная фотография с устройства

	def setCamId(self, setting_id): 							    # Сеттер для уникального айди номера камеры
		self.cameraParams['id'] = setting_id

	def setIpCamName(self, setting_camName):					    # Сеттер для уникального имени камеры
		self.cameraParams['name'] = setting_camName

	def getDataFromCam(self): 									    # Геттер для извлечения всех переменных камеры
		return self.cameraParams

	def setGUI_logger(self, proxy_link): 						    # Сеттер ссылки на логгер
		self.cameraParams['GUI_logger'] = proxy_link[0]
		self.cameraParams['log_ui_object'] = proxy_link[1]

	def write_log(self, message):								    # Функция передачи сообщения логгеру в другой тред
		self.cameraParams['GUI_logger'].emit([message, self.cameraParams['log_ui_object']])
		#print(message)
	
	def startPipeline(self):									    # Функция запускающая инициализацию камеры (И рестарт)
		self.CAM = TIS.TIS("49910146", 1280, 1024, 30, True)		# cam id was: 49910146 # was 960 720
		self.CAM.Start_pipeline()                                   # Start the pipeline so the camera streams
		self.write_log('Camera Pipeline #{} started!'.format('49910146')) # 49910146

	def read_cam_settings_fromBD(self):
		self.cameraParams['gain_autoMode'] = dbcontroller.read_settings_FromDB(params = {'setting':'GAIN_MODE'})
		self.cameraParams['gain_level'] = dbcontroller.read_settings_FromDB(params = {'setting':'GAIN_LEVEL'})
		self.cameraParams['exposure_autoMode'] = dbcontroller.read_settings_FromDB(params = {'setting':'EXPOSURE_MODE'})
		self.cameraParams['exposure_level'] = dbcontroller.read_settings_FromDB(params = {'setting':'EXPOSURE_LEVEL'})

	def compare_settings_fromCAM(self):
		#==================================
		#self.CAM.Get_Property('None')
		#==================================
		print('DB_gain_autoMode: ', self.cameraParams['gain_autoMode'])
		print('DB_gain_level: ', self.cameraParams['gain_level'])
		print('DB_exposure_autoMode: ', self.cameraParams['exposure_autoMode'])
		print('DB_exposure_level: ', self.cameraParams['exposure_level'])


	def update_cam_settings(self):
		if self.cameraParams['update_settings_counter'] < 30:
			self.cameraParams['update_settings_counter'] += 1
		else:
			self.cameraParams['update_settings_counter'] = 0
			self.read_cam_settings_fromBD()
			try:
				# self.CAM.Set_Property('Gain', float(self.cameraParams['gain_level']))
				# self.CAM.Set_Property('Exposure', int(self.cameraParams['exposure_level']))
				# print(self.cameraParams['gain_level'], self.cameraParams['exposure_level'])
				self.compare_settings_fromCAM()
			except:
				print('CANT CHANGE CAMERA SETTINS!')



	# def stopPipeline(self):									    # Функция дял остановки пайпа камеры - не работает
	# 	self.Tis.Stop_pipeline()								    # и не используется на данный момент :[

	def getFrame(self): # A slot takes no params
		try:
			if self.CAM.Snap_image(1) is True:  				    # Snap an image with one second timeout
				frame = self.CAM.Get_image()  					    # Get the image. It is a numpy array
				self.cameraParams['currentRawFrame'] = frame
				self.cameraParams['online'] = True
				#self.update_cam_settings()
				
				'''
				propertie = self.CAM.Get_Property('Gain Auto')
				print(propertie)
				0 - CameraProperty(status=True, value='Off', min=0, max=0, default='Off', step=0, type='enum', flags=0, category='Exposure', group='Gain')
				1 - CameraProperty(status=True, value='Continuous', min=0, max=0, default='Continuous', step=0, type='enum', flags=0, category='Exposure', group='Gain')
				'''
			else:
				print('error')
				self.cameraParams['online'] = False
				self.write_log('Camera is Offline! Restarting...')
				try:
					print('trying stop pipeline')
					self.stopPipeline()						# Depricated! # @ FIX THIS!
					QtCore.QThread.msleep(1000)
					print('trying delete CAM object')
					del self.CAM
					QtCore.QThread.msleep(1000)
					print('trying restart pipline')
					self.startPipeline()
					#time.sleep(2)
					QtCore.QThread.msleep(1000)
				except:
					print('error 2')							# @ FIX THIS!
		except:
			print('erorr 3')									## @ FIX THIS!
			#time.sleep(2)
			QtCore.QThread.msleep(1000)
			

		
		
		




















		# if self.cap.isOpened():
		# 	ret, frame = self.cap.read() # shape frame: (1280,720)
		# 	self.cameraParams['ret'] = ret
		# 	if ret:
		# 		self.cameraParams['Error'] = None
		# 		if self.cameraParams['indicator'] == False:
		# 			self.cameraParams['indicator'] = True
		# 		else:
		# 			self.cameraParams['indicator'] = False
		# 		self.cameraParams['currentFrame'] = frame
		# 	else:
		# 		frame = None
		# 		self.cap.release()
		# 		self.cameraParams['Error'] = 'Error.failRet'
		# 		# GUI_logger 📢
		# 		self.updateGUI_logger('Ошибка получения кадра с IP-камеры. Закрываю стрим..', time=False, currentTime=None, spacer=False)
		# 		self.cameraParams['currentFrame'] = frame
		# else:
		# 	# GUI_logger 📢
		# 	self.updateGUI_logger('Стрим закрыт. Перезапуск..', time=False, currentTime=None, spacer=False)
		# 	self.cap.open(self.cameraParams['camUrl'])
		# 	self.cameraParams['Error'] = 'Error.failCapOpen'
		# 	frame = None
		# 	self.cameraParams['currentFrame'] = frame
