
import json
import sys
import ast
import subprocess
import time

from datetime import datetime
import numpy as np
from tkinter import filedialog

from ui_interface import *
import Custom_Dialog

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox, QHBoxLayout, QVBoxLayout, QStackedWidget, QGridLayout
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QPainter, QPen, QFont, QPolygonF, QPainterPath

class Canvas(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAutoFillBackground(True) 

        self.nodes = []
        self.edges = {}
        self.firstNode = None
        self.secondNode = None
        self.radius = 20 

        self.dragging_node = None

        self.selected_edge = None
        self.selected_node = None

    def mousePressEvent(self, event):
        newPosition = event.position().toPoint() 

        if event.button() == Qt.LeftButton:

            if not any((newPosition.x() - node.x())**2 + (newPosition.y() - node.y())**2 < self.radius**2.5 for node in self.nodes):
                self.nodes.append(newPosition)
                self.update()
            else:
                closestNode = min(self.nodes, key=lambda node: (newPosition.x() - node.x())**2 + (newPosition.y() - node.y())**2)

                if self.firstNode is None:
                    self.firstNode = closestNode
                else:
                    self.secondNode = closestNode
                    if self.firstNode != self.secondNode:
                        node1_index = self.nodes.index(self.firstNode)
                        node2_index = self.nodes.index(self.secondNode)
                        if self.firstNode != self.secondNode and (node1_index, node2_index) not in self.edges:
                            self.edges[(node1_index, node2_index)] = [0, 0]
                    self.firstNode = None
                    self.secondNode = None

                self.selected_node = closestNode
                self.selected_edge = None
                
                self.update()
                

        elif event.button() == Qt.RightButton:
            if not any((newPosition.x() - node.x())**2 + (newPosition.y() - node.y())**2 < self.radius**2 for node in self.nodes):
                selected_edge = self.getClosestEdge(event.position().toPoint())

                if selected_edge:
                    self.editEdges(selected_edge)

                self.selected_edge = selected_edge
                self.selected_node = None
            
            else:
                # move node functionality
                closestNode = min(self.nodes, key=lambda node: (newPosition.x() - node.x())**2 + (newPosition.y() - node.y())**2)
                self.dragging_node = closestNode


    def mouseMoveEvent(self, event):
        if self.dragging_node:
            self.dragging_node.setX(event.position().x())
            self.dragging_node.setY(event.position().y())

            self.update()
    

    def mouseReleaseEvent(self, event):
        self.dragging_node = None  # Stop dragging


    def getClosestEdge(self, click_point):
        closest_edges = []
        
        for edge in self.edges:
            idx_node1, idx_node2 = edge

            distance, closest_x, closest_y = self.getDistanceToEdge(click_point, self.nodes[idx_node1], self.nodes[idx_node2])

            closest_edges.append((distance, edge, closest_x, closest_y))

        closest_edges.sort(key=lambda x: x[0])

        if not closest_edges:
            return None  

        if len(closest_edges) > 1 and closest_edges[0][0] == closest_edges[1][0]:
            edge1, edge2 = closest_edges[0], closest_edges[1]
    
            dist_to_second_1 = np.hypot(click_point.x() - self.nodes[edge1[1][1]].x(), click_point.y() - self.nodes[edge1[1][1]].y())
            dist_to_second_2 = np.hypot(click_point.x() - self.nodes[edge2[1][1]].x(), click_point.y() - self.nodes[edge2[1][1]].y())

            return edge1[1] if dist_to_second_1 < dist_to_second_2 else edge2[1]

        return closest_edges[0][1]


    def getDistanceToEdge(self, click_point, node1, node2):
        """Calculate the shortest distance from click_point to the straight line edge."""
        x1, y1 = node1.x(), node1.y()
        x2, y2 = node2.x(), node2.y()
        x0, y0 = click_point.x(), click_point.y()

        numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
        denominator = np.hypot(y2 - y1, x2 - x1)

        if denominator == 0:
            return float('inf'), None, None

        distance = numerator / denominator

        t = ((x0 - x1) * (x2 - x1) + (y0 - y1) * (y2 - y1)) / (denominator ** 2)

        t = max(0, min(1, t))

        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)

        return distance, closest_x, closest_y


    def paintEvent(self, event):
        qp = QPainter(self)
        
        for i, node in enumerate(self.nodes, start=1):

            pen_color = Qt.red if node == self.selected_node else Qt.black

            qp.setPen(QPen(pen_color, 3))
            qp.drawEllipse(node, self.radius, self.radius)

            qp.setPen(QPen(Qt.black, 3))
            qp.setFont(QFont("Arial", 12, QFont.Bold))
            qp.drawText(node.x() - 7.5, node.y() + 7.5, str(i))

        # Draw edges
        for edge in self.edges:
            self.drawEdge(qp, self.nodes[edge[0]], self.nodes[edge[1]])

        qp.end()


    def drawEdge(self, qp, node1, node2):
        dx = node2.x() - node1.x()
        dy = node2.y() - node1.y()
        length = np.hypot(dx, dy)
        if length == 0:
            return  

        dx /= length
        dy /= length

        start = QPointF(node1.x() + dx * self.radius, node1.y() + dy * self.radius)
        end = QPointF(node2.x() - dx * self.radius, node2.y() - dy * self.radius)

        mid_x = (start.x() + end.x()) / 2
        mid_y = (start.y() + end.y()) / 2

        curve_offset = 40 
        control_x = mid_x - dy * curve_offset
        control_y = mid_y + dx * curve_offset
        control = QPointF(control_x, control_y)

        index1 = self.nodes.index(node1)
        index2 = self.nodes.index(node2)
        edge_key = (index1, index2)

        pen_color = Qt.red if edge_key == self.selected_edge else Qt.black
        qp.setPen(QPen(pen_color, 3))

        path = QPainterPath()
        path.moveTo(start)
        path.quadTo(control, end)

        # Apply pen color to the edge
        qp.drawPath(path)

        arrow_size = 10  

        p1 = QPointF(node2.x() - dx * self.radius, node2.y() - dy * self.radius)
        left = QPointF(p1.x() - dy * arrow_size - dx * arrow_size, p1.y() + dx * arrow_size - dy * arrow_size)
        right = QPointF(p1.x() + dy * arrow_size - dx * arrow_size, p1.y() - dx * arrow_size - dy * arrow_size)

        pen_color = Qt.red if edge_key == self.selected_edge else Qt.black
        qp.setPen(QPen(pen_color, 3))

        arrow_head = QPolygonF([p1, left, right])
        qp.setBrush(Qt.black)
        qp.drawPolygon(arrow_head)
        qp.setBrush(Qt.NoBrush)


        if edge_key in self.edges:
            current_flow, max_flow = self.edges[edge_key]
            text = f"{current_flow}/{max_flow}"

            text_x = node1.x() + 0.7 * (node2.x() - node1.x())
            text_y = node1.y() + 0.7 * (node2.y() - node1.y())

            qp.setFont(QFont("Arial", 10, QFont.Bold))
            qp.drawText(text_x, text_y, text)

            qp.setPen(QPen(Qt.black, 3))
        else:
            # If edge doesn't exist, optionally print or handle the case
            print(f"Edge not found in self.edges: {edge_key}")
            

    def editEdges(self, edge):
        # print("Editing edge")
        # print(edge)
        # print("Edges list")
        # for elem in self.edges:
        #     print(elem)

        current_flow, max_flow = self.edges[edge]

        dialog = Custom_Dialog.EdgeValueDialog(current_flow, max_flow)
        if dialog.exec():
            try:
                flow = int (dialog.flow_input.text())
                max_flow = int(dialog.max_flow.text())

                if flow < 0 or max_flow < 0:
                    raise ValueError(("Both values must be >= 0"))
                if flow > max_flow:
                    raise ValueError(("Current flow cannot exceed max flow"))

                self.edges[edge] = [flow, max_flow]
                self.update()
            except ValueError as e:
                QMessageBox.warning(self, "Error", f"Invalid: {str(e)}")


    def delete(self):
        # Ask for confirmation before deletion
        confirmation = QMessageBox.question(self, 
                                            "Confirm Deletion", 
                                            "Are you sure you want to delete this node or edge?", 
                                            QMessageBox.Yes | QMessageBox.No, 
                                            QMessageBox.No)

        if self.selected_node is not None:
            if confirmation == QMessageBox.Yes:
                self.nodes.remove(self.selected_node)
                self.edges = {edge: value for edge, value in self.edges.items() if self.selected_node not in edge}
                self.update()
        elif self.selected_edge is not None:
            if confirmation == QMessageBox.Yes:
                self.edges.pop(self.selected_edge)
                self.update()
        else:
            QMessageBox.warning(self, "Error", "Select a node or an edge to delete")


    def saveGraph(self):
        nodes_data = [(node.x(), node.y()) for node in self.nodes]  
        edges_data = {
            f"[{node1}, {node2}]": {"flow": current_flow, "max_flow": max_flow} 
            for (node1, node2), (current_flow, max_flow) in self.edges.items()
        }

        graph_data = {
            "nodes": nodes_data,
            "edges": edges_data
        }

        currentTime = datetime.now().strftime("%Y_%m_%d-%p%I_%M")
        with open(f'graph_{currentTime}.json', 'w') as f:
            json.dump(graph_data, f)
    

    def loadGraph(self):
        filePath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not filePath: 
            return

        with open(filePath, 'r') as f:
            data = json.load(f)

            self.nodes = [QPoint(x, y) for x, y in data["nodes"]]

            self.edges = {
                tuple(ast.literal_eval(edge)): [value["flow"], value["max_flow"]]
                for edge, value in data["edges"].items()
            }


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.canvas = Canvas(self.GraphDrawWidget)
        layout = QVBoxLayout(self.GraphDrawWidget)
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)

        self.GraphDrawWidget.setLayout(layout)

        self.deleteButton.clicked.connect(self.canvas.delete)
        self.saveButton.clicked.connect(self.canvas.saveGraph)
        self.loadButton.clicked.connect(self.canvas.loadGraph)
        




def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()