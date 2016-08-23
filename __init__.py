# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "generic OSC panel",
    "author": "Dealga McArdle",
    "version": (0, 2),
    "blender": (2, 7, 7),
    "location": "",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Text Editor"
}


import argparse
import importlib
import threading

import bpy
from bpy.props import (
    BoolProperty, StringProperty, FloatProperty,
    IntProperty, PointerProperty, CollectionProperty
)


NOT_FOUND = 0
FOUND = 1
STOPPED = 2
RUNNING = 3


try:
    STATUS = FOUND
    if ('pythonosc' in locals()):
        print('bp_externall : reload event. handled')
    else:
        import pythonosc
        from pythonosc import osc_server
        from pythonosc import dispatcher
        print('bp_externall loaded pythonosc')

except:
    STATUS = NOT_FOUND
    print('python osc not found!, or failed to reimport')


add = bpy.utils.register_class
remove = bpy.utils.unregister_class


def general_handler(path, value):
    '''
    path will be something like /circle
    this Modal OSC panel's operator expects to find a textblock called 'do_circle'
    it will execute the code it contains whenever it receives a new path/value pair.

    '''
    textfile_name = 'do_' + path[1:]
    d = bpy.data.texts.get(textfile_name)
    if d:
        try:
            exec(d.as_string())
            print('called random_integer handler', value)
        except:
            print('failed to evaluate/exec {0}'.format(textfile_name))

# handlers can be added later but I think the server needs to be stopped and restarted..
osc_statemachine = {'status': STATUS}
osc_statemachine['handlers'] = {}


def start_server_comms(ip, port, paths):
    # paths = ['random_integer', 'circle']

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default=ip, help="The ip to listen on")
    parser.add_argument("--port", type=int, default=port, help="The port to listen on")
    args = parser.parse_args()
    osc_statemachine['args'] = args

    dispatch = dispatcher.Dispatcher()

    for path in paths:
        dispatch.map("/" + path, general_handler)

    osc_statemachine['dispatcher'] = dispatch

    try:
        server = osc_server.ThreadingOSCUDPServer((args.ip, args.port), dispatch)
        print("Serving on {}".format(server.server_address))
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.start()
        osc_statemachine['server'] = server

    except:

        print('already active')
        server = osc_statemachine['server']


class GenericOscClient(bpy.types.Operator, object):

    bl_idname = "wm.generic_osc_server"
    bl_label = "start and stop osc server"

    _timer = None
    speed = FloatProperty()
    mode = StringProperty()

    def modal(self, context, event):

        if osc_statemachine['status'] == STOPPED:
            self.cancel(context)
            return {'FINISHED'}

        if not (event.type == 'TIMER'):
            return {'PASS_THROUGH'}

        # call block here
        return {'PASS_THROUGH'}

    def event_dispatcher(self, context, type_op):
        if type_op == 'start':

            wm = context.window_manager
            self._timer = wm.event_timer_add(self.speed, context.window)
            wm.modal_handler_add(self)

            osc_statemachine['status'] = RUNNING
            props = context.scene.generic_osc
            paths = context.scene.generic_osc_list
            start_server_comms(props.ip, props.port, [i.path for i in paths])

        if type_op == 'end':
            osc_statemachine['server'].shutdown()
            osc_statemachine['status'] = STOPPED

    def execute(self, context):
        self.event_dispatcher(context, self.mode)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        osc_statemachine['server'].shutdown()


class GenericOSCpanel(bpy.types.Panel):

    bl_idname = "GenericOSCpanel"
    bl_label = "generic OSC panel"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    # bl_options = {'DEFAULT_CLOSED'}
    use_pin = True

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        state = osc_statemachine['status']

        row = col.row(align=True)
        row.prop(context.scene.generic_osc, 'new_path', text='')
        config = row.operator('wm.osc_path_ops', icon='ZOOMIN', text='')
        config.fn_name = 'ADD'

        props_list = context.scene.generic_osc_list
        for i, p in enumerate(props_list):
            path_row = col.row(align=True)
            path_row.label('listening on /{}'.format(p.path))
            config = path_row.operator('wm.osc_path_ops', icon='ZOOMOUT', text='')
            config.fn_name = 'REMOVE'
            config.idx = i

        # exit early
        if state == NOT_FOUND:
            col.label('failed to (re)import pythonosc - see console')
            return

        # promising! continue
        tstr = ''
        if state in {FOUND, STOPPED}:
            tstr = 'start'
            col.prop(context.scene.generic_osc, 'ip')
            col.prop(context.scene.generic_osc, 'port')

        elif state == RUNNING:
            props = context.scene.generic_osc
            col.label('listening on ip {0} and port {1}'.format(props.ip, props.port))

            
            tstr = 'end'

        if tstr:
            op = col.operator('wm.generic_osc_server', text=tstr)
            op.mode = tstr
            op.speed = 1



class GenericOscProps(bpy.types.PropertyGroup):
    ip = StringProperty(default='127.0.0.1')
    port = IntProperty(default=7771)
    new_path = StringProperty()


class GenericOscPathGroup(bpy.types.PropertyGroup):
    path = StringProperty()


class GenericOscPathOps(bpy.types.Operator):

    bl_idname = "wm.osc_path_ops"
    bl_label = "Add Remove paths"

    fn_name = bpy.props.StringProperty(default='')
    idx = IntProperty()

    def dispatch(self, context, type_op):

        if type_op == 'ADD':
            new_path = context.scene.generic_osc_list.add()
            new_path.path = context.scene.generic_osc.new_path
            context.scene.generic_osc.new_path = ""

        elif type_op == 'REMOVE':
            context.scene.generic_osc_list.remove(self.idx)

    def execute(self, context):
        self.dispatch(context, self.fn_name)
        return {'FINISHED'}



def register():
    add(GenericOscProps)
    add(GenericOscPathGroup)
    bpy.types.Scene.generic_osc = PointerProperty(name="properties", type=GenericOscProps)
    bpy.types.Scene.generic_osc_list = CollectionProperty(name="paths", type=GenericOscPathGroup)
    add(GenericOSCpanel)
    add(GenericOscClient)
    add(GenericOscPathOps)


def unregister():
    remove(GenericOscProps)
    remove(GenericOscPathGroup)
    remove(GenericOSCpanel)
    remove(GenericOscClient)
    remove(GenericOscPathOps)
    del bpy.types.Scene.generic_osc
    del bpy.types.Scene.generic_osc_list
