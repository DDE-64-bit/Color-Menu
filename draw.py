import sys
import subprocess
import logging
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QInputDialog, QPlainTextEdit, QMessageBox

class SemiTransparentDrawingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drawing App with Undo and Redo")
        self.setGeometry(0, 0, QApplication.primaryScreen().size().width(), QApplication.primaryScreen().size().height())

        # Transparant venster instellen
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Initializeer variabelen
        self.drawing = False
        self.last_point = QPoint()
        self.pen_color = QColor(Qt.red)  # Startkleur van de pen
        self.pen_thickness = 3
        self.lines = []  # Lijst van volledige lijnen
        self.current_line = []  # Lijst van punten voor de huidige lijn
        self.opacity = 0  # Beginwaarde voor de doorzichtigheid (0-100, 0 is volledig zichtbaar)
        self.undo_stack = []  # Stack voor ongedaan maken
        self.redo_stack = []  # Stack voor opnieuw doen

        # Positie voor het verplaatsen van de output text edit
        self.output_text_edit_start_pos = QPoint(100, 100)  # Startpositie van de output text edit
        self.output_text_edit_drag_pos = QPoint()  # Voor muis slepen
        self.output_text_edit_dragging = False  # Drag status

        # Maak een interface voor de kleurknoppen en de clear-knop
        self.initUI()

        # QPlainTextEdit voor het weergeven van de LLM-uitvoer, standaard verborgen
        self.output_text_edit = QPlainTextEdit(self)
        self.output_text_edit.setGeometry(self.output_text_edit_start_pos.x(), self.output_text_edit_start_pos.y(), 300, 200)  # Kleinere grootte
        self.output_text_edit.setReadOnly(True)  # Maak het alleen-lezen
        self.output_text_edit.setStyleSheet("background-color: lightgray; font-size: 14px;")  # Stijl voor de uitvoer
        self.output_text_edit.hide()  # Verborgen totdat er een prompt is ingevoerd

        # Toon het venster in fullscreen
        self.showFullScreen()

    def initUI(self):
        """Maak de zijbalk met kleurknoppen, clear-knop en knoppen voor doorzichtigheid."""
        self.button_widget = QWidget(self)
        self.button_widget.setGeometry(self.width() - 100, 0, 100, self.height())  # Zet de balk aan de rechterkant
        self.button_widget.setStyleSheet("background-color: white;")  # Witte achtergrond

        layout = QVBoxLayout(self.button_widget)  # Verander naar een verticale layout

        # Pijltje voor het verbergen van de instellingenbalk
        self.toggle_button = QPushButton("▶")  # Pijltje naar rechts
        self.toggle_button.setStyleSheet("font-size: 20px; border: none; padding: 0px;")
        self.toggle_button.clicked.connect(self.toggleSettings)
        layout.addWidget(self.toggle_button)

        # Kleurknoppen inclusief wit
        colors = [QColor(Qt.red), QColor(Qt.green), QColor(Qt.blue), QColor(Qt.yellow), QColor(Qt.black), QColor(Qt.white)]
        for color in colors:
            color_button = QPushButton()
            color_button.setStyleSheet(f"background-color: {color.name()}; border-radius: 20px; border: 2px solid black; width: 40px; height: 40px;")
            color_button.clicked.connect(lambda checked, c=color: self.setPenColor(c))
            layout.addWidget(color_button)

        # Clear-knop
        clear_button = QPushButton("Clear")
        clear_button.setStyleSheet("background-color: red; color: white; font-weight: bold; border-radius: 20px; padding: 10px;")
        clear_button.clicked.connect(self.clearCanvas)
        layout.addWidget(clear_button)

        # Knoppen voor doorzichtigheid (met 1 toegevoegd)
        opacity_values = [100, 80, 60, 40, 20, 1, 0]  # Voeg 1 toe voor 99% transparant
        for value in opacity_values:
            opacity_button = QPushButton(str(value))
            opacity_button.setStyleSheet("border-radius: 20px; border: 2px solid black; width: 40px; height: 40px;")
            opacity_button.clicked.connect(lambda checked, v=value: self.setOpacity(v))
            layout.addWidget(opacity_button)

        # Extra knop voor het openen van de tekstinvoer, met ronde hoeken
        input_button = QPushButton("Input Prompt")
        input_button.setStyleSheet("background-color: blue; color: white; font-weight: bold; border-radius: 20px; padding: 10px;")
        input_button.clicked.connect(self.openInputDialog)
        layout.addWidget(input_button)

        # Nieuwe knop voor het sluiten van het prompt venster
        close_prompt_button = QPushButton("Sluit Prompt")
        close_prompt_button.setStyleSheet("background-color: orange; color: white; font-weight: bold; border-radius: 20px; padding: 10px;")
        close_prompt_button.clicked.connect(self.closePromptWindow)  # Verbind de knop met de functie om het prompt venster te sluiten
        layout.addWidget(close_prompt_button)

    def toggleSettings(self):
        """Verberg of toon de instellingenbalk."""
        if self.button_widget.isVisible():
            self.button_widget.hide()
            self.toggle_button.setText("◀")  # Pijltje naar links
        else:
            self.button_widget.show()
            self.toggle_button.setText("▶")  # Pijltje naar rechts

    def setPenColor(self, color):
        """Stel de penkleur in op de geselecteerde kleur."""
        self.pen_color = color

    def setOpacity(self, value):
        # Voor andere waardes, stel de normale doorzichtigheid in
        self.opacity = value
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # Schakel transparantie weer in
        self.update()  # Herteken het venster


    def clearCanvas(self):
        """Leeg het canvas."""
        self.lines.clear()
        self.undo_stack.clear()  # Leeg de undo stack
        self.redo_stack.clear()  # Leeg de redo stack
        self.update()  # Herteken het venster

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()
            self.current_line = [(self.last_point, self.pen_color, self.pen_thickness)]  # Start een nieuwe lijn

            # Controleer of de muis in het tekstvak is geklikt
            if self.output_text_edit.geometry().contains(event.pos()):
                self.output_text_edit_dragging = True
                self.output_text_edit_drag_pos = event.pos() - self.output_text_edit.pos()  # Sla de offset op

    def mouseMoveEvent(self, event):
        if self.drawing:
            # Voeg de huidige punt toe aan de lijn
            self.current_line.append((event.pos(), self.pen_color, self.pen_thickness))
            self.last_point = event.pos()
            self.update()
        elif self.output_text_edit_dragging:
            # Verplaats het output text edit venster
            self.output_text_edit.move(event.pos() - self.output_text_edit_drag_pos)  # Beweeg de widget

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
            if self.output_text_edit_dragging:
                self.output_text_edit_dragging = False  # Stop met slepen
            else:
                # Voeg de volledige lijn toe aan de lijnenlijst
                self.lines.append(self.current_line)
                self.undo_stack.append(self.lines.copy())  # Voeg de huidige lijnenlijst toe aan de undo stack
                self.redo_stack.clear()  # Maak de redo stack leeg omdat er een nieuwe actie is
                self.current_line = []  # Maak de huidige lijn leeg

    def paintEvent(self, event):
        # Teken de lijnen op de overlay
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Teken de semi-transparante achtergrond
        semi_transparent_color = QColor(0, 0, 0, self.opacity)  # Zwarte achtergrond met variabele doorzichtigheid
        painter.fillRect(self.rect(), semi_transparent_color)

        # Teken alle lijnen
        for line in self.lines:
            for i in range(1, len(line)):
                painter.setPen(QPen(line[i][1], line[i][2], Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.drawLine(line[i - 1][0], line[i][0])

        # Teken de huidige lijn
        if self.current_line:
            for i in range(1, len(self.current_line)):
                painter.setPen(QPen(self.current_line[i][1], self.current_line[i][2], Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.drawLine(self.current_line[i - 1][0], self.current_line[i][0])

    def openInputDialog(self):
        """Open een invoerdialoog voor de gebruiker om een prompt in te voeren."""
        text, ok = QInputDialog.getText(self, "Input Prompt", "Voer de prompt in:")
        if ok and text:
            self.processPrompt(text)  # Verwerk de prompt

    def processPrompt(self, prompt):
        """Verwerk de ingevoerde prompt."""
        try:
            # Start het model subprocess en haal het resultaat op
            result = subprocess.run(
                ['ollama', 'run', "llava"],
                input=prompt,
                text=True,
                capture_output=True,
                check=True,
                encoding='utf-8'  # Voeg dit toe om Unicodeproblemen te voorkomen
            )
            logging.debug(f"Model output: {result.stdout.strip()}")
            self.output_text_edit.setPlainText(result.stdout.strip())  # Toon uitvoer in QPlainTextEdit
            self.output_text_edit.move(self.output_text_edit_start_pos)  # Zet naar startpositie
            self.output_text_edit.show()  # Maak het zichtbaar

        except subprocess.CalledProcessError as e:
            logging.error(f"Error running model: {e.stderr.strip()}")
            self.output_text_edit.setPlainText("Failed to run the model.")  # Toon foutmelding in de QPlainTextEdit
            self.output_text_edit.move(self.output_text_edit_start_pos)  # Zet naar startpositie
            self.output_text_edit.show()  # Maak het zichtbaar

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            self.output_text_edit.setPlainText("An unexpected error occurred.")  # Toon foutmelding in de QPlainTextEdit
            self.output_text_edit.move(self.output_text_edit_start_pos)  # Zet naar startpositie
            self.output_text_edit.show()  # Maak het zichtbaar

    def closeOutput(self):
        """Sluit het uitvoervenster."""
        self.output_text_edit.hide()  # Verberg de QPlainTextEdit

    def closePromptWindow(self):
        """Sluit het prompt venster en verbergt de uitvoer."""
        self.closeOutput()  # Sluit het uitvoervenster

    def keyPressEvent(self, event):
        """Behandel toetsenbordinvoer."""
        if event.key() == Qt.Key_Escape:
            self.close()  # Sluit de applicatie als de Escape-toets wordt ingedrukt
        elif event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
            self.undo()  # Voer ongedaan maken uit bij Ctrl + Z
        elif event.key() == Qt.Key_Y and event.modifiers() == Qt.ControlModifier:
            self.redo()  # Voer opnieuw doen uit bij Ctrl + Y

    def undo(self):
        """Voer de ongedaan maken actie uit."""
        if self.undo_stack:
            self.redo_stack.append(self.undo_stack.pop())  # Verplaats de laatst gemaakte actie naar de redo stack
            self.lines = self.undo_stack[-1] if self.undo_stack else []  # Herstel de laatst opgeslagen lijnenlijst
            self.update()  # Herteken het venster

    def redo(self):
        """Voer de opnieuw doen actie uit."""
        if self.redo_stack:
            self.undo_stack.append(self.redo_stack.pop())  # Verplaats de laatst gemaakte actie naar de undo stack
            self.lines = self.undo_stack[-1]  # Herstel de laatst opgeslagen lijnenlijst
            self.update()  # Herteken het venster

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication(sys.argv)
    window = SemiTransparentDrawingApp()
    window.setMouseTracking(True)  # Zorg ervoor dat muistracking werkt
    sys.exit(app.exec_())
