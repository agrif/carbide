import carbide
import numpy as np

s = carbide.scene.Scene()
s.camera = carbide.scene.ThinlensCamera()
s.camera.focus_distance = 10
s.camera.aperture_size = 0.1
s.camera.aperture = carbide.scene.BladeTexture()
s.camera.resolution.modify(1920, 1080)
s.renderer.spp = 64
s.renderer.spp_step = 4
s.integrator = carbide.scene.BidirectionalPathTracer()

sky = carbide.scene.Skydome()
sky.name = 'sky'
sun = carbide.scene.InfiniteSphereCap(skydome=sky.name)
sun.emission = carbide.scene.ConstantTexture.grey(20.0)
s.primitives += [sky, sun]

floor = carbide.scene.Disk()
floor.bsdf = carbide.scene.MirrorBsdf()
floor.scale(4.0)
floor.translate(0, -2, 10)
s.primitives += [floor]

for _ in range(100):
    c = carbide.scene.Cube()
    c.scale(0.5)
    c.rotate(np.random.uniform(-1, 1, size=3), np.random.uniform() * 360)
    c.translate(*(np.random.uniform(-1, 1, size=3) * 2))
    c.translate(0, 0, 10)
    if np.random.random() < 0.1:
        c.bsdf.albedo = carbide.scene.ConstantTexture.color(1.0, 0.0, 0.0)
        c.emission = carbide.scene.BladeTexture.color(2.0, 0.0, 0.0)
        c.emission.modify(blades=6)
    else:
        c.bsdf.albedo = carbide.scene.CheckerTexture(res_u=4, res_v=4)
    s.primitives += [c]


def update(status):
    print('{}: {} / {}'.format(status.state.name, status.current_spp,
                               status.total_spp))


print(s.dumps(None, indent=4))
s.render('render.png', update=update)
