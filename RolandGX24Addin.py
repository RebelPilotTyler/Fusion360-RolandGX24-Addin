import os
import subprocess
import sys
import traceback
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import adsk.core
import adsk.fusion


APP = adsk.core.Application.get()
UI = APP.userInterface if APP else None

CMD_EXPORT_ID = 'rolandGX24ExportHPGL'
CMD_SEND_ID = 'rolandGX24ExportAndSend'
CMD_EXPORT_NAME = 'GX-24: Export HPGL'
CMD_SEND_NAME = 'GX-24: Export + Send'
CMD_DESCRIPTION = 'Export selected sketch curves as HPGL for Roland GX-24 vinyl cutter.'
PANEL_ID = 'SolidScriptsAddinsPanel'
WORKSPACE_ID = 'FusionSolidEnvironment'

handlers = []


@dataclass
class ExportOptions:
    units: str
    scale: float
    tolerance: float
    origin_mode: str
    output_path: str
    filename: str


class HPGLExporter:
    """Converts sketch curves to HPGL polyline commands."""

    def __init__(self, options: ExportOptions):
        self.options = options

    def export(self, curves: Sequence[adsk.fusion.SketchCurve]) -> str:
        if not curves:
            raise ValueError('No sketch curves were selected.')

        polylines = [self._curve_to_polyline(c) for c in curves]
        bbox_min = self._bounding_min(polylines)
        origin = bbox_min if self.options.origin_mode == 'lower_left' else (0.0, 0.0)

        hpgl_lines = ['IN;', 'SP1;']
        for poly in polylines:
            transformed = [self._to_plotter_units(p[0] - origin[0], p[1] - origin[1]) for p in poly]
            if len(transformed) < 2:
                continue
            start = transformed[0]
            hpgl_lines.append(f'PU{start[0]},{start[1]};')
            draw_coords = ','.join(f'{x},{y}' for x, y in transformed[1:])
            hpgl_lines.append(f'PD{draw_coords};')
            hpgl_lines.append('PU;')

        hpgl_lines.append('SP0;')
        return '\n'.join(hpgl_lines) + '\n'

    def _curve_to_polyline(self, curve: adsk.fusion.SketchCurve) -> List[Tuple[float, float]]:
        geom = curve.geometry
        if geom.objectType == adsk.core.Line3D.classType():
            line = adsk.core.Line3D.cast(geom)
            return [(line.startPoint.x, line.startPoint.y), (line.endPoint.x, line.endPoint.y)]

        if geom.objectType == adsk.core.Arc3D.classType():
            arc = adsk.core.Arc3D.cast(geom)
            sweep = abs(arc.endAngle - arc.startAngle)
            return self._sample_curve(curve, self._arc_segment_count(arc.radius, sweep))

        if geom.objectType == adsk.core.Circle3D.classType():
            circle = adsk.core.Circle3D.cast(geom)
            return self._sample_curve(curve, self._arc_segment_count(circle.radius, 2.0 * 3.141592653589793))

        return self._sample_curve(curve, None)

    def _sample_curve(self, curve: adsk.fusion.SketchCurve, segments: Optional[int]) -> List[Tuple[float, float]]:
        evaluator = curve.geometry.evaluator
        ok, start_param, end_param = evaluator.getParameterExtents()
        if not ok:
            raise ValueError('Unable to evaluate selected curve.')

        if segments is None:
            ok, length = evaluator.getLengthAtParameter(start_param, end_param)
            if not ok:
                length = 1.0
            tol_cm = self._tolerance_in_cm()
            segments = max(4, min(400, int(length / max(tol_cm, 1e-5)) + 1))

        points = []
        for i in range(segments + 1):
            t = start_param + (end_param - start_param) * (i / segments)
            ok, p = evaluator.getPointAtParameter(t)
            if ok:
                points.append((p.x, p.y))

        if len(points) < 2:
            raise ValueError('Curve sampling produced insufficient points.')

        deduped = [points[0]]
        for p in points[1:]:
            if p != deduped[-1]:
                deduped.append(p)
        return deduped

    def _arc_segment_count(self, radius_cm: float, sweep_rad: float) -> int:
        tol_cm = max(self._tolerance_in_cm(), 1e-6)
        if tol_cm >= radius_cm:
            return 8
        step = 2.0 * __import__('math').acos(max(-1.0, min(1.0, 1.0 - (tol_cm / radius_cm))))
        if step <= 0:
            return 32
        return max(8, min(720, int(__import__('math').ceil(sweep_rad / step))))

    def _to_plotter_units(self, x_cm: float, y_cm: float) -> Tuple[int, int]:
        x_u = self._cm_to_output_units(x_cm) * self.options.scale
        y_u = self._cm_to_output_units(y_cm) * self.options.scale
        factor = 40.0 if self.options.units == 'mm' else 1016.0
        return int(round(x_u * factor)), int(round(y_u * factor))

    def _cm_to_output_units(self, cm_value: float) -> float:
        return cm_value * 10.0 if self.options.units == 'mm' else cm_value / 2.54

    def _tolerance_in_cm(self) -> float:
        return self.options.tolerance * (0.1 if self.options.units == 'mm' else 2.54)

    @staticmethod
    def _bounding_min(polylines: Sequence[Sequence[Tuple[float, float]]]) -> Tuple[float, float]:
        min_x = min(p[0] for poly in polylines for p in poly)
        min_y = min(p[1] for poly in polylines for p in poly)
        return min_x, min_y


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, send_after_export: bool):
        super().__init__()
        self.send_after_export = send_after_export

    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        try:
            cmd = args.command
            cmd.isExecutedWhenPreEmpted = False

            inputs = cmd.commandInputs
            sel = inputs.addSelectionInput('curves', 'Sketch Curves', 'Select one or more 2D sketch curves')
            sel.addSelectionFilter('SketchCurves')
            sel.setSelectionLimits(1)

            units_dd = inputs.addDropDownCommandInput('units', 'Units', adsk.core.DropDownStyles.TextListDropDownStyle)
            units_dd.listItems.add('mm', True)
            units_dd.listItems.add('inch', False)

            inputs.addValueInput('scale', 'Scale Factor', '', adsk.core.ValueInput.createByReal(1.0))
            inputs.addValueInput('tolerance', 'Tolerance', '', adsk.core.ValueInput.createByReal(0.1))

            origin_dd = inputs.addDropDownCommandInput('origin', 'Origin', adsk.core.DropDownStyles.TextListDropDownStyle)
            origin_dd.listItems.add('Lower Left of Bounding Box', True)
            origin_dd.listItems.add('Sketch Origin', False)

            inputs.addStringValueInput('outputPath', 'Output Path', '')
            inputs.addStringValueInput('filename', 'Filename', 'output.plt')

            on_execute = CommandExecuteHandler(self.send_after_export)
            cmd.execute.add(on_execute)
            handlers.append(on_execute)
        except Exception:
            _message(traceback.format_exc())


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, send_after_export: bool):
        super().__init__()
        self.send_after_export = send_after_export

    def notify(self, args: adsk.core.CommandEventArgs):
        try:
            inputs = args.command.commandInputs
            sel = adsk.core.SelectionCommandInput.cast(inputs.itemById('curves'))

            curves = []
            for i in range(sel.selectionCount):
                entity = adsk.fusion.SketchCurve.cast(sel.selection(i).entity)
                if entity:
                    curves.append(entity)

            options = ExportOptions(
                units=_selected_text(inputs.itemById('units')),
                scale=adsk.core.ValueCommandInput.cast(inputs.itemById('scale')).value,
                tolerance=adsk.core.ValueCommandInput.cast(inputs.itemById('tolerance')).value,
                origin_mode='lower_left' if _selected_text(inputs.itemById('origin')).startswith('Lower') else 'sketch_origin',
                output_path=adsk.core.StringValueCommandInput.cast(inputs.itemById('outputPath')).value,
                filename=adsk.core.StringValueCommandInput.cast(inputs.itemById('filename')).value,
            )

            if not options.output_path:
                raise ValueError('Output Path is required.')

            filename = options.filename if options.filename.lower().endswith('.plt') else f'{options.filename}.plt'
            os.makedirs(options.output_path, exist_ok=True)
            full_path = os.path.join(options.output_path, filename)

            exporter = HPGLExporter(options)
            hpgl = exporter.export(curves)

            with open(full_path, 'w', encoding='ascii', newline='\n') as f:
                f.write(hpgl)

            _message(f'HPGL exported to:\n{full_path}')

            if self.send_after_export:
                helper_path = os.path.join(os.path.dirname(__file__), 'helper', 'send_to_printer.py')
                if os.path.exists(helper_path):
                    subprocess.Popen([sys.executable, helper_path, full_path], creationflags=_creation_flags())
                else:
                    _message(f'Helper script not found:\n{helper_path}')
        except Exception as ex:
            _message(f'Error: {ex}\n\n{traceback.format_exc()}')


def _selected_text(dropdown_input) -> str:
    dd = adsk.core.DropDownCommandInput.cast(dropdown_input)
    return dd.selectedItem.name if dd and dd.selectedItem else ''


def _creation_flags() -> int:
    return 0x00000008 if sys.platform.startswith('win') else 0


def _message(text: str):
    if UI:
        UI.messageBox(text)


def _create_command(cmd_id: str, name: str, description: str, send_after_export: bool):
    cmd_def = UI.commandDefinitions.itemById(cmd_id)
    if cmd_def:
        cmd_def.deleteMe()

    cmd_def = UI.commandDefinitions.addButtonDefinition(cmd_id, name, description)
    on_created = CommandCreatedHandler(send_after_export)
    cmd_def.commandCreated.add(on_created)
    handlers.append(on_created)

    workspace = UI.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    control = panel.controls.itemById(cmd_id)
    if control:
        control.deleteMe()
    panel.controls.addCommand(cmd_def)


def run(context):
    try:
        _create_command(CMD_EXPORT_ID, CMD_EXPORT_NAME, CMD_DESCRIPTION, False)
        _create_command(CMD_SEND_ID, CMD_SEND_NAME, CMD_DESCRIPTION, True)
    except Exception:
        _message(f'Add-In failed to start:\n{traceback.format_exc()}')


def stop(context):
    try:
        workspace = UI.workspaces.itemById(WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(PANEL_ID)

        for cmd_id in [CMD_EXPORT_ID, CMD_SEND_ID]:
            control = panel.controls.itemById(cmd_id)
            if control:
                control.deleteMe()

            cmd_def = UI.commandDefinitions.itemById(cmd_id)
            if cmd_def:
                cmd_def.deleteMe()
    except Exception:
        _message(f'Add-In failed to stop:\n{traceback.format_exc()}')
