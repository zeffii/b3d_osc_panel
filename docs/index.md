The add-on adds a panel to TextEditor

During the startup (and while the underlying modal operator is not running) you get a chance to add `paths` to the listener.

### Set up

set the local IP and port to listen on.

![image](https://cloud.githubusercontent.com/assets/619340/17868600/cae776c2-68af-11e6-9750-9b9ea215b87a.png)

### Adding Paths

Add `circle` if you want to listen to `/circle`
Add `circle/damn/rock` if you want to listen to `/circle/damn/rock` (untested.. but should work)
you can add any number of paths, notice that the first `/` is added by the operator automatically, just less typing..and it would always start with a slash anyway.

![image](https://cloud.githubusercontent.com/assets/619340/17868632/f3c8f7c8-68af-11e6-93e1-f16b550dfe39.png)

press the little plus

![image](https://cloud.githubusercontent.com/assets/619340/17868664/10b22fda-68b0-11e6-9fbc-12c8dee13e0b.png)

notice how it now says 'listening on /circle', this doesn't mean it is currently listening, but it _will be_ listening on that path in the future.

### Add a function to call when a Path receives a new value

When you add something like `circle` you should add a `bpy.data.texts` called `do_circle`. Then the modal operator will execute whatever is inside `bpy.data.texts['do_circle']`

### Path function file explained.

an example of what you might write in `do_circle`

```python
bpy.data.objects['Cube'].location.z = value
```

in this case `value` is supplied as a local variable (magic!)  and you can assign its value to anything in bpy.

ps. I haven't tried to do complicated stuff with that as I don't have an multi output OSC controller attached, but I've tested with Supercollider sending rapid OSC signals and it seems to work.

### Then press start.

And the modal operator shall try to update as often as possible.
