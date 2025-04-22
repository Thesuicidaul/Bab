from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

import maya.OpenMayaUI as mui
import shiboken2
import maya.cmds as cmds

# Fonction pour obtenir la fenêtre principale de Maya

def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken2.wrapInstance(int(ptr), QWidget)
    return None

# Classe principale pour la fenêtre de l'outil

class BaB(QDialog):
    def __init__(self):
        super(BaB, self).__init__(getMayaWindow(), Qt.Window)
        self.setWindowTitle("BaB Hugo")
        self.setMinimumSize(300, 200)
        self.initUI()
        self.show()

    # Initialisation de l'interface utilisateur
    def initUI(self):
        self.stack = QStackedWidget()
        self.mainWidget = QWidget()
        self.contrainteWidget = QWidget()

        self.initMainUI()
        self.initContrainteUI()

        self.stack.addWidget(self.mainWidget)
        self.stack.addWidget(self.contrainteWidget)

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

    # Interface principale
    def initMainUI(self):
        layout = QVBoxLayout(self.mainWidget)

        title_label = QLabel("Outils")
        title_label.setAlignment(Qt.AlignCenter)
        font = title_label.font()
        font.setPointSize(12)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setFixedHeight(2)
        layout.addWidget(separator)

        # Boutons pour les outils NPO, CPD, et CTS
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignLeft)
        npo_button = QPushButton("NPO")
        cts_button = QPushButton("CTS")
        pivot_button.setFixedSize(80, 30)
        button_layout.addWidget(npo_button)
        button_layout.addWidget(cts_button)
        button_layout.addStretch()
        button_layout.addWidget(pivot_button, alignment=Qt.AlignCenter)
        layout.addLayout(button_layout)

        # Menu pour créer des courbes
        curve_layout = QHBoxLayout()
        curve_layout.setAlignment(Qt.AlignLeft)
        curve_menu = QComboBox()
        curve_menu.addItem("Sélectionner une forme")
        curve_menu.addItem("Cercle")
        curve_menu.addItem("Carré")
        curve_menu.setFixedSize(120, 30)
        create_curve_button = QPushButton("Créer")
        create_curve_button.setFixedSize(80, 30)
        curve_layout.addWidget(curve_menu)
        curve_layout.addWidget(create_curve_button)
        layout.addLayout(curve_layout)

        # Connexion des boutons
        cts_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.contrainteWidget))
        npo_button.clicked.connect(self.MainNpo)
        create_curve_button.clicked.connect(lambda: self.createCurve(curve_menu.currentText()))
        pivot_button.clicked.connect(self.createDynamicPivot)

    # Interface pour les contraintes
    def initContrainteUI(self):
        layout = QVBoxLayout(self.contrainteWidget)

        back_button = QPushButton("Retour")
        back_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.mainWidget))
        layout.addWidget(back_button)

        desc_label1 = QLabel("Réalisation d'une contrainte pour tous les objets sélectionnés")
        layout.addWidget(desc_label1)

        desc_label2 = QLabel("Le dernier objet sélectionné est le Driver")
        layout.addWidget(desc_label2)

        self.with_offset_checkbox = QCheckBox("With Offset")
        layout.addWidget(self.with_offset_checkbox)

        checkboxes_layout = QHBoxLayout()
        checkboxes_layout.setAlignment(Qt.AlignLeft)
        self.scale_checkbox = QCheckBox("Scale")
        self.rotation_checkbox = QCheckBox("Rotation")
        self.translation_checkbox = QCheckBox("Translation")
        checkboxes_layout.addWidget(self.scale_checkbox)
        checkboxes_layout.addWidget(self.rotation_checkbox)
        checkboxes_layout.addWidget(self.translation_checkbox)
        layout.addLayout(checkboxes_layout)

        create_cst_button = QPushButton("Créer CST")
        create_cst_button.clicked.connect(self.createCst)
        layout.addWidget(create_cst_button)

    

    # Fonction pour créer une contrainte
    def createCst(self):
        sel = cmds.ls(selection=True)
        if len(sel) < 2:
            cmds.warning("Sélectionner au moins deux objets.")
            return
    
        driver = sel[-1]
    
        for driven in sel[:-1]:
            # Créer le multMatrix principal
            mult_node = cmds.createNode('multMatrix', name=f'{driven}_multMatrix')
            decomp_node = cmds.createNode('decomposeMatrix', name=f'{driven}_decomposeMatrix')
    
            # Si l'option "With Offset" est cochée, on calcule l'offset
            if self.with_offset_checkbox.isChecked():
                cmds.addAttr(mult_node, longName="offset_mat", attributeType="matrix")
                
                # Créer un second multMatrix pour calculer l'offset
                offset_mult = cmds.createNode('multMatrix', name=f'{driven}_offset_multMatrix')
    
                # Connecter les matrices pour obtenir la différence entre le driven et le driver
                cmds.connectAttr(f'{driven}.worldMatrix[0]', f'{offset_mult}.matrixIn[0]')
                cmds.connectAttr(f'{driver}.worldInverseMatrix[0]', f'{offset_mult}.matrixIn[1]')
    
                # Stocker l'offset dans l’attribut "offset_mat"
                cmds.connectAttr(f'{offset_mult}.matrixSum', f'{mult_node}.offset_mat')
    
                # Récupérer la valeur et la stocker définitivement
                offset_matrix = cmds.getAttr(f'{mult_node}.offset_mat')
    
                # Déconnecter et supprimer le node temporaire
                cmds.disconnectAttr(f'{offset_mult}.matrixSum', f'{mult_node}.offset_mat')
                cmds.delete(offset_mult)
    
                # Appliquer l'offset à l'entrée de la matrice
                cmds.setAttr(f'{mult_node}.matrixIn[0]', offset_matrix, type="matrix")
    
                index = 1  # Décalage des indices pour les autres connexions
            else:
                index = 0  # Aucune transformation d'offset
    
            # Connexions principales
            cmds.connectAttr(f'{driver}.worldMatrix[0]', f'{mult_node}.matrixIn[{index}]')
            cmds.connectAttr(f'{driven}.parentInverseMatrix[0]', f'{mult_node}.matrixIn[{index + 1}]')
            cmds.connectAttr(f'{mult_node}.matrixSum', f'{decomp_node}.inputMatrix')
    
            # Connexion des transformations en fonction des cases cochées
            if self.translation_checkbox.isChecked():
                cmds.connectAttr(f'{decomp_node}.outputTranslate', f'{driven}.translate')
            if self.rotation_checkbox.isChecked():
                cmds.connectAttr(f'{decomp_node}.outputRotate', f'{driven}.rotate')
            if self.scale_checkbox.isChecked():
                cmds.connectAttr(f'{decomp_node}.outputScale', f'{driven}.scale')
    
        print("CST créé")



    # Fonction pour créer des courbes
    def createCurve(self, shape):
        if shape == "Cercle":
            cmds.circle()
        elif shape == "Carré":
            cmds.curve(d=1, p=[(-1, 0, -1), (-1, 0, 1), (1, 0, 1), (1, 0, -1), (-1, 0, -1)], k=[0, 1, 2, 3, 4])

    # Fonction pour créer des groupes NPO
    def MainNpo(self):
        sel = cmds.ls(selection=True)
        if not sel:
            cmds.warning("Aucun objet sélectionné.")
            return

        for obj in sel:
            N_Split = obj.split("_")
            New_Name = "X_" + "_".join(N_Split) if len(N_Split) > 1 else "X_" + N_Split[0]
            parent = cmds.listRelatives(obj, parent=True)
            Name_Node = self.AddNpo(New_Name, obj)
            if parent:
                cmds.parent(Name_Node, parent[0])
            print(f"Objet {New_Name} réalisé")

    # Fonction pour ajouter des groupes NPO
    def AddNpo(self, Name, Obj):
        Name = cmds.createNode("transform", name=Name, parent=Obj)
        cmds.matchTransform(Name, Obj)
        cmds.parent(Name, world=True)
        cmds.parent(Obj, Name)
        cmds.makeIdentity(Obj, apply=True)
        cmds.xform(Obj, translation=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1))
        return Name

window = BaB()
