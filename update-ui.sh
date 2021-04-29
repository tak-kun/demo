# update .ui file:
pyuic5 -x gui/GUI_BASE.ui -o gui/ui_main.py

#update .qrc file:
pyrcc5 -o files_rc.py gui/files.qrc

echo 'Updated!'
