import numpy as np
import shelve
from copy import deepcopy

from PyQt5 import QtGui, QtWidgets

from .Functions import funcByRef as fref
from .Functions import funcFile as ffile
from .Functions import funcSeqAll as fseq
from .Functions import funcPeakAlign as fpeak
from .Functions import funcGeneral as fGen

from . import myWidgets as my_widgets


class DlgSeqAlign(QtWidgets.QWidget):
    def __init__(self, dProject, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.title = QtWidgets.QLabel(self.tr("<center><b>SEQUENCE ALIGNMENT</b></center>"))
        self.name = "Sequence Alignment"
        self.toolID = 1

        self.dProject = dProject
        self.dProjOut = deepcopy(dProject)

        self.fileReadSeq = my_widgets.DlgSelectFile('Seq. File', "Base Files (*.txt *.fasta *.gbk *.seq )", self.dProject['dir'])
        self.fileReadSeq.lineEdit0.setText(self.dProject['fNameSeq'])
        self.seqRNA3to5 = self.dProjOut['RNA'][::-1]
        self.seqRNA3to5N = fseq.changeNucToN(self.seqRNA3to5, self.dProjOut)
        self.NSeqRNA = len(self.dProjOut['RNA'])

        ###  SEQUENCE FIND
        label0 = QtWidgets.QLabel("Channel")
        label1 = QtWidgets.QLabel("ddNTP")
        label2 = QtWidgets.QLabel('Thres')

        self.comboBox0 = QtWidgets.QComboBox()
        self.comboBox1 = QtWidgets.QComboBox()
        self.comboBox2 = QtWidgets.QComboBox()
        self.comboBox3 = QtWidgets.QComboBox()

        self.spinBox0 = QtWidgets.QDoubleSpinBox()
        self.spinBox0.setRange(-3, 3)
        self.spinBox0.setValue(0.5)
        self.spinBox0.setSingleStep(0.1)

        choices0 = ['BGS1', 'RXS1']
        self.choicesNuc = ['ddC', 'ddG', 'ddA', 'ddT']
        self.nucNames = ['G', 'C', 'U', 'A']

        self.comboBox0.addItems(choices0)
        self.comboBox1.addItems(self.choicesNuc)
        self.comboBox1.setCurrentIndex(self.nucNames.index(self.dProject['nuc1']))

        self.radioSeqFind0 = QtWidgets.QRadioButton('Histogram')
        self.radioSeqFind1 = QtWidgets.QRadioButton('Background')

        layoutMethod = my_widgets.myHBoxLayout()
        layoutMethod.addWidget(self.radioSeqFind0)
        layoutMethod.addWidget(self.radioSeqFind1)

        gridLayout = my_widgets.myGridLayout()

        gridLayout.addWidget(label0, 0, 0)
        gridLayout.addWidget(label1, 0, 1)
        #      gridLayout.addWidget(label2, 0, 2)
        gridLayout.addWidget(self.comboBox0, 1, 0)
        gridLayout.addWidget(self.comboBox1, 1, 1)
        #     gridLayout.addWidget(self.spinBox0, 1, 2)

        if self.dProject['isSeq2']:  # ('RXS2' in self.dInput.keys()) and ('BGS2' in self.dInput.keys()):
            choices2 = ['BGS2', 'RXS2']
            self.comboBox2.addItems(choices2)
            self.comboBox3.addItems(self.choicesNuc)
            self.comboBox3.setCurrentIndex(self.nucNames.index(self.dProject['nuc2']))
            self.spinBox1 = QtWidgets.QDoubleSpinBox()
            self.spinBox1.setRange(-3, 3)
            self.spinBox1.setValue(0.5)
            self.spinBox1.setSingleStep(0.1)
            gridLayout.addWidget(self.comboBox2, 2, 0)
            gridLayout.addWidget(self.comboBox3, 2, 1)
        #    gridLayout.addWidget(self.spinBox1, 2, 2)

        self.checkBox0 = QtWidgets.QCheckBox('Check for high BG peaks')

        self.groupBoxBaseCall = QtWidgets.QGroupBox('Base Calling')
        self.groupBoxBaseCall.setLayout(gridLayout)
        self.groupBoxBaseCall.setCheckable(True)

        ##  LAYOUTS
        labelSetting2 = QtWidgets.QLabel("Seq Range: From")
        labelSetting3 = QtWidgets.QLabel("To:")
        labelSetting4 = QtWidgets.QLabel("Seq Start: ")

        self.spinBoxSeqRangeFrom = QtWidgets.QSpinBox()
        self.spinBoxSeqRangeTo = QtWidgets.QSpinBox()
        try:
            self.setSpinBoxSeq()
        except:
            pass
        self.spinBoxSeqOffset = QtWidgets.QSpinBox()
        self.spinBoxSeqOffset.setRange(0, len(self.dProject['RNA']))

        self.checkBoxLineDraw = QtWidgets.QCheckBox('Draw peak match lines')
        self.checkBoxLineDraw.setChecked(True)
        layoutSetting = my_widgets.myGridLayout()
        layoutSetting.addWidget(labelSetting2, 0, 0)
        layoutSetting.addWidget(self.spinBoxSeqRangeFrom, 0, 1)
        layoutSetting.addWidget(labelSetting3, 0, 2)
        layoutSetting.addWidget(self.spinBoxSeqRangeTo, 0, 3)
        #       layoutSetting.addWidget(self.checkBoxLineDraw, 1, 0, 1, 2)

        self.groupBoxSettings = QtWidgets.QGroupBox('Settings')
        self.groupBoxSettings.setLayout(layoutSetting)

        text = "HINT: Click a Nuc to change the type. \
                Press Key 'A' button and click to add a Nuc.\
                Press Key 'D' button and click to delete a Nuc. \
                Press Key 'Shift' button and select a peak to change position. "

        self.hint = my_widgets.my_widgets.hintLabel(text)

        # self.connect(self.fileReadSeq.pushButton0, QtCore.SIGNAL("clicked()"), self.changeSeqFile)
        self.fileReadSeq.pushButton0.clicked.connect(self.changeSeqFile)

        self.buttonBox = my_widgets.ToolButton()

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.title)
        mainLayout.addWidget(self.fileReadSeq)
        mainLayout.addWidget(self.groupBoxBaseCall)
        mainLayout.addWidget(self.groupBoxSettings)
        mainLayout.addWidget(self.hint)
        mainLayout.addStretch()
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
        self.isToolApplied = False

    def apply(self):
        if self.groupBoxBaseCall.isChecked():
            self.dProjOut['dData'] = fGen.equalLen(self.dProject['dData'])
            self.applySeqFindFunc()
            self.groupBoxBaseCall.setChecked(False)

            start = self.NSeqRNA - self.spinBoxSeqRangeFrom.value()
            end = self.NSeqRNA - self.spinBoxSeqRangeTo.value()
            self.dProjOut = fseq.applySeqAlign(self.dProjOut, self.seqRNA3to5N, start, end)
            alignedSeqRNA, alignedSeq, newSeqX, startNucI, endNucI = fseq.shapeSeqAlign(self.dProjOut, self.seqRNA3to5N[start:end])

            newSeqX, newSeq = fseq.nucAddDelete(alignedSeqRNA, alignedSeq, newSeqX)

            startNucI = startNucI + start
            endNucI = startNucI + len(newSeqX)
            self.dProjOut['start'] = self.NSeqRNA - startNucI
            self.dProjOut['end'] = self.dProjOut['start'] - len(newSeqX)
            self.dProjOut['seqX'] = np.array(newSeqX, int)
            self.dProjOut['seqX0'] = np.array(newSeqX, int)
            self.dProjOut['seq0'] = newSeq
            self.dProjOut['seqRNA'] = self.dProjOut['RNA'][::-1][startNucI:endNucI]
            self.dProjOut['seqNum'] = np.arange(self.dProjOut['start'], self.dProjOut['end'], -1)
            self.spinBoxSeqRangeFrom.setValue((self.dProjOut['start'] + 10))
            self.spinBoxSeqRangeTo.setValue((self.dProjOut['end'] - 10))

            self.dProjOut = fpeak.peakListAll(self.dProjOut, ['RX', 'BG'])
            self.dProjOut['dPeakBG'], self.controlRX = fpeak.peakLinking(self.dProjOut['seqX'], self.dProjOut['dPeakBG'], self.dProjOut['dData']['BG'])
            self.dProjOut['dPeakRX'], self.controlBG = fpeak.peakLinking(self.dProjOut['dPeakBG']['pos'], self.dProjOut['dPeakRX'],
                                                                   self.dProjOut['dData']['RX'])
        else:
            self.applyFastSeqAlign()
        self.isToolApplied = True

    def applyFastSeqAlign(self):
        s = self.NSeqRNA - self.spinBoxSeqRangeFrom.value()
        e = self.NSeqRNA - self.spinBoxSeqRangeTo.value()
        startNucI = fseq.seqAlignFast(self.seqRNA3to5N[s:e], self.dProjOut['seq0'])
        startNucI = startNucI + s
        self.NSeq0 = len(self.dProjOut['seq0'])
        endNucI = startNucI + self.NSeq0
        self.dProjOut['start'] = self.NSeqRNA - startNucI
        self.dProjOut['end'] = self.NSeqRNA - endNucI
        self.dProjOut['seqRNA'] = self.dProjOut['RNA'][::-1][startNucI:endNucI]
        self.dProjOut['seqNum'] = np.arange(self.dProjOut['start'], self.dProjOut['end'], -1)
        self.dProjOut['seqX'] = self.dProjOut['seqX0']
        self.spinBoxSeqRangeFrom.setValue((self.dProjOut['start'] + 10))
        self.spinBoxSeqRangeTo.setValue((self.dProjOut['end'] - 10))

    def applySeqFindFunc(self):
        self.dProjOut['ddNTP1'] = str(self.comboBox1.currentText())
        self.dProjOut['nuc1'] = self.nucNames[self.comboBox1.currentIndex()]
        if self.dProjOut['isSeq2']:
            self.dProjOut['ddNTP2'] = str(self.comboBox3.currentText())
            self.dProjOut['nuc2'] = self.nucNames[self.comboBox3.currentIndex()]

        t1 = self.spinBox0.value()
        keyS1 = str(self.comboBox0.currentText())

        if self.dProjOut['isSeq2']:
            t2 = self.spinBox1.value()
            keyS2 = str(self.comboBox2.currentText())
        else:
            keyS2 = 'BGS2'
            t2 = 0.5

        #   self.dProjOut=seqAlignAllNew(self.dProjOut, keyS1, keyS2)
        #   self.dProjOut=seqFindWithBG(self.dProjOut, keyS1, t1, keyS2, t2)
        self.dProjOut = fseq.seqFindFinal0(self.dProjOut, keyS1, keyS2)

    #  self.dProjOut['seq0'], self.dProjOut['seqX0']=seqFindNorm(self.dProjOut, keyS1, t1, keyS2, t2)

    #     self.dProjOut['seq0'], self.dProjOut['seqX0']=seqFindLast(self.dProjOut, keyS1, t1, keyS2, t2)

    def changeSeqFile(self):
        self.dProjOut['fNameSeq'] = str(self.fileReadSeq.lineEdit0.text())
        self.dProjOut['RNA'] = ffile.readBaseFile(self.dProjOut['fNameSeq'])
        self.seqRNA3to5 = self.dProjOut['RNA'][::-1]
        self.seqRNA3to5N = fseq.changeNucToN(self.seqRNA3to5, self.dProjOut)
        self.NSeqRNA = len(self.seqRNA3to5)
        self.setSpinBoxSeq()

    def setSpinBoxSeq(self):
        self.spinBoxSeqRangeFrom.setRange(0, len(self.dProjOut['RNA']))
        self.spinBoxSeqRangeFrom.setValue(len(self.dProjOut['RNA']))
        self.spinBoxSeqRangeTo.setRange(0, len(self.dProjOut['RNA']))


class DlgReactivity(QtWidgets.QWidget):
    def __init__(self, dProject, dProjRef, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.labelTitle = QtWidgets.QLabel(self.tr("<center><b>REACTIVITY</b></center>"))
        self.name = "Reactivity"
        self.toolID = 1

        self.dProject = dProject
        self.dProjRef = dProjRef
        self.dProjOut = deepcopy(self.dProject)

        self.scaleFactor = 1

        self.checkBox0 = QtWidgets.QCheckBox('Scale and Normalize with Reference')

        ## SCALE
        self.groupBox1 = my_widgets.scaleGroupBox("Scale BG")

        ## NORMALIZATION
        label0 = QtWidgets.QLabel('Outlier')
        label1 = QtWidgets.QLabel('Average')
        self.spinBox0 = QtWidgets.QDoubleSpinBox()
        self.spinBox1 = QtWidgets.QDoubleSpinBox()
        self.spinBox0.setRange(0, 9)
        self.spinBox1.setRange(0, 15)
        self.spinBox0.setSuffix("%")
        self.spinBox1.setSuffix("%")
        self.spinBox0.setSingleStep(0.25)
        self.spinBox1.setSingleStep(0.25)
        self.spinBox0.setValue(2.0)
        self.spinBox1.setValue(10.0)

        self.checkBox1 = QtWidgets.QCheckBox("Set Negative Value to Zero")

        layout2 = my_widgets.myHBoxLayout()
        layout2.addWidget(label0)
        layout2.addWidget(self.spinBox0)
        #  layout2.addWidget(label1)
        #  layout2.addWidget(self.spinBox1)

        layout21 = my_widgets.myVBoxLayout()
        #   layout21.addWidget(self.radioNormCluster)
        layout21.addLayout(layout2)
        layout21.addWidget(self.checkBox1)

        self.groupBox2 = QtWidgets.QGroupBox(self.tr('Normalization'))
        self.groupBox2.setLayout(layout21)
        #   self.groupBox2.setEnabled(False)

        self.radio3to5 = QtWidgets.QRadioButton("3' to 5'")
        self.radio5to3 = QtWidgets.QRadioButton("5' to 3'")
        self.radio3to5.setChecked(True)

        self.pushButton0 = QtWidgets.QPushButton('Reactivity')
        self.pushButton1 = QtWidgets.QPushButton('Peak Area')
        self.pushButton2 = QtWidgets.QPushButton('Data')

        layout3 = my_widgets.myGridLayout()
        layout3.addWidget(self.radio3to5, 0, 0)
        layout3.addWidget(self.radio5to3, 0, 1)
        layout3.addWidget(self.pushButton0, 1, 0)
        layout3.addWidget(self.pushButton1, 1, 1)
        layout3.addWidget(self.pushButton2, 1, 3)

        self.groupBox3 = QtWidgets.QGroupBox(self.tr('Select Plot Type'))
        self.groupBox3.setLayout(layout3)
        #    self.groupBox3.setEnabled(False)

        self.buttonBox = my_widgets.ToolButton()

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.labelTitle)
        mainLayout.addWidget(self.groupBox1)
        mainLayout.addWidget(self.groupBox2)
        mainLayout.addWidget(self.groupBox3)

        mainLayout.addStretch()
        mainLayout.addWidget(self.buttonBox)

        self.setLayout(mainLayout)
        self.isToolApplied = False

    #   self.initialize()

    def initialize(self):
        self.dProjOut1 = deepcopy(self.dProject)
        self.dProjOut1['dPeakRX'] = fseq.fitShapeData(self.dProjOut1['dPeakRX'], self.dProjOut1['dData']['RX'])
        self.dProjOut1['dPeakBG'] = fseq.fitShapeData(self.dProjOut1['dPeakBG'], self.dProjOut1['dData']['BG'])

        self.scaleFactor = fseq.scaleShapeData(self.dProjOut1['dPeakRX']['amp'], self.dProjOut1['dPeakBG']['amp'])
        self.groupBox1.doubleSpinBox0.setValue(self.scaleFactor)

        self.dProjOut1['areaDiff'] = self.dProjOut1['dPeakRX']['area'] - self.dProjOut1['dPeakBG']['area'] * self.scaleFactor
        self.POutlier, self.PAver = fseq.findPOutlierBox(self.dProjOut1['areaDiff'])

        self.spinBox0.setValue(self.POutlier)
        self.spinBox1.setValue(self.PAver)

        if len(self.dProjOut1['dPeakRX']['amp']) > 160:
            self.groupBox1.checkBoxScale0.setChecked(True)

    def apply(self):
        self.dProjOut = deepcopy(self.dProjOut1)
        scaleFactorData = 1
        if self.groupBox1.checkBoxScale0.isChecked():
            scaleFactor = fseq.scaleShapeDataWindow(self.dProjOut['dPeakRX']['amp'], self.dProjOut['dPeakBG']['amp'], deg=40, rate=0.25, step=10,
                                               fit='linear')
            scaleFactorData = fseq.fitLinear(self.dProjOut['dPeakBG']['pos'], scaleFactor, NData=len(self.dProjOut['dData']['BG']))
        else:
            scaleFactor = float(self.groupBox1.doubleSpinBox0.value())
            scaleFactorData = scaleFactor

        self.dProjOut['areaDiff'] = self.dProjOut['dPeakRX']['area'] - self.dProjOut['dPeakBG']['area'] * scaleFactor
        self.POutlier = self.spinBox0.value()
        self.PAver = self.spinBox1.value()

        self.dProjOut['normDiff'], aver = fseq.normSimple(self.dProjOut['areaDiff'], self.POutlier, self.PAver)
        if self.checkBox1.isChecked():
            self.dProjOut['normDiff'] = fGen.setNegToZero(self.dProjOut['normDiff'])

        self.dProjOut['scaleFactor'] = np.array([scaleFactor])
        self.dProjOut['dPeakBG']['area'] = self.dProjOut['dPeakBG']['area'] * scaleFactor
        self.dProjOut['dPeakBG']['amp'] = self.dProjOut['dPeakBG']['amp'] * scaleFactor
        self.dProjOut['dData']['BG'] = self.dProjOut['dData']['BG'] * scaleFactorData

        self.isToolApplied = True


class DlgReportTable(QtWidgets.QWidget):
    def __init__(self, dProject, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.labelTitle = QtWidgets.QLabel(self.tr("<center><b>REPORT</b></center>"))
        self.name = "Report"
        self.toolID = 1

        self.dProject = dProject
        self.dReport = fseq.createDReport(dProject)

        for key in self.dReport.keys():
            self.dReport[key] = self.dReport[key][::-1]

        self.saveTextButton = QtWidgets.QPushButton("Save as Text")

        # self.connect(self.saveTextButton, QtCore.SIGNAL('clicked()'), self.saveTextReport)
        self.saveTextButton.clicked.connect(self.saveTextReport)

        self.layout0 = QtWidgets.QHBoxLayout()
        self.layout0.addWidget(self.saveTextButton)
        self.layout0.addStretch()

        N = len(self.dReport['seqNum'])
        self.table = QtWidgets.QTableWidget()
        self.table.setRowCount(N)
        self.table.setColumnCount(len(fseq.reportKeys))
        self.table.setHorizontalHeaderLabels(fseq.reportKeys)
        self.table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.table.setSelectionMode(QtWidgets.QTableWidget.SingleSelection)
        self.font = QtGui.QFont()
        self.font.setPointSize(9)
        self.table.setFont(self.font)

        for i in range(N):
            for key in fseq.reportKeys:
                if key == 'seqRNA':
                    item = QtWidgets.QTableWidgetItem(self.dReport[key][i])
                elif key in ['seqNum', 'posSeq', 'posRX', 'posBG']:
                    item = QtWidgets.QTableWidgetItem("%d" % self.dReport[key][i])
                else:
                    item = QtWidgets.QTableWidgetItem("%.2f" % self.dReport[key][i])
                col = fseq.reportKeys.index(key)
                self.table.setItem(int(i), int(col), item)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.labelTitle)
        mainLayout.addWidget(self.table)
        mainLayout.addLayout(self.layout0)
        self.setLayout(mainLayout)

    def saveTextReport(self):
        fName = QtWidgets.QFileDialog.getSaveFileName(self, "Save As", self.dProject['dir'])
        if fName:
            fName = str(fName) + '.txt'
            fseq.writeReportFile(self.dReport, fName)


class DlgSeqAlignRef(QtWidgets.QWidget):
    def __init__(self, dProject, dProjRef, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.title = QtWidgets.QLabel(self.tr("<center><b>SEQUENCE ALIGNMENT BY REFERENCE</b></center>"))
        self.name = "Sequence Alignment by Reference"
        self.toolID = 1

        self.dProject = dProject
        self.dProjRef = dProjRef
        self.linkXR, self.linkXS = np.array([]), np.array([])
        self.linkYR, self.linkYS = np.array([]), np.array([])
        self.dataR, self.dataS = np.array([]), np.array([])

        #### BY REFERENCE
        self.fileReadRef = my_widgets.DlgSelectFile('Ref. Proj.', "Reference Project (*.pyShape *.qushape)", self.dProject['dir'])
        if 'fNameRef' in self.dProject.keys():
            self.fileReadRef.lineEdit0.setText(self.dProject['fNameRef'])
        # self.connect(self.fileReadRef.pushButton0, QtCore.SIGNAL("clicked()"), self.changeRefFile)
        self.fileReadRef.pushButton0.clicked.connect(self.changeRefFile)

        label10 = QtWidgets.QLabel("Ref. Channel")
        self.comboBox10 = QtWidgets.QComboBox()
        self.comboBox10.addItems(fGen.chKeysRS)
        self.comboBox10.setCurrentIndex(3)

        label11 = QtWidgets.QLabel("Sample Channel")
        self.comboBox11 = QtWidgets.QComboBox()
        self.comboBox11.addItems(fGen.chKeysRS)
        self.comboBox11.setCurrentIndex(3)

        layout0 = my_widgets.myGridLayout()
        layout0.addWidget(self.fileReadRef, 0, 0, 1, 2)
        layout0.addWidget(label10, 1, 0)
        layout0.addWidget(self.comboBox10, 1, 1)
        layout0.addWidget(label11, 2, 0)
        layout0.addWidget(self.comboBox11, 2, 1)

        self.groupBox0 = QtWidgets.QGroupBox(self.tr('Signal Alignment'))
        self.groupBox0.setLayout(layout0)
        self.groupBox0.setCheckable(True)

        labelRX = QtWidgets.QLabel('Scale Factor for RX')
        labelBG = QtWidgets.QLabel('Scale Factor for BG')
        self.spinBoxRX = QtWidgets.QDoubleSpinBox()
        self.spinBoxRX.setRange(0.01, 100.00)
        self.spinBoxRX.setValue(1.00)
        self.spinBoxRX.setSingleStep(0.01)
        self.spinBoxBG = QtWidgets.QDoubleSpinBox()
        self.spinBoxBG.setRange(0.01, 100.00)
        self.spinBoxBG.setValue(1.00)
        self.spinBoxBG.setSingleStep(0.01)

        self.checkBoxScale0 = QtWidgets.QCheckBox('Scale by windowing')

        layout1 = my_widgets.myGridLayout()
        layout1.addWidget(labelRX, 0, 0)
        layout1.addWidget(self.spinBoxRX, 0, 1)
        layout1.addWidget(labelBG, 1, 0)
        layout1.addWidget(self.spinBoxBG, 1, 1)
        layout1.addWidget(self.checkBoxScale0, 2, 0, 1, 2)

        self.groupBox1 = QtWidgets.QGroupBox(self.tr('Scale RX and BG'))
        self.groupBox1.setLayout(layout1)
        # self.groupBox1.setCheckable(True)

        #  self.button0=QtWidgets.QPushButton('Modify Matched Peaks')
        #  self.button0.setEnabled(False)

        self.button0 = my_widgets.peakMatchModifyButton()

        self.button1 = QtWidgets.QPushButton('Modify Peak Link by Reference')
        self.button1.setEnabled(False)
        self.button1.setWhatsThis(self.tr(" Check the accuracy of linked peaks"
                                          " by C\changing the peak position in the sample RX and BG peaks."
                                          " Press Key 'Shift' button and select a sample peak to change position. "
                                          ))
        text = self.tr(
            "HINT: When the matched peaks are modified; Key 'A'  to add a Peak. Key 'D'  to delete a Peak. Key 'Shift' to change position. ")
        self.hint = my_widgets.hintLabel(text)

        ### BUTTON BOX
        self.buttonBox = my_widgets.ToolButton()

        ## MAIN LAYOUT
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.title)
        mainLayout.addWidget(self.groupBox0)
        mainLayout.addWidget(self.button0)
        mainLayout.addWidget(self.button1)
        mainLayout.addWidget(self.hint)
        mainLayout.addStretch()
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
        self.isClickedModifyMatchedPeaks = True
        self.isToolApplied = False
        self.isMatchedPeaksChanged = True

    def apply(self):
        if self.dProject['fNameRef'] == '':
            msg = "Select a Reference Project"
            QtWidgets.QMessageBox.warning(self, "QuShape - ", msg)
            return

        if self.groupBox0.isChecked():
            self.keyR = str(self.comboBox10.currentText())
            self.keyS = str(self.comboBox11.currentText())
            self.dataR = self.dProjRef['dData'][self.keyR]
            self.dataS = self.dProject['dData'][self.keyS]
            self.linkXR, self.linkXS = fseq.seqAlignRef(self.dProjRef, self.dProject, self.keyR, self.keyS)
            self.groupBox0.setChecked(False)
            self.button0.setEnabled(True)
            self.isMatchedPeaksChanged = True

        if self.isMatchedPeaksChanged:
            self.dProjOut = deepcopy(self.dProject)
            NDataR = len(self.dataR)
            for key in self.dProjOut['chKeyRS']:
                self.dProjOut['dData'][key] = fpeak.splineSampleData(self.dProject['dData'][key], self.dataR, self.linkXR, self.linkXS, False)
            self.linkYR = self.dataR[self.linkXR]
            self.linkYS = self.dataS[self.linkXS]

            self.dProjOut = fref.postSeqAlignRef(self.dProjRef, self.dProjOut)
            self.dProjOut['dPeakRX'] = fpeak.fPeakList(self.dProjOut['dData']['RX'])
            self.dProjOut['dPeakBG'] = fpeak.fPeakList(self.dProjOut['dData']['BG'])
            self.dProjOut['dPeakBG'], self.controlRX = fseq.peakLinking(self.dProjRef['dPeakBG']['pos'], self.dProjOut['dPeakBG'],
                                                                        self.dProjOut['dData']['BG'])
            self.dProjOut['dPeakRX'], self.controlBG = fseq.peakLinking(self.dProjRef['dPeakRX']['pos'], self.dProjOut['dPeakRX'],
                                                                        self.dProjOut['dData']['RX'])
            self.button1.setEnabled(True)
            self.isMatchedPeaksChanged = False
        self.isToolApplied = True

    def changeRefFile(self):
        self.fName = str(self.fileReadRef.lineEdit0.text())
        if self.fName != '':
            self.dBase = shelve.open(str(self.fName))
            self.dProjRef = self.dBase['dProject']
            self.dProject['fNameRef'] = str(self.fName)


class DlgReactivityRef(QtWidgets.QWidget):
    def __init__(self, dProject, dProjRef, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.title = QtWidgets.QLabel(self.tr("<center><b>REACTIVITY BY REFERENCE</b></center>"))
        self.name = "Reactivity by Reference"
        self.toolID = 1

        self.dProject = dProject
        self.dProjOut = deepcopy(dProject)
        self.dProjRef = dProjRef
        self.isToolApplied = False

        ### SCALE RX
        self.groupBox0 = my_widgets.scaleGroupBox("Scale RX")
        ### SCALE BG
        self.groupBox1 = my_widgets.scaleGroupBox("Scale BG")
        ### SCALE REACTIVITY
        self.groupBox2 = my_widgets.scaleGroupBox("Scale Reactivity")

        self.pushButton0 = QtWidgets.QPushButton('Reactivity')
        self.pushButton1 = QtWidgets.QPushButton('Peak Area')
        self.pushButton2 = QtWidgets.QPushButton('Data')

        layout3 = my_widgets.myGridLayout()
        layout3.addWidget(self.pushButton0, 1, 0)
        layout3.addWidget(self.pushButton1, 1, 1)
        layout3.addWidget(self.pushButton2, 1, 3)

        self.groupBox3 = QtWidgets.QGroupBox(self.tr('Select Plot Type'))
        self.groupBox3.setLayout(layout3)

        ### BUTTON BOX
        self.buttonBox = my_widgets.ToolButton()
        ## MAIN LAYOUT
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.title)
        mainLayout.addWidget(self.groupBox0)
        mainLayout.addWidget(self.groupBox1)
        mainLayout.addWidget(self.groupBox2)
        mainLayout.addWidget(self.groupBox3)

        mainLayout.addStretch()
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
        self.isClickedApply = False

    def initialize(self):
        self.dProjOut1 = deepcopy(self.dProject)

        self.dProjOut1['dPeakRX'] = fseq.fitShapeData(self.dProjOut1['dPeakRX'], self.dProjOut1['dData']['RX'])
        self.dProjOut1['dPeakBG'] = fseq.fitShapeData(self.dProjOut1['dPeakBG'], self.dProjOut1['dData']['BG'])

        self.scaleFactor0 = fseq.scaleShapeData(self.dProjRef['dPeakRX']['area'], self.dProjOut1['dPeakRX']['area'], rate=1)
        self.groupBox0.doubleSpinBox0.setValue(self.scaleFactor0)

        self.scaleFactor1 = fseq.scaleShapeData(self.dProjRef['dPeakBG']['area'], self.dProjOut1['dPeakBG']['area'], rate=1)
        self.groupBox1.doubleSpinBox0.setValue(self.scaleFactor1)

        areaDiff = self.dProjOut1['dPeakRX']['area'] * self.scaleFactor0 - self.dProjOut1['dPeakBG']['area'] * self.scaleFactor1
        self.POutlier, self.PAver = fseq.findPOutlierBox(areaDiff)
        normDiff, aver = fseq.normSimple(areaDiff, self.POutlier, self.PAver)

        self.scaleFactor2 = fseq.scaleShapeData(self.dProjRef['normDiff'], normDiff, rate=1)
        self.groupBox2.doubleSpinBox0.setValue(self.scaleFactor2)

    def apply(self):
        self.dProjOut = deepcopy(self.dProjOut1)
        if self.groupBox0.checkBoxScale0.isChecked():
            self.scaleFactor0 = fseq.scaleShapeDataWindow(self.dProjRef['dPeakRX']['area'], self.dProjOut1['dPeakRX']['area'])
            scaleFactorData0 = fGen.fitLinear(self.dProjOut1['dPeakRX']['pos'], self.scaleFactor0, NData=len(self.dProjOut1['dData']['RX']))
        else:
            self.scaleFactor0 = float(self.groupBox0.doubleSpinBox0.value())
            scaleFactorData0 = self.scaleFactor0

        self.dProjOut['dPeakRX']['area'] = self.dProjOut1['dPeakRX']['area'] * self.scaleFactor0
        self.dProjOut['dPeakRX']['amp'] = self.dProjOut1['dPeakRX']['amp'] * self.scaleFactor0
        self.dProjOut['dData']['RX'] = self.dProjOut1['dData']['RX'] * scaleFactorData0

        if self.groupBox1.checkBoxScale0.isChecked():
            self.scaleFactor1 = fseq.scaleShapeDataWindow(self.dProjRef['dPeakBG']['area'], self.dProjOut1['dPeakBG']['area'])
            scaleFactorData1 = fGen.fitLinear(self.dProjOut1['dPeakBG']['pos'], self.scaleFactor1, NData=len(self.dProjOut1['dData']['BG']))
        else:
            self.scaleFactor1 = float(self.groupBox1.doubleSpinBox0.value())
            scaleFactorData1 = self.scaleFactor1

        self.dProjOut['dPeakBG']['area'] = self.dProjOut1['dPeakBG']['area'] * self.scaleFactor1
        self.dProjOut['dPeakBG']['amp'] = self.dProjOut1['dPeakBG']['amp'] * self.scaleFactor1
        self.dProjOut['dData']['BG'] = self.dProjOut1['dData']['BG'] * scaleFactorData1

        self.dProjOut['areaDiff'] = self.dProjOut['dPeakRX']['area'] - self.dProjOut['dPeakBG']['area']
        self.POutlier, self.PAver = fseq.findPOutlierBox(self.dProjOut['areaDiff'])
        self.dProjOut['normDiff'], aver = fseq.normSimple(self.dProjOut['areaDiff'], self.POutlier, self.PAver)
        if self.groupBox2.checkBoxScale0.isChecked():
            self.scaleFactor2 = fseq.scaleShapeDataWindow(self.dProjRef['normDiff'], self.dProjOut['normDiff'])
        else:
            self.scaleFactor2 = float(self.groupBox2.doubleSpinBox0.value())
        self.dProjOut['normDiff'] = self.dProjOut['normDiff'] * self.scaleFactor2
        self.isToolApplied = True


class DlgApplyAutoRef(QtWidgets.QWidget):
    def __init__(self, dProject, dProjRef, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.title = QtWidgets.QLabel(self.tr("<center><b>AUTOMATED ANALYSIS BY REFERENCE</b></center>"))
        self.name = "Automated by Reference"
        self.toolID = 1

        self.dProject = dProject
        self.dProjOut = deepcopy(dProject)
        self.dProjRef = dProjRef
        self.isToolApplied = False

        self.checkBox0 = QtWidgets.QCheckBox("Tools")
        self.checkBox1 = QtWidgets.QCheckBox("Sequence Alignment")
        self.checkBox0.setChecked(True)
        self.checkBox1.setChecked(True)

        self.pushButton0 = QtWidgets.QPushButton('Reactivity')
        self.pushButton1 = QtWidgets.QPushButton('Peak Area')
        self.pushButton2 = QtWidgets.QPushButton('Data')

        layout3 = my_widgets.myGridLayout()
        layout3.addWidget(self.checkBox0, 1, 0, 1, 3)
        layout3.addWidget(self.checkBox1, 2, 0, 1, 3)
        layout3.addWidget(self.pushButton0, 3, 0)
        layout3.addWidget(self.pushButton1, 3, 1)
        layout3.addWidget(self.pushButton2, 3, 3)

        self.groupBox3 = QtWidgets.QGroupBox(self.tr('Select Plot Type'))
        self.groupBox3.setLayout(layout3)

        ### BUTTON BOX
        self.buttonBox = my_widgets.ToolButton()
        ## MAIN LAYOUT
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.title)
        mainLayout.addWidget(self.groupBox3)
        mainLayout.addStretch()
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)

    def apply(self):
        self.dProjOut = deepcopy(self.dProject)
        if self.checkBox0.isChecked():
            self.dProjOut = fref.applyAllToolsAuto1(self.dProject, self.dProjRef)
        if self.checkBox1.isChecked():
            self.dProjOut = fref.applyAllSeq(self.dProjOut, self.dProjRef)
        self.isToolApplied = True
