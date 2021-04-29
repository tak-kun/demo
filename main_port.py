# -*- coding: utf-8 -*-
#===================================================================================================================================================|
#| Импорт библиотек	| 																											| Импорт библиотек	|
#===================================================================================================================================================|
#===================================================================================================================================================|
#																																| Common libraries	|
#===================================================================================================================================================|
from threading import Thread														# Импорт библиотеки, реализующей мультипоточное программирование
import sys																			# Импорт системной библиотеки Python
import time																			# Импорт библиотеки для работы со временем
import os
import traceback
import numpy as np
import cv2
import logging
import glob
#===================================================================================================================================================|
# 																																| PyQt5 Libraries	|
#===================================================================================================================================================|
from PyQt5 import QtCore, QtGui, QtWidgets											# Далее идет блок импорта модулей библиотеки PyQt5
from PyQt5.QtWidgets import QApplication, QSizeGrip, QWidget, QMainWindow, QPushButton, QToolTip, QMessageBox, QLabel, QTextBrowser, QSplashScreen
from PyQt5.QtWidgets import QProgressBar, QGraphicsDropShadowEffect
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
from PyQt5.QtCore import QObject, pyqtSignal, Qt

#===================================================================================================================================================|
# 																																	  | GUI modules |
#===================================================================================================================================================|
from gui.ui_main import Ui_MainWindow											   # Импорт файл описания интерфейса конвертированный из .UI
from gui.ui_styles import Style													   # Импорт модуля стилей (аналог CSS)
from modules.ui_functions import *											   	   # Импорт модуля с функциями для кастомизации интерфейса окон Pyqt5

#===================================================================================================================================================|
# 																													 | Functional and logic modules |
#===================================================================================================================================================|
from modules import cameracontroller
from modules import plccontroller
from modules import dbcontroller
from modules import imgprocessor

#===================================================================================================================================================|
#| Класс основного окна программы	| 																			| Класс основного окна программы	|
#===================================================================================================================================================|
class MainWindow(QMainWindow):														# Объявление класса
	def __init__(self):																# функция инициализации срабатывающая при объвлении класса
		QMainWindow.__init__(self)													# наследование параметров 
		self.ui = Ui_MainWindow()													# передача переменной интерфейса в "ui"
		self.ui.setupUi(self)
		self.customise_interface_init()												# вызываем функцию для применения кастомизации интерфейса Pyqt5
		self.connect_slots()		
		self.SHARE_OBJECTS = {  'CAM_WORKER': None, 								# Objects proxy
								'PLC_WORKER' : None,
								'IMG_PROCESSOR_WORKER': None,

								'emulate_start_button': self.ui.emulate_start_button,
								'emulate_reset_button': self.ui.emulate_reset_button,
								'plc_watchdog_indicator': self.ui.plc_watchdog_indicator,
								'EMULATE_CONNECTION': self.ui.emulate_plc_connection,

								'label_view_port': self.ui.label_view_port,
								'label_view_settings': self.ui.label_view_settings,
								'label_top_info_CAM': self.ui.label_top_info_CAM,
								'label_top_info_PLC': self.ui.label_top_info_PLC,
								'label_top_info_IMGPROC': self.ui.label_top_info_IMGPROC,
								'label_current_operation': self.ui.label_current_operation,
								'progressBar_proc': self.ui.progressBar_proc,
								'turnROI': self.ui.checkBox_turnROI,
								'turnCALIBRATION': self.ui.checkBox_turnCalibrationFilter,
								'makeLensCALIBRATION': self.ui.make_lens_calibration,

								'save_frame_callibration_btns': [self.ui.save_frame_callibration_1, 
																self.ui.save_frame_callibration_1,
																self.ui.save_frame_callibration_2,
																self.ui.save_frame_callibration_3,
																self.ui.save_frame_callibration_4,
																self.ui.save_frame_callibration_5,
																self.ui.save_frame_callibration_6,
																self.ui.save_frame_callibration_7,
																self.ui.save_frame_callibration_8,
																self.ui.save_frame_callibration_9],
								'testSizeCoefficient': self.ui.check_size_template_calibration,

								'generalUILogBrowser': self.ui.textBrowser_generalLog
								}
		
#===================================================================================================================================================|
#| Threads creation	| 																											| Threads creation	|
#===================================================================================================================================================|
#===================================================================================================================================================|
#																																|  CAMERA THREAD	|
#===================================================================================================================================================|
		self.objThread_CAM = CAM_WORKER()
		self.thread_CAM = QThread()
		self.objThread_CAM.CAM_WORKER_frameSignal.connect(UIFunctions.updateCameraView)	# Need check this func, after that remove comment!
		self.objThread_CAM.CAM_WORKER_loggerSignal.connect(UIFunctions.printToGeneralUILog) # OK!
		self.objThread_CAM.CAM_WORKER_SyncSignal.connect(self.create_PLC_thread)			# OK!
		self.objThread_CAM.moveToThread(self.thread_CAM)
		self.thread_CAM.started.connect(self.objThread_CAM.camera)
		self.thread_CAM.start()

#===================================================================================================================================================|
#																																	|  PLC THREAD	|
#===================================================================================================================================================|
	def create_PLC_thread(self):
		self.objThread_PLC = PLC_WORKER()
		self.thread_PLC = QThread()
		self.objThread_PLC.PLC_WORKER_guiSignal.connect(UIFunctions.updatePLC_UI)			# OK!
		self.objThread_PLC.PLC_WORKER_loggerSignal.connect(UIFunctions.printToGeneralUILog)	# OK!
		self.objThread_PLC.PLC_WORKER_SyncSignal.connect(self.create_IMGPROCESSOR_thread)	# OK!
		self.objThread_PLC.moveToThread(self.thread_PLC)
		self.thread_PLC.started.connect(self.objThread_PLC.plc)
		self.thread_PLC.start()

#===================================================================================================================================================|
#																															|  IMGPROCESSOR THREAD	|
#===================================================================================================================================================|
	def create_IMGPROCESSOR_thread(self):
		self.objThread_IMGPROCESSOR = IMGPROCESSOR_WORKER()
		self.thread_IMGPROCESSOR = QThread()
		self.objThread_IMGPROCESSOR.IMGPROCESSOR_WORKER_guiSignal.connect(UIFunctions.updateImgProc_UI)
		self.objThread_IMGPROCESSOR.IMGPROCESSOR_WORKER_loggerSignal.connect(UIFunctions.printToGeneralUILog)
		#self.objThread_IMGPROCESSOR.IMGPROCESSOR_WORKER_ErrorSignal.connect(self.imgProcessorHandleError)	# This func not need cause already have "updateImgProc_UI"
		self.objThread_IMGPROCESSOR.moveToThread(self.thread_IMGPROCESSOR)
		self.thread_IMGPROCESSOR.started.connect(self.objThread_IMGPROCESSOR.processor)
		self.thread_IMGPROCESSOR.start()

#===================================================================================================================================================|
#| UI Functions		| 																											| UI Functions		|
#===================================================================================================================================================|
	def connect_slots(self):
		UIFunctions.start_spinboxes(self)
		UIFunctions.load_imgrocParams(self)
		# ROI tuning buttons:
		self.ui.hardware_page_spinBox_roibox_x.valueChanged.connect(lambda: UIFunctions.udpate_roi_slide_x(self))
		self.ui.hardware_page_spinBox_roibox_y.valueChanged.connect(lambda: UIFunctions.udpate_roi_slide_y(self))
		self.ui.hardware_page_spinBox_roibox_size.valueChanged.connect(lambda: UIFunctions.udpate_roi_slide_size(self))
		self.ui.hardware_page_button_roibox_reduce_x.clicked.connect(lambda: UIFunctions.reduce_roi_click_x(self))
		self.ui.hardware_page_button_roibox_reduce_y.clicked.connect(lambda: UIFunctions.reduce_roi_click_y(self))
		self.ui.hardware_page_button_roibox_enlarge_x.clicked.connect(lambda: UIFunctions.enlarge_roi_click_x(self))
		self.ui.hardware_page_button_roibox_enlarge_y.clicked.connect(lambda: UIFunctions.enlarge_roi_click_y(self))
		self.ui.hardware_page_button_roibox_size_reduce.clicked.connect(lambda: UIFunctions.reduce_roi_click_size(self))
		self.ui.hardware_page_button_roibox_size_enlarge.clicked.connect(lambda: UIFunctions.enlarge_roi_click_size(self))
		# HOUGH SEARCH settings buttons:
		self.ui.lineEdit_BLUR_RATE.textChanged.connect(lambda: UIFunctions.udpate_imgrocParams(self))
		self.ui.lineEdit_DP.textChanged.connect(lambda: UIFunctions.udpate_imgrocParams(self))
		self.ui.lineEdit_PARAM1.textChanged.connect(lambda: UIFunctions.udpate_imgrocParams(self))
		self.ui.lineEdit_MINRAD.textChanged.connect(lambda: UIFunctions.udpate_imgrocParams(self))
		self.ui.lineEdit_MINDIST.textChanged.connect(lambda: UIFunctions.udpate_imgrocParams(self))
		self.ui.lineEdit_PARAM2.textChanged.connect(lambda: UIFunctions.udpate_imgrocParams(self))
		self.ui.lineEdit_DELTAD.textChanged.connect(lambda: UIFunctions.udpate_imgrocParams(self))
		self.ui.lineEdit_MAXRAD.textChanged.connect(lambda: UIFunctions.udpate_imgrocParams(self))
		# Calibration buttons:

	def customise_interface_init(self):
		UIFunctions.customise_interface(self)

	def Button(self):
		btnWidget = self.sender()

		if btnWidget.objectName() == "btn_home":									# Redirect to HOME page by clicked on her icon in left bar
			self.ui.stackedWidget.setCurrentWidget(self.ui.page_home)
			UIFunctions.resetStyle(self, "btn_home")
			UIFunctions.labelPage(self, "Главная страница")
			btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))

		# if btnWidget.objectName() == "btn_new_user":
		# 	self.ui.stackedWidget.setCurrentWidget(self.ui.page_home)
		# 	UIFunctions.resetStyle(self, "btn_new_user")
		# 	UIFunctions.labelPage(self, "New User")
		# 	btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))

		if btnWidget.objectName() == "btn_widgets":									# Redirect to DEMO page by clicked on her icon in left bar
			self.ui.stackedWidget.setCurrentWidget(self.ui.page_widgets)
			UIFunctions.resetStyle(self, "btn_widgets")
			UIFunctions.labelPage(self, "Custom Widgets")
			btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))

		if btnWidget.objectName() == "camera-view-page":							# Redirect to CAMERA VIEW page by clicked on her icon in left bar
			self.ui.stackedWidget.setCurrentWidget(self.ui.camera_view_page)
			UIFunctions.resetStyle(self, "btn_widgets")
			UIFunctions.labelPage(self, "Визуальный контроль")
			btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))

		if btnWidget.objectName() == "camera-settings-page":						# Redirect to CAMERA SETTINGS page by clicked on her icon in left bar
			self.ui.stackedWidget.setCurrentWidget(self.ui.camera_settings_page)
			UIFunctions.resetStyle(self, "btn_widgets")
			UIFunctions.labelPage(self, "Настройки камеры")
			btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))

	def mousePressEvent(self, event):
		self.dragPos = event.globalPos()

#===================================================================================================================================================|
#| WORKER CLASSES	|																											| WORKER CLASSES	|
#===================================================================================================================================================|
#===================================================================================================================================================|
#																																| CAM WORKER CLASS	|
#===================================================================================================================================================|
class CAM_WORKER(QObject):
	CAM_WORKER_frameSignal = pyqtSignal(list)
	CAM_WORKER_loggerSignal = pyqtSignal(list)
	CAM_WORKER_SyncSignal = pyqtSignal(bool)
 
	@pyqtSlot()
	def camera(self):
		logging.warning('IP_CAM_WORKER started')
		CAM_UI_PACK = {'TOP_LABEL': window.SHARE_OBJECTS['label_top_info_CAM'],
					   'VIEW_SETUP': window.SHARE_OBJECTS['label_view_settings'],
					   'turnROI':  window.SHARE_OBJECTS['turnROI'],
					   'turnCALIBRATION':  window.SHARE_OBJECTS['turnCALIBRATION'],
					   'save_frame_callibration_btns': window.SHARE_OBJECTS['save_frame_callibration_btns'],
					   'testSizeCoefficient': window.SHARE_OBJECTS['testSizeCoefficient']
						}
		CAMERA_OBJ = cameracontroller.CAMERA_CLASS()
		CAMERA_OBJ.setGUI_logger([self.CAM_WORKER_loggerSignal, window.SHARE_OBJECTS['generalUILogBrowser']])
		CAMERA_OBJ.read_cam_settings_fromBD()										# read global settings from db
		CAMERA_OBJ.startPipeline()													# initialization pipeline
		window.SHARE_OBJECTS['CAM_WORKER'] = CAMERA_OBJ								# share this object to proxy
		QtCore.QThread.msleep(1000)													# let them cooldown!
		self.CAM_WORKER_SyncSignal.emit(True)										# Make signal, that camera object is ready, next object!
  
		while True:
			CAMERA_OBJ.getFrame()
			dataForEmitSignal = CAMERA_OBJ.getDataFromCam()
			self.CAM_WORKER_frameSignal.emit([dataForEmitSignal,CAM_UI_PACK])
			#print('@IP_CAM_WORKER')
			QtCore.QThread.msleep(100)

#===================================================================================================================================================|
#																																| PLC WORKER CLASS	|
#===================================================================================================================================================|
class PLC_WORKER(QObject):
	PLC_WORKER_guiSignal = pyqtSignal(list)
	PLC_WORKER_loggerSignal = pyqtSignal(list)
	PLC_WORKER_SyncSignal = pyqtSignal(bool)
 
	@pyqtSlot()
	def plc(self):
		logging.warning('PLC_WORKER started')
		PLC_UI_PACK = {'TOP_LABEL': window.SHARE_OBJECTS['label_top_info_PLC'],
					   'INDICATOR': window.SHARE_OBJECTS['plc_watchdog_indicator'],
					   'EMULATE_CONNECTION': window.SHARE_OBJECTS['EMULATE_CONNECTION']
					   }
		PLC_OBJ = plccontroller.PLC_CLASS()
		PLC_OBJ.setGUI_logger([self.PLC_WORKER_loggerSignal, window.SHARE_OBJECTS['generalUILogBrowser']])
		PLC_OBJ.setButtons([window.SHARE_OBJECTS['emulate_start_button'], window.SHARE_OBJECTS['emulate_reset_button']])
		window.SHARE_OBJECTS['PLC_WORKER'] = PLC_OBJ
		self.PLC_WORKER_SyncSignal.emit(True)
  
		while True:
			if PLC_UI_PACK['EMULATE_CONNECTION'].isChecked() is True:
				PLC_OBJ.emulateConnection()											# Testing mode
			else:
				PLC_OBJ.dataRead()													# Read all data
			PLC_OBJ.checkResetConveer()												# Testing mode - read debug buttons
			#PLC_OBJ.dataRead()														# Read all data
			dataForEmitSignal = PLC_OBJ.getDataFromPlc()							# пакуем собранные данные
			self.PLC_WORKER_guiSignal.emit([dataForEmitSignal, PLC_UI_PACK])		# передаем данные в обработчик интерфейса
			PLC_OBJ.checkTargetLocked()												# send target data if done 
			QtCore.QThread.msleep(1000)

#===================================================================================================================================================|
#																														| IMGPROCESSOR WORKER CLASS	|
#===================================================================================================================================================|
class IMGPROCESSOR_WORKER(QObject):
	IMGPROCESSOR_WORKER_guiSignal = pyqtSignal(list)
	IMGPROCESSOR_WORKER_loggerSignal = pyqtSignal(list) 
	@pyqtSlot()
	def processor(self):
		logging.warning('IMGPROCESSOR_WORKER started')
		IMGPROCESSOR_UI_PACK = {'TOP_LABEL': window.SHARE_OBJECTS['label_top_info_IMGPROC'], 
								'VIEW_PORT': window.SHARE_OBJECTS['label_view_port'],
								'CURRENT_ACTION': window.SHARE_OBJECTS['label_current_operation'],
								'PROGRESS': window.SHARE_OBJECTS['progressBar_proc'],
								'turnCALIBRATION': window.SHARE_OBJECTS['turnCALIBRATION'],
								'makeLensCALIBRATION': window.SHARE_OBJECTS['makeLensCALIBRATION']
								}
		IMGPROCESSOR_OBJ = imgprocessor.IMG_PROCESSOR_CLASS()
		IMGPROCESSOR_OBJ.setGUI_logger([self.IMGPROCESSOR_WORKER_loggerSignal, window.SHARE_OBJECTS['generalUILogBrowser']])
		IMGPROCESSOR_OBJ.attach_CALIBRATION_BTTN(window.SHARE_OBJECTS['turnCALIBRATION'])
		IMGPROCESSOR_OBJ.attach_makeCALIBRATION_BTTN(window.SHARE_OBJECTS['makeLensCALIBRATION'])
		IMGPROCESSOR_OBJ.attach_CAM_OBJ(window.SHARE_OBJECTS['CAM_WORKER']) 
		IMGPROCESSOR_OBJ.attach_PLC_OBJ(window.SHARE_OBJECTS['PLC_WORKER'])
		window.SHARE_OBJECTS['IMG_PROCESSOR_WORKER'] = IMGPROCESSOR_OBJ
		IMGPROCESSOR_OBJ.reloadCalibrationParams()

		def updateUI(IMGPROCESSOR_OBJ, IMGPROCESSOR_WORKER_guiSignal, IMGPROCESSOR_UI_PACK):
			dataForEmitSignal = IMGPROCESSOR_OBJ.getDataFromIMGProcessor()	# Collect data from this worker				
			IMGPROCESSOR_WORKER_guiSignal.emit([dataForEmitSignal, IMGPROCESSOR_UI_PACK])	# send it
			# dataForEmitSignal = IMGPROCESSOR_OBJ.getDataFromIMGProcessor()	# Collect data from this worker				
			# self.IMGPROCESSOR_WORKER_guiSignal.emit([dataForEmitSignal, IMGPROCESSOR_UI_PACK])	# send it

  
		while True:
			IMGPROCESSOR_OBJ.getDataFrom_other_workers() 								# Collect data from other workers
			lockFrame_trigger, lockFrame_count = IMGPROCESSOR_OBJ.checkForLockFrame()	# Check is everything is ready?
			IMGPROCESSOR_OBJ.checkMakeLensCalibration()

			if lockFrame_trigger == True and lockFrame_count == 1:						# PLC, CAM and Target on the go!
				errorCodeLockFrame = IMGPROCESSOR_OBJ.prepare_all_versions_of_image()
				updateUI(IMGPROCESSOR_OBJ, self.IMGPROCESSOR_WORKER_guiSignal, IMGPROCESSOR_UI_PACK)

				if errorCodeLockFrame == False:
					for i in range(12):
						IMGPROCESSOR_OBJ.getDataFrom_other_workers()
						IMGPROCESSOR_OBJ.prepare_all_versions_of_image()
						errorCodeLugSearch = IMGPROCESSOR_OBJ.findGroundsOfLugsByHough()
						updateUI(IMGPROCESSOR_OBJ, self.IMGPROCESSOR_WORKER_guiSignal, IMGPROCESSOR_UI_PACK)

					IMGPROCESSOR_OBJ.getMidleErrorWithLugPoints()
					if errorCodeLugSearch == False:
						IMGPROCESSOR_OBJ.calculateAngleByLugs()

			updateUI(IMGPROCESSOR_OBJ, self.IMGPROCESSOR_WORKER_guiSignal, IMGPROCESSOR_UI_PACK)
			QtCore.QThread.msleep(2000)

#===================================================================================================================================================|
#| STARTING APP	|																													| STARTING APP	|
#===================================================================================================================================================|
if __name__ == '__main__':											
	app = QApplication(sys.argv)
	logging.basicConfig(filename='app.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')
	logging.warning('Application started')

	# import fonts:
	QtGui.QFontDatabase.addApplicationFont('gui/fonts/segoeui.ttf')
	QtGui.QFontDatabase.addApplicationFont('gui/fonts/segoeuib.ttf')                      		    

	window = MainWindow()
	sys.exit(app.exec_())    
	
