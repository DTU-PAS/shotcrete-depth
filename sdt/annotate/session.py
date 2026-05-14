import numpy
from os import makedirs
from os.path import exists
from enum import Enum
from pyvista import (
    Plotter, 
    Plane, 
    numpy_to_texture
)
from typing import Optional
from sdt.constants import RGB_LEFT
from sdt.utils import (
    project_and_overlay
)
from sdt.annotate.utils import (
    make_vertex_polydata,
    annotations_to_colors
)
from sdt.annotate.manager import SessionManager, Operation


class Interaction(str, Enum):
    MOVE = "move"
    SELECT = "select"


class Session:
    def __init__(self, rosbag_path: str, annotations_path: str, simple_mode: bool = False, flag: Optional[str] = None):   
        self._manager = SessionManager(rosbag_path, annotations_path, flag)
        
        if not exists(annotations_path):
            makedirs(annotations_path)
        
        self._simple_mode = simple_mode

        self._operation: Operation = Operation.KEEP
        self._interaction: Interaction = Interaction.MOVE

        # UI
        self._plotter = None
        self._interaction_text = None
        self._sample_name_text = None
        self._flag_text = None

        self._init_ui()
        self._load_cloud()
        self._update_colors()
        self._update_interaction_text()
        self._update_flag_text()
        self._update_sample_name()


    def _init_ui(self):
        self._plotter = Plotter(shape=(1, 2))
        self._plotter.set_background("#0b0f19")
        self._plotter.add_axes()
        self._plotter.add_bounding_box(line_width=1)

        help_lines = ["Drag a rectangle in SELECT mode"]

        if self._simple_mode:
            help_lines.append("Colors: KEPT - green, REMOVED - magenta")
        else:
            help_lines.append("Colors: KEPT - green/blue (algorithm/user), REMOVED - yellow/magenta (algorithm/user)")

        help_lines += [
            "D: Toggle Mode REMOVE/KEEP",
            "R: Toggle Interaction MOVE/SELECT",
            "S: Save  |  U: Undo  |  M: mark EVAL  |  N: mark FACE",
            "Right: Next sample  |  Left: Previous sample  |  Q: Quit batch",
        ]
        self._plotter.add_text("\n".join(help_lines), font_size=9, color="white", position="lower_right")
        self._interaction_text = self._plotter.add_text("", font_size=14, color="cyan")
        self._sample_name_text = self._plotter.add_text("", font_size=14, color="cyan")
        self._flag_text = self._plotter.add_text("", font_size=14, color="cyan")

        # Event bindings
        self._plotter.add_key_event("d", self._on_toggle_operation)
        self._plotter.add_key_event("D", self._on_toggle_operation)
        self._plotter.add_key_event("r", self._on_toggle_interaction)
        self._plotter.add_key_event("R", self._on_toggle_interaction)
        self._plotter.add_key_event("m", self._on_toggle_eval)
        self._plotter.add_key_event("M", self._on_toggle_eval)
        self._plotter.add_key_event("n", self._on_toggle_face)
        self._plotter.add_key_event("N", self._on_toggle_face)
        self._plotter.add_key_event("u", self._on_undo)
        self._plotter.add_key_event("U", self._on_undo)
        self._plotter.add_key_event("s", self._on_save)
        self._plotter.add_key_event("S", self._on_save)
        self._plotter.add_key_event("Right", self._on_next)
        self._plotter.add_key_event("Left", self._on_previous)
        self._plotter.enable_cell_picking(callback=self._on_pick, through=True, show=False, style="wireframe", show_message=False)


    def _load_cloud(self):
        self.cloud = make_vertex_polydata(self._manager.lidar_points)
        self.cloud.point_data["colors"] = annotations_to_colors(self._manager.annotations(), self._simple_mode)
        self._plotter.add_mesh(
            self.cloud,
            point_size=4,
            render_points_as_spheres=True,
            scalars="colors",
            rgb=True,
            pickable=True,
            name="cloud",
        )

    def _update_colors(self):
        colors = annotations_to_colors(self._manager.annotations(), self._simple_mode)

        # point cloud
        self.cloud.point_data["colors"] = colors

        # image preview
        image = self._manager.sample_element(RGB_LEFT)
        preview, _ = project_and_overlay(self._manager.lidar_points, colors, image, self._manager.intrinsics(), self._manager.extrinsics(), 2)
        plane = Plane(i_size=preview.shape[1], j_size=preview.shape[0])
        self._plotter.subplot(0, 1)
        self._plotter.add_mesh(plane, texture=numpy_to_texture(preview), name="image")
        self._plotter.view_xy()
        self._plotter.camera.zoom(1.0)
        self._plotter.subplot(0, 0)


    def _update_interaction_text(self):
        text = f"Operation: {str(self._operation.name).upper()}  |  Interaction: {str(self._interaction.name).upper()}"
        self._interaction_text.set_text("lower_left", text)


    def _update_flag_text(self):
        flags = []
        if self._manager.is_marked_for_evaluation():
            flags.append("EVAL")
        if self._manager.is_marked_as_contains_face():
            flags.append("FACE")
        self._flag_text.set_text("upper_right", " | ".join(flags))


    def _update_sample_name(self):
        self._sample_name_text.set_text("upper_left", f"{self._manager.sample_name()}\n{self._manager.sample_index() + 1}/{len(self._manager)}")


    def _on_toggle_operation(self):
        self._operation = Operation.REMOVE if self._operation is Operation.KEEP else Operation.KEEP
        self._update_interaction_text()
        self._plotter.render()


    def _on_toggle_interaction(self):
        self._interaction = Interaction.SELECT if self._interaction is Interaction.MOVE else Interaction.MOVE
        self._update_interaction_text()
        self._plotter.render()


    def _on_toggle_eval(self):
        self._manager.toggle_evaluation_mark()
        self._update_flag_text()
        self._plotter.render()
    
    def _on_toggle_face(self):
        self._manager.toggle_face_mark()
        self._update_flag_text()
        self._plotter.render()


    def _on_next(self):
        if self._manager.next_sample():
            self._update_sample_name()
            self._update_flag_text()
            self._load_cloud()
            self._update_colors()
            self._plotter.render()


    def _on_previous(self):
        if self._manager.previous_sample():
            self._update_sample_name()
            self._update_flag_text()
            self._load_cloud()
            self._update_colors()
            self._plotter.render()


    def _on_pick(self, picked):        
        if hasattr(picked, "cell_data") and "orig_id" in picked.cell_data:
            ids = numpy.asarray(picked.cell_data["orig_id"]).astype(int)
            if ids.size == 0:
                return
            
            self._manager.apply_pick(ids, self._operation)
            self._update_colors()
            self._plotter.render()


    def _on_undo(self):
        if self._manager.undo():
            self._update_colors()
            self._plotter.render()


    def _on_save(self):
        self._manager.save()


    def run(self):
        self._plotter.show()
 