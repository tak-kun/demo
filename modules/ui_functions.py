#===================================================================================================================================================|
# 																																| Импорт библиотек	|
#===================================================================================================================================================|
from main_port import *
import pickle
from scipy.spatial import distance as dist

GLOBAL_STATE = 0
GLOBAL_TITLE_BAR = True
count = 1

class UIFunctions(MainWindow):
	GLOBAL_STATE = 0
	GLOBAL_TITLE_BAR = True
	GLOBAL_CALIBRATION_STATUS = False
	GLOBAL_TESTSIZECOEFF_COUNTER = 0

	f = open('calibration/store-mtx.pckl', 'rb')
	GLOBAL_mtx = pickle.load(f)
	f.close() 
	f = open('calibration/store-dist.pckl', 'rb')
	GLOBAL_dist = pickle.load(f)
	f.close()
	f = open('calibration/store-newcameramtx.pckl', 'rb')
	GLOBAL_newcameramtx = pickle.load(f)
	f.close()


	#trainingPacket = {'lockedFrameReady': None, 'currentKC': None} 										  # создаем словарь для окна обучения точек?
	def start_spinboxes(self):
		self.ui.hardware_page_spinBox_roibox_x.setValue(dbcontroller.read_settings_FromDB(params = {'setting':'ROI_FRAME_X'}))
		self.ui.hardware_page_spinBox_roibox_y.setValue(dbcontroller.read_settings_FromDB(params = {'setting':'ROI_FRAME_Y'}))
		self.ui.hardware_page_spinBox_roibox_size.setValue(dbcontroller.read_settings_FromDB(params = {'setting':'ROI_FRAME_SIZE'}))
		self.ui.hardware_page_roibox_size_label.setText('ROIseize: '+str(dbcontroller.read_settings_FromDB(params = {'setting':'ROI_FRAME_SIZE'})))

	def udpate_roi_slide_x(self):
		value = self.ui.hardware_page_spinBox_roibox_x.value()
		dbcontroller.update_settings_FromDB(params = {'setting':'ROI_FRAME_X', 'value': value}) # (setting, value)
	def udpate_roi_slide_y(self):
		value = self.ui.hardware_page_spinBox_roibox_y.value()
		dbcontroller.update_settings_FromDB(params = {'setting':'ROI_FRAME_Y', 'value': value}) # (setting, value)

	def reduce_roi_click_x(self):
		newValue = self.ui.hardware_page_spinBox_roibox_x.value() -1 
		self.ui.hardware_page_spinBox_roibox_x.setValue(newValue)
		dbcontroller.update_settings_FromDB(params = {'setting':'ROI_FRAME_X', 'value': newValue})
	def reduce_roi_click_y(self):
		newValue = self.ui.hardware_page_spinBox_roibox_y.value() -1 
		self.ui.hardware_page_spinBox_roibox_y.setValue(newValue)
		dbcontroller.update_settings_FromDB(params = {'setting':'ROI_FRAME_Y', 'value': newValue})
	def enlarge_roi_click_x(self):
		newValue = self.ui.hardware_page_spinBox_roibox_x.value() +1 
		self.ui.hardware_page_spinBox_roibox_x.setValue(newValue)
		dbcontroller.update_settings_FromDB(params = {'setting':'ROI_FRAME_X', 'value': newValue})
	def enlarge_roi_click_y(self):
		newValue = self.ui.hardware_page_spinBox_roibox_y.value() +1 
		self.ui.hardware_page_spinBox_roibox_y.setValue(newValue)
		dbcontroller.update_settings_FromDB(params = {'setting':'ROI_FRAME_Y', 'value': newValue})

	def reduce_roi_click_size(self):	# УВЕЛИЧЕНИЕ ROI ПО КЛИКУ НА СТРЕЛКУ
		newValue = self.ui.hardware_page_spinBox_roibox_size.value() -4 
		self.ui.hardware_page_spinBox_roibox_size.setValue(newValue)
		dbcontroller.update_settings_FromDB(params = {'setting':'ROI_FRAME_SIZE', 'value': newValue})
	def enlarge_roi_click_size(self):	# УВЕЛИЧЕНИЕ ROI ПО КЛИКУ НА СТРЕЛКУ
		newValue = self.ui.hardware_page_spinBox_roibox_size.value() +4 
		self.ui.hardware_page_spinBox_roibox_size.setValue(newValue)
		dbcontroller.update_settings_FromDB(params = {'setting':'ROI_FRAME_SIZE', 'value': newValue})	

	def udpate_roi_slide_size(self):	# УВЕЛИЧЕНИЕ ROI ПО КЛИКУ ПО СЛАЙДЕРУ
		value = self.ui.hardware_page_spinBox_roibox_size.value()
		while value%4 != 0:
			value = value + 1
		dbcontroller.update_settings_FromDB(params = {'setting':'ROI_FRAME_SIZE', 'value': value}) # (setting, value)
		self.ui.hardware_page_roibox_size_label.setText('ROIseize: '+str(value))

	def udpate_imgrocParams(self):
		lines_dict = {
			'BLUR_RATE': self.ui.lineEdit_BLUR_RATE,
			'DP': self.ui.lineEdit_DP,
			'PARAM1': self.ui.lineEdit_PARAM1,
			'MINRAD': self.ui.lineEdit_MINRAD,
			'MINDIST': self.ui.lineEdit_MINDIST,
			'PARAM2': self.ui.lineEdit_PARAM2,
			'MAXRAD': self.ui.lineEdit_MAXRAD,
			'DELTAD': self.ui.lineEdit_DELTAD }
		lines_dict_keys = lines_dict.keys()
		for key in lines_dict_keys:
			value = int(lines_dict[key].text())
			# <------------------------------------ тут нужен неплохой блок проверок на полученное число!
			dbcontroller.update_settings_FromDB(params = {'setting':key, 'value': value})

	def load_imgrocParams(self):
		lines_dict = {
			'BLUR_RATE': self.ui.lineEdit_BLUR_RATE,
			'DP': self.ui.lineEdit_DP,
			'PARAM1': self.ui.lineEdit_PARAM1,
			'MINRAD': self.ui.lineEdit_MINRAD,
			'MINDIST': self.ui.lineEdit_MINDIST,
			'PARAM2': self.ui.lineEdit_PARAM2,
			'MAXRAD': self.ui.lineEdit_MAXRAD,
			'DELTAD': self.ui.lineEdit_DELTAD }
		lines_dict_keys = lines_dict.keys()
		for key in lines_dict_keys:
			lines_dict[key].setText(str(dbcontroller.read_settings_FromDB(params = {'setting':key})))

#===================================================================================================================================================|
# 																														| Main View Frame Function	|
#===================================================================================================================================================|
	@classmethod 
	def updateCameraView(self, packet): 				
		if packet[0]['currentRawFrame'] is not None:

			ui_objects = packet[1]
			#UPDATE UI:
			ui_objects['TOP_LABEL'].setText('ONLINE')
			if packet[0]['online'] is True:
				ui_objects['TOP_LABEL'].setStyleSheet('color: rgb(115, 210, 22);')
			else:
				ui_objects['TOP_LABEL'].setStyleSheet('color:#ff0000;')

			self.frameToUpdate = packet[0]['currentRawFrame'].copy()
			frameToUpdateResized = self.frameToUpdate
			#frameToUpdateResized = frameToUpdateResized[0:720, 220:940]
			x, y, z = frameToUpdateResized.shape 


			# DEBUG CAMERA CALLIBRATION:
			###############################################################################
			turnCALLIBRATIONstate = ui_objects['turnCALIBRATION'].isChecked()
			if turnCALLIBRATIONstate is True:
				frameToUpdateResized = cv2.undistort(frameToUpdateResized, self.GLOBAL_mtx, self.GLOBAL_dist, None, self.GLOBAL_newcameramtx)
			###############################################################################

			frameToUpdateResized = cv2.cvtColor(frameToUpdateResized, cv2.COLOR_BGR2RGB )

			# DEBUG TEST SIZE CALLIBRATION:
			###############################################################################
			turnTestSizeCoefficient = ui_objects['testSizeCoefficient'].isChecked()
			if turnTestSizeCoefficient is True:
				if self.GLOBAL_TESTSIZECOEFF_COUNTER < 30:
					self.GLOBAL_TESTSIZECOEFF_COUNTER = self.GLOBAL_TESTSIZECOEFF_COUNTER + 1
					gray_test = frameToUpdateResized.copy()
					gray_test= cv2.cvtColor(gray_test,cv2.COLOR_RGB2GRAY)
					ret, corners = cv2.findChessboardCorners(gray_test, (9,6),None)
					if ret == True:
						x1 = int(corners[0][0][0])
						y1 = int(corners[0][0][1])
						x2 = int(corners[-1][0][0])
						y2 = int(corners[-1][0][1])
						cv2.circle(frameToUpdateResized,(x1, y1), 3, (0,255,0), thickness =4)
						cv2.circle(frameToUpdateResized,(x2, y2), 3, (0,255,0), thickness =4)
						distance = dist.euclidean((x1, y1), (x2, y2))
						cv2.line(frameToUpdateResized,(x1, y1),
								(x2, y2),(0,140,255),2)
						
						#background:
						cv2.rectangle(frameToUpdateResized, (int(x1), int(y1+3)), (int(x1+ 480), int(y1-25)), (0,0,0), -1)

						cv2.putText(frameToUpdateResized, "Dist-PX: " + str(distance),  
						(x1, y1),  
						fontFace=cv2.FONT_HERSHEY_DUPLEX,  
						fontScale=1,  
						color=(255,255,255))
						coefficient = 230.6 / distance
						
						#background:
						cv2.rectangle(frameToUpdateResized, (int(x2), int(y2+3)), (int(x2+ 480), int(y2-25)), (0,0,0), -1)

						cv2.putText(frameToUpdateResized, "Koef-MM: " + str(coefficient),  
						(x2, y2),  
						fontFace=cv2.FONT_HERSHEY_DUPLEX,  
						fontScale=1,  
						color=(255,255,255))
						#----------------------------------------__# TESTING
						# test_coeff = 0.41793
						# test = distance * test_coeff
						# print(test)
						#----------------------------------------__# TESTING
			else:
				self.GLOBAL_TESTSIZECOEFF_COUNTER = 0


			
			###############################################################################
			# DEBUG TEST SIZE CALLIBRATION:

			# CIRCLE SEARCH ROI DRAW BLOCK
			########################################################################################################
			turnROIstate = ui_objects['turnROI'].isChecked()
			if turnROIstate is True:

				ROI_FRAME_X = dbcontroller.read_settings_FromDB(params = {'setting':'ROI_FRAME_X'}) # read roi frame for first time!
				ROI_FRAME_Y = dbcontroller.read_settings_FromDB(params = {'setting':'ROI_FRAME_Y'})
				ROI_FRAME_SIZE = dbcontroller.read_settings_FromDB(params = {'setting':'ROI_FRAME_SIZE'})
				
				start_point = (0+ROI_FRAME_X, 0+ROI_FRAME_Y) 
				end_point = (ROI_FRAME_SIZE+ROI_FRAME_X, ROI_FRAME_SIZE+ROI_FRAME_Y)  # //// 640
				color = (0, 0, 0)
				#cover_image:
				cover_image = frameToUpdateResized.copy()
				upper_block = [ (0, 0), (y,  ROI_FRAME_Y)]
				bottom_block = [(0, ROI_FRAME_Y+ROI_FRAME_SIZE), (y, x)]
				left_block = [(0, ROI_FRAME_Y), (ROI_FRAME_X, ROI_FRAME_Y+ROI_FRAME_SIZE)]
				right_block = [(ROI_FRAME_X+ROI_FRAME_SIZE, ROI_FRAME_Y), (y, ROI_FRAME_Y+ROI_FRAME_SIZE)]

				frameToUpdateResized = cv2.rectangle(frameToUpdateResized, upper_block[0], upper_block[1], color, -1)		# black background
				frameToUpdateResized = cv2.rectangle(frameToUpdateResized, bottom_block[0], bottom_block[1], color, -1) 
				frameToUpdateResized = cv2.rectangle(frameToUpdateResized, left_block[0], left_block[1], color, -1) 
				frameToUpdateResized = cv2.rectangle(frameToUpdateResized, right_block[0], right_block[1], color, -1) 

				# DRAW CENTER OF FRAME: 
				cv2.line(frameToUpdateResized,( int(y/2)-40, int(x/2) ) ,(int(y/2)+40, int(x/2)),(255,0,0),3) # cross in the center of wheel
				cv2.line(frameToUpdateResized,(int(y/2), int(x/2)-40), (int(y/2), int(x/2)+40),(255,0,0),3) # cross in the center of wheel

				frameToUpdateResized = cv2.addWeighted(cover_image, 0.5, frameToUpdateResized, 0.5, 0)						# deploy black background
				
				frameToUpdateResized = cv2.rectangle(frameToUpdateResized, start_point, end_point, (0,255,0), 3) 			# green contour
				
				halfOfRect = [ (int(ROI_FRAME_X+(ROI_FRAME_SIZE/2)), ROI_FRAME_Y), (int(ROI_FRAME_X+(ROI_FRAME_SIZE/2)), ROI_FRAME_Y+ROI_FRAME_SIZE) ]
				halfOfRect_2 = [ (ROI_FRAME_X, int(ROI_FRAME_Y+(ROI_FRAME_SIZE/2))), (ROI_FRAME_X+ROI_FRAME_SIZE, int(ROI_FRAME_Y+(ROI_FRAME_SIZE/2))) ]
				frameToUpdateResized = cv2.rectangle(frameToUpdateResized, halfOfRect[0], halfOfRect[1], (0,140,255), 2) 
				frameToUpdateResized = cv2.rectangle(frameToUpdateResized, halfOfRect_2[0], halfOfRect_2[1], (0,140,255), 2) 


			image_profile = QtGui.QImage(frameToUpdateResized, y, x, QtGui.QImage.Format_RGB888).rgbSwapped()
			image_profile = image_profile.scaled(640, 512, aspectRatioMode=QtCore.Qt.KeepAspectRatio, transformMode=QtCore.Qt.SmoothTransformation) # 640,512 # 480,360
			#label_view = packet[1]
			#ui_objects['VIEW_PORT'].setPixmap(QtGui.QPixmap.fromImage(image_profile))
			#label_view_settings = packet[2]
			ui_objects['VIEW_SETUP'].setPixmap(QtGui.QPixmap.fromImage(image_profile))

			# SAVING CALLIBRATION IMAGES:
			for i in ui_objects['save_frame_callibration_btns']:
				testState = i.isChecked()
				if testState is True:
					print(i.objectName()[-1])
					cv2.imwrite('calibration/' + i.objectName()[-1] + '.png', packet[0]['currentRawFrame'].copy())

		else: 
			ui_objects = packet[1]
			ui_objects['TOP_LABEL'].setText('OFFLINE')
			ui_objects['TOP_LABEL'].setStyleSheet('color:#ff0000;')

#===================================================================================================================================================|
# 																																| General UI LOG	|
#===================================================================================================================================================|
	@classmethod 
	def printToGeneralUILog(self, message):
		try:
			message[1].append(message[0])
			#message[1].append(" ")
		except:
			print('@LOGGER_NEED_HERE: missed print to general ui log!')

#===================================================================================================================================================|
# 																																| General UI LOG	|
#===================================================================================================================================================|
	# @classmethod 
	# def printToGeneralUILog(self, message):
	# 	message[1].append(message[0])

#===================================================================================================================================================|
# 																																| General UI LOG	|
#===================================================================================================================================================|
	@classmethod 
	def updatePLC_UI(self, message):
		data = message[0]
		ui_objects = message[1]

		#ui_objects['TOP_LABEL'].setText(str(data['online'])) 				# обновляем пункт "плк онлайн" "plc status"
		ui_objects['TOP_LABEL'].setText('ONLINE')
		if data['online'] is True:
			ui_objects['TOP_LABEL'].setStyleSheet('color: rgb(115, 210, 22);')
		else:
			ui_objects['TOP_LABEL'].setStyleSheet('color:#ff0000;')

		if data['watchdogState'] is True:
			ui_objects['INDICATOR'].setStyleSheet('background-color: rgb(115, 210, 22);')
		else:
			ui_objects['INDICATOR'].setStyleSheet('background-color: rgb(0, 0, 0);')

#===================================================================================================================================================|
# 																																| General UI LOG	|
#===================================================================================================================================================|
	@classmethod 
	def updateImgProc_UI(self, message):
		#color: rgb(46, 52, 54);
		data = message[0]
		ui_objects = message[1]

		ui_objects['CURRENT_ACTION'].setText("IMGworker: " + data['currentOperation'])

		ui_objects['PROGRESS'].setValue(data['currentProgress'])

		if ui_objects['makeLensCALIBRATION'].text() == 'ГОТОВО':
			f = open('calibration/store-mtx.pckl', 'rb')
			self.GLOBAL_mtx = pickle.load(f)
			f.close() 
			f = open('calibration/store-dist.pckl', 'rb')
			self.GLOBAL_dist = pickle.load(f)
			f.close()
			f = open('calibration/store-newcameramtx.pckl', 'rb')
			self.GLOBAL_newcameramtx = pickle.load(f)
			f.close()
			ui_objects['makeLensCALIBRATION'].setText('Калибровка')

		ui_objects['TOP_LABEL'].setText(data['status'])
		if data['status'] == 'READY':
			ui_objects['TOP_LABEL'].setStyleSheet('color: rgb(245, 121, 0)')
		if data['status'] == 'LOCKED FRAME..':
			ui_objects['TOP_LABEL'].setStyleSheet('color: rgb(252, 233, 79)')

		if data['currentProgress'] >= 40:					# Обновляем КАРТИНКУ Захват кадра
			roi_frame = data['lockedFrameRingDrawed'].copy()

			if len(roi_frame.shape) > 2:
				x, y, z = roi_frame.shape
			else:
				x, y = roi_frame.shape
				roi_frame = cv2.cvtColor(roi_frame, cv2.COLOR_GRAY2RGB )
			
			image_profile = QtGui.QImage(roi_frame, x, y, QtGui.QImage.Format_RGB888).rgbSwapped()
			image_profile = image_profile.scaled(512,512, aspectRatioMode=QtCore.Qt.KeepAspectRatio, transformMode=QtCore.Qt.SmoothTransformation)
			ui_objects['VIEW_PORT'].setPixmap(QtGui.QPixmap.fromImage(image_profile))
		if data['currentProgress'] == 0 and data['lockedFrameRingDrawed'] is not None:
			old_roi_frame = data['lockedFrameRingDrawed'].copy()
			
			if len(old_roi_frame.shape) == 3:
				x, y, z = old_roi_frame.shape
				plug = np.zeros((x,y,z), np.uint8)
			else:
				x, y = old_roi_frame.shape
				plug = np.zeros((x,y), np.uint8)

			#x, y = old_roi_frame.shape
			#plug = np.zeros((x,y), np.uint8)
			merge = cv2.addWeighted(old_roi_frame, 0.2, plug, 0.8, 0)	
			if len(merge.shape) == 2 :
				merge = cv2.cvtColor(merge, cv2.COLOR_GRAY2RGB )
			cv2.putText(merge, "Waiting command",  
										(int(x/2) - 140, int(y/2)),  
										fontFace=cv2.FONT_HERSHEY_DUPLEX,  
										fontScale=1,  
										color=(255, 255, 255))  
			image_profile = QtGui.QImage(merge, x, y, QtGui.QImage.Format_RGB888).rgbSwapped()
			image_profile = image_profile.scaled(512,512, aspectRatioMode=QtCore.Qt.KeepAspectRatio, transformMode=QtCore.Qt.SmoothTransformation)
			ui_objects['VIEW_PORT'].setPixmap(QtGui.QPixmap.fromImage(image_profile))
		else: 
			pass
			



#===================================================================================================================================================|
# 																														| Main Window GUI Functions	|
#===================================================================================================================================================|
	def maximize_restore(self):
		global GLOBAL_STATE
		status = GLOBAL_STATE
		if status == 0:
			self.showMaximized()
			GLOBAL_STATE = 1
			self.ui.horizontalLayout.setContentsMargins(0, 0, 0, 0)
			self.ui.btn_maximize_restore.setToolTip("Restore")
			self.ui.btn_maximize_restore.setIcon(QtGui.QIcon(u":/16x16/icons/16x16/cil-window-restore.png"))
			self.ui.frame_top_btns.setStyleSheet("background-color: rgb(27, 29, 35)")
			self.ui.frame_size_grip.hide()
		else:
			GLOBAL_STATE = 0
			self.showNormal()
			self.resize(self.width()+1, self.height()+1)
			self.ui.horizontalLayout.setContentsMargins(10, 10, 10, 10)
			self.ui.btn_maximize_restore.setToolTip("Maximize")
			self.ui.btn_maximize_restore.setIcon(QtGui.QIcon(u":/16x16/icons/16x16/cil-window-maximize.png"))
			self.ui.frame_top_btns.setStyleSheet("background-color: rgba(27, 29, 35, 200)")
			self.ui.frame_size_grip.show()

	def returStatus():
		return GLOBAL_STATE

	def setStatus(status):
		global GLOBAL_STATE
		GLOBAL_STATE = status

	def enableMaximumSize(self, width, height):
		if width != '' and height != '':
			self.setMaximumSize(QSize(width, height))
			self.ui.frame_size_grip.hide()
			self.ui.btn_maximize_restore.hide()

	def toggleMenu(self, maxWidth, enable):
		if enable:
			# GET WIDTH
			width = self.ui.frame_left_menu.width()
			maxExtend = maxWidth
			standard = 70 #70
			# SET MAX WIDTH
			if width == 70: #70
				widthExtended = maxExtend
			else:
				widthExtended = standard
			# ANIMATION
			self.animation = QPropertyAnimation(self.ui.frame_left_menu, b"minimumWidth")
			self.animation.setDuration(300)
			self.animation.setStartValue(width)
			self.animation.setEndValue(widthExtended)
			self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
			self.animation.start()

	def removeTitleBar(status):
		global GLOBAL_TITLE_BAR
		GLOBAL_TITLE_BAR = status

	def labelTitle(self, text):
		self.ui.label_title_bar_top.setText(text)

	#def labelDescription(self, text):				# DEPRECATED!
		#self.ui.label_top_info_1.setText(text)

	def addNewMenu(self, name, objName, icon, isTopMenu):
		font = QFont()
		font.setFamily(u"Segoe UI")
		button = QPushButton(str(count),self)
		button.setObjectName(objName)
		sizePolicy3 = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		sizePolicy3.setHorizontalStretch(0)
		sizePolicy3.setVerticalStretch(0)
		sizePolicy3.setHeightForWidth(button.sizePolicy().hasHeightForWidth())
		button.setSizePolicy(sizePolicy3)
		button.setMinimumSize(QSize(0, 70))
		button.setLayoutDirection(Qt.LeftToRight)
		button.setFont(font)
		button.setStyleSheet(Style.style_bt_standard.replace('ICON_REPLACE', icon))
		button.setText(name)
		button.setToolTip(name)
		button.clicked.connect(self.Button)
		if isTopMenu:
			self.ui.layout_menus.addWidget(button)
		else:
			self.ui.layout_menu_bottom.addWidget(button)

	def selectMenu(getStyle):
		select = getStyle + ("QPushButton { border-right: 7px solid rgb(44, 49, 60); }")
		return select

	def deselectMenu(getStyle):
		deselect = getStyle.replace("QPushButton { border-right: 7px solid rgb(44, 49, 60); }", "")
		return deselect

	def selectStandardMenu(self, widget):
		for w in self.ui.frame_left_menu.findChildren(QPushButton):
			if w.objectName() == widget:
				w.setStyleSheet(UIFunctions.selectMenu(w.styleSheet()))

	def resetStyle(self, widget):
		for w in self.ui.frame_left_menu.findChildren(QPushButton):
			if w.objectName() != widget:
				w.setStyleSheet(UIFunctions.deselectMenu(w.styleSheet()))

	def labelPage(self, text):
		newText = '| ' + text.upper()
		self.ui.label_top_info_2.setText(newText)

	def userIcon(self, initialsTooltip, icon, showHide):
		if showHide:
			# SET TEXT
			self.ui.label_user_icon.setText(initialsTooltip)
			# SET ICON
			if icon:
				style = self.ui.label_user_icon.styleSheet()
				setIcon = "QLabel { background-image: " + icon + "; }"
				self.ui.label_user_icon.setStyleSheet(style + setIcon)
				self.ui.label_user_icon.setText('')
				self.ui.label_user_icon.setToolTip(initialsTooltip)
		else:
			self.ui.label_user_icon.hide()

#===================================================================================================================================================|
# 																													| Main Window GUI DEFINITIONS	|
#===================================================================================================================================================|
	def uiDefinitions(self):
		def dobleClickMaximizeRestore(event):
			# IF DOUBLE CLICK CHANGE STATUS
			if event.type() == QtCore.QEvent.MouseButtonDblClick:
				QtCore.QTimer.singleShot(250, lambda: UIFunctions.maximize_restore(self))

		## REMOVE ==> STANDARD TITLE BAR
		if GLOBAL_TITLE_BAR:
			self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
			self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
			self.ui.frame_label_top_btns.mouseDoubleClickEvent = dobleClickMaximizeRestore
		else:
			self.ui.horizontalLayout.setContentsMargins(0, 0, 0, 0)
			self.ui.frame_label_top_btns.setContentsMargins(8, 0, 0, 5)
			self.ui.frame_label_top_btns.setMinimumHeight(42)
			self.ui.frame_icon_top_bar.hide()
			self.ui.frame_btns_right.hide()
			self.ui.frame_size_grip.hide()


		## SHOW ==> DROP SHADOW
		self.shadow = QGraphicsDropShadowEffect(self)
		self.shadow.setBlurRadius(17)
		self.shadow.setXOffset(0)
		self.shadow.setYOffset(0)
		self.shadow.setColor(QColor(0, 0, 0, 150))
		self.ui.frame_main.setGraphicsEffect(self.shadow)

		## ==> RESIZE WINDOW
		self.sizegrip = QSizeGrip(self.ui.frame_size_grip)
		self.sizegrip.setStyleSheet("width: 20px; height: 20px; margin 0px; padding: 0px;")

		### ==> MINIMIZE
		self.ui.btn_minimize.clicked.connect(lambda: self.showMinimized())

		## ==> MAXIMIZE/RESTORE
		self.ui.btn_maximize_restore.clicked.connect(lambda: UIFunctions.maximize_restore(self))

		## SHOW ==> CLOSE APPLICATION
		self.ui.btn_close.clicked.connect(lambda: self.close())

#===================================================================================================================================================|
# 																													| Main Window GUI CUSTOMIZING	|
#===================================================================================================================================================|
	def customise_interface(self): 
		## START - WINDOW ATTRIBUTES
		UIFunctions.removeTitleBar(True)

		## SET ==> WINDOW TITLE
		#self.setWindowTitle('Main Window - Python Base TEST')
		#UIFunctions.labelTitle(self, 'Main Window - Python Base')
		#UIFunctions.labelDescription(self, 'Set text')					# DEPRECATED!

		## WINDOW SIZE ==> DEFAULT SIZE 			
		startSize = QSize(1000, 720)
		self.resize(startSize)
		self.setMinimumSize(startSize)
		# UIFunctions.enableMaximumSize(self, 500, 720)

		## ==> CREATE MENUS
		## ==> TOGGLE MENU SIZE
		self.ui.btn_toggle_menu.clicked.connect(lambda: UIFunctions.toggleMenu(self, 220, True))

		## ==> ADD CUSTOM MENUS
		self.ui.stackedWidget.setMinimumWidth(20)
		#UIFunctions.addNewMenu(self, "HOME", "btn_home", "url(:/16x16/icons/16x16/cil-home.png)", True)
		UIFunctions.addNewMenu(self, "HOME", "btn_home", "url(:/16x16/icons/16x16/cil-home.png)", True)
		#UIFunctions.addNewMenu(self, "Add User", "btn_new_user", "url(:/16x16/icons/16x16/cil-user-follow.png)", True)			# DEPRECATED
		UIFunctions.addNewMenu(self, "Custom Widgets", "btn_widgets", "url(:/16x16/icons/16x16/cil-equalizer.png)", False)
		
		# страница которую добавил я
		UIFunctions.addNewMenu(self, "Camera view", "camera-view-page", "url(:/16x16/icons/16x16/cil-image1.png)", True)
		UIFunctions.addNewMenu(self, "Camera settings", "camera-settings-page", "url(:/16x16/icons/16x16/cil-exposure.png)", True)

		# START MENU => SELECTION
		UIFunctions.selectStandardMenu(self, "btn_home")

		## ==> START PAGE
		self.ui.stackedWidget.setCurrentWidget(self.ui.page_home)   				# Выбирает окно отображаемое при старте

		## USER ICON ==> SHOW HIDE
		#UIFunctions.userIcon(self, "User", "", True)

		## ==> MOVE WINDOW / MAXIMIZE / RESTORE
		def moveWindow(event):
			# IF MAXIMIZED CHANGE TO NORMAL
			if UIFunctions.returStatus() == 1:
				UIFunctions.maximize_restore(self)

			# MOVE WINDOW
			if event.buttons() == Qt.LeftButton:
				self.move(self.pos() + event.globalPos() - self.dragPos)
				self.dragPos = event.globalPos()
				event.accept()

		# WIDGET TO MOVE
		self.ui.frame_label_top_btns.mouseMoveEvent = moveWindow

		## ==> LOAD DEFINITIONS
		UIFunctions.uiDefinitions(self)

	 	## ==> QTableWidget RARAMETERS
		self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

		self.show()

#===================================================================================================================================================|
# 																														| Main Window GUI EVENTS	|
#===================================================================================================================================================|
	## EVENT ==> MOUSE DOUBLE CLICK
	def eventFilter(self, watched, event):
		if watched == self.le and event.type() == QtCore.QEvent.MouseButtonDblClick:
			print("pos: ", event.pos())

	## EVENT ==> MOUSE CLICK
	# def mousePressEvent(self, event):
	# 	self.dragPos = event.globalPos()
	# 	if event.buttons() == Qt.LeftButton:
	# 		print('Mouse click: LEFT CLICK')
	# 	if event.buttons() == Qt.RightButton:
	# 		print('Mouse click: RIGHT CLICK')
	# 	if event.buttons() == Qt.MidButton:
	# 		print('Mouse click: MIDDLE BUTTON')

	## EVENT ==> KEY PRESSED
	def keyPressEvent(self, event):
		print('Key: ' + str(event.key()) + ' | Text Press: ' + str(event.text()))

	## EVENT ==> RESIZE EVENT
	def resizeEvent(self, event):
		self.resizeFunction()
		return super(MainWindow, self).resizeEvent(event)

	def resizeFunction(self):
		print('Height: ' + str(self.height()) + ' | Width: ' + str(self.width()))
	## END ==> APP EVENTS