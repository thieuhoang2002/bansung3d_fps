from ursina import *

app = Ursina()

DirectionalLight()
Sky()

# Tạo mặt đất
ground = Entity(
    model='plane',
    scale=(100, 1, 100),
    color=color.green,
    texture='white_cube',
    texture_scale=(20, 20),
    collider='box',
    y=-1
)

# Tạo xe
car = Entity(
    model='audi_tts_coupe.glb',
    scale=30,
    position=(0, 0, 0),
    rotation_y=180,
    collider='box'   
)

# Tốc độ di chuyển
speed = 5

# Cập nhật mỗi frame
def update():
    direction = Vec3(0, 0, 0)

    if held_keys['w']:
        direction -= car.forward
    if held_keys['s']:
        direction += car.forward
    if held_keys['a']:
        car.rotation_y -= 100 * time.dt
    if held_keys['d']:
        car.rotation_y += 100 * time.dt

    car.position += direction * time.dt * speed

EditorCamera()
app.run()
