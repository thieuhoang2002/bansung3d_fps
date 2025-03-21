from ursinanetworking import easyursinanetworking
from ursinanetworking import *
from twisted.internet.protocol import DatagramProtocol
import pyaudio
from data.RandomPosition import playerRandomPositions
# server = UrsinaNetworkingServer('192.168.167.238', 6000)
class MyServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.start_server = True
        self.update_server = False
        self.server = None
        self.easy = None
        self.user_active = {}
        self.messages = []
        self.notifycation = None
        self.notifycation_content = None
        self.audioPort = 3000
        self.numberOfPlayers = 0

    def handle(self):
        if self.start_server:
            self.server = UrsinaNetworkingServer(self.ip, self.port)
            self.easy = easyursinanetworking.EasyUrsinaNetworkingServer(self.server)
            print("Server đã khởi tạo và đăng ký các event.")

            @self.server.event
            def onClientConnected(Client):
                print(f"{Client.id} joined game")
                self.numberOfPlayers += 1
                start_position = playerRandomPositions[Client.id]  # Gán vị trí ngẫu nhiên dựa vào ID

                # Tạo replicated variable
                self.easy.create_replicated_variable(Client.id,
                    {
                        "id": Client.id,
                        'position': start_position,  
                        'rotation': (0,0,0),
                        'status': 'stand',
                        'hp': 100,
                    }
                )

            # Debug danh sách player trên server
                print("🔵 Danh sách replicated trên server sau khi cập nhật:", self.easy.replicated_variables)

                # Gửi ID và danh sách toàn bộ player về client mới
                Client.send_message('GetID', Client.id)
                Client.send_message('updatePosition', start_position)
                Client.send_message('allPlayersData', {pid: data.content for pid, data in self.easy.replicated_variables.items()})

                # Thông báo với các client khác về người chơi mới
                self.server.broadcast('newPlayerLogin', {'id': Client.id, 'position': start_position})


            @self.server.event
            def onClientDisconnected(Client):
                print(f"{Client} leave game")
                # self.notifycation_content.text += "\n" + f"{Client.id} leave game"
                self.easy.remove_replicated_variable_by_name(Client.id)
                self.server.broadcast('existedClientDisConnected', Client.id)

            @self.server.event
            def messageFromClient(Client,message):
                print(f"{message}")
                # self.notifycation_content.text += "\n" + f"chatmessage feature: {message}"
                self.server.broadcast('newMessage',message)

            @self.server.event
            def updatePosition(Client, content):
                if Client.id in self.easy.replicated_variables:
                    self.easy.update_replicated_variable_by_name(Client.id, 'position', content)
                    self.server.broadcast('updateOtherPlayerPosition', {'id': Client.id, 'position': content})


            @self.server.event
            def updateRotation(Client, content):
                # Cập nhật biến replicated
                self.easy.update_replicated_variable_by_name(Client.id, 'rotation', content)
                # Broadcast thông tin xoay cho các client
                self.server.broadcast('updateOtherPlayerRotation', {'id': Client.id, 'rotation': content})

            @self.server.event
            def updateStatus(Client, content):
                self.easy.update_replicated_variable_by_name(Client.id, 'status', content)
                # Broadcast trạng thái (running, stand) cho các client
                self.server.broadcast('updateOtherPlayerStatus', {'id': Client.id, 'status': content})


            @self.server.event
            def clientShooting(Client,content):
                print('server recieved client shooting signal:', content)
                self.server.broadcast('bulletFromOtherPlayer',{
                    'id':Client.id,
                    'position': tuple(content['position']),
                    'direction':content['direction'],
                })
                print(f"Broadcasting bullet from player {Client.id} at position {content['position']}")

            @self.server.event
            def player_shot(Client, content):
                try:
                    target_id = content.get('id')
                    # Lấy dữ liệu người chơi từ replicated variables
                    if target_id in self.easy.replicated_variables:
                        current_data = self.easy.replicated_variables[target_id].content
                        current_hp = current_data.get('hp', 100)  # Mặc định là 100 nếu không có hp
                        new_hp = current_hp - 20
                        # Cập nhật lại replicated variable cho HP
                        self.easy.update_replicated_variable_by_name(target_id, 'hp', new_hp)
                        print(f"Server: Người chơi {target_id} bị bắn! HP thay đổi từ {current_hp} xuống {new_hp}")
                        # Broadcast kết quả giảm HP cho tất cả client
                        self.server.broadcast('decrease_hp', {'id': target_id, 'hp': new_hp})
                    else:
                        print(f"Server: Không tìm thấy thông tin cho người chơi {target_id}")
                except Exception as e:
                    print("Lỗi trong player_shot:", e)
            
            @self.server.event
            def checkPlayerSurvival(Client, content):
                dead_id = content.get('id')
                print('Server: Nhận checkPlayerSurvival từ người chơi', dead_id)
                
                # Loại bỏ người chơi chết khỏi replicated variables
                self.easy.remove_replicated_variable_by_name(dead_id)
                
                # Tính lại số người chơi còn sống
                remaining_players = list(self.easy.replicated_variables.keys())
                print("Server: Người chơi còn sống:", remaining_players)
                
                if len(remaining_players) == 1:
                    winner = int(remaining_players[0])
                    print(f"Server: Đã xác định người thắng là {winner}")
                    self.server.broadcast('endGame', {'id': winner})

            
            @self.server.event
            def openOtherVoiceChat(Client, content):
                print(content)
                self.server.broadcast('hearFromOtherClient', content)
                
            @self.server.event
            def stopOtherVoiceChat(Client, content):
                print(content)
                self.server.broadcast('stopHearFromOtherClient', content)

            @self.server.event
            def resetGameRequest(Client, content):
                print("Server: Nhận yêu cầu reset game từ Client:", Client.id)

                # Xóa toàn bộ replicated variables cũ
                for key in list(self.easy.replicated_variables.keys()):
                    self.easy.remove_replicated_variable_by_name(key)

                # Tạo lại danh sách người chơi với vị trí mới
                new_players_data = {}
                for client in self.server.clients:
                    client_id = client.id  
                    start_position = playerRandomPositions[int(client_id)]  # Lấy vị trí mới
                    self.easy.create_replicated_variable(client_id, {
                        "id": client_id,
                        'position': start_position,
                        'rotation': (0,0,0),
                        'status': 'stand',
                        'hp': 100
                    })
                    new_players_data[str(client_id)] = {
                        'position': start_position,
                        'hp': 100
                    }

                # Gửi dữ liệu mới về tất cả client
                print("Server: Broadcast reset_game với dữ liệu mới:", new_players_data)
                self.server.broadcast('reset_game', new_players_data)


            self.start_server = False
            self.update_server = True


    def input(self,key):
        if held_keys[ 'w']:
            self.notifycation_content.y += .05
        if held_keys['s']:
            self.notifycation_content.y -=.05
        if held_keys[ 'a']:
            self.notifycation_content.x -=.05
        if held_keys[ 'd']:
            self.notifycation_content.x +=.05
        if key =='space':
            print(self.notifycation_content.position)
            

