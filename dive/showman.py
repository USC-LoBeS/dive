import re
import subprocess
import numpy as np
import pyvista as pv
from dive.loading import load
from fury import ui,window
from numbers import Number
from dive.helper import Mesh, Colors
from collections import OrderedDict
from dive.csv_tocolors import Colors_csv
from fury.data import read_viz_icons
from vtkmodules.vtkCommonColor import vtkNamedColors
from fury.ui.core import UI,Button2D, Disk2D, Rectangle2D, TextBlock2D
import os
selected_item = None
class Panel2D(UI):
    """A 2D UI Panel.

    Can contain one or more UI elements.

    Attributes
    ----------
    alignment : [left, right]
        Alignment of the panel with respect to the overall screen.
    """

    def __init__(
        self,
        size,
        position=(0, 0),
        color=(0.1, 0.1, 0.1),
        opacity=0.7,
        align='left',
        border_color=(1, 1, 1),
        border_width=0,
        has_border=False,
    ):
        """Init class instance.

        Parameters
        ----------
        size : (int, int)
            Size (width, height) in pixels of the panel.
        position : (float, float)
            Absolute coordinates (x, y) of the lower-left corner of the panel.
        color : (float, float, float)
            Must take values in [0, 1].
        opacity : float
            Must take values in [0, 1].
        align : [left, right]
            Alignment of the panel with respect to the overall screen.
        border_color: (float, float, float), optional
            Must take values in [0, 1].
        border_width: float, optional
            width of the border
        has_border: bool, optional
            If the panel should have borders.
        """
        self.has_border = has_border
        self._border_color = border_color
        self._border_width = border_width
        super(Panel2D, self).__init__(position)
        self.resize(size)
        self.alignment = align
        self.color = color
        self.opacity = opacity
        self.position = position
        self._drag_offset = None



    def _setup(self):
        """Setup this UI component.

        Create the background (Rectangle2D) of the panel.
        Create the borders (Rectangle2D) of the panel.
        """
        self._elements = []
        self.element_offsets = []
        self.background = Rectangle2D()

        if self.has_border:
            self.borders = {
                'left': Rectangle2D(),
                'right': Rectangle2D(),
                'top': Rectangle2D(),
                'bottom': Rectangle2D(),
            }

            self.border_coords = {
                'left': (0.0, 0.0),
                'right': (1.0, 0.0),
                'top': (0.0, 1.0),
                'bottom': (0.0, 0.0),
            }

            for key in self.borders.keys():
                self.borders[key].color = self._border_color
                self.add_element(self.borders[key], self.border_coords[key])

            for key in self.borders.keys():
                self.borders[
                    key
                ].on_left_mouse_button_pressed = self.left_button_pressed

                self.borders[
                    key
                ].on_left_mouse_button_dragged = self.left_button_dragged

        self.add_element(self.background, (0, 0))

        self.background.on_left_mouse_button_pressed = self.left_button_pressed
        self.background.on_left_mouse_button_dragged = self.left_button_dragged

    def _get_actors(self):
        """Get the actors composing this UI component."""
        actors = []
        for element in self._elements:
            actors += element.actors

        return actors

    def _add_to_scene(self, scene):
        """Add all subcomponents or VTK props that compose this UI component.

        Parameters
        ----------
        scene : scene
        """
        for element in self._elements:
            element.add_to_scene(scene)

    def _get_size(self):
        return self.background.size

    def resize(self, size):
        """Set the panel size.

        Parameters
        ----------
        size : (float, float)
            Panel size (width, height) in pixels.
        """
        self.background.resize(size)

        if self.has_border:
            self.borders['left'].resize(
                (self._border_width, size[1] + self._border_width)
            )

            self.borders['right'].resize(
                (self._border_width, size[1] + self._border_width)
            )

            self.borders['top'].resize(
                (self.size[0] + self._border_width, self._border_width)
            )

            self.borders['bottom'].resize(
                (self.size[0] + self._border_width, self._border_width)
            )

            self.update_border_coords()



    def _set_position(self, coords):
        """Set the lower-left corner position of this UI component.

        Parameters
        ----------
        coords: (float, float)
            Absolute pixel coordinates (x, y).

        """
        coords = np.array(coords)
        for element, offset in self.element_offsets:
            element.position = coords + offset

    def set_visibility(self, visibility):
        for element in self._elements:
            element.set_visibility(visibility)



    @property
    def color(self):
        return self.background.color

    @color.setter
    def color(self, color):
        self.background.color = color

    @property
    def opacity(self):
        return self.background.opacity

    @opacity.setter
    def opacity(self, opacity):
        self.background.opacity = opacity

    def add_element(self, element, coords, anchor='position'):
        """Add a UI component to the panel.

        The coordinates represent an offset from the lower left corner of the
        panel.

        Parameters
        ----------
        element : UI
            The UI item to be added.
        coords : (float, float) or (int, int)
            If float, normalized coordinates are assumed and they must be
            between [0,1].
            If int, pixels coordinates are assumed and it must fit within the
            panel's size.

        """
        coords = np.array(coords)

        if np.issubdtype(coords.dtype, np.floating):
            if np.any(coords < 0) or np.any(coords > 1):
                raise ValueError('Normalized coordinates must be in [0,1].')

            coords = coords * self.size

        if anchor == 'center':
            element.center = self.position + coords
        elif anchor == 'position':
            element.position = self.position + coords
        else:
            msg = "Unknown anchor {}. Supported anchors are 'position'" " and 'center'."
            raise ValueError(msg)

        self._elements.append(element)
        offset = element.position - self.position
        self.element_offsets.append((element, offset))

    def remove_element(self, element):
        """Remove a UI component from the panel.

        Parameters
        ----------
        element : UI
            The UI item to be removed.
        """
        idx = self._elements.index(element)
        del self._elements[idx]
        del self.element_offsets[idx]

    def update_element(self, element, coords, anchor='position'):
        """Update the position of a UI component in the panel.

        Parameters
        ----------
        element : UI
            The UI item to be updated.
        coords : (float, float) or (int, int)
            New coordinates.
            If float, normalized coordinates are assumed and they must be
            between [0,1].
            If int, pixels coordinates are assumed and it must fit within the
            panel's size.
        """
        self.remove_element(element)
        self.add_element(element, coords, anchor)

    
    def update_element_color(self, element, color,coords=(0.001, 0.7),anchor='position'):
        """Update the position of a UI component in the panel.

        Parameters
        ----------
        element : UI
            The UI item to be updated.
        coords : (float, float) or (int, int)
            New coordinates.
            If float, normalized coordinates are assumed and they must be
            between [0,1].
            If int, pixels coordinates are assumed and it must fit within the
            panel's size.
        """
        self.remove_element(element)
        element.color = color
        self.add_element(element, coords, anchor)

    def left_button_pressed(self, i_ren, _obj, panel2d_object):
        click_pos = np.array(i_ren.event.position)
        self._drag_offset = click_pos - self.position
        i_ren.event.abort()  


    def left_button_dragged(self, i_ren, _obj, _panel2d_object):
        if self._drag_offset is not None:
            click_position = np.array(i_ren.event.position)
            new_position = click_position - self._drag_offset
            self.position = new_position
        i_ren.force_render()


    def re_align(self, window_size_change):
        """Re-organise the elements in case the window size is changed.

        Parameters
        ----------
        window_size_change : (int, int)
            New window size (width, height) in pixels.
        """
        if self.alignment == 'left':
            pass
        elif self.alignment == 'right':
            self.position += np.array(window_size_change)
        else:
            msg = 'You can only left-align or right-align objects in a panel.'
            raise ValueError(msg)


    def update_border_coords(self):
        """Update the coordinates of the borders"""
        self.border_coords = {
            'left': (0.0, 0.0),
            'right': (1.0, 0.0),
            'top': (0.0, 1.0),
            'bottom': (0.0, 0.0),
        }

        for key in self.borders.keys():
            self.update_element(self.borders[key], self.border_coords[key])



    @property
    def border_color(self):
        sides = ['left', 'right', 'top', 'bottom']
        return [self.borders[side].color for side in sides]

    @border_color.setter
    def border_color(self, side_color):
        """Set the color of a specific border

        Parameters
        ----------
        side_color: Iterable
            Iterable to pack side, color values
        """
        side, color = side_color

        if side.lower() not in ['left', 'right', 'top', 'bottom']:
            raise ValueError(f'{side} not a valid border side')

        self.borders[side].color = color

    @property
    def border_width(self):
        sides = ['left', 'right', 'top', 'bottom']
        widths = []

        for side in sides:
            if side in ['left', 'right']:
                widths.append(self.borders[side].width)
            elif side in ['top', 'bottom']:
                widths.append(self.borders[side].height)
            else:
                raise ValueError(f'{side} not a valid border side')
        return widths

    @border_width.setter
    def border_width(self, side_width):
        """Set the border width of a specific border

        Parameters
        ----------
        side_width: Iterable
            Iterable to pack side, width values
        """
        side, border_width = side_width

        if side.lower() in ['left', 'right']:
            self.borders[side].width = border_width
        elif side.lower() in ['top', 'bottom']:
            self.borders[side].height = border_width
        else:
            raise ValueError(f'{side} not a valid border side')


class ComboBox2D(UI):
    """UI element to create drop-down menus.

    Attributes
    ----------
    selection_box: :class: 'TextBox2D'
        Display selection and placeholder text.
    drop_down_button: :class: 'Button2D'
        Button to show or hide menu.
    drop_down_menu: :class: 'ListBox2D'
        Container for item list.
    """

    def __init__(
        self,
        items=[],
        position=(0, 0),
        size=(150, 400),
        placeholder='Choose selection...',
        draggable=False,
        selection_text_color=(0, 0, 0),
        selection_bg_color=(0.9, 0.9, 0.9),
        menu_text_color=(0.2, 0.2, 0.2),
        selected_color=(0.6, 0.6, 0.9),
        unselected_color=(0.6, 0.6, 0.6),
        scroll_bar_active_color=(0.2, 0.2, 0.6),
        scroll_bar_inactive_color=(0.0, 0.0, 0.9),
        menu_opacity=1.0,
        reverse_scrolling=True,
        font_size=20,
        line_spacing=1.0,
        others = []
    ):
        """Init class Instance.

        Parameters
        ----------
        items: list(string)
            List of items to be displayed as choices.
        position : (float, float)
            Absolute coordinates (x, y) of the lower-left corner of this
            UI component.
        size : (int, int)
            Width and height in pixels of this UI component.
        placeholder : str
            Holds the default text to be displayed.
        draggable: {True, False}
            Whether the UI element is draggable or not.
        selection_text_color : tuple of 3 floats
            Color of the selected text to be displayed.
        selection_bg_color : tuple of 3 floats
            Background color of the selection text.
        menu_text_color : tuple of 3 floats.
            Color of the options displayed in drop down menu.
        selected_color : tuple of 3 floats.
            Background color of the selected option in drop down menu.
        unselected_color : tuple of 3 floats.
            Background color of the unselected option in drop down menu.
        scroll_bar_active_color : tuple of 3 floats.
            Color of the scrollbar when in active use.
        scroll_bar_inactive_color : tuple of 3 floats.
            Color of the scrollbar when inactive.
        reverse_scrolling: {True, False}
            If True, scrolling up will move the list of files down.
        font_size: int
            The font size of selected text in pixels.
        line_spacing: float
            Distance between drop down menu's items in pixels.
        """
        self.items = items.copy()
        self.font_size = font_size
        self.reverse_scrolling = reverse_scrolling
        self.line_spacing = line_spacing
        self.panel_size = size
        self._selection = placeholder
        self.main_placeholder = placeholder
        self._menu_visibility = False
        self._selection_ID = None
        self.draggable = draggable
        self.sel_text_color = selection_text_color
        self.sel_bg_color = selection_bg_color
        self.menu_txt_color = menu_text_color
        self.selected_color = selected_color
        self.unselected_color = unselected_color
        self.scroll_active_color = scroll_bar_active_color
        self.scroll_inactive_color = scroll_bar_inactive_color
        self.menu_opacity = menu_opacity
        self.others = others
        self.on_change = lambda combobox: None
        self.text_block_size = (int(size[0]), int(size[1]))
        self.drop_menu_size = (int(0.9 * size[0]), int(0.7 * size[1]))
        self.drop_button_size = (int(0.08 * size[0]), int(0.14 * size[1]))

        self._icon_files = [
            ('left', read_viz_icons(fname= os.path.dirname(__file__)+"/add.png")),
            ('down', read_viz_icons(fname= os.path.dirname(__file__)+"/minus.png")),
        ]

        super(ComboBox2D, self).__init__()
        self.position = position



    def _setup(self):
        """Setup this UI component.

        Create the ListBox filled with empty slots (ListBoxItem2D).
        Create TextBox with placeholder text.
        Create Button for toggling drop down menu.
        """
        self.selection_box = TextBlock2D(
            size=(20,20),
            color=self.sel_text_color,
            text=self._selection,
        )

        self.drop_down_button = Button2D(
            icon_fnames=self._icon_files, size=self.drop_button_size
        )

        self.drop_down_menu = ui.ListBox2D(
            values=self.items,
            multiselection=False,
            font_size=self.font_size,
            line_spacing=self.line_spacing,
            text_color=self.menu_txt_color,
            selected_color=self.selected_color,
            unselected_color=self.unselected_color,
            scroll_bar_active_color=self.scroll_active_color,
            scroll_bar_inactive_color=self.scroll_inactive_color,
            background_opacity=self.menu_opacity,
            reverse_scrolling=self.reverse_scrolling,
            size=self.drop_menu_size,
        )

        self.drop_down_menu.set_visibility(False)

        self.panel = ui.Panel2D(self.panel_size, opacity=0.0)
        self.panel.add_element(self.selection_box, (0.001, 0.7))
        self.panel.add_element(self.drop_down_button, (0.8, 0.7))
        self.panel.add_element(self.drop_down_menu, (0, 0))

        self.panel.background.on_left_mouse_button_dragged = (
            lambda i_ren, _obj, _comp: i_ren.force_render
        )
        self.drop_down_menu.panel.background.on_left_mouse_button_dragged = (
            lambda i_ren, _obj, _comp: i_ren.force_render
        )

        for slot in self.drop_down_menu.slots:
            slot.add_callback(
                slot.textblock.actor,
                'LeftButtonPressEvent',
                self.select_option_callback,
            )

            slot.add_callback(
                slot.background.actor,
                'LeftButtonPressEvent',
                self.select_option_callback,
            )

        self.drop_down_button.on_left_mouse_button_clicked = (
            self.menu_toggle_callback
        )

        self.on_change = lambda ui: None

    def _get_actors(self):
        """Get the actors composing this UI component."""
        return self.panel.actors
    def _handle_option_change(self):
        """Update whenever an option changes.

        Parameters
        ----------
        option : :class:`Option`
        """
        if self.drop_down_button.current_icon_id==1:
            self.selection_box.bold = True
        else:
            self.selection_box.bold = False

        self.on_change(self)
    def resize(self, size):
        """Resize ComboBox2D.

        Parameters
        ----------
        size : (int, int)
            ComboBox size(width, height) in pixels.
        """
        self.panel.resize(size)
        self.drop_menu_size = (size[0], int(0.7 * size[1]))
        self.drop_button_size = (int(0.2 * size[0]), int(0.3 * size[1]))
        self.panel.update_element(self.selection_box, (0.001, 0.7))
        self.panel.update_element(self.drop_down_button, (0.8, 0.7))
        self.panel.update_element(self.drop_down_menu, (0, 0))
        self.drop_down_button.resize(self.drop_button_size)
        self.drop_down_menu.resize(self.drop_menu_size)




    def _set_position(self, coords):
        """Set the lower-left corner position of this UI component.

        Parameters
        ----------
        coords: (float, float)
            Absolute pixel coordinates (x, y).

        """
        self.panel.position = coords

    def _add_to_scene(self, scene):
        """Add all subcomponents or VTK props that compose this UI component.

        Parameters
        ----------
        scene : scene

        """
        self.panel.add_to_scene(scene)
        self.selection_box.font_size = self.font_size

    def _get_size(self):
        return self.panel.size

    @property
    def selected_text(self):
        return self._selection

    @property
    def selected_text_index(self):
        return self._selection_ID

    def set_visibility(self, visibility):
        super().set_visibility(visibility)
        if not self._menu_visibility:
            self.drop_down_menu.set_visibility(False)

    def append_item(self, *items):
        """Append additional options to the menu.

        Parameters
        ----------
        items : n-d list, n-d tuple, Number or str
            Additional options.

        """
        for item in items:
            if isinstance(item, (list, tuple)):
                # Useful when n-d lists/tuples are used.
                self.append_item(*item)
            elif isinstance(item, (str, Number)):
                self.items.append(str(item))
            else:
                raise TypeError('Invalid item instance {}'.format(type(item)))

        self.drop_down_menu.update()
        self.resize(self.panel_size)
        self.drop_down_menu.set_visibility(False)
        if not self._menu_visibility:
            self.drop_down_menu.scroll_bar.set_visibility(False)

    def remove_item(self,string_to_remove):
        while string_to_remove in self.items:
            self.items.remove(string_to_remove)
            self.drop_down_menu.update()
            
            self.resize(self.panel_size)
            self._selection =  self.main_placeholder 
            self.selection_box.message = self._selection
            self._selection_ID = None
            self.drop_down_menu.set_visibility(False)


    def select_option_callback(self, i_ren, _obj, listboxitem):
        """Select the appropriate option

        Parameters
        ----------
        i_ren: :class:`CustomInteractorStyle`
        obj: :class:`vtkActor`
            The picked actor
        listboxitem: :class:`ListBoxItem2D`

        """
        global selected_item
        selected_item = listboxitem.element
        truncated_string = listboxitem.element[:15] if len(listboxitem.element) > 15 else listboxitem.element
        self._selection =  self.main_placeholder + truncated_string
        self._selection_ID = self.items.index(listboxitem.element)
        self.selection_box.message = self._selection
        self.drop_down_menu.set_visibility(False)
        self._menu_visibility = False

        self.drop_down_button.next_icon()
        if self.drop_down_button.current_icon_id==1:
            for i in self.others:
                i.set_visibility(False)
        else:
            for i in self.others:
                i.set_visibility(True)
        self.on_change(self)

        i_ren.force_render()
        i_ren.event.abort()


    def menu_toggle_callback(self, i_ren, _vtkactor, _combobox):
        """Toggle visibility of drop down menu list.

        Parameters
        ----------
        i_ren : :class:`CustomInteractorStyle`
        vtkactor : :class:`vtkActor`
            The picked actor
        combobox : :class:`ComboBox2D`

        """
        

        self._menu_visibility = not self._menu_visibility
        self.drop_down_menu.set_visibility(self._menu_visibility)
        self.drop_down_button.next_icon()
        if self.drop_down_button.current_icon_id==1:
            for i in self.others:
                i.set_visibility(False)
                if str(type(i))=="<class 'showman.ComboBox2D'>":
                    i.selection_box.bold = False
        else:
            for i in self.others:
                i.set_visibility(True)
        i_ren.force_render()
        i_ren.event.abort()

    def left_button_pressed(self, i_ren, _obj, _sub_component):
        click_pos = np.array(i_ren.event.position)
        self._click_position = click_pos
        i_ren.event.abort()

    def left_button_dragged(self, i_ren, _obj, _sub_component):
        click_position = np.array(i_ren.event.position)
        change = click_position - self._click_position
        self.panel.position += change
        self._click_position = click_position
        i_ren.force_render()


class Option(UI):

    """A set of a Button2D and a TextBlock2D to act as a single option
    for checkboxes and radio buttons.
    Clicking the button toggles its checked/unchecked status.

    Attributes
    ----------
    label : str
        The label for the option.
    font_size : int
            Font Size of the label.

    """
    def __init__(self, label, position=(0, 0), font_size=18, checked=False):
        """Init this class instance.

        Parameters
        ----------
        label : str
            Text to be displayed next to the option's button.
        position : (float, float)
            Absolute coordinates (x, y) of the lower-left corner of
            the button of the option.
        font_size : int
            Font size of the label.
        checked : bool, optional
            Boolean value indicates the initial state of the option

        """
        self.label = label
        self.font_size = font_size
        self.checked = checked
        self.button_size = (font_size * 1.2, font_size * 1.2)
        self.button_label_gap = 10
        super(Option, self).__init__(position)
        self.on_change = lambda obj: None



    def _setup(self):
        """Setup this UI component."""
        self.button_icons = []
        self.button_icons.append(('unchecked', read_viz_icons(fname='stop2.png')))
        self.button_icons.append(('checked', read_viz_icons(fname='checkmark.png')))
        self.button = Button2D(icon_fnames=self.button_icons, size=self.button_size)

        self.text = TextBlock2D(text=self.label, font_size=self.font_size,color=(0,0,0))
        if self.checked:
            self.button.set_icon_by_name('checked')

        self.button.on_left_mouse_button_clicked = self.toggle
        self.text.on_left_mouse_button_clicked = self.toggle

    def _get_actors(self):
        """Get the actors composing this UI component."""
        return self.button.actors + self.text.actors

    def _add_to_scene(self, scene):
        """Add all subcomponents or VTK props that compose this UI component.

        Parameters
        ----------
        scene : scene

        """
        self.button.add_to_scene(scene)
        self.text.add_to_scene(scene)

    def _get_size(self):
        width = self.button.size[0] + self.button_label_gap + self.text.size[0]
        height = max(self.button.size[1], self.text.size[1])
        return np.array([width, height])

    def _set_position(self, coords):
        """Set the lower-left corner position of this UI component.

        Parameters
        ----------
        coords: (float, float)
            Absolute pixel coordinates (x, y).

        """
        num_newlines = self.label.count('\n')
        self.button.position = coords + (0, num_newlines * self.font_size * 0.5)
        offset = (self.button.size[0] + self.button_label_gap, 0)
        self.text.position = coords + offset

    def toggle(self, i_ren, _obj, _element):
        if self.checked:
            self.deselect()
        else:
            self.select()

        self.on_change(self)
        i_ren.force_render()
    def select(self):
        self.checked = True
        self.button.set_icon_by_name('checked')

    def deselect(self):
        self.checked = False
        self.button.set_icon_by_name('unchecked')

class Option_Add(UI):

    """A set of a Button2D and a TextBlock2D to act as a single option
    for checkboxes and radio buttons.
    Clicking the button toggles its checked/unchecked status.

    Attributes
    ----------
    label : str
        The label for the option.
    font_size : int
            Font Size of the label.

    """
    def __init__(self, label, position=(0, 0), font_size=18, checked=False):
        """Init this class instance.

        Parameters
        ----------
        label : str
            Text to be displayed next to the option's button.
        position : (float, float)
            Absolute coordinates (x, y) of the lower-left corner of
            the button of the option.
        font_size : int
            Font size of the label.
        checked : bool, optional
            Boolean value indicates the initial state of the option

        """
        self.label = label
        self.font_size = font_size
        self.checked = checked
        self.button_size = (font_size * 1.2, font_size * 1.2)
        self.button_label_gap = 10
        super(Option_Add, self).__init__(position)

        self.on_change = lambda obj: None



    def _setup(self):
        """Setup this UI component."""
        self.button_icons = []
        self.button_icons.append(('unchecked', read_viz_icons(fname= os.path.dirname(__file__)+"/add.png")))
        self.button_icons.append(('checked', read_viz_icons(fname= os.path.dirname(__file__)+"/add.png")))
        self.button = Button2D(icon_fnames=self.button_icons, size=self.button_size)
        self.text = TextBlock2D(text=self.label, font_size=self.font_size,color=(0,0,0))

        if self.checked:
            self.button.set_icon_by_name('checked')

        self.button.on_left_mouse_button_clicked = self.toggle
        self.text.on_left_mouse_button_clicked = self.toggle

    def _get_actors(self):
        """Get the actors composing this UI component."""
        return self.button.actors + self.text.actors

    def _add_to_scene(self, scene):
        """Add all subcomponents or VTK props that compose this UI component.

        Parameters
        ----------
        scene : scene

        """
        self.button.add_to_scene(scene)
        self.text.add_to_scene(scene)

    def _get_size(self):
        width = self.button.size[0] + self.button_label_gap + self.text.size[0]
        height = max(self.button.size[1], self.text.size[1])
        return np.array([width, height])

    def _set_position(self, coords):
        """Set the lower-left corner position of this UI component.

        Parameters
        ----------
        coords: (float, float)
            Absolute pixel coordinates (x, y).

        """
        num_newlines = self.label.count('\n')
        self.button.position = coords + (0, num_newlines * self.font_size * 0.5)
        offset = (self.button.size[0] + self.button_label_gap, 0)
        self.text.position = coords + offset

    def toggle(self, i_ren, _obj, _element):
        if self.checked:
            self.deselect()
        else:
            self.select()

        self.on_change(self)
        i_ren.force_render()
    def select(self):
        self.checked = True
        self.button.set_icon_by_name('checked')

    def deselect(self):
        self.checked = False
        self.button.set_icon_by_name('unchecked')

class Option_Rem(UI):

    """A set of a Button2D and a TextBlock2D to act as a single option
    for checkboxes and radio buttons.
    Clicking the button toggles its checked/unchecked status.

    Attributes
    ----------
    label : str
        The label for the option.
    font_size : int
            Font Size of the label.

    """
    def __init__(self, label, position=(0, 0), font_size=18, checked=False):
        """Init this class instance.

        Parameters
        ----------
        label : str
            Text to be displayed next to the option's button.
        position : (float, float)
            Absolute coordinates (x, y) of the lower-left corner of
            the button of the option.
        font_size : int
            Font size of the label.
        checked : bool, optional
            Boolean value indicates the initial state of the option

        """
        self.label = label
        self.font_size = font_size
        self.checked = checked
        self.button_size = (font_size * 1.2, font_size * 1.2)
        self.button_label_gap = 10
        super(Option_Rem, self).__init__(position)

        self.on_change = lambda obj: None



    def _setup(self):
        """Setup this UI component."""
        # Option's button
        self.button_icons = []
        self.button_icons.append(('unchecked', read_viz_icons(fname= os.path.dirname(__file__)+"/minus.png")))
        self.button_icons.append(('checked', read_viz_icons(fname= os.path.dirname(__file__)+"/minus.png")))
        self.button = Button2D(icon_fnames=self.button_icons, size=self.button_size)

        self.text = TextBlock2D(text=self.label, font_size=self.font_size,color=(0,0,0))

        # Display initial state
        if self.checked:
            self.button.set_icon_by_name('checked')

        # Add callbacks
        self.button.on_left_mouse_button_clicked = self.toggle
        self.text.on_left_mouse_button_clicked = self.toggle

    def _get_actors(self):
        """Get the actors composing this UI component."""
        return self.button.actors + self.text.actors

    def _add_to_scene(self, scene):
        """Add all subcomponents or VTK props that compose this UI component.

        Parameters
        ----------
        scene : scene

        """
        self.button.add_to_scene(scene)
        self.text.add_to_scene(scene)

    def _get_size(self):
        width = self.button.size[0] + self.button_label_gap + self.text.size[0]
        height = max(self.button.size[1], self.text.size[1])
        return np.array([width, height])

    def _set_position(self, coords):
        """Set the lower-left corner position of this UI component.

        Parameters
        ----------
        coords: (float, float)
            Absolute pixel coordinates (x, y).

        """
        num_newlines = self.label.count('\n')
        self.button.position = coords + (0, num_newlines * self.font_size * 0.5)
        offset = (self.button.size[0] + self.button_label_gap, 0)
        self.text.position = coords + offset

    def toggle(self, i_ren, _obj, _element):
        if self.checked:
            self.deselect()
        else:
            self.select()

        self.on_change(self)
        i_ren.force_render()
    def select(self):
        self.checked = True
        self.button.set_icon_by_name('checked')

    def deselect(self):
        self.checked = False
        self.button.set_icon_by_name('unchecked')



class Checkbox(UI):

    """A 2D set of :class:'Option' objects.
    Multiple options can be selected.

    Attributes
    ----------
    labels : list(string)
        List of labels of each option.
    options : dict(Option)
        Dictionary of all the options in the checkbox set.
    padding : float
        Distance between two adjacent options
    """
    def __init__(
        self,
        labels,
        checked_labels=(),
        padding=1,
        font_size=18,
        font_family='Arial',
        position=(0, 0),
    ):
        """Init this class instance.

        Parameters
        ----------
        labels : list(str)
            List of labels of each option.
        checked_labels: list(str), optional
            List of labels that are checked on setting up.
        padding : float, optional
            The distance between two adjacent options
        font_size : int, optional
            Size of the text font.
        font_family : str, optional
            Currently only supports Arial.
        position : (float, float), optional
            Absolute coordinates (x, y) of the lower-left corner of
            the button of the first option.
        """

        self.labels = list(reversed(list(labels)))
        self._padding = padding
        self._font_size = font_size
        self.font_family = font_family
        self.checked_labels = list(checked_labels)
        super(Checkbox, self).__init__(position)
        self.on_change = lambda checkbox: None



    def _setup(self):
        """Setup this UI component."""
        self.options = OrderedDict()
        button_y = self.position[1]
        for label in self.labels:

            option = Option(
                label=label,
                font_size=self.font_size,
                position=(self.position[0], button_y),
                checked=(label in self.checked_labels),
            )

            line_spacing = option.text.actor.GetTextProperty().GetLineSpacing()
            button_y = (
                button_y
                + self.font_size * (label.count('\n') + 1) * (line_spacing + 0.1)
                + self.padding
            )
            self.options[label] = option

            # Set callback
            option.on_change = self._handle_option_change

    def _get_actors(self):
        """Get the actors composing this UI component."""
        actors = []
        for option in self.options.values():
            actors = actors + option.actors
        return actors

    def _add_to_scene(self, scene):
        """Add all subcomponents or VTK props that compose this UI component.

        Parameters
        ----------
        scene : scene

        """
        for option in self.options.values():
            # print(option.label)
            if option.label=="Flipped":
                # option._set_position((0,0))
                option.add_to_scene(scene)
            else:
                option.add_to_scene(scene)

    def _get_size(self):
        option_width, option_height = self.options.values()[0].get_size()
        height = len(self.labels) * (option_height + self.padding) - self.padding
        return np.asarray([option_width, height])

    def _handle_option_change(self, option):
        """Update whenever an option changes.

        Parameters
        ----------
        option : :class:`Option`
        """
        if option.checked:
            self.checked_labels.append(option.label)
        else:
            self.checked_labels.remove(option.label)

        self.on_change(self)

    def _set_position(self, coords):
        """Set the lower-left corner position of this UI component.

        Parameters
        ----------
        coords: (float, float)
            Absolute pixel coordinates (x, y).

        """
        button_y = coords[1]
        for option_no, option in enumerate(self.options.values()):
            option.position = (coords[0], button_y)
            line_spacing = option.text.actor.GetTextProperty().GetLineSpacing()
            button_y = (
                button_y
                + self.font_size
                * (self.labels[option_no].count('\n') + 1)
                * (line_spacing + 0.1)
                + self.padding
            )

    @property
    def font_size(self):
        """Gets the font size of text."""
        return self._font_size

    @property
    def padding(self):
        """Get the padding between options."""
        return self._padding


class RadioButton(Checkbox):
    """A 2D set of :class:'Option' objects.
    Only one option can be selected.

    Attributes
    ----------
    labels : list(string)
        List of labels of each option.
    options : dict(Option)
        Dictionary of all the options in the checkbox set.
    padding : float
        Distance between two adjacent options

    """
    def __init__(
        self,
        labels,
        checked_labels,
        padding=1,
        font_size=18,
        font_family='Arial',
        position=(0, 0),
    ):
        """Init class instance.

        Parameters
        ----------
        labels : list(str)
            List of labels of each option.
        checked_labels: list(str), optional
            List of labels that are checked on setting up.
        padding : float, optional
            The distance between two adjacent options
        font_size : int, optional
            Size of the text font.
        font_family : str, optional
            Currently only supports Arial.
        position : (float, float), optional
            Absolute coordinates (x, y) of the lower-left corner of
            the button of the first option.
        """
        if len(checked_labels) > 1:
            err_msg = 'Only one option can be pre-selected for radio buttons.'
            raise ValueError(err_msg)

        super(RadioButton, self).__init__(
            labels=labels,
            position=position,
            padding=padding,
            font_size=font_size,
            font_family=font_family,
            checked_labels=checked_labels,
        )



    def _handle_option_change(self, option):
        for option_ in self.options.values():
            option_.deselect()

        option.select()
        self.checked_labels = [option.label]
        self.on_change(self)


class LineSlider2D(UI):
    """A 2D Line Slider.

    A sliding handle on a line with a percentage indicator.

    Attributes
    ----------
    line_width : int
        Width of the line on which the disk will slide.
    length : int
        Length of the slider.
    track : :class:`Rectangle2D`
        The line on which the slider's handle moves.
    handle : :class:`Disk2D`
        The moving part of the slider.
    text : :class:`TextBlock2D`
        The text that shows percentage.
    shape : string
        Describes the shape of the handle.
        Currently supports 'disk' and 'square'.
    default_color : (float, float, float)
        Color of the handle when in unpressed state.
    active_color : (float, float, float)
        Color of the handle when it is pressed.
    """

    def __init__(
        self,
        center=(0, 0),
        initial_value=50,
        min_value=0,
        max_value=100,
        length=200,
        line_width=5,
        inner_radius=0,
        outer_radius=10,
        handle_side=20,
        font_size=16,
        orientation='horizontal',
        text_alignment='',
        text_template='{value:.1f} ({ratio:.0%})',
        shape='disk',
    ):
        """Init this UI element.

        Parameters
        ----------
        center : (float, float)
            Center of the slider's center.
        initial_value : float
            Initial value of the slider.
        min_value : float
            Minimum value of the slider.
        max_value : float
            Maximum value of the slider.
        length : int
            Length of the slider.
        line_width : int
            Width of the line on which the disk will slide.
        inner_radius : int
            Inner radius of the handles (if disk).
        outer_radius : int
            Outer radius of the handles (if disk).
        handle_side : int
            Side length of the handles (if square).
        font_size : int
            Size of the text to display alongside the slider (pt).
        orientation : str
            horizontal or vertical
        text_alignment : str
            define text alignment on a slider. Left (default)/ right for the
            vertical slider or top/bottom (default) for an horizontal slider.
        text_template : str, callable
            If str, text template can contain one or multiple of the
            replacement fields: `{value:}`, `{ratio:}`.
            If callable, this instance of `:class:LineSlider2D` will be
            passed as argument to the text template function.
        shape : string
            Describes the shape of the handle.
            Currently supports 'disk' and 'square'.

        """
        self.shape = shape
        self.orientation = orientation.lower().strip()
        self.align_dict = {
            'horizontal': ['top', 'bottom'],
            'vertical': ['left', 'right'],
        }
        self.default_color = (0, 0, 0)
        self.active_color = (0, 0, 1)
        self.alignment = text_alignment.lower()
        super(LineSlider2D, self).__init__()

        if self.orientation == 'horizontal':
            self.alignment = 'bottom' if not self.alignment else self.alignment
            self.track.width = length
            self.track.height = line_width
        elif self.orientation == 'vertical':
            self.alignment = 'left' if not self.alignment else self.alignment
            self.track.width = line_width
            self.track.height = length
        else:
            raise ValueError('Unknown orientation')

        if self.alignment not in self.align_dict[self.orientation]:
            raise ValueError(
                "Unknown alignment: choose from '{}' or '{}'".format(
                    *self.align_dict[self.orientation]
                )
            )

        if shape == 'disk':
            self.handle.inner_radius = inner_radius
            self.handle.outer_radius = outer_radius
        elif shape == 'square':
            self.handle.width = handle_side
            self.handle.height = handle_side
        self.center = center

        self.min_value = min_value
        self.max_value = max_value
        self.text.font_size = font_size
        self.text_template = text_template

        # Offer some standard hooks to the user.
        self.on_change = lambda ui: None
        self.on_value_changed = lambda ui: None
        self.on_moving_slider = lambda ui: None

        self.value = initial_value
        self.update()



    def _setup(self):
        """Setup this UI component.

        Create the slider's track (Rectangle2D), the handle (Disk2D) and
        the text (TextBlock2D).
        """
        # Slider's track
        self.track = Rectangle2D()
        self.track.color = (0, 0, 1)

        # Slider's handle
        if self.shape == 'disk':
            self.handle = Disk2D(outer_radius=1)
        elif self.shape == 'square':
            self.handle = Rectangle2D(size=(1, 1))
        self.handle.color = self.default_color

        # Slider Text
        self.text = TextBlock2D(justification='center', vertical_justification='top',color = (0,0,0))

        # Add default events listener for this UI component.
        self.track.on_left_mouse_button_pressed = self.track_click_callback
        self.track.on_left_mouse_button_dragged = self.handle_move_callback
        self.track.on_left_mouse_button_released = self.handle_release_callback
        self.handle.on_left_mouse_button_dragged = self.handle_move_callback
        self.handle.on_left_mouse_button_released = self.handle_release_callback

    def _get_actors(self):
        """Get the actors composing this UI component."""
        return self.track.actors + self.handle.actors + self.text.actors

    def _add_to_scene(self, scene):
        """Add all subcomponents or VTK props that compose this UI component.

        Parameters
        ----------
        scene : scene

        """
        self.track.add_to_scene(scene)
        self.handle.add_to_scene(scene)
        self.text.add_to_scene(scene)

    def _get_size(self):
        # Consider the handle's size when computing the slider's size.
        width = None
        height = None
        if self.orientation == 'horizontal':
            width = self.track.width + self.handle.size[0]
            height = max(self.track.height, self.handle.size[1])
        else:
            width = max(self.track.width, self.handle.size[0])
            height = self.track.height + self.handle.size[1]

        return np.array([width, height])

    def _set_position(self, coords):
        """Set the lower-left corner position of this UI component.

        Parameters
        ----------
        coords: (float, float)
            Absolute pixel coordinates (x, y).
        """
        # Offset the slider line by the handle's radius.
        track_position = coords + self.handle.size / 2.0
        if self.orientation == 'horizontal':
            # Offset the slider line height by half the slider line width.
            track_position[1] -= self.track.size[1] / 2.0
        else:
            # Offset the slider line width by half the slider line height.
            track_position[0] += self.track.size[0] / 2.0

        self.track.position = track_position
        self.handle.position = self.handle.position.astype(float)
        self.handle.position += coords - self.position
        # Position the text below the handle.
        if self.orientation == 'horizontal':
            align = 35 if self.alignment == 'top' else -10
            self.text.position = (
                self.handle.center[0],
                self.handle.position[1] + align,
            )
        else:
            align = 70 if self.alignment == 'right' else -35
            self.text.position = (
                self.handle.position[0] + align,
                self.handle.center[1] + 2,
            )

    @property
    def bottom_y_position(self):
        return self.track.position[1]

    @property
    def top_y_position(self):
        return self.track.position[1] + self.track.size[1]

    @property
    def left_x_position(self):
        return self.track.position[0]

    @property
    def right_x_position(self):
        return self.track.position[0] + self.track.size[0]

    def set_position(self, position):
        """Set the disk's position.

        Parameters
        ----------
        position : (float, float)
            The absolute position of the disk (x, y).
        """

        # Move slider disk.
        if self.orientation == 'horizontal':
            x_position = position[0]
            x_position = max(x_position, self.left_x_position)
            x_position = min(x_position, self.right_x_position)
            self.handle.center = (x_position, self.track.center[1])
        else:
            y_position = position[1]
            y_position = max(y_position, self.bottom_y_position)
            y_position = min(y_position, self.top_y_position)
            self.handle.center = (self.track.center[0], y_position)
        self.update()  # Update information.



    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        value_range = self.max_value - self.min_value
        self.ratio = (value - self.min_value) / value_range if value_range else 0
        self.on_value_changed(self)

    @property
    def ratio(self):
        return self._ratio

    @ratio.setter
    def ratio(self, ratio):
        position_x = self.left_x_position + ratio * self.track.width
        position_y = self.bottom_y_position + ratio * self.track.height
        self.set_position((position_x, position_y))

    def format_text(self):
        """Return formatted text to display along the slider."""
        if callable(self.text_template):
            return self.text_template(self)
        return self.text_template.format(ratio=self.ratio, value=self.value)


    def update(self):
        """Update the slider."""
        # Compute the ratio determined by the position of the slider disk.
        disk_position_x = None
        disk_position_y = None

        if self.orientation == 'horizontal':
            length = float(self.right_x_position - self.left_x_position)
            length = np.round(length, decimals=6)
            if length != self.track.width:
                raise ValueError('Disk position outside the slider line')
            disk_position_x = self.handle.center[0]
            self._ratio = (disk_position_x - self.left_x_position) / length
        else:
            length = float(self.top_y_position - self.bottom_y_position)
            if length != self.track.height:
                raise ValueError('Disk position outside the slider line')
            disk_position_y = self.handle.center[1]
            self._ratio = (disk_position_y - self.bottom_y_position) / length

        # Compute the selected value considering min_value and max_value.
        value_range = self.max_value - self.min_value
        self._value = self.min_value + self.ratio * value_range

        # Update text.
        text = self.format_text()
        self.text.message = text

        # Move the text below the slider's handle.
        if self.orientation == 'horizontal':
            self.text.position = (disk_position_x, self.text.position[1])
        else:
            self.text.position = (self.text.position[0], disk_position_y)

        self.on_change(self)


    def track_click_callback(self, i_ren, _vtkactor, _slider):
        """Update disk position and grab the focus.

        Parameters
        ----------
        i_ren : :class:`CustomInteractorStyle`
        vtkactor : :class:`vtkActor`
            The picked actor
        _slider : :class:`LineSlider2D`

        """
        position = i_ren.event.position
        self.set_position(position)
        self.on_moving_slider(self)
        i_ren.force_render()
        i_ren.event.abort()  # Stop propagating the event.

    def handle_move_callback(self, i_ren, _vtkactor, _slider):
        """Handle movement.

        Parameters
        ----------
        i_ren : :class:`CustomInteractorStyle`
        vtkactor : :class:`vtkActor`
            The picked actor
        slider : :class:`LineSlider2D`

        """
        self.handle.color = self.active_color
        position = i_ren.event.position
        self.set_position(position)
        self.on_moving_slider(self)
        i_ren.force_render()
        i_ren.event.abort()  # Stop propagating the event.


    def handle_release_callback(self, i_ren, _vtkactor, _slider):
        """Change color when handle is released.

        Parameters
        ----------
        i_ren : :class:`CustomInteractorStyle`
        vtkactor : :class:`vtkActor`
            The picked actor
        slider : :class:`LineSlider2D`

        """
        self.handle.color = self.default_color
        i_ren.force_render()


class Show:


    def define_scene(self):
        """
        Defines and generate the output window
        """
        colors = vtkNamedColors()
        self.scene  = window.Scene()
        if self.background == 1:
            self.scene.SetBackground(colors.GetColor3d("White"))
        '''Setting the default Camera angle to Sagittal View'''
        self.scene.set_camera(position=(400, 0, 0), focal_point=(0, 0, 0), view_up=(0, 0, 1))
        return self.scene



    def build_label(self,text,title=False):
        """
        Args: 
        text: string - Value that is to be written
        title: boolean - If True then increase the font size, and make it bold 
        Return: Label actor
        Use to make the text for the pannel on side
        """
        label = ui.TextBlock2D()
        label.message = text
        label.font_size = 18
        label.font_family = 'Arial'
        label.justification = 'left'
        label.bold = False
        label.italic = False
        label.shadow = False
        label.color = (0, 0, 0)
        if title:
            label.font_size = 20
            label.bold = True
        return label

    def pannel(self):
        self.panel.add_element(self.view,(0.1,0.05))
        self.panel.add_element(self.flipper,(0.5,0.09))
        self.panel.add_element(self.combox_mask,(0.1,0.65))
        self.panel.add_element(self.combox_track,(0.1,0.55))
        self.panel.add_element(self.combox_mesh,(0.1,0.45))
        self.panel.add_element(self.combox_brain,(0.1,0.35))
        self.panel.add_element(self.slice_slider_label,(0.2,0.53))
        self.panel.add_element(self.slice_slider,(0.55,0.53))
        self.panel.add_element(self.remove_button,(0.5,0.4))
        self.panel.add_element(self.add_button,(0.1,0.4))
        self.panel.add_element(self.opacity_slider_label,(0.1,0.3))
        self.panel.add_element(self.opacity_slider,(0.55,0.3))

    
    def define_maxview(self,maxval=180,slice_actor=None,brain_2d=None):
        self.brain_2d = brain_2d
        self.slice_actor = slice_actor
        self.max_value_view = maxval
        # print(self.slice_actor.shape,self.brain_2d)

    def __init__(self,background) -> None:
        self.background = background
        self.scene = None
        self.slice_actor = None
        self.brain_2d = None
        self.max_value_view = None
        global selected_item
        self.selected_actor = selected_item
        self.ori = 1
        self.slider_cut = None
        self.rois = None
        self.indexxx = 0
    def slice_actorvalues(self,val):
        self.brain_2d = val
    def change_view(self,radio):
        """
        Args: 
        radio: ui.RadioButton - A button to rotate the camera
        Changes the orientation depending on the button press
        """
        options = {'Sagittal':1,'Axial':2,'Coronal':3}
        self.ori = options[radio.checked_labels[0]]
        if self.slice_actor:
            self.slice_actor.GetProperty().SetOpacity(1)
        self.flipper.deselect()
        self.selected_actor = self.slice_actor
        if self.ori==1:
            self.scene.set_camera(position=(400, 0, 0), focal_point=(0, 0, 0), view_up=(0, 0, 1))
            if self.slice_actor:
                self.scene.rm(self.slice_actor)
                if self.slider_cut==None:
                    cut = int(self.brain_2d[0]) if self.brain_2d!=None else self.slice_actor.shape[0] // 2
                else: cut = self.slider_cut
                self.slice_actor.display(cut, None, None)
                self.scene.add(self.slice_actor)
        if self.ori==2:
            self.scene.set_camera(position=(0, 0, -400), focal_point=(0, 0, 0), view_up=(0, 1, 0))
            if self.slice_actor:
                self.scene.rm(self.slice_actor)
                if self.slider_cut==None:
                    cut = int(self.brain_2d[2]) if self.brain_2d!=None else self.slice_actor.shape[2] // 2
                else:  cut = self.slider_cut 
                self.slice_actor.display(None,None,cut)
                self.scene.add(self.slice_actor)
        if self.ori==3:
            self.scene.set_camera(position=(0, 400, 0), focal_point=(0, 0, 0), view_up=(0, 0, 1))
            if self.slice_actor:
                self.scene.rm(self.slice_actor)
                if self.slider_cut==None:
                    cut = int(self.brain_2d[1]) if self.brain_2d!=None else self.slice_actor.shape[1] // 2
                else: cut = self.slider_cut
                self.slice_actor.display(None,cut, None)
                self.scene.add(self.slice_actor)

    def saveresults(self,output_path):
        '''If dont want to visualize in 3d'''
        self.scene.zoom(0.9)
        self.scene.set_camera(position=(400, 0, 0), focal_point=(0, 0, 0), view_up=(0, 0, 1))
        if self.slice_actor:
             cut = int(self.brain_2d[0]) if self.brain_2d!=None else self.slice_actor.shape[0] // 2
             self.slice_actor.display(cut,None,None)
        fname=str(output_path)+"_sagittal"+".png"
        window.record(self.scene, out_path=fname, size=(2000, 2000), reset_camera=False)

        self.scene.set_camera(position=(-400, 0, 0), focal_point=(0, 0, 0), view_up=(0, 0, 1))
        if self.slice_actor:
             cut = int(self.brain_2d[0]) if self.brain_2d!=None else self.slice_actor.shape[0] // 2
             self.slice_actor.display(cut,None,None)
        fname=str(output_path)+"_sagittal_flipped"+".png"
        window.record(self.scene, out_path=fname, size=(2000, 2000), reset_camera=False)


        self.scene.set_camera(position=(0, 0, -400), focal_point=(0, 0, 0), view_up=(0, 1, 0))
        if self.slice_actor:
             cut = int(self.brain_2d[2]) if self.brain_2d!=None else self.slice_actor.shape[2] // 2
             self.slice_actor.display(None,None,cut)
        fname=str(output_path)+"_axial"+".png"
        window.record(self.scene, out_path=fname, size=(2000, 2000), reset_camera=False)

        self.scene.set_camera(position=(0, 0, 400), focal_point=(0, 0, 0), view_up=(0, 1, 0))
        if self.slice_actor:
             cut = int(self.brain_2d[2]) if self.brain_2d!=None else self.slice_actor.shape[2] // 2
             self.slice_actor.display(None,None,cut)
        fname=str(output_path)+"_axial_flipped"+".png"
        window.record(self.scene, out_path=fname, size=(2000, 2000), reset_camera=False)

        self.scene.set_camera(position=(0, 400, 0), focal_point=(0, 0, 0), view_up=(0, 0, 1))
        if self.slice_actor:
             cut = int(self.brain_2d[1]) if self.brain_2d!=None else self.slice_actor.shape[1] // 2
             self.slice_actor.display(None,cut,None)
        fname=str(output_path)+"_coronal"+".png"
        window.record(self.scene, out_path=fname, size=(2000, 2000), reset_camera=False)

        self.scene.set_camera(position=(0, -400, 0), focal_point=(0, 0, 0), view_up=(0, 0, 1))
        if self.slice_actor:
             cut = int(self.brain_2d[1]) if self.brain_2d!=None else self.slice_actor.shape[1] // 2
             self.slice_actor.display(None,cut,None)
        fname=str(output_path)+"_coronal_flipped"+".png"
        window.record(self.scene, out_path=fname, size=(2000, 2000), reset_camera=False)


    def Showmanger_init(self,di,rois,interactive,output_path):
        global selected_item
        self.size_screen = (1200,900)
        self.show_m = window.ShowManager(self.scene,title='DiVE',size = self.size_screen)
        if not interactive:
            self.saveresults(output_path)
        else:
            self.slice_slider_label = self.build_label(text=str("Slice"))
            self.remove_button = Option_Rem('Remove')
            self.add_button = Option_Add('Add')
            if self.max_value_view==None:
                self.max_value_view = 180
            self.slice_slider = LineSlider2D(min_value=0, max_value=self.max_value_view, initial_value=0, length=100,text_template='{value:.0f}')
            self.opacity_slider_label = self.build_label(text=str("Opacity"))
            self.opacity_slider = LineSlider2D(min_value=0.0, max_value=1, initial_value=1, length=100,text_template='{value:.1f}')               ## initial value does not work
            self.combox_brain = ComboBox2D(items=di['Brain'],placeholder="Brain: ",size=(290,150),others=[self.slice_slider,self.slice_slider_label,self.add_button,self.remove_button,self.opacity_slider_label,self.opacity_slider])
            self.combox_mesh = ComboBox2D(items=di['Mesh'],placeholder="Mesh: ",size=(290,150),others=[self.combox_brain,self.slice_slider,self.slice_slider_label])
            self.combox_track = ComboBox2D(items=di['Tract'],placeholder="Tract:  ",size=(290,150),others=[self.combox_brain,self.combox_mesh,self.slice_slider,self.slice_slider_label])
            self.combox_mask = ComboBox2D(items=di["Mask"],placeholder="Mask:  ",size=(290,150),others=[self.combox_brain,self.combox_track,self.combox_mesh])
            self.rois = rois
            self.panel = Panel2D(size=(300, 400), color=(0.9, 0.9, 0.9), opacity=1, align='left')
            self.view = RadioButton(['Axial','Coronal','Sagittal'],checked_labels=['Sagittal'])
            self.flipper = Option('Flipped')
            
            self.pannel()
            if self.slice_actor:
                self.slice_actor.GetProperty().SetOpacity(0)
            self.interaction()
            self.show_m.scene.add(self.panel)
            self.show_m.render()
            self.show_m.start(multithreaded=True)
    

    def interact_selected_actor(self):
        global selected_item
        self.selected_actor = self.rois[selected_item]



    def change_opacity(self,slider):
        global selected_item
        self.selected_actor = self.rois[selected_item]
        if str(type(self.selected_actor))=="<class 'vtkmodules.vtkRenderingCore.vtkAssembly'>":
            slicer_opacity = slider.value
            for i in range(self.selected_actor.GetParts().GetNumberOfItems()):
                self.selected_actor.GetParts().GetItemAsObject(i).GetProperty().SetOpacity(slicer_opacity)
                # self.selected_actor.GetParts().GetItemAsObject(i).GetProperty().SetOpacity(0.1)      ## Iyad
        else:
            self.selected_actor.GetProperty().SetOpacity(slider.value)
            # self.selected_actor.GetProperty().SetOpacity(0.1)       ## Iyad
    
    
    
    def handle_csv(self,command,flag):
            command_csv_path_mask = re.findall(r'--stats_csv\s(.*?)(?=\s--|$)', command)
            command_csv_path_mask = " ".join(command_csv_path_mask)
            command_csv_threshold_mask = re.findall(r'--threshold \s(.*?)(?=\s--|$)', command)
            command_csv_threshold_mask = " ".join(command_csv_threshold_mask) if command_csv_threshold_mask!=None else 0.5
            command_csv_threshold_p_value = re.findall(r'--log_p_value\s(.*?)(?=\s--|$)', command)
            command_csv_threshold_p_value = " ".join(command_csv_threshold_p_value) if command_csv_threshold_p_value!=None else False
            command_csv_range_p_value = re.findall(r'--range_p_value\s(.*?)(?=\s--|$)', command)
            command_csv_range_p_value = [match.split() for match in command_csv_range_p_value] if command_csv_range_p_value!=None else None
            if command_csv_range_p_value:command_csv_range_p_value = [float(i) for i in command_csv_range_p_value[0]]
            command_csv_map_p_value = re.findall(r'--map\s(.*?)(?=\s--|$)', command)
            command_csv_map_p_value = " ".join(command_csv_map_p_value) if command_csv_map_p_value!=None else "RdBu"

            if flag=="MASK":
                cc = Colors_csv(command_csv_path_mask)
                color_map_mask = cc.assign_colors(map=command_csv_map_p_value,range_value = command_csv_range_p_value,log_p_value=command_csv_threshold_p_value,threshold=command_csv_threshold_mask)
                return color_map_mask


    def adding_elements(self,command):
        matched_tract_index=0
        matched_mask_index=0
        width_tract_val=1
        matches_mask = re.findall(r'--mask\s(.*?)(?=\s--|$)', command)
        matches_mask = [match.split() for match in matches_mask]
        matches_tract = re.findall(r'--tract\s(.*?)(?=\s--|$)', command)
        matches_tract = [match.split() for match in matches_tract]
        matches_mesh = re.findall(r'--mesh\s(.*?)(?=\s--|$)', command)
        matches_mesh = [match.split() for match in matches_mesh]
        matches_csv = re.findall(r'--stats_csv\s(.*?)(?=\s--|$)', command)
        matches_csv = [match.split() for match in matches_csv]
        matches_csv_tract = re.findall(r'--stats_csv_tract_value\s(.*?)(?=\s--|$)', command)
        matches_csv_tract = [match.split() for match in matches_csv_tract]
        width_tract_val = re.findall(r'--width_tract\s(.*?)(?=\s--|$)', command)
        colors_tract = re.findall(r'--color_tract\s(.*?)(?=\s--|$)', command)
        colors_mask = re.findall(r'--color_mask\s(.*?)(?=\s--|$)', command)
        colors_mesh = re.findall(r'--color_mesh\s(.*?)(?=\s--|$)', command)
        colors_caller = Colors()
        colors_tract = " ".join(colors_tract)
        colors_mask = " ".join(colors_mask)
        colors_mesh = " ".join(colors_mesh)
        colors_tract = colors_caller.string_to_list(input_string = colors_tract) if colors_tract else  None
        colors_mask = colors_caller.string_to_list(input_string = colors_mask) if colors_mask else  None
        colors_mesh = colors_caller.string_to_list(input_string = colors_mesh) if colors_mesh else  None
        print(command)
        
        if matches_csv:
            color_map_mask_val = self.handle_csv(command,flag="MASK")
        load_caller = load()
        
        if matches_mask:
            for i in matches_mask[0]:
                if colors_mask and len(colors_mask)>matched_mask_index:
                    mask_value = load_caller.load_mask(mask_args = i,color=colors_mask[matched_mask_index])
                
                elif matches_csv and len(matches_csv)>matched_mask_index:
                    mask_value = load_caller.load_mask(mask_args = i,color_map_mask=color_map_mask_val)

                else:
                    mask_value = load_caller.load_mask(mask_args = i)
                self.combox_mask.append_item([os.path.basename(i)])
                self.rois[os.path.basename(i)]=mask_value
                self.show_m.scene.add(mask_value)
                matched_mask_index +=1
        if matches_tract:
            for i in matches_tract[0]:
                if colors_tract and len(colors_tract)>matched_tract_index:
                    tract_value = load_caller.load_tract(tract_args = i,tract_width=int(width_tract_val[0]),tract_color=colors_tract[matched_tract_index])
                else:
                    tract_value = load_caller.load_tract(tract_args = i,tract_width=int(width_tract_val[0]))
                self.combox_track.append_item([os.path.basename(i)])
                self.rois[os.path.basename(i)]=tract_value
                self.show_m.scene.add(tract_value)
                matched_tract_index= matched_tract_index+1
        if matches_mesh:
            index_mesh = 0
            for i in matches_mesh[0]:
                if colors_mesh and len(colors_mesh)>index_mesh:
                    mesh_caller = Mesh(pv.PolyData(i),colors_mesh[index_mesh])
                else:
                    mesh_caller = Mesh(pv.PolyData(i),color_list=Colors.get_tab20_color(index = index_mesh, type_='vtk'))
                index_mesh += 1
                actor_vtk = mesh_caller.load_mesh()
                self.combox_mesh.append_item([os.path.basename(i)])
                self.rois[os.path.basename(i)]= actor_vtk

                self.show_m.scene.add(actor_vtk)
        self.indexxx+=1
        
    def add_element(self,option):
        # Create an NSOpenPanel to display the file dialog
            completed_process = subprocess.run(['python', os.path.dirname(__file__)+'/Viz_UI.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            selected_file_path = completed_process.stdout
            self.adding_elements(selected_file_path)

    

    def remove_element(self,option):
        global selected_item
        remove_combo_box = None
        if selected_item in self.combox_mesh.items:
            remove_combo_box = self.combox_mesh
        elif selected_item in self.combox_mask.items:
            remove_combo_box = self.combox_mask
        elif selected_item in self.combox_track.items:
             remove_combo_box = self.combox_track
        self.selected_actor = self.rois[selected_item]
        remove_combo_box.remove_item(selected_item)
        self.show_m.scene.rm(self.selected_actor)

    def flip_view(self,option):
        if self.flipper.checked:
            if self.ori==1:
                self.scene.set_camera(position=(-400, 0, 0), focal_point=(0, 0, 0), view_up=(0, 0, 1))
            if self.ori==2:
                self.scene.set_camera(position=(0, 0, 400), focal_point=(0, 0, 0), view_up=(0, 1, 0))
            if self.ori==3:
                self.scene.set_camera(position=(0, -400, 0), focal_point=(0, 0, 0), view_up=(0, 0, 1))
        else:
            if self.ori==1:
                self.scene.set_camera(position=(400, 0, 0), focal_point=(0, 0, 0), view_up=(0, 0, 1))
            if self.ori==2:
                self.scene.set_camera(position=(0, 0, -400), focal_point=(0, 0, 0), view_up=(0, 1, 0))
            if self.ori==3:
                self.scene.set_camera(position=(0, 400, 0), focal_point=(0, 0, 0), view_up=(0, 0, 1))

    def change_slice_handler(self,slider):
        self.slider_cut = int(slider.value)
        self.scene.rm(self.slice_actor)
        if self.ori==1:
            self.slice_actor.display(self.slider_cut,None,None)
        elif self.ori==2:
            self.slice_actor.display(None,None,self.slider_cut)
        elif self.ori==3:
            self.slice_actor.display(None,self.slider_cut,None)
        self.scene.add(self.slice_actor)


    def interaction(self):
        self.opacity_slider.on_change = self.change_opacity
        self.view.on_change = self.change_view
        self.flipper.on_change = self.flip_view
        self.slice_slider.on_change = self.change_slice_handler
        self.remove_button.on_change = self.remove_element
        self.add_button.on_change = self.add_element
        
