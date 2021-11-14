import sys
from time import time
HEADER_SIZE = 12

class RtpPacket:	
	header = bytearray(HEADER_SIZE)
	
	def __init__(self):
		pass
		
	def encode(self, version, padding, extension, cc, seqnum, marker, pt, ssrc, payload):
		timestamp=int(time())  #lấy thời gian hiện tại
		header=bytearray(HEADER_SIZE)

        #Điền vào bytearray tiêu đề với các trường tiêu đề RTP

        #cho biết phiên bản của giao thức, chiếm 2bits
		header[0] = (header[0] | version << 6) & 0xC0

        # P (Padding): (1 bit) Được sử dụng để cho biết  nếu có thêm byte đệm ở cuối gói RTP.
		header[0] = (header[0] | padding << 5)

        #X (Phần mở rộng): (1 bit) Cho biết sự hiện diện của  tiêu đề mở rộng giữa tiêu 
        #đề và dữ liệu trọng tải.
		header[0] = (header[0] | extension << 4) # 1 bit

        #CC (Đếm CSRC): (4 bit) Chứa số lượng nhận dạng CSRC
		header[0] = (header[0] | (cc & 0x0F))  

        #M (Marker): (1 bit) Báo hiệu được sử dụng ở  cấp ứng dụng theo cách cụ thể.
		header[1] = (header[1] | marker << 7)   

        #PT (Loại tải trọng): (7 bit) Cho biết định dạng của tải trọng và do đó xác định 
        #cách giải thích của nó bởi ứng dụng.
		header[1] = (header[1] | (pt & 0x7f))     

        #Số thứ tự: (16 bit) Số thứ tự được tăng lên cho mỗi gói dữ liệu RTP được gửi 
        #đi và sẽ được người  nhận sử dụng để phát hiện mất gói [1] và để đáp ứng việc 
        #phân phối không theo thứ tự.
		header[2] = (seqnum & 0xFF00) >> 8 
		header[3] = (seqnum & 0xFF)

        #Dấu thời gian: (32 bit) Được bộ thu sử dụng để phát lại các mẫu đã nhận tại thời 
        #điểm và khoảng thời gian thích hợp. Khi có nhiều luồng phương tiện, các dấu thời 
        #gian có thể độc lập trong mỗi luồng.
		header[4] = (timestamp >> 24) # 32 bit timestamp
		header[5] = (timestamp >> 16) & 0xFF
		header[6] = (timestamp >> 8) & 0xFF
		header[7] = (timestamp & 0xFF)

        #SSRC: (32 bit) Mã định danh nguồn đồng bộ hóa xác định duy nhất nguồn của một luồng.
		header[8] = (ssrc >> 24); # 32 bit ssrc
		header[9] = (ssrc >> 16) & 0xFF
		header[10] = (ssrc >> 8) & 0xFF

		self.header=header
		self.payload=payload
		
	def decode(self, byteStream):
		"""Decode the RTP packet."""
		self.header = bytearray(byteStream[:HEADER_SIZE])
		self.payload = byteStream[HEADER_SIZE:]
	
	def version(self):
		"""Return RTP version."""
		return int(self.header[0] >> 6)
	
	def seqNum(self):
		"""Return sequence (frame) number."""
		seqNum = self.header[2] << 8 | self.header[3]
		return int(seqNum)
	
	def timestamp(self):
		"""Return timestamp."""
		timestamp = self.header[4] << 24 | self.header[5] << 16 | self.header[6] << 8 | self.header[7]
		return int(timestamp)
	
	def payloadType(self):
		"""Return payload type."""
		pt = self.header[1] & 127
		return int(pt)
	
	def getPayload(self):
		"""Return payload."""
		return self.payload
		
	def getPacket(self):
		"""Return RTP packet."""
		return self.header + self.payload
