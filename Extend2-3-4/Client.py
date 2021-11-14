from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
import datetime
from RtpPacket import RtpPacket
import time

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
    DESCRIBE = 4
    FORWARD = 5
    BACKWARD= 6

    checkSocketIsOpen = False
    checkPlay = False
    flagFirstPlay= True
    counter = 0

    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)

        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.currentTime = 0
        self.frameNbr = 0
        self.totalTime = 0

        self.flagForward = 0
        self.flagBackward = 0
        self.createWidgets()

        # statistical data
        

        #self.setupMovie()

    def createWidgets(self):
        """Build GUI."""
        # Create Play button
        self.start = Button(self.master, width=15, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["activebackground"] = "red"
        self.start["command"] = self.playMovie
        self.start.grid(row=2, column=0, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=15, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["activebackground"] = "red"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=2, column=1, padx=2, pady=2)

        # Create Stop button
        self.stop = Button(self.master, width=15, padx=3, pady=3)
        self.stop["text"] = "Stop"
        self.stop["activebackground"] = "red"
        self.stop["command"] = self.resetMovie
        self.stop.grid(row=2, column=2, padx=2, pady=2)

        # Create Describe button
        self.describe = Button(self.master, width=15, padx=3, pady=3)
        self.describe["text"] = "Describe"
        self.describe["activebackground"] = "red"
        self.describe["command"] = self.describeMovie
        self.describe.grid(row=2, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=18)
        self.label.grid(row=0, column=0, columnspan=5, sticky=W + E + N + S, padx=5, pady=5)

        # Create a label to display total time of the movie
        self.totaltimeInfor = Label(self.master, width=16, text="Total time: 00:00")
        self.totaltimeInfor.grid(row=1, column=3, columnspan=1, padx=5, pady=5)

        # Create a label to display remaining time of the movie

        self.remainTimeBox = Label(self.master, width=16, text="Remaining time: 00:00")
        self.remainTimeBox.grid(row=1, column=0, columnspan=1, padx=5, pady=5)

        # Create forward button
        self.forward = Button(self.master, width=15, padx=3, pady=3)
        self.forward["text"] = ">>"
        self.forward["activebackground"] = "red"
        self.forward["command"] = self.forwardMovie
        self.forward.grid(row=1, column=2, padx=2, sticky= E + W, pady=2)

        # Create backward button
        self.backward = Button(self.master, width=15, padx=3, pady=3)
        self.backward["text"] = "<<"
        self.backward["activebackground"] = "red"
        self.backward["command"] = self.backwardMovie
        self.backward.grid(row=1, column=1, sticky = E + W, padx=2, pady=2)



    def describeMovie(self):
        """Describe button handler"""
        self.sendRtspRequest(self.DESCRIBE)

    def setupMovie(self):
        """Setup button handler."""
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)

    def resetMovie(self):
        """Teardown button handler."""
        if self.checkPlay:
            self.checkPlay = False
            self.sendRtspRequest(self.TEARDOWN)
            try:
                for i in os.listdir():
                    if i.find(CACHE_FILE_NAME) == 0:
                        os.remove(i)
            except:
                pass
            time.sleep(1)
            self.rtspSeq = 0
            self.sessionId = 0
            self.requestSent = -1
            self.teardownAcked = 0
            self.counter = 0
            self.flagFirstPlay = True
            self.flagForward = 0
            self.flagBackward = 0
            self.currentTime = 0
            # if not (self.checkSocketIsOpen):
            self.connectToServer()
            self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.label.pack_forget()
            self.label.image = ''
            

    def pauseMovie(self):
        """Pause button handler."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)


    def playMovie(self):
        """Play button handler."""
        if self.state == self.INIT and self.flagFirstPlay == True:
            self.flagFirstPlay = False
            self.checkPlay = True
            self.frameNbr = 0
            self.setupMovie()
            while self.state != self.READY:
                pass

        if self.state == self.READY:
            self.checkPlay = True
            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)

    def forwardMovie(self):
        self.sendRtspRequest(self.FORWARD)
        self.flagForward = 1

    def backwardMovie(self):
        self.sendRtspRequest(self.BACKWARD)
        if self.frameNbr <= 50:
            self.frameNbr = 0
        else:
            self.frameNbr -= 50
        self.flagBackward = 1
    
    def displayDescription(self, lines):
        top = Toplevel()
        top.title("Description")
        top.geometry('300x180')
        listboxret = Listbox(top, width=50, height=30)
        listboxret.insert(1, "Describe: ")
        listboxret.insert(2, "Video Name: " + str(self.fileName))
        listboxret.insert(3, lines[1])
        listboxret.insert(4, lines[2])
        listboxret.insert(5, lines[3])
        listboxret.insert(6, lines[4])
        listboxret.insert(7, lines[5])
        listboxret.insert(8, lines[6])
        listboxret.insert(9, lines[7])
        listboxret.insert(10, lines[8])
        listboxret.pack()

    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:

                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    
                    print("Current Seq Num: " + str(rtpPacket.seqNum()))
                    
                    try:
                        if (self.frameNbr + 1 != rtpPacket.seqNum()) & (not(self.flagForward | self.flagBackward)):
                            print('count: ',self.counter)
                            self.counter += 1
                            print('=' * 100 + "\n\nLoss Packet\n\n" + '=' * 100)
                        currFrameNbr = rtpPacket.seqNum()
                        self.currentTime = int(currFrameNbr * 0.05)
                        # Update remaining time
                        self.totaltimeInfor.configure(text="Total time: %02d:%02d" % (self.totalTime // 60, self.totalTime % 60))
                        self.remainTimeBox.configure(text="Remaining time: %02d:%02d" % ((self.totalTime - self.currentTime)// 60, (self.totalTime - self.currentTime) % 60))
                    


                    except:
                        print("seqNum() Error \n")
                        traceback.print_exc(file=sys.stdout)
                        print("\n")
                    if currFrameNbr > self.frameNbr:  # Discard the late packet
                        self.frameNbr = currFrameNbr
                        self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
                        # statUpdate
                       
            except:
                # Stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    
                    break

                # Upon receiving ACK for TEARDOWN request,
                # close the RTP socket
                if self.teardownAcked == 1:
                    
                    self.checkSocketIsOpen = False
                    try:
                        self.rtpSocket.shutdown(socket.SHUT_RDWR)
                        self.rtpSocket.close()
                    except:
                        pass
                    break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()
        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo, height=288)
        self.label.image = photo

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.checkSocketIsOpen = True
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
        # Setup request
        if requestCode == self.SETUP:  # and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "SETUP %s RTSP/1.0\nCSeq: %d\nTRANSPORT: RTP/UDP; Client_port= %d" % (self.fileName, self.rtspSeq, self.rtpPort)

            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.SETUP
        # Play request
        elif requestCode == self.PLAY:  # and self.state == self.READY:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "PLAY %s RTSP/1.0\nCSeq: %d\nSESSION: %d" % (self.fileName, self.rtspSeq, self.sessionId)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.PLAY
        # Pause request
        elif requestCode == self.PAUSE:  # and self.state == self.PLAYING:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "PAUSE %s RTSP/1.0\nCSeq: %d\nSESSION: %d" % (self.fileName, self.rtspSeq, self.sessionId)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.PAUSE
        # Teardown request
        elif requestCode == self.TEARDOWN:  # and not self.state == self.INIT:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "TEARDOWN %s RTSP/1.0\nCSeq: %d\nSESSION: %d" % (self.fileName, self.rtspSeq, self.sessionId)

            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.TEARDOWN
        elif requestCode == self.DESCRIBE:
            self.rtspSeq = self.rtspSeq + 1
            request = "DESCRIBE %s RTSP/1.0\nCSeq: %d\nSESSION: %d" % (self.fileName, self.rtspSeq, self.sessionId)
            self.requestSent = self.DESCRIBE

        elif requestCode == self.FORWARD:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "FORWARD %s RTSP/1.0\nCSeq: %d\nSESSION: %d" % (self.fileName, self.rtspSeq, self.sessionId)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.FORWARD

        elif requestCode == self.BACKWARD:
            # Update RTSP sequence number.
            # ...
            if self.rtspSeq <= 50:
                self.rtspSeq = 0
            else:
                self.rtspSeq = self.rtspSeq - 50
            # Write the RTSP request to be sent.
            # request = ...
            request = "BACKWARD %s RTSP/1.0\nCSeq: %d\nSESSION: %d" % (self.fileName, self.rtspSeq, self.sessionId)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.BACKWARD

        else:
            return

        # Send the RTSP request using rtspSocket.
        # ...
        self.rtspSocket.send(request.encode())
        print('\nData sent:\n' + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))

            # Close the RTSP socket upon requesting Teardown
            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = data.split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # Process only if the server reply's sequence number is the same as the request's
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
                        # self.state = ...
                        self.totalTime = float(lines[3].split(' ')[1])
                        self.state = self.READY
                        # Open RTP port.
                        self.openRtpPort()
                    elif self.requestSent == self.PLAY:
                        # self.state = ...
                        self.state = self.PLAYING
                        
                    elif self.requestSent == self.PAUSE:
                        # self.state = ...
                        self.state = self.READY

                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()
                    elif self.requestSent == self.TEARDOWN:
                        # self.state = ...
                        self.state = self.INIT
                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1

                    elif self.requestSent == self.DESCRIBE:
                        # self.state = ...
                        self.displayDescription(lines)

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # -------------
        # TO COMPLETE
        # -------------
        # Create a new datagram socket to receive RTP packets from the server
        # self.rtpSocket = ...
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the timeout value of the socket to 0.5sec
        # ...
        self.rtpSocket.settimeout(0.5)
        try:
            # Bind the socket to the address using the RTP port given by the client user
            # ...
            self.state = self.READY
            self.rtpSocket.bind(('', self.rtpPort))
        except:
            tkinter.messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self): 
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if tkinter.messagebox.askokcancel("Quit?", "Are you sure to quit?"):
            self.sendRtspRequest(self.TEARDOWN)
            if (self.checkSocketIsOpen and self.state != self.INIT):
                self.rtpSocket.shutdown(socket.SHUT_RDWR)
                self.rtpSocket.close()
            self.master.destroy()  
            sys.exit(0)


    

    


