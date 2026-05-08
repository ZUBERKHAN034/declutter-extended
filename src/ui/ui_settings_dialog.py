# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QRadioButton, QSizePolicy, QSpacerItem,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)
from zeno.ui.widgets import MacComboBox

class Ui_settingsDialog(object):
    def setupUi(self, settingsDialog):
        if not settingsDialog.objectName():
            settingsDialog.setObjectName(u"settingsDialog")
        settingsDialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        settingsDialog.resize(490, 300)
        self.gridLayout = QGridLayout(settingsDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tabWidget = QTabWidget(settingsDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.mainTab = QWidget()
        self.mainTab.setObjectName(u"mainTab")
        self.gridLayout_4 = QGridLayout(self.mainTab)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_2 = QLabel(self.mainTab)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)

        self.ruleExecIntervalEdit = QLineEdit(self.mainTab)
        self.ruleExecIntervalEdit.setObjectName(u"ruleExecIntervalEdit")
        self.ruleExecIntervalEdit.setMaximumSize(QSize(50, 16777215))
        self.ruleExecIntervalEdit.setMaxLength(8)

        self.horizontalLayout.addWidget(self.ruleExecIntervalEdit)

        self.label_3 = QLabel(self.mainTab)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout.addWidget(self.label_3)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")

        self.verticalLayout_5.addLayout(self.horizontalLayout)

        self.scheduleGroupBox = QGroupBox(self.mainTab)
        self.scheduleGroupBox.setObjectName(u"scheduleGroupBox")

        self.scheduleGroupBox.setLayout(self.verticalLayout_5)

        self.verticalLayout_2.addWidget(self.scheduleGroupBox)

        self.geminiGroupBox = QGroupBox(self.mainTab)
        self.geminiGroupBox.setObjectName(u"geminiGroupBox")
        self.verticalLayout_3 = QVBoxLayout(self.geminiGroupBox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.geminiEnableCheckBox = QCheckBox(self.geminiGroupBox)
        self.geminiEnableCheckBox.setObjectName(u"geminiEnableCheckBox")

        self.verticalLayout_3.addWidget(self.geminiEnableCheckBox)

        self.geminiKeyLayout = QHBoxLayout()
        self.geminiKeyLayout.setObjectName(u"geminiKeyLayout")
        self.geminiKeyEdit = QLineEdit(self.geminiGroupBox)
        self.geminiKeyEdit.setObjectName(u"geminiKeyEdit")
        self.geminiKeyEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.geminiKeyEdit.setPlaceholderText("Please Provide a Valid Gemini API Key Here")

        self.geminiKeyLayout.addWidget(self.geminiKeyEdit)

        self.geminiShowHideButton = QPushButton(self.geminiGroupBox)
        self.geminiShowHideButton.setObjectName(u"geminiShowHideButton")
        self.geminiShowHideButton.setCheckable(True)

        self.geminiKeyLayout.addWidget(self.geminiShowHideButton)


        self.verticalLayout_3.addLayout(self.geminiKeyLayout)

        self.geminiModelLayout = QHBoxLayout()
        self.geminiModelLayout.setObjectName(u"geminiModelLayout")

        self.geminiModelCombo = MacComboBox(self.geminiGroupBox)
        self.geminiModelCombo.setObjectName(u"geminiModelCombo")
        self.geminiModelCombo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.geminiModelCombo.setPlaceholderText("Select a Model Here")
        self.geminiModelCombo.addItem("Select a Model Here")

        self.geminiModelLayout.addWidget(self.geminiModelCombo, 3)

        self.geminiTestButton = QPushButton(self.geminiGroupBox)
        self.geminiTestButton.setObjectName(u"geminiTestButton")
        self.geminiTestButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.geminiModelLayout.addWidget(self.geminiTestButton, 1)


        self.verticalLayout_3.addLayout(self.geminiModelLayout)


        self.verticalLayout_2.addWidget(self.geminiGroupBox)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")

        self.startAtLoginCheckBox = QCheckBox(self.mainTab)
        self.startAtLoginCheckBox.setObjectName(u"startAtLoginCheckBox")

        self.verticalLayout_4.addWidget(self.startAtLoginCheckBox)

        self.startupGroupBox = QGroupBox(self.mainTab)
        self.startupGroupBox.setObjectName(u"startupGroupBox")

        self.startupGroupBox.setLayout(self.verticalLayout_4)

        self.verticalLayout_2.addWidget(self.startupGroupBox)

        self.verticalSpacer_2 = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)


        self.gridLayout_4.addLayout(self.verticalLayout_2, 0, 0, 1, 1)

        self.tabWidget.addTab(self.mainTab, "")
        self.dateTab = QWidget()
        self.dateTab.setObjectName(u"dateTab")
        self.gridLayout_2 = QGridLayout(self.dateTab)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.dateDefGroupBox = QGroupBox(self.dateTab)
        self.dateDefGroupBox.setObjectName(u"dateDefGroupBox")
        self.gridLayout_3 = QGridLayout(self.dateDefGroupBox)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.dateDefGroupBox)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.radioButton = QRadioButton(self.dateDefGroupBox)
        self.radioButton.setObjectName(u"radioButton")

        self.verticalLayout.addWidget(self.radioButton)

        self.radioButton_2 = QRadioButton(self.dateDefGroupBox)
        self.radioButton_2.setObjectName(u"radioButton_2")

        self.verticalLayout.addWidget(self.radioButton_2)

        self.radioButton_3 = QRadioButton(self.dateDefGroupBox)
        self.radioButton_3.setObjectName(u"radioButton_3")

        self.verticalLayout.addWidget(self.radioButton_3)

        self.radioButton_4 = QRadioButton(self.dateDefGroupBox)
        self.radioButton_4.setObjectName(u"radioButton_4")

        self.verticalLayout.addWidget(self.radioButton_4)

        self.radioButton_5 = QRadioButton(self.dateDefGroupBox)
        self.radioButton_5.setObjectName(u"radioButton_5")

        self.verticalLayout.addWidget(self.radioButton_5)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.gridLayout_3.addLayout(self.verticalLayout, 0, 0, 1, 1)


        self.gridLayout_2.addWidget(self.dateDefGroupBox, 0, 0, 1, 1)

        self.tabWidget.addTab(self.dateTab, "")
        self.fileTypesTab = QWidget()
        self.fileTypesTab.setObjectName(u"fileTypesTab")
        self.gridLayout_6 = QGridLayout(self.fileTypesTab)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.fileTypesTable = QTableWidget(self.fileTypesTab)
        if (self.fileTypesTable.columnCount() < 2):
            self.fileTypesTable.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.fileTypesTable.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.fileTypesTable.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        self.fileTypesTable.setObjectName(u"fileTypesTable")
        self.fileTypesTable.setColumnCount(2)
        self.fileTypesTable.horizontalHeader().setStretchLastSection(True)
        self.fileTypesTable.verticalHeader().setVisible(False)

        self.gridLayout_6.addWidget(self.fileTypesTable, 0, 0, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.addFileTypeButton = QPushButton(self.fileTypesTab)
        self.addFileTypeButton.setObjectName(u"addFileTypeButton")

        self.horizontalLayout_3.addWidget(self.addFileTypeButton)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.label_5 = QLabel(self.fileTypesTab)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_3.addWidget(self.label_5)


        self.gridLayout_6.addLayout(self.horizontalLayout_3, 1, 0, 1, 1)

        self.tabWidget.addTab(self.fileTypesTab, "")
        self.aboutTab = QWidget()
        self.aboutTab.setObjectName(u"aboutTab")
        self.aboutTabLayout = QVBoxLayout(self.aboutTab)
        self.aboutTabLayout.setObjectName(u"aboutTabLayout")
        self.aboutTopSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.aboutTabLayout.addItem(self.aboutTopSpacer)

        self.aboutLogoLabel = QLabel(self.aboutTab)
        self.aboutLogoLabel.setObjectName(u"aboutLogoLabel")
        self.aboutLogoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.aboutTabLayout.addWidget(self.aboutLogoLabel)

        self.aboutNameLabel = QLabel(self.aboutTab)
        self.aboutNameLabel.setObjectName(u"aboutNameLabel")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.aboutNameLabel.setFont(font)
        self.aboutNameLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.aboutTabLayout.addWidget(self.aboutNameLabel)

        self.aboutVersionLabel = QLabel(self.aboutTab)
        self.aboutVersionLabel.setObjectName(u"aboutVersionLabel")
        self.aboutVersionLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.aboutTabLayout.addWidget(self.aboutVersionLabel)

        self.aboutGithubLabel = QLabel(self.aboutTab)
        self.aboutGithubLabel.setObjectName(u"aboutGithubLabel")
        self.aboutGithubLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aboutGithubLabel.setOpenExternalLinks(True)

        self.aboutTabLayout.addWidget(self.aboutGithubLabel)

        self.aboutBottomSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.aboutTabLayout.addItem(self.aboutBottomSpacer)

        self.tabWidget.addTab(self.aboutTab, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.buttonBox = QDialogButtonBox(settingsDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)


        self.retranslateUi(settingsDialog)
        self.buttonBox.accepted.connect(settingsDialog.accept)
        self.buttonBox.rejected.connect(settingsDialog.reject)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(settingsDialog)
    # setupUi

    def retranslateUi(self, settingsDialog):
        settingsDialog.setWindowTitle(QCoreApplication.translate("settingsDialog", u"Settings", None))
        self.label_2.setText(QCoreApplication.translate("settingsDialog", u"Process rules every", None))
        self.label_3.setText(QCoreApplication.translate("settingsDialog", u"minutes", None))
        self.scheduleGroupBox.setTitle("")
        self.geminiGroupBox.setTitle("")
        self.geminiEnableCheckBox.setText(QCoreApplication.translate("settingsDialog", u"Enable AI Generation", None))
        self.geminiShowHideButton.setText(QCoreApplication.translate("settingsDialog", u"Show", None))
        self.geminiTestButton.setText(QCoreApplication.translate("settingsDialog", u"Test Connection", None))
        self.startAtLoginCheckBox.setText(QCoreApplication.translate("settingsDialog", u"Launch Zeno at login", None))
        self.startupGroupBox.setTitle("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.mainTab), QCoreApplication.translate("settingsDialog", u"Main", None))
        self.dateDefGroupBox.setTitle(QCoreApplication.translate("settingsDialog", u"Date definition", None))
        self.label.setText(QCoreApplication.translate("settingsDialog", u"Which date (from file metadata) should be used in rule conditions?", None))
        self.radioButton.setText(QCoreApplication.translate("settingsDialog", u"earliest of modified && created (default)", None))
        self.radioButton_2.setText(QCoreApplication.translate("settingsDialog", u"modified", None))
        self.radioButton_3.setText(QCoreApplication.translate("settingsDialog", u"created", None))
        self.radioButton_4.setText(QCoreApplication.translate("settingsDialog", u"latest of modified && created", None))
        self.radioButton_5.setText(QCoreApplication.translate("settingsDialog", u"last access", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.dateTab), QCoreApplication.translate("settingsDialog", u"Date", None))
        ___qtablewidgetitem = self.fileTypesTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("settingsDialog", u"Name", None))
        ___qtablewidgetitem1 = self.fileTypesTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("settingsDialog", u"Filemask", None))
        self.addFileTypeButton.setText(QCoreApplication.translate("settingsDialog", u"Add New", None))
        self.label_5.setText(QCoreApplication.translate("settingsDialog", u"To remove a format leave its name empty", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.fileTypesTab), QCoreApplication.translate("settingsDialog", u"File Types", None))
        self.aboutLogoLabel.setText("")
        self.aboutNameLabel.setText(QCoreApplication.translate("settingsDialog", u"Zeno", None))
        self.aboutVersionLabel.setText(QCoreApplication.translate("settingsDialog", u"Version", None))
        self.aboutGithubLabel.setText(QCoreApplication.translate("settingsDialog", u"<a href=\"https://github.com/ZUBERKHAN034/zeno\">View on GitHub</a>", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.aboutTab), QCoreApplication.translate("settingsDialog", u"About", None))
    # retranslateUi

