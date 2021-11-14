import sys, socket

from ServerWorker import ServerWorker

class Server:
	
	def main(self):
		#print('Server: def main')
		try: # Xử lý nhập SERVER_PORT
			SERVER_PORT = int(sys.argv[1])
		except:
			print("[Usage: Server.py Server_port]\n")
		rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
		rtspSocket.bind(('', SERVER_PORT)) 
		rtspSocket.listen(5)

		
		while True:
			clientInfo = {}
			clientInfo['rtspSocket'] = rtspSocket.accept()
			ServerWorker(clientInfo).run()
	
if __name__ == "__main__":
	(Server()).main()