import sys
from pyexpat import model
from random import random, randint
from direct.actor.Actor import Actor
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

from modules.BulletManage import BulletManage
from modules.Bullet import Bullet
from modules.Character import Character
from modules.CustomHearbar import CustomHealthBar
from helpers.CustomLib import createMyCube

class Player(FirstPersonController):
    def __init__(self, client, position, clientCallback, ignorePosition, player_info):
        self.client = client
        self.player_info = player_info
        self.ndk_death_message = None
        self.death_text = None  # Thêm biến để lưu thông báo từ death()
        self.character = Character(position)
        self.modController = 1
        self.clientCallback = clientCallback
        self.cubeModel = createMyCube(position.x, position.z, 25, color.black)
        self.cubeModel.visible_setter(False)
        self.cubeModel.y+= 10
        super().__init__(
            position=position,
            model=self.character.stand_entity,
            jump_height=20.5,
            jump_duration=0.05,
            gravity=10,
            origin_y=1,
            # collider="box",
            speed=100
        )
        self.bulletNotification = BulletManage()
        self.ignorePosition = ignorePosition
        self.walksound = Audio('asset/static/sound_effect/running-sounds.mp3', loop = True)
        self.reload = Audio('asset/static/sound_effect/reload.mp3', loop=False, autoplay=False)
        self.walksound.volume = 0
        self.walksound.autoplay = True
        self.bullet = None
        self.cursor.color = color.rgba(255, 0, 0, 122)
        self.ak47 = Entity(parent=camera,
                           model='asset/static/gun/G32SMGModel.fbx',
                           texture='asset/static/gun/gun_blue_violet_texture.png',
                           scale=.18,
                           position=(1, -6, 0),
                           collider = 'box',
                           visible=False)
        self.pistol = Entity(parent=camera,
                                    model='asset/static/gun/Beretta Pistol.fbx',
                                    texture='asset/static/gun/RenderResult.png',
                                    scale=0.03,  # Chỉnh sửa kích thước
                                    position=(8, -10, 24),
                                    visible=False
                                    )

        self.gun = [self.ak47, self.pistol]
        self.curr_weapon = 0
        self.switch_weapon()
        
        self.healthbar = CustomHealthBar(1, (0,0,0))
        self.death_message_shown = False
        # difine for camera position
        camera.y = 50
        camera.z = -60
        # switch to third controller
        self.ndk_switch_mode(1)
        self.print_position_for_test()
        self.just_reset = False
        

    def print_position_for_test(self):
        print('class player - position',self.position)
        print('class player - world position',self.world_position)
    def switch_weapon(self):
        for i,v in enumerate(self.gun):
            if i == self.curr_weapon:
                v.visible = True
            else:
                v.visible = False
    def input(self, key):
        self.healthbar.input(key)
        # first controller
        try:
            weapon_index = int(key) - 1
            if 0 <= weapon_index < len(self.gun):
                self.curr_weapon = weapon_index
                self.switch_weapon()
        except ValueError:
            pass
        if key == Keys.escape:
            sys.exit()
        #súng 1 là ak
        if key == '1' and self.modController == 1:
            self.curr_weapon = self.gun.index(self.ak47)
            self.switch_weapon()
        # súng 2 là pistol
        if key == '2' and self.modController == 1:
            self.curr_weapon = self.gun.index(self.pistol)
            self.switch_weapon()
        # bắn bằng trái chuột
        if key == 'left mouse down' and self.modController == 1:
            self.shootBullet()
        if key == 'space':
            # self.jump()
            pass
        if key == 'r':
            self.modController = 1
            self.ndk_switch_mode(self.modController)
        #nạp lại đạn
        if key == 'f':
            if self.bulletNotification.num < 5:
                self.bulletNotification.setnumOfBullet(5)
                self.reload.play()
        if key == 't':
            self.modController = 3
            self.ndk_switch_mode(self.modController)
        # third controller 
        if held_keys['w'] and self.modController == 3:
            self.character.running_entity.visible = True
            self.model = self.character.running_entity
        if not held_keys['w'] and not held_keys['s'] and not held_keys['a'] and not held_keys['d'] and self.modController == 3:
            self.character.running_entity.visible = False
            self.model = self.character.stand_entity
            self.character.running_entity.rotation_y = 180
        if held_keys['s'] and self.modController == 3:
            self.character.running_entity.visible = True
            self.model = self.character.running_entity
            self.character.running_entity.rotation_y = 0
        if held_keys['a'] and self.modController == 3:
            self.character.running_entity.visible = True
            self.model = self.character.running_entity
            self.character.running_entity.rotation_y = 90
        if held_keys['d'] and self.modController == 3:
            self.character.running_entity.visible = True
            self.model = self.character.running_entity
            self.character.running_entity.rotation_y = 270
        if held_keys['a'] or held_keys['s'] or held_keys['d'] or held_keys['w']:
            self.print_position_for_test()
        if key == Keys.enter:
            print('vi tri nguoi choi:', self.world_position)



    def ndk_death(self):
        for gun in self.gun:
            gun.disable()  # Ẩn súng
        self.disable()  # Tắt bộ điều khiển
        self.ndk_death_message = Text(text="You are dead!", origin=Vec2(0, 0), scale=3)  # Hiển thị thông báo

    def ndk_revival(self):
        self.ndk_switch_mode(1)
        self.enable()
        if self.ndk_death_message:
            destroy(self.ndk_death_message)
            self.ndk_death_message = None
        if self.death_text:
            destroy(self.death_text)
            self.death_text = None
        self.death_message_shown = False  # Reset trạng thái hiển thị thông báo

    def reset(self, position):
            # Xóa model nhân vật cũ
            if self.character:
                destroy(self.character.stand_entity)
                destroy(self.character.running_entity)
                self.character = None
            # Tái tạo nhân vật mới
            self.character = Character(position)
            self.world_position = position  # Đồng bộ vị trí của FirstPersonController
            self.position = position
            self.character.stand_entity.world_position = position  # Đồng bộ entity trong Character
            self.character.running_entity.world_position = position
            self.healthbar.value = 100  # Reset máu
            self.model = self.character.stand_entity

            # Đồng bộ cubeModel
            if hasattr(self, 'cubeModel'):
                self.cubeModel.world_position = position + Vec3(0, 10, 0)
                print(f"Đã đặt cubeModel tại: {self.cubeModel.world_position}")

            self.ndk_revival()  # Bật lại nhân vật
            self.switch_weapon()  # Reset vũ khí

            self.just_reset = True  # Đánh dấu vừa reset
            invoke(lambda: setattr(self, 'just_reset', False), delay=0.1)  # Tắt sau 0.1 giây

            print(f"Đã reset Player tại: {self.world_position}")

    def ndk_switch_mode(self, controllerMode):
        if controllerMode == 3:
            for gun in self.gun:
                gun.disable()  # Ẩn súng
            self.character.stand_entity.visible = True
            self.character.running_entity.visible = False
        else:
            self.character.stand_entity.visible = False
            self.character.running_entity.visible = False
            for gun in self.gun:
                gun.enable()  # Bật súng
            self.curr_weapon = 0
            self.gun[self.curr_weapon].visible = True

    def update(self):
        if self.bullet:
            self.bullet.update()  # Cập nhật vị trí của viên đạn
        # self.healthbar.scale_x = self.health / 100 * self.healthbar_size.x
        if self.healthbar.value <= 0:
            if not self.death_message_shown:
                self.death_message_shown = True
                # Sử dụng callback để gửi thông điệp checkPlayerSurvival thay vì self.client.send_message
                self.client.client.send_message('checkPlayerSurvival', {'id': self.player_info['id']})
            self.ndk_death()

        else:
            if not self.just_reset:  # Chỉ chạy logic di chuyển nếu không vừa reset
                super().update()
        
                if held_keys['w'] or held_keys['a'] or held_keys['d'] or held_keys['s']:
                    self.cubeModel.x_setter(self.world_position.x)
                    self.cubeModel.z_setter(self.world_position.z)
                    if self.walksound.volume != 1:
                        self.walksound.volume += .1
                    
                if not held_keys['w'] and not held_keys['a'] and not held_keys['d'] and not held_keys['s']:
                    self.walksound.volume = 0
                
                # self.moveCopyModel()   
                hit_info = self.cubeModel.intersects()
                if hit_info.hit and hit_info.entity.position != Vec3(0,0,0):
                    if held_keys['w']:
                        self.world_position -= self.forward*2
                    if held_keys['s']:
                        self.world_position += self.forward*2
                    if held_keys['a']:
                        self.world_position += self.right*2
                    if held_keys['d']:
                        self.world_position -= self.right*2
                        
                    self.cubeModel.x_setter(self.world_position.x)
                    self.cubeModel.z_setter(self.world_position.z)
            
    
    
    def moveCopyModel(self):
        if held_keys[Keys.up_arrow]:
            self.cubeModel.y += 1
        if held_keys[Keys.down_arrow]:
            self.cubeModel.y -= 1
        if held_keys[Keys.left_arrow]:
            self.scale_x -= 1
        if held_keys[Keys.right_arrow]:
            self.scale_x += 1
            
    def getClass(self):
        return self.__class__
    def shootBullet(self):
        if(self.bulletNotification.num > 0):
            self.clientCallback[0](self.character.getPos()+(0,4,0), self.gun[self.curr_weapon].forward)
            print(f"Sending bullet from position: {self.character.getPos() + (0, 4, 0)}")
            self.bullet = Bullet(self.gun[self.curr_weapon].world_position, direction=self.gun[self.curr_weapon].forward, listObjectIgnore=[*self.gun, self.character.stand_entity, self.character.running_entity, self.character.stand_actor, self.character.running_actor],getPlayerClass=self.getClass ,listClientCallBack= self.clientCallback, ignorePosition=self.ignorePosition)
            self.bullet.shoot()
            self.bulletNotification.setnumOfBullet(self.bulletNotification.num-1)
        