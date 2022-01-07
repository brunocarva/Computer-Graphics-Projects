import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import time
import wx
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import re
import sys
import math

allData = []
motionData = []
offset = []
channels = []
positionAt = 0
bvhTree = []
channelPointer = 0
frame_motion_channels = []
motionCounter = 0
Root = []
flag = 0

Joint = []
drawJointFlag = 0
global jointNextPosition
jointPoint = []
jointPoint.append("hip")
global checkList
global myPanel

global currentPosition
global currrentVelocity
velocityFlag = 0

global slider
global jointSlider
global userInput
global frameText
global jointBtn
jointFlag = 0

pointPosition = []
pointFlag = 0
lineFlag = 0



class Node:

    def __init__(self, name, children, offset, channels):
        self.name = name
        self.offset = offset
        self.children = children
        self.channels = channels


class CreateBvhTree:

    def __init__(self, names):
        self.fileParser(names)
        root = self.createChildren(childBlocks=[[0, len(allData)]])[0]
        self.setMotionData()
        Root.append(root)

    def fileParser(self, names):
        with open(str(names)) as f:
            datafile = f.readlines()
            target = allData
            for line in datafile[1:]:
                if 'MOTION' in line:
                    target = motionData
                    continue
                target.append(line)

    def createChildren(self, childBlocks, depth=0):
        global channelPointer, Joint
        children = []
        for childBlock in childBlocks:
            block_start = childBlock[0]
            block_end = childBlock[1]
            name = allData[block_start].split()[1]
            offset = [float(_) for _ in allData[block_start + 2].split()[1:]]
            channelList = allData[block_start + 3].split()[2:]
            channelCount = len(channelList)
            channels = {}
            for channel in channelList:
                channels[channel] = channelPointer
                channelPointer += 1

            node = Node(name=name, offset=offset, channels=channels, children=None)
            children.append(node)
            Joint.append(str(node.name))

            newChildBlocks = []
            for i in range(block_start, block_end):
                if re.match('^\s{' + str(2 * (depth + 1)) + '}End Site', allData[i]):
                    break
                if re.match('^\s{' + str(2 * (depth + 1)) + '}JOINT', allData[i]):
                    newBlockStart = i
                if re.match('^\s{' + str(2 * (depth + 1)) + '}}', allData[i]):
                    newChildBlocks.append([newBlockStart, i])

            node.children = self.createChildren(childBlocks=newChildBlocks, depth=depth + 1)
        return children

    def printBvh(self, node, depth=0, offset=None):
        if offset is None:
            offset = node.offset
        offset[0] += node.offset[0]
        offset[1] += node.offset[1]
        offset[2] += node.offset[2]

        print("%s%s %s" % ('  ' * depth, node.name, offset))
        for child in node.children:
            self.printBvh(node=child, depth=depth + 1, offset=offset)

    def setMotionData(self):
        global frame_motion_channels
        frames = int(motionData[0].strip().split(':')[1])
        frameTime = float(motionData[1].strip().split(':')[1])
        frame_motion_channels = []
        for motionLine in motionData[2:]:
            motion_channels = [float(_) for _ in motionLine.strip().split()]
            frame_motion_channels.append(motion_channels)

    def drawBvh(self, node, depth=0, frame=0):
        global frame_motion_channels
        parent = node
        hieranchy = '  ' * depth
        print("%s%s " % (hieranchy, node.name))
        print('%sparent-channels:' % hieranchy)
        for channel_name, pointer in node.channels.items():
            print('%s%s[%s]: %s' % (hieranchy, channel_name, pointer, frame_motion_channels[frame][pointer]))

        for child in node.children:
            print('%sparent-offset: %s - child-offset: %s' % (hieranchy, parent.offset, child.offset))
            self.drawBvh(child, depth + 1)


class PBLCanvas(glcanvas.GLCanvas):

    def __init__(self, parent):
        global flag
        glcanvas.GLCanvas.__init__(self, parent, -1, size=(720, 600))
        self.move = True
        self.context = glcanvas.GLContext(self)
        self.SetCurrent(self.context)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        flag = 0
        # Bindings
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, event):
        wx.PaintDC(self)
        self.onDraw()

    def onDraw(self):
        global motionCounter, flag, positionAt, pointFlag, drawJointFlag
        if motionCounter == len(frame_motion_channels) - 2:
            motionCounter = 0
        else:
            motionCounter += 1
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glMatrixMode(GL_MODELVIEW)
        self.drawGrid()
        if flag == 1:
            self.animate(parent=Root[0], frame=positionAt)
            time.sleep(0.0000001)
            if positionAt == len(frame_motion_channels) - 1:
                positionAt = 0
            positionAt += 1

        if pointFlag == 1:
            self.drawPoint()

        if lineFlag == 1:
            self.drawLine()

        if self.move:
            self.Refresh()
        self.SwapBuffers()

    def drawGrid(self):

        glLoadIdentity()
        glOrtho(10, -10, -15, 25, -10, 10)
        gluLookAt(1 * np.sin(2), 1., 1 * np.cos(2), 0, 0, 0, 0, 1, 0)

        # Draw a rectangular grid

        glBegin(GL_POLYGON)
        #glColor3ub(255, 255, 255)
        glColor3f(1.0,1.0,1.0)
        glVertex3f(6, 6, -6)
        glVertex3f(-6, 6, -6)
        glColor3f(0.0,0.5,0.5)
        glVertex3f(-6, 6, 6)
        glVertex3f(6, 6, 6)
        glEnd()

        # Draw Coordinate System

        glLoadIdentity()
        glOrtho(-2.7, 2.5, -3.2, 3.8, -1, 12)
        gluLookAt(.1 * np.sin(4.3), 0.05, .1 * np.cos(4.3), 0, 0, 0, 0, 1, 0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glLineWidth(3)
        glBegin(GL_LINES)
        glColor3ub(255, 0, 0)
        glVertex3fv(np.array([0., 0., 0.]))
        glVertex3fv(np.array([-1., 0., 0.]))
        glColor3ub(0, 255, 0)
        glVertex3fv(np.array([0., 0., 0.]))
        glVertex3fv(np.array([0., 1., 0.]))
        glColor3ub(0, 0, 255)
        glVertex3fv(np.array([0., 0., 0.]))
        glVertex3fv(np.array([0., 0., -1.]))

        glEnd()

    def drawSkeleton(self, parent, position=np.array([0., 0., 0., 1.])):
        T = np.identity(4)
        offset = np.array([parent.offset[0], parent.offset[1], parent.offset[2]])
        T[:3,3] = offset
        newPosition = T @ position

        glPushMatrix()
        glLoadIdentity()
        glScalef(0.0099, 0.0099, 0.0099)

        glPointSize(5)
        glLineWidth(5)
        glBegin(GL_LINES)
        glColor4f(1., 0.5, 0., 0.)
        glVertex3fv(newPosition[:-1])
        glVertex3fv(position[:-1])
        glEnd()
        glPopMatrix()

        for child in parent.children:
            self.drawSkeleton(parent=child, position=newPosition)

    def animate(self, parent, position=np.array([0., 0., 0., 1.]), rotationMatrix=None, frame = None, lastPosition=None):
        global jointPoint, currentPosition, velocityFlag
        if "Xposition" in parent.channels.keys():
            offset = np.array([
                frame_motion_channels[frame][parent.channels["Xposition"]],
                frame_motion_channels[frame][parent.channels["Yposition"]],
                frame_motion_channels[frame][parent.channels["Zposition"]]
            ])

        else:
            offset = np.array([parent.offset[0], parent.offset[1], parent.offset[2]])

        T = np.identity(4)
        T[:3,3] = offset
        M = np.identity(4)
        xAngle = np.radians(frame_motion_channels[frame][parent.channels["Xrotation"]])
        yAngle = np.radians(frame_motion_channels[frame][parent.channels["Yrotation"]])
        zAngle = np.radians(frame_motion_channels[frame][parent.channels["Zrotation"]])
        RotationX = np.array([[1,0,0],[0, np.cos(xAngle), -np.sin(xAngle)],[0, np.sin(xAngle), np.cos(xAngle)]])
        RotationY = np.array([[np.cos(yAngle), 0, np.sin(yAngle)],[0,1,0],[-np.sin(yAngle), 0, np.cos(yAngle)]])
        RotationZ = np.array([[np.cos(zAngle), -np.sin(zAngle), 0],[np.sin(zAngle), np.cos(zAngle), 0],[0,0,1]])
        M[:3,:3] = RotationZ @ RotationX @ RotationY

        if rotationMatrix is not None:
            rotationMatrix = rotationMatrix @ T @ M
        else:
            rotationMatrix = T @ M
        newPosition = rotationMatrix @ np.array([0.,0.,0.,1.])
        if parent.offset[0] == 0 and parent.offset[1] == 0 and parent.offset[2] == 0:
            pass
        else:
            glPushMatrix()
            glLoadIdentity()
            glScalef(0.0045, 0.0045, 0.0045)
            glPointSize(5)
            glBegin(GL_LINES)
            glColor4f(1., 0.5, 0., 0.)
            glVertex3fv(newPosition[:-1])
            glVertex3fv(position[:-1])
            glEnd()
            if not jointPoint:
                pass
            else:
                if parent.name == jointPoint[0] and (drawJointFlag == 1 or velocityFlag == 1):
                    if drawJointFlag == 1:
                        glPointSize(10)
                        glBegin(GL_POINTS)
                        glColor3f(0., 0., 1.)
                        glVertex3fv(newPosition[:-1])
                        glEnd()
                        currentPosition = newPosition
                        #print(currentPosition)
                    if lastPosition is not None and velocityFlag == 1:
                        velocity = newPosition - lastPosition
                        glBegin(GL_LINES)
                        glColor3f(1., 1., 1.)
                        glVertex3fv(newPosition[:-1])
                        glVertex3fv(velocity[:-1])
                        glEnd()

            glPopMatrix()
            lastPosition = newPosition

        for child in parent.children:
            self.animate(parent=child, position=newPosition, rotationMatrix=rotationMatrix, frame = frame, lastPosition=lastPosition)


    def drawPoint(self):
        global pointPosition
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-2.7, 2.5, -3.2, 3.8, -1, 12)
        gluLookAt(.1 * np.sin(4.3), 0.05, .1 * np.cos(4.3), 0, 0, 0, 0, 1, 0)
        glScalef(0.045, 0.045, 0.045)
        glPointSize(10)
        glBegin(GL_POINTS)
        glColor3ub(255, 0, 0)
        glVertex3fv(pointPosition)
        glEnd()
        glPopMatrix()

    def drawLine(self):
        global pointPosition
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-2.7, 2.5, -3.2, 3.8, -1, 12)
        gluLookAt(.1 * np.sin(4.3), 0.05, .1 * np.cos(4.3), 0, 0, 0, 0, 1, 0)
        glScalef(0.045, 0.045, 0.045)
        glPointSize(10)
        glBegin(GL_LINES)
        glColor3ub(255, 0, 0)
        glVertex3f(pointPosition[0], pointPosition[1], pointPosition[2])
        glVertex3f(pointPosition[3], pointPosition[4], pointPosition[5])
        glEnd()
        glPopMatrix()


class PBLPanel(wx.Panel):

    def __init__(self, parent):
        global slider, userInput, frameText, jointSlider, jointBtn, checkList, Joint
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour("LIGHT BLUE")

        # Time Line Slider:
        slider = wx.Slider(self, -1, 25, 0, 50,
                           style=wx.SL_AUTOTICKS | wx.SL_LABELS)
        slider.SetTickFreq(50)
        slider.SetSize(100, 620, 500, -1)

        self.Bind(wx.EVT_COMMAND_SCROLL_THUMBTRACK, self.jumpFrame)
        slider.Bind(wx.EVT_COMMAND_SCROLL_CHANGED, self.jumpFrame)

        # Start/Stop Button:
        self.startStopBtn = wx.Button(self, -1, label="Play/Stop", pos=(740, 10), size=(120, 50))
        self.startStopBtn.BackgroundColour = [125, 125, 125]
        self.startStopBtn.ForegroundColour = [0, 0, 0]
        self.Bind(wx.EVT_BUTTON, self.move, self.startStopBtn)

        # File Box:
        self.SetDropTarget(DropFiles(self))

        # --------------------------------------------------------------------------------------

        # Draw point box:
        self.drawPointBtn = wx.Button(self, -1, label="Draw Point", pos=(740, 80), size=(120, 50))
        self.drawPointBtn.BackgroundColour = [125, 125, 125]
        self.drawPointBtn.ForegroundColour = [0, 0, 0]
        self.drawPointBtn.id = 1
        self.Bind(wx.EVT_BUTTON, self.DrawPointMessage, self.drawPointBtn)

        # Draw line box:
        self.drawLineBtn = wx.Button(self, -1, label="Draw Line", pos=(740, 150), size=(120, 50))
        self.drawLineBtn.BackgroundColour = [125, 125, 125]
        self.drawLineBtn.ForegroundColour = [0, 0, 0]
        self.drawLineBtn.id = 2
        self.Bind(wx.EVT_BUTTON, self.DrawPointMessage, self.drawLineBtn)

        # Frame Input:
        self.sizer = wx.GridBagSizer()
        frameText = wx.StaticText(self, label='Frame...')
        self.sizer.Add(frameText, (14, 74), (1, 1), wx.ALL, 5)
        userInput = wx.TextCtrl(self, -1, value="Frame Number")
        self.sizer.Add(userInput, (15, 74), (10, 10), wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.frameBtn = wx.Button(self, -1, label="OK", pos=(775, 340), size=(50, 25))
        self.frameBtn.BackgroundColour = [125, 125, 125]
        self.frameBtn.ForegroundColour = [0, 0, 0]
        self.Bind(wx.EVT_BUTTON, self.frameMessage, self.frameBtn)

        # Joint Position and Linear Velocity:

        checkList = wx.CheckListBox(self, -1, (745, 425), (100, 100), Joint)
        self.Bind(wx.EVT_CHECKBOX, self.jointAction, checkList)

        jointBtn = wx.Button(self, -1, label="Position", pos=(745, 545), size=(100, 30))
        jointBtn.BackgroundColour = [125, 125, 125]
        jointBtn.ForegroundColour = [0, 0, 0]
        self.Bind(wx.EVT_BUTTON, self.jointPosition, jointBtn)

        self.velocityBtn = wx.Button(self, -1, label="Linear Velocity", pos=(745, 590), size=(100, 30))
        self.velocityBtn.BackgroundColour = [125, 125, 125]
        self.velocityBtn.ForegroundColour = [0, 0, 0]
        self.Bind(wx.EVT_BUTTON, self.jointPosition, self.velocityBtn)

        # Canvas:
        self.canvas = PBLCanvas(self)


    def move(self, event):
        if not self.canvas.move:
            self.canvas.move = True
            self.canvas.Refresh()
        else:
            self.canvas.move = False

    def jumpFrame(self, event):
        frame = slider.GetValue()
        global positionAt
        if flag == 1:
            positionAt = frame
            time.sleep(0.01)
        else:
            pass

    def jointAction(self, event):
        global jointPoint
        if jointFlag == 1:
            jointPoint = checkList.GetCheckedStrings()
            #print(jointPoint)
        else:
            pass

    def jointPosition(self, event):
        global drawJointFlag, jointFlag, flag, pointFlag, lineFlag, velocityFlag
        btn = event.GetEventObject()
        code = btn.GetLabel()
        #print(code)
        if code == "Position" or code == "Back":
            if jointFlag == 1:
                if drawJointFlag == 1:
                    jointBtn.SetLabel("Position")
                    drawJointFlag = 0
                    flag = 1
                else:
                    jointBtn.SetLabel("Back")
                    pointFlag = 0
                    lineFlag = 0
                    drawJointFlag = 1
            else:
                pass
        else:
            if jointFlag == 1:
                if velocityFlag == 1:
                    btn.SetLabel("Linear Velocity")
                    velocityFlag = 0

                else:
                    btn.SetLabel("Close")
                    pointFlag = 0
                    lineFlag = 0
                    velocityFlag = 1

            else:
                pass

    def frameMessage(self, event):
        global positionAt, flag, userInput
        if flag == 1:
            if userInput.GetLineText(0).isnumeric():
                positionAt = int(userInput.GetLineText(0))
        else:
            pass

    def DrawPointMessage(self, event):
        global pointFlag, pointPosition, lineFlag
        stopHere = 0
        idNumber = event.GetEventObject().id
        if idNumber == 1:
            stopHere = 3
            self.dlg = wx.TextEntryDialog(self, ("Enter the position of the point in X, Y and Z:"),
                                          "Text Entry")
        elif idNumber == 2:
            stopHere = 6
            self.dlg = wx.TextEntryDialog(self, ("Enter the position of the 2 points in X, Y and Z (6 numbers):"),
                                          "Text Entry")
        if self.dlg.ShowModal() == wx.ID_OK:
            if pointFlag == 1 or lineFlag == 1:
                pointPosition = []
                pointFlag = 0
                lineFlag = 0
            number = self.dlg.GetValue()
            number = re.sub(r"[a-z]", "", number, flags=re.I)
            number = re.sub(r"\s+"," ", number, flags=re.I)
            numberList = []
            numberList.append(number.split())
            for i in range(0, stopHere):
                pointPosition.append(int(numberList[0][i]))
            if idNumber == 1:
                pointFlag = 1
            elif idNumber == 2:
                lineFlag = 1
            self.dlg.Destroy()


class DropFiles(wx.FileDropTarget, wx.Panel):

    def __init__(self, target):
        wx.FileDropTarget.__init__(self)
        self.target = target

    def OnDropFiles(self, x, y, names):
        global Root, frame_motion_channels, motionData, offset, allData, channels, \
            positionAt, bvhTree, channelPointer, motionCounter, jointFlag, checkList
        global flag

        if flag == 1:
            flag = 0
            Root = []
            motionData = []
            offset = []
            allData = []
            channels = []
            positionAt = 0
            frame_motion_channels = []
            bvhTree = []
            channelPointer = 0
            motionCounter = 0
            jointFlag = 0

        print("File Path: " + str(names))
        CreateBvhTree(names[0])
        flag = 1
        jointFlag = 1
        slider.SetMax((len(frame_motion_channels) - 2))
        slider.SetValue(math.floor(len(frame_motion_channels)/2))
        frameText.SetLabel("Max Frame: " + str((len(frame_motion_channels) - 2)))
        checkList.Destroy()
        checkList = wx.CheckListBox(myPanel, -1, (745, 425), (100, 100), Joint)
        myPanel.Bind(wx.EVT_CHECKLISTBOX, myPanel.jointAction, checkList)
        return True


class PBLFrame(wx.Frame):
    def __init__(self):
        global myPanel
        self.size = (900, 720)
        wx.Frame.__init__(self, None, title="PBL Assignment #3", size=self.size, style=wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(self.size)
        self.SetMaxSize(self.size)
        myPanel = PBLPanel(self)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        self.Destroy()
        sys.exit(0)


class mainApp(wx.App):
    def OnInit(self):
        frame = PBLFrame()
        frame.Show()
        return True


if __name__ == "__main__":
    app = mainApp()
    app.MainLoop()


