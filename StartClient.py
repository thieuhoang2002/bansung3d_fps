from ursina import *
from helpers.CustomLib import *
from networks.Login import LoginForm
from networks.client import MyClient
from data.Map import Map
from networks.database import getIpServer

def start_game(username):
    app = Ursina()

    my_client = MyClient(username, str(getIpServer()), 6000, Vec3(0, 1.4, 0))
    Sky()
    my_map = Map()

    def input(key):
        if key == Keys.escape:
            app.user_exit()
        if my_client:
            my_client.input(key)

    def update():
        if my_client:
            my_client.client.process_net_events()
            my_client.easy.process_net_events()
            for bullet in my_client.other_bullet:
                bullet.update()
            my_client.chatMessage.scrollcustom()

    app.run()

if __name__ == "__main__":
    # Chỉ khởi tạo login form, chưa có game
    LoginForm([start_game])
