Tungsten Blender Exporter
=========================

This is a [Blender][] addon for interfacing with the [Tungsten][] renderer.

 [Blender]: http://www.blender.org/
 [Tungsten]: https://github.com/tunabrain/tungsten

Installation
------------

You will need at least Blender 2.67 to use this addon.

To install, grab the [zip file][] then install it into Blender as an
addon by opening File, then User Preferences..., then Addons, and clicking
"Install from File...".

 [zip file]: https://github.com/agrif/tungsten-blender/archive/master.zip

Alternatively, you can check out this git repo directly into Blender's
addons folder.

After installation, in the addons preferences menu, be sure to set the
path option that shows up under "Render: Tungsten" to point to your
compiled `tungsten_server` executable.

Use
---

To begin using Tungsten as your renderer in Blender, select it from
the render engines drop down at the top of the screen (it defaults to
saying 'Blender Render').

Please note that existing Blender materials and textures are not
compatible with Tungsten. Also, Tungsten materials are heavily
node-based.

Due to a limitation of Blender, some links between objects will not
continue to work after renames. In particular, be aware that renaming
textures used in nodes, or the node trees themselves, will break
existing materials, and will need to be fixed manually.

As a convenience, an option is added to the "Export" menu to allow you
to export a tungsten scene directly, without rendering it. It includes
support for self-contained scenes as well as creating a zip file.
