from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket
import threading
import sys
import traceback
import os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    FORWARD = 4
    BACKWARD = 5

    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0
        self.totalframe = 500 
        self.remainframe = self.totalframe
    # THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI
    def createWidgets(self):
        """Build GUI."""
        #Extend 4 -------------------------------
        self.totaltimebt = Button(self.master, width=20, padx=3, pady=3)
        self.totaltimebt["text"] = "Total time: ...s"
        self.totaltimebt["activebackground"] = "red"
        self.totaltimebt["bd"] = 3
        self.totaltimebt.grid(row=1, column=0, padx=2, pady=2)
        
        self.remaintimebt = Button(self.master, width=20, padx=3, pady=3)
        self.remaintimebt["text"] = "Remain time: ...s"
        self.remaintimebt["activebackground"] = "red"
        self.remaintimebt["bd"] = 3
        self.remaintimebt.grid(row=1, column=1, padx=2, pady=2)

        self.backward = Button(self.master, width=20, padx=3, pady=3)
        self.backward["text"] = "<<"
        self.backward["command"] = self.backwardMovie
        self.backward["activebackground"] = "red"
        self.backward["bd"] = 3
        self.backward.grid(row=1, column=2, padx=2, pady=2)

        self.forward = Button(self.master, width=20, padx=3, pady=3)
        self.forward["text"] = ">>"
        self.forward["command"] = self.forwardMovie
        self.forward["activebackground"] = "red"
        self.forward["bd"] = 3
        self.forward.grid(row=1, column=3, padx=2, pady=2)

        #-------------------------------
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup["activebackground"] = "red"
        self.setup["bd"] = 3
        self.setup.grid(row=2, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start["activebackground"] = "red"
        self.start["bd"] = 3
        self.start.grid(row=2, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause["activebackground"] = "red"
        self.pause["bd"] = 3
        self.pause.grid(row=2, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown["activebackground"] = "red"
        self.teardown["bd"] = 3
        self.teardown.grid(row=2, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4,
                        sticky=W+E+N+S, padx=5, pady=5)

    def setupMovie(self):
        """Setup button handler."""
        # TODO
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)
            #Extend 4 -------------------------------
            self.totaltimebt["text"] = "Total time: "+str(self.totalframe*0.05)+"s"
            self.remaintimebt["text"] = "Remain time: "+str(self.totalframe*0.05)+"s"
            # -------------------------------

    def exitClient(self):
        """Teardown button handler."""
        # TODO
        self.sendRtspRequest(self.TEARDOWN)
        self.master.destroy()  # Close the GUI window
        os.remove(CACHE_FILE_NAME + str(self.sessionId) +
                  CACHE_FILE_EXT)  # Delete the cache image

    def pauseMovie(self):
        """Pause button handler."""
        # TODO
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self):
        """Play button handler."""
        # TODO
        if self.state == self.READY:
            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)

    def forwardMovie(self):
        if not self.state == self.INIT:
            self.sendRtspRequest(self.FORWARD)
            self.remainframe -= 50
    def backwardMovie(self):
        if not self.state == self.INIT:
            self.sendRtspRequest(self.BACKWARD)
            if self.frameNbr > 50:
                self.frameNbr -= 50
                self.remainframe += 50
            else:
                #self.countbackward += self.frameNbr
                self.frameNbr = 0
                self.remainframe = 0


    def listenRtp(self):
        """Listen for RTP packets."""
        # TODO
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    currentFrameNbr = rtpPacket.seqNum()
                    print("Current Seq Num: " + str(currentFrameNbr))

                    if currentFrameNbr > self.frameNbr:  # Discard the late packet
                        #Extend 4 -------------------------------
                        self.remainframe -= 1
                        self.remaintimebt["text"] = "Remain time: "+str(round(self.remainframe*0.05,1))+ "s"
                        #Extend 4 -------------------------------
                        self.frameNbr = currentFrameNbr
                        self.updateMovie(self.writeFrame(
                            rtpPacket.getPayload()))
            except:
                # Stop listening (PAUSE or TEARDOWN)
                if self.playEvent.isSet():
                    break

                # Close the RTP socket (TEARDOWN)
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        # TODO
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()

        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        # TODO
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo, height=300)
        self.label.image = photo

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        # TODO
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # -------------
        # TO COMPLETE
        # -------------
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()
            # Update RTSP sequence number.
            self.rtspSeq += 1

            # Write the RTSP request to be sent.
            request = 'SETUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)

            # Keep track of the sent request.
            self.requestSent = self.SETUP

        # Play 
        elif requestCode == self.PLAY and self.state == self.READY:
            # Update RTSP sequence number.
            self.rtspSeq += 1

            # Write the RTSP request to be sent.
            request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

            # Keep track of the sent request.
            self.requestSent = self.PLAY

        # Pause 
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            # Update RTSP sequence number.
            self.rtspSeq += 1

            # Write the RTSP request to be sent.
            request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + \
                str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

            # Keep track of the sent request.
            self.requestSent = self.PAUSE

        # Teardown 
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            # Update RTSP sequence number.
            self.rtspSeq += 1

            # Write the RTSP request to be sent.
            request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + \
                str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

            # Keep track of the sent request.
            self.requestSent = self.TEARDOWN
        elif requestCode == self.FORWARD and not self.state == self.INIT:
            self.rtspSeq += 1
            request = 'FORWARD ' + self.fileName + ' RTSP/1.0\nCSeq: ' + \
                str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

            # Keep track of the sent request.
            self.requestSent = self.FORWARD
        elif requestCode == self.BACKWARD and not self.state == self.INIT:
            self.rtspSeq += 1
            request = 'BACKWARD ' + self.fileName + ' RTSP/1.0\nCSeq: ' + \
                str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

            # Keep track of the sent request.
            self.requestSent = self.BACKWARD
        
            
        else:
            return

        # Send the RTSP request using rtspSocket.
        self.rtspSocket.send(bytes(request, "utf-8"))

        print('\nData sent:\n' + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        # TODO
        while True:
            reply = self.rtspSocket.recv(1024)
            if reply:
                self.parseRtspReply(reply.decode("utf-8"))
            # Close the RTSP socket (TEARDOWN)
            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        # TODO
        lines = data.split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # Process only if the server reply's sequence number is the same as the request's one
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            # New RTSP session ID
            if self.sessionId == 0:
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:
                        # -------------
                        # TO COMPLETE
                        # -------------
                        # Update RTSP state.
                        self.state = self.READY

                        # Open RTP port.
                        self.openRtpPort()
                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY

                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()
                    elif self.requestSent == self.TEARDOWN:
                        self.state = self.INIT

                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # -------------
        # TO COMPLETE
        # -------------
        # Create a new datagram socket to receive RTP packets from the server
        # self.rtpSocket = ...
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set the timeout value of the socket to 0.5sec
        self.rtpSocket.settimeout(0.5)

        try:
            # Bind the socket to the address using the RTP port given by the client user
            self.rtpSocket.bind(("", self.rtpPort))
        except:
            tkinter.messagebox.showwarning(
                'Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        # TODO
        self.pauseMovie()
        if tkinter.messagebox.askokcancel("EXIT", "Are you sure to exit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            self.playMovie()
