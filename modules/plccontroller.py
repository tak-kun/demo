import snap7
import platform
import csv
from modules import DBlayout
import sys, traceback

platformType = platform.platform()
print(platformType)
if platformType == 'Linux-5.4.0-72-generic-x86_64-with-Ubuntu-18.04-bionic':
	from snap7.snap7types import *
else:
	from snap7.types import *
from snap7.util import *

class PLC_CLASS():
	def __init__(self):
		self.proxyObject_IMG_PROCESSOR = None
		self.dataFromProxyObject_IMG_PROCESSOR = None
		self.plc = snap7.client.Client() # объект плк
		self.plc.set_connection_type(2) # тип соединения с ПЛК

		self.plcParams = { 
						   'db_number' : 100,										# 101
						   'plcUrl' : '192.168.1.10',								# 192.168.3.140
						   'plcError': None,
						   'sleepPlc' : None,
						   'dbArea': 0x84,
						   'lostConnection': None,
						   'GUI_logger': None,
						   'log_ui_object': None,
						   'reset_button': None,
						   'fake_start_button': None }

		self.dataFromPlc = {
							'name': None,

							'rawDataPacket': None,
							'structedDataPacket': None,
							'watchdogState': False,

							'lineID': None,											# deprecated var
							'online': False,
							'currentKC': None,										# deprecated var
							'wheelAvailable': None,									# userfull
							'needTrainWheel': None,									# deprecated var
							'needResetWheel': None,									# deprecated var
							'needTrainWheel_done': None,							# deprecated var
							'needResetWheel_done': None,							# deprecated var
							'lastSendInfo_wheelAvailable': None,
							#----------------------------------
							'shotTrigger': False,
							'CameraDone': False,
							'shiftAngle': 0.0 } 
							


#===========================================================================================|
# | Функции для инициализации	|															|
#===========================================================================================|
	def attach_IMG_PROCESSOR(self, name_link): # Присоединяет прокси обработчика изображения
		while True:
			self.proxyObject_IMG_PROCESSOR = ui.SHARE_OBJECTS[name_link]
			if self.proxyObject_IMG_PROCESSOR is not None:
				break
	
	def emulateConnection(self): 						# фейковый аналог вотчдога
		self.dataFromPlc['online'] = True
		

	def checkResetConveer(self):
		reset_button_status = self.plcParams['reset_button'].isChecked() 						# фейковый запрос и получение информации о готовности колеса
		if reset_button_status == True:
			self.dataFromPlc['wheelAvailable'] = False									# записываем фейковую информацию в пакет
			#self.write_log('Была нажата кнопка сброса!')		
		fake_start_button_status = self.plcParams['fake_start_button'].isChecked()
		if fake_start_button_status == True:
			self.dataFromPlc['wheelAvailable'] = True
			#self.write_log('Была нажата кнопка имитации старта!')

	# def setGUI_logger(self, proxy_link): 						# Сеттер ссылки на логгер
	# 	self.plcParams['GUI_logger'] = proxy_link

	def setGUI_logger(self, proxy_link): 						    # Сеттер ссылки на логгер
		self.plcParams['GUI_logger'] = proxy_link[0]
		self.plcParams['log_ui_object'] = proxy_link[1]

	def setButtons(self, buttons_link): 						# Сеттер ссылки на логгер
		self.plcParams['fake_start_button'] = buttons_link[0]
		self.plcParams['reset_button'] = buttons_link[1]
	
	# def write_log(self, message):								# Функция передачи сообщения логгеру в другой тред
	# 	self.plcParams['GUI_logger'].emit(message)
	def write_log(self, message):								    # Функция передачи сообщения логгеру в другой тред
		self.plcParams['GUI_logger'].emit([message, self.plcParams['log_ui_object']])


	def getPlcParams(self): # Получить параметры данного ПЛК
		return self.plcParams

	def getDataFromPlc(self): # Получить пакет информации от данного ПЛК
		return self.dataFromPlc






#===========================================================================================|
# | Основные функции	|																	|
#===========================================================================================|
	def dataRead(self):
		try:
			self.plc.connect(self.plcParams['plcUrl'], 0, 1)
			self.dataFromPlc['rawDataPacket'] = self.plc.db_read(self.plcParams['db_number'], 0, 12)  # read 430 bytes from db 100 staring from byte 0
			self.dataFromPlc['structedDataPacket']  = snap7.util.DB(
				self.plcParams['db_number'],              				# the db we use
				self.dataFromPlc['rawDataPacket'],              		# bytearray from the plc
				DBlayout.layout,        								# layout specification DB variable data
																		# A DB specification is the specification of a
																		# DB object in the PLC you can find it using
																		# the dataview option on a DB object in PCS7
				14,                  									# size of the specification 428 is start
																		# of last value
																		# which is a INT which is 2 bytes,
				1,                      								# number of row's / specifications
				id_field=None,          								# field we can use to identify a row.
																		# default index is used
				layout_offset=0,        								# sometimes specification does not start a 0
																		# like in our example
				db_offset=0             								# At which point in 'all_data' should we start
																		# reading. if could be that the specification
																		# does not start at 0
				)
			
			self.dataFromPlc['online'] = True

			self.dataFromPlc['wheelAvailable'] = self.dataFromPlc['structedDataPacket'][0]['scan']
			self.dataFromPlc['watchdogState'] = self.dataFromPlc['structedDataPacket'][0]['watchdog']

			self.dataFromPlc['structedDataPacket'][0]['watchdog'] = not self.dataFromPlc['watchdogState']
			self.dataFromPlc['structedDataPacket'][0]['done'] = self.dataFromPlc['CameraDone']
			#TEST WRITING SHIFT VALUES:
			# self.dataFromPlc['structedDataPacket'][0]['coordinateX'] = self.dataFromPlc['shiftXmm']
			# self.dataFromPlc['structedDataPacket'][0]['coordinateY'] = self.dataFromPlc['shiftYmm']
			self.dataFromPlc['structedDataPacket'][0].write(self.plc)

			self.plc.disconnect()


		except:
			self.dataFromPlc['online'] = False
			print('PLC CONNECTION IS LOST!')
			print("-"*60)
			traceback.print_exc(file=sys.stdout)
			print("-"*60)
			self.plc.disconnect()

	def checkTargetLocked(self):
		try:
			if self.dataFromPlc['shotTrigger']:
				self.plc.connect(self.plcParams['plcUrl'], 0, 1)
				#print('DUDES WE GONNA DO THIS WITH ANGLE: ', preparedAngle)
				self.dataFromPlc['structedDataPacket'][0]['coordinateX'] = self.dataFromPlc['shiftAngle']
				#preparedAngle = float(self.dataFromPlc['nippelAngle'])
				# self.dataFromPlc['structedDataPacket'][0]['Angle'] = preparedAngle
				self.dataFromPlc['structedDataPacket'][0].write(self.plc)
				self.write_log('Значения отправлены в ПЛК!')

				self.dataFromPlc['shotTrigger'] = False
				self.plc.disconnect()
		except:
			print('ERROR WHILE SENDING ANGLE TO PLC!')
			self.plc.disconnect()
		
































	# def setConnection(self, setting_connectionState): # Установить объект соединения с ПЛК по Ethernet
	# 	if setting_connectionState is True:
	# 		self.plc.connect(self.plcParams['plcUrl'], 0, 1)
	# 	else:
	# 		self.plc.disconnect()
	# 	self.plcParams['plcConnectionState'] = setting_connectionState

	# def check_infoAboutCurrentWheel(self): # Проверить актуальность информации о наличии диска на центрователе
	# 	if self.dataFromPlc['wheelAvailable'] != self.dataFromPlc['lastSendInfo_wheelAvailable']:
	# 		self.dataFromPlc['lastSendInfo_wheelAvailable'] = self.dataFromPlc['wheelAvailable']

	# def checkConnectionWithPLC_decorator(function_to_decorate): # Декоратор соединения с ПЛК
	# 	def the_wrapper_around_the_original_function(self):
	# 		if self.plcParams['plcConnectionState'] or self.plcParams['lostConnection'] == True:
	# 			try:

	# 				function_to_decorate(self)

	# 			except:
	# 				print(traceback.format_exc()) 
	# 				# Update GUI 📢f
	# 				self.updateGUI_logger('Ошибка отправки сообщения в PLC!', time=True, currentTime=self.getCurretDateTime(), spacer=False)

	# 				self.plcParams['lostConnection'] = True   # Флаг о неудачи поднятия сессии чтения с ПК
	# 				try:
	# 					self.setConnection(False)
	# 					time.sleep(2)
	# 					self.setConnection(True)
	# 				except:
	# 					print(traceback.format_exc())
	# 					# Update GUI 📢
	# 					self.updateGUI_logger('Переподключение к PLC..', time=True, currentTime=self.getCurretDateTime(), spacer=False)


	# 	return the_wrapper_around_the_original_function

	# @checkConnectionWithPLC_decorator
	# def getInformation(self):

	# 	byteData_currentKC = self.plc.read_area(self.plcParams['dbArea'], 147, 0, 2) # читаем блок массива с номером КС
	# 	currentKC = int.from_bytes(byteData_currentKC, byteorder='big', signed=False) # конвертируем в десятичные
	# 	self.dataFromPlc['currentKC'] = currentKC                                     # сохраняем сконвертируемое в словарь данных ПЛК

	# 	dataByte_watchdog = self.plc.read_area(self.plcParams['dbArea'], 147, 3, 1) # читаем блок массива с вотчдогом (мб можно не читать)
	# 	self.dataFromPlc['currentDataPacket_watchdog'] = dataByte_watchdog          # сохраняем сразу блок в словарь данных ПЛК

	# 	byteData_wheelAvailable = self.plc.read_area(self.plcParams['dbArea'], 147, 2, 2) # читаем блок из массива данных с наличием диска
	# 	self.dataFromPlc['currentDataPacket_wheelAvailable'] = byteData_wheelAvailable
	# 	wheelAvailable = get_bool(byteData_wheelAvailable, 0,0)                     # конвертируем в понятный формат
	# 	self.dataFromPlc['wheelAvailable'] = wheelAvailable                         # сохраняем в словарь данных ПЛК

	# 	byteData_needTrainWheel = self.plc.read_area(self.plcParams['dbArea'], 147, 4, 1) # читаем блок данных о необходимости внести фото в БД
	# 	needTrainWheel = get_bool(byteData_needTrainWheel, 0,0)                     # конвертируем в понятный формат
	# 	self.dataFromPlc['needTrainWheel'] = needTrainWheel                         # сохраняем в словарь данных ПЛК

	# 	byteData_needResetWheel = self.plc.read_area(self.plcParams['dbArea'], 147, 5, 1) # читаем блок данных о необходимости удалить фото в БД
	# 	self.dataFromPlc['currentDataPacket_needTrainWheel'] = byteData_needResetWheel
	# 	needResetWheel = get_bool(byteData_needResetWheel, 0,0)                     # конвертируем в понятный формат
	# 	self.dataFromPlc['needResetWheel'] = needResetWheel                         # сохраняем в словарь данных ПЛК



	# 	self.plcParams['lostConnection'] = False  # Последняя строчка в блоке Try, обозначает что все операции выполнены успешно, флаг
	   

	# 	# Update GUI 📢
	# 	if self.dataFromPlc['lastSendInfo_wheelAvailable'] != self.dataFromPlc['wheelAvailable'] and self.dataFromPlc['wheelAvailable'] == True:
	# 		self.updateGUI_logger('!Требуется проверка диска!', time=True, currentTime=self.getCurretDateTime(), spacer=False) 

	# 	if self.dataFromPlc['lastSendInfo_wheelAvailable'] != self.dataFromPlc['wheelAvailable'] and self.dataFromPlc['wheelAvailable'] == False:
	# 		self.updateGUI_logger('!Сброс результатов проверок!', time=True, currentTime=self.getCurretDateTime(), spacer=True, progressBar=0)
	# 	#------------------------------------------------------------------------------------------------------------------------------

	# def update_Watchdog(self):
	# 	if self.dataFromPlc['currentDataPacket_watchdog'] is not None:
	# 		if self.plcParams['watchdogState']: # Часть кода которая инвертирует переменную Вотчдога и отправляет в контроллер
	# 			self.plcParams['watchdogState'] = False
	# 		else:
	# 			self.plcParams['watchdogState'] = True
	# 	set_bool(self.dataFromPlc['currentDataPacket_watchdog'], 0, 0, self.plcParams['watchdogState'])
	# 	self.plc.write_area(self.plcParams['dbArea'], 147, 3, self.dataFromPlc['currentDataPacket_watchdog'])

	# def updateUnknownKC(self):
	# 	if self.dataFromProxyObject_IMG_PROCESSOR['unknownKC'] is True:
	# 		test_UNKNOWN_WHEEL_STATE = get_bool(self.dataFromPlc['currentDataPacket_wheelAvailable'], 0,2)
	# 		if test_UNKNOWN_WHEEL_STATE is False:
	# 			set_bool(self.dataFromPlc['currentDataPacket_wheelAvailable'], 0, 2, self.dataFromProxyObject_IMG_PROCESSOR['unknownKC'])
	# 			self.plc.write_area(self.plcParams['dbArea'], 147, 2, self.dataFromPlc['currentDataPacket_wheelAvailable'])
	# 			# Update GUI 📢
	# 			self.updateGUI_logger('Сообщение "Шаблон КС отсутствует" отправлено в ПЛК!', time=False, currentTime=None, spacer=True)

	# 	elif self.dataFromProxyObject_IMG_PROCESSOR['unknownKC'] is False:
	# 		test_UNKNOWN_WHEEL_STATE = get_bool(self.dataFromPlc['currentDataPacket_wheelAvailable'], 0,2)
	# 		if test_UNKNOWN_WHEEL_STATE is True:
	# 			set_bool(self.dataFromPlc['currentDataPacket_wheelAvailable'], 0, 2, self.dataFromProxyObject_IMG_PROCESSOR['unknownKC'])
	# 			self.plc.write_area(self.plcParams['dbArea'], 147, 2, self.dataFromPlc['currentDataPacket_wheelAvailable'])
	# 			# Update GUI 📢
	# 			self.updateGUI_logger('Сообщение "Шаблон КС отсутствует" снято из ПЛК!', time=False, currentTime=None, spacer=False)

	# def updateVerificationSolution(self):
	# 	#if self.dataFromProxyObject_IMG_PROCESSOR['verificationSolution'] is True:
	# 	if self.dataFromProxyObject_IMG_PROCESSOR['verificationSolution'] is True:
	# 		set_bool(self.dataFromPlc['currentDataPacket_wheelAvailable'], 0, 1, self.dataFromProxyObject_IMG_PROCESSOR['verificationSolution']) 
	# 		self.plc.write_area(self.plcParams['dbArea'], 147, 2, self.dataFromPlc['currentDataPacket_wheelAvailable'])
	# 	else:
	# 		set_bool(self.dataFromPlc['currentDataPacket_wheelAvailable'], 0, 1, False) 
	# 		self.plc.write_area(self.plcParams['dbArea'], 147, 2, self.dataFromPlc['currentDataPacket_wheelAvailable'])



	# def updateResetWheel(self):
	# 	if self.dataFromPlc['needResetWheel'] is True:
	# 		set_bool(self.dataFromPlc['currentDataPacket_needTrainWheel'], 0, 0, False) # установить в блоке данных dataByte_reset переменную False
	# 		self.plc.write_area(self.plcParams['dbArea'], 147, 5, self.dataFromPlc['currentDataPacket_needTrainWheel']) # отправить пакет в ПЛК
	# 		# Update GUI 📢
	# 		self.updateGUI_logger('Кнопка "Reset KC" сброшена.', time=True, currentTime=self.getCurretDateTime(), spacer=False)


	# @checkConnectionWithPLC_decorator
	# def sendInformation(self):
	# 	self.update_Watchdog()
	# 	self.updateUnknownKC()
	# 	self.updateResetWheel()
	# 	self.updateVerificationSolution()

