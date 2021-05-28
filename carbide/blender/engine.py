import bpy
import os.path
import time
import tempfile

from carbide.blender.register import add_class
import carbide.blender.preferences
import carbide.tungsten
import carbide.scene


@add_class
class TungstenRenderEngine(bpy.types.RenderEngine):
    bl_idname = 'TUNGSTEN'
    bl_label = 'Tungsten'

    bl_use_preview = True

    def update(self, data, depsgraph):
        blscene = depsgraph.scene

        scale = blscene.render.resolution_percentage / 100.0
        width = int(blscene.render.resolution_x * scale)
        height = int(blscene.render.resolution_y * scale)

        self.scene = carbide.scene.Scene()
        self.scene.camera.resolution.modify(width, height)
        sphere = carbide.scene.Sphere().translate(0, 2, 10)
        sphere.emission = carbide.scene.ConstantTexture.grey(2.0)
        self.scene.primitives += [sphere]

        cube = carbide.scene.Cube().translate(0, 0, 10)
        cube.bsdf.albedo = carbide.scene.ConstantTexture.white()
        self.scene.primitives += [cube]

        self.scene.renderer.spp = 32
        self.scene.renderer.spp_step = 4

        self.threads = blscene.render.threads

    def render(self, depsgraph):
        blscene = depsgraph.scene

        res = self.scene.camera.resolution
        result = self.begin_result(0, 0, res.width, res.height)
        layer = result.layers[0]

        prefs = carbide.blender.preferences.get()
        pexe = prefs.tungsten_server_path
        exe = None
        if pexe:
            exe = bpy.path.abspath(pexe)

        print('rendering...')
        with tempfile.TemporaryDirectory(prefix='carbide.') as tmp:
            scenefile = os.path.join(tmp, 'scene.json')
            previewfile = os.path.join(tmp, 'preview.png')
            start = time.time()
            with open(scenefile, 'w') as f:
                self.scene.dump(self.scene, f)

            # try to launch tungsten
            try:
                t = carbide.tungsten.Tungsten(
                    scenefile, command=exe, threads=self.threads,
                    output_file='final.png', output_directory=tmp)
            except Exception:
                if not pexe:
                    self.report(
                        {'ERROR'},
                        'tungsten_server path not set, and not in PATH')
                    return
                if not os.path.exists(exe):
                    self.report(
                        {'ERROR'},
                        'tungsten_server path does not exist: ' + pexe)
                    return
                self.report({'ERROR'}, 'tungsten_server failed to start')
                return

            last_spp = 0
            while t.poll():
                time.sleep(0.1)
                # do not do status if it's a preview
                if self.is_preview:
                    continue

                try:
                    s = t.get_status()
                except carbide.tungsten.TungstenFinished:
                    break

                # cancel if needed
                if self.test_break():
                    t.cancel()
                    self.end_result(result)
                    return

                if s.current_spp != last_spp:
                    last_spp = s.current_spp

                    # update status, image
                    tmpf = None
                    try:
                        with open(previewfile, 'wb') as f:
                            f.write(t.get_render())
                        layer.load_from_file(previewfile)
                        self.update_result(result)
                    except OSError:
                        pass

                    self.update_stats(
                        'current spp: {0}'.format(last_spp),
                        'total spp: {0}'.format(s.total_spp))
                    self.update_progress(last_spp / s.total_spp)

            try:
                product, = t.finish()
            except Exception:
                self.report({'ERROR'}, 'Tungsten exited in error.')
                return

            if not os.path.exists(product.output_file):
                self.report({'ERROR'}, 'Tungsten did not produce an image.')
                return

            end = time.time()
            print('done rendering in', end - start, 's')
            layer.load_from_file(product.output_file)

        self.end_result(result)
