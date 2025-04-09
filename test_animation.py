from ursina import *
from direct.actor.Actor import Actor

app = Ursina()

e = Entity()
actor = Actor("asset/animation/cutegirl/test3.gltf")
actor.reparent_to(e)
actor.loop('Animation')  # đúng tên trong file gltf
e.scale = 0.7
e.position = (0,0,0)
e.visible = True

app.run()
