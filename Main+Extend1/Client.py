from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket
import threading
import sys
import traceback
import os
import time

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

    counter = 0

    payload = 0

    start_time = 0
    end_time = 0
    execute_time = 0

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

    # THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI
    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup["activebackground"] = "red"
        self.setup["bd"] = 3
        self.setup.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start["activebackground"] = "red"
        self.start["bd"] = 3
        self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause["activebackground"] = "red"
        self.pause["bd"] = 3
        self.pause.grid(row=1, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown["activebackground"] = "red"
        self.teardown["bd"] = 3
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4,
                        sticky=W+E+N+S, padx=5, pady=5)

    def setupMovie(self):
        #Khi nút SETUP được nhấn
        if self.state == self.INIT:
            #Gửi yêu cầu SETUP lên Server
            self.sendRtspRequest(self.SETUP)

    def exitClient(self):
        #Khi nút TEARDOWN được nhấn
        #Dùng để tính video data rate
        if self.start_time:
            self.end_time = time.time()
            self.execute_time += self.end_time - self.start_time
        #Gửi yêu cầu TEARDOWN lên Server
        self.sendRtspRequest(self.TEARDOWN)
        #Đóng GUI
        self.master.destroy() 
        #Xóa các file hình ảnh trong bộ nhớ đệm
        os.remove(CACHE_FILE_NAME + str(self.sessionId) +
                  CACHE_FILE_EXT)  
        # Tính và in ra RTP packet loss rate
        if self.frameNbr:
            lossrate = float((self.frameNbr - self.counter)/self.frameNbr)
            print("RTP Packet loss rate: " + str(lossrate))
        # Tính và in ra video data rate
        if self.execute_time:
            datarate = self.payload / self.execute_time
            print("Video data rate: " + str(datarate) + " bytes per second")

    def pauseMovie(self):
        #Khi nút PAUSE đươc nhấn
        if self.state == self.PLAYING:
            #Gửi yêu cầu PAUSE lên máy chủ
            self.end_time = time.time()
            self.execute_time += self.end_time - self.start_time
            self.start_time = 0
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self):
        #Khi nút Button được nhấn
        if self.state == self.READY:
            self.start_time = time.time()
            #Tạo một luồng để nhận các gói RTP
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()

            #Gửi yêu cầu PLAY lên Server
            self.sendRtspRequest(self.PLAY)

    def listenRtp(self):
        #Nhận các gói RTP
        while True:
            try:
                #Nhận gói RTP tối đa 20480 byte vào biến data
                data = self.rtpSocket.recv(20480)
                #Nếu biến data không rỗng thì phân tách gói RTP nhận được
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    #Lấy số thứ tự RTP
                    currentFrameNbr = rtpPacket.seqNum()
                    self.counter += 1
                    print("Current Seq Num: " + str(currentFrameNbr))

                    #Bỏ qua gói tin trễ
                    if currentFrameNbr > self.frameNbr: 
                        # Tính payload
                        self.payload += len(rtpPacket.getPayload())
                        #Cập nhật số thứ tự RTP
                        self.frameNbr = currentFrameNbr
                        #Chuyển gói tin vừa nhận được thành hình ảnh và phát lên GUI
                        self.updateMovie(self.writeFrame(
                            rtpPacket.getPayload()))
            except:
                #Dừng nhận gói tin khi nút PAUSE  và TEARDOWN được nhấn
                if self.playEvent.isSet():
                    break

               #Dóng Socket RTP khi nút TEARDOWN được nhấn
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        #Ghi các Frame nhận được vào tệp hình ảnh

        #Tạo tên file
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        #Tạo file hình ảnh
        file = open(cachename, "wb")
        #Ghi dữ liệu frame vào tệp hình ảnh
        file.write(data)
        #đóng file
        file.close()

        #Trả về tệp hình ảnh
        return cachename

    def updateMovie(self, imageFile):
        #cập nhật tệp hình ảnh dưới dạng khung video
        photo=ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo, height=288)
        self.label.image=photo

    def connectToServer(self):
        #Tạo một Socket, bắt đầu một phiên RTPS/TCP
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            #Thiết lập kết nối TCP
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            #Nếu không thiết lập được thfi thông báo
            tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

    def sendRtspRequest(self, requestCode):
       #Gửi một yêu cầu từ Client lên Server

       #Gửi yêu cầu SETUP
        if requestCode == self.SETUP and self.state == self.INIT:
            #Tạo một thread để nhận phản hồi yêu cầu
            threading.Thread(target=self.recvRtspReply).start()
            #Cập nhật số thứ tự RTPS
            self.rtspSeq += 1

            #Viết yêu cầu
            request = 'SETUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)

           #Theo dõi yêu cầu đã gửi
            self.requestSent = self.SETUP

        # Gửi yêu cầu PLAY
        elif requestCode == self.PLAY and self.state == self.READY:
            # Cập nhật số thứ tự RTPS
            self.rtspSeq += 1

            #Viết yêu cầu
            request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

            #Theo dõi yêu cầu đã gửi
            self.requestSent = self.PLAY

        # Gửi yêu cầu PAUSE
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            #Cập nhật số thứ tự RTPS
            self.rtspSeq += 1

            #Viết yêu cầu
            request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

            #Theo dõi yêu cầu đã gửi
            self.requestSent = self.PAUSE

        # Gửi yêu cầu TEARDOWN
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            #Cập nhật số thứ tự RTPS
            self.rtspSeq += 1

            # Viết yêu cầu 
            request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

            #Theo dõi yêu cầu đã gửi
            self.requestSent = self.TEARDOWN
        else:
            #Nếu không có yêu cầu nào được gửi thì thoát
            return

        #Gửi yêu cầu lên Server
        self.rtspSocket.send(bytes(request, "utf-8"))

        #In gói đã gửi
        print('\nData sent:\n' + request)

    def recvRtspReply(self):
        #Nhận phản hồi từ Server
        while True:
            #Nhận tối đa 1024 byte
            reply = self.rtspSocket.recv(1024)
            if reply:
                #Nếu gói tin không rỗng, chuyển chuỗi bit về dạng chuỗi kí tự Unicode 8bit
                self.parseRtspReply(reply.decode("utf-8"))
            #Nếu yêu cầu hiện tại là TEARDOWN thì hủy kết nối Socket
            if self.requestSent == self.TEARDOWN:
                #Tắt việc đọc và viết vào socket
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                #Đóng socket
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
       #Phân tách phản hồi từ Server

       #data là một danh sách  chứa 3 thành phần
        lines = data.split('\n')
        #lấy số thứ tự RTPS
        seqNum = int(lines[1].split(' ')[1])

       #Chỉ xử lí nếu số thứ tự của máy chủ bằng với số thứ tự của yêu cầu
        if seqNum == self.rtspSeq:
            #Lấy phiên bản
            session = int(lines[2].split(' ')[1])

            #Tạo một ID phiên mới
            if self.sessionId == 0:
                self.sessionId = session

            # Chỉ xử lí nếu ID phiên giống nhau
            if self.sessionId == session:
                #Nếu mã trạng thái 200 OK (Yêu cầu đã thành công và 
                #thông tin được trả lại trong phản hồi)
                if int(lines[0].split(' ')[1]) == 200:

                    if self.requestSent == self.SETUP:
                        #Trngaj thái sẵn sàng
                        self.state = self.READY

                        #Mở Soclet để bắt đầu gửi các gói RTP
                        self.openRtpPort()
                    elif self.requestSent == self.PLAY:
                        #Trạng thái đang phát
                        self.state = self.PLAYING
                    elif self.requestSent == self.PAUSE:
                        #Trạng thái sẵn sàng
                        self.state = self.READY

                        #Kết thúc một luồng, tạo một luồng mới
                        self.playEvent.set()
                    elif self.requestSent == self.TEARDOWN:
                        #Trở về trạng thái bắt đầu
                        self.state = self.INIT

                        #Khởi tạo cờ để khóa Socket
                        self.teardownAcked = 1

    def openRtpPort(self):
        #Tạo Socket để truyền RTP/UDP
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        #Dặt thời gian chờ của Socket
        self.rtpSocket.settimeout(0.5)

        try:
            #Ràng buộc Socket với địa chỉ RTP do máy chủ cung cấp
            self.rtpSocket.bind(("", self.rtpPort))
        except:
            #Nếu không kết nối được thfi gửi thông báo
            tkinter.messagebox.showwarning(
                'Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        #Đóng cửa sổ GUI

        #Ngừng phát video
        self.pauseMovie()
        #Hỏi người dùng có thật sự muốn thoát
        if tkinter.messagebox.askokcancel("EXIT", "Are you sure to exit?"):
            #Nếu dược xác nhận thì đóng
            self.exitClient()
        else: 
            #Nếu người dùng hủy, thì tiếp tục phát video
            self.playMovie()