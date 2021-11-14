class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0
		
	def nextFrame(self):
		"""Get next frame."""
		data = self.file.read(5) # Get the framelength from the first 5 bits
		if data: 
			framelength = int(data)
							
			# Read the current frame
			data = self.file.read(framelength)
			self.frameNum += 1
		return data
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum
	def get_total_time_video(self):
		count_frame=0
		while True:
			data = self.file.read(5)
			if data:
				framelength = int(data)
				data = self.file.read(framelength)
				count_frame += 1
			else:
				self.file.seek(0)
				break
		return count_frame	

	def previousFrame():
		pass
	