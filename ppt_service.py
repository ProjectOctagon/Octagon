from pptx import Presentation
from pptx.util import Pt, Cm
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR_TYPE
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.text import MSO_ANCHOR

import os
from datetime import datetime

from slide_models import SlideModel, BoxModel, PresentationModel


class PptService:
    DEFAULT_COLORS = {
        "HEAD": RGBColor(0, 15, 45),
        "ASSISTANT": RGBColor(26, 153, 171),
        "UNIT": RGBColor(189, 215, 255),
        "DOTTED": RGBColor(89, 89, 89),
        "HIGHLIGHT": RGBColor(0, 204, 102),
        "LINE": RGBColor(90, 90, 90)
    }

    def __init__(self, template_dir: str, output_dir: str, base_url: str):
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.base_url = base_url
        # Per-instance working palette; starts from defaults and may be
        # overridden per request via generate_presentation(colors=...).
        self.COLORS = dict(self.DEFAULT_COLORS)

    @staticmethod
    def _parse_hex_color(value):
        """Convert a '#RRGGBB' / 'RRGGBB' string to an RGBColor, or None."""
        if not value or not isinstance(value, str):
            return None

        hex_str = value.strip().lstrip("#")

        if len(hex_str) != 6:
            return None

        try:
            return RGBColor(
                int(hex_str[0:2], 16),
                int(hex_str[2:4], 16),
                int(hex_str[4:6], 16)
            )
        except ValueError:
            return None

    def _apply_color_overrides(self, colors):
        """
        Reset to defaults, then apply any valid overrides from the request.
        Unknown keys and invalid hex values are ignored.
        """
        self.COLORS = dict(self.DEFAULT_COLORS)

        if not colors:
            return

        for key, value in colors.items():
            key = str(key).upper()

            if key not in self.DEFAULT_COLORS:
                continue

            parsed = self._parse_hex_color(value)
            if parsed is not None:
                self.COLORS[key] = parsed

    def generate_presentation(
        self,
        model: PresentationModel,
        template_name: str,
        output_name: str = None,
        colors: dict = None
    ):
        # Apply per-request color overrides (resets to defaults each call).
        self._apply_color_overrides(colors)

        template_path = os.path.join(self.template_dir, f"{template_name}.pptx")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        prs = Presentation(template_path)

        # clear template slides while keeping layouts and theme
        for i in range(len(prs.slides) - 1, -1, -1):
            r_id = prs.slides._sldIdLst[i].rId
            prs.part.drop_rel(r_id)
            del prs.slides._sldIdLst[i]

        org_id_to_slide = {}

       
        pending_links = []

        for slide_model in model.slides:
            slide_type = getattr(slide_model, "type", None)

            if slide_type == "org_chart":
                slide, link_shapes = self._add_org_chart_slide(prs, slide_model)

                slide_org_id = getattr(slide_model, "org_id", None)
                if slide_org_id is not None:
                    slide_org_id = str(slide_org_id)
                    # keep the first slide for an org as the canonical target
                    if slide_org_id not in org_id_to_slide:
                        org_id_to_slide[slide_org_id] = slide

                pending_links.extend(link_shapes)

        # wire up internal jump to slide hyperlinks now that all slides exist
        for shape, target_org_id in pending_links:
            target_slide = org_id_to_slide.get(str(target_org_id))

            if target_slide is not None:
                self._set_internal_hyperlink(shape, target_slide)

        filename = self._generate_filename(output_name)
        output_path = os.path.join(self.output_dir, filename)

        os.makedirs(self.output_dir, exist_ok=True)
        prs.save(output_path)

        return self._build_file_url(filename)

    def _add_org_chart_slide(self, prs, slide_model: SlideModel):
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # remove default ppt placeholders
        for shape in list(slide.shapes):
            if shape.is_placeholder:
                sp = shape._sp
                sp.getparent().remove(sp)

        # slide title
        title_shape = slide.shapes.add_textbox(
            Cm(1.3),
            Cm(0.76),
            Cm(22.86),
            Cm(2.54)
        )

        tf = title_shape.text_frame
        tf.text = f"{slide_model.title} {slide_model.hierarchy_level}".strip()

        title_paragraph = tf.paragraphs[0]
        title_paragraph.font.name = "Nokia Pure Headline Light"
        title_paragraph.font.size = Pt(28)
        title_paragraph.font.color.rgb = RGBColor(0, 102, 255)

        # basic layout settings
        col_width = Cm(8)
        start_y = Cm(3.05)
        row_spacing = Cm(1.59)

        box_width = Cm(6.93)
        box_height = Cm(1.33)

        # manager box position
        manager_x = Cm(7.62)
        manager_y = Cm(15.75)
        manager_width = Cm(6.93)
        manager_height = Cm(1.33)

        all_box_positions = []

        # store box coordinates before drawing connectors
        for i, column in enumerate(slide_model.columns):
            current_x = Cm(3.8) + (i * (col_width + Cm(0.76)))
            column_positions = []

            for j, unit in enumerate(column):
                unit_y = start_y  + (j * row_spacing)

                column_positions.append({
                    "box": unit,
                    "x": current_x,
                    "y": unit_y,
                    "width": box_width,
                    "height": box_height
                })

            if column_positions:
                all_box_positions.append(column_positions)

        # draw connectors first so boxes stay on top
        if all_box_positions:
            self._draw_connection_lines(
                slide=slide,
                all_box_positions=all_box_positions,
                manager_x=manager_x,
                manager_y=manager_y,
                manager_width=manager_width,
                box_height=box_height,
                start_y=start_y
            )

        # shapes that should become jump to slide hyperlinks, paired with the org_id they point to
        link_shapes = []

        # draw organization, employee boxes
        for column_positions in all_box_positions:
            for box_position in column_positions:
                shape = self._draw_box(
                    slide,
                    box_position["x"],
                    box_position["y"],
                    box_position["box"],
                    width=box_position["width"],
                    height=box_position["height"]
                )

                target_org_id = getattr(box_position["box"], "target_org_id", None)
                if target_org_id is not None:
                    link_shapes.append((shape, str(target_org_id)))

        # draw head manager
        self._draw_box(
            slide,
            manager_x,
            manager_y,
            slide_model.head_of_unit,
            width=manager_width,
            height=manager_height
        )

        # draw assistant box when available
        if slide_model.assistant:
            self._draw_box(
                slide,
                Cm(14.23),
                Cm(15.75),
                slide_model.assistant,
                width=Cm(6.93),
                height=Cm(1.33)
            )

        self._add_footer(slide)

        return slide, link_shapes

    def _draw_connection_lines(
        self,
        slide,
        all_box_positions,
        manager_x,
        manager_y,
        manager_width,
        box_height,
        start_y
    ):
        manager_center_x = int(manager_x + manager_width/2)
        manager_center_y = int(manager_y + Cm(1.33) / 2)
        

        # main vertical spines start from the middle of first box in their column
        main_line_y = start_y + box_height/2

        if not all_box_positions:
            return

        column_spine_x_values = []

        # each column gets a vertical spine
        for column_positions in all_box_positions:
            first_box = column_positions[0]
            spine_x = int(first_box["x"] - Cm(0.8))
            column_spine_x_values.append(spine_x)

       
        leftmost_x = min(column_spine_x_values)
        rightmost_x = max(column_spine_x_values)
        bottom_connector_y = manager_y - box_height/2


        # main horizontal connector across the bottom of the column structure when there's only one column on the page
        self._draw_horizontal_line(slide, leftmost_x, manager_center_x, bottom_connector_y)

        #extend the connector when there are more than one columns.
        self._draw_horizontal_line(slide, manager_center_x, rightmost_x, bottom_connector_y)


        #drawing a vertical line in the middle od the manager box to connect it to the bottom connector
        self._draw_vertical_line(slide, manager_center_x, bottom_connector_y, manager_y)
        
        for col_idx, column_positions in enumerate(all_box_positions):
            #last_box = column_positions[-1]
            spine_x = column_spine_x_values[col_idx]

            #last_box_center_y = int(last_box["y"] + last_box["height"] / 2)

            # connect each column spine to the first box of the column and then to the bottom connector
            self._draw_vertical_line(slide, spine_x, main_line_y, bottom_connector_y)

            # add short horizontal connectors from the spine to every box
            for box_position in column_positions:
                box_center_y = int(box_position["y"] + box_position["height"] / 2)
                box_left_x = int(box_position["x"])

                self._draw_horizontal_line(slide, spine_x, box_left_x, box_center_y)

        


    def _draw_vertical_line(self, slide, x, y_top, y_bottom):
        x = int(x)
        y_top = int(y_top)
        y_bottom = int(y_bottom)

        if y_top > y_bottom:
            y_top, y_bottom = y_bottom, y_top

        line = slide.shapes.add_connector(
            MSO_CONNECTOR_TYPE.STRAIGHT,
            x,
            y_top,
            x,
            y_bottom
        )

        line.line.fill.solid()
        line.line.fill.fore_color.rgb = self.COLORS["LINE"]
        line.line.color.rgb = self.COLORS["LINE"]
        line.line.width = Pt(1.2)

        return line

    def _draw_horizontal_line(self, slide, x_left, x_right, y):
        x_left = int(x_left)
        x_right = int(x_right)
        y = int(y)

        if x_left > x_right:
            x_left, x_right = x_right, x_left

        line = slide.shapes.add_connector(
            MSO_CONNECTOR_TYPE.STRAIGHT,
            x_left,
            y,
            x_right,
            y
        )

        line.line.fill.solid()
        line.line.fill.fore_color.rgb = self.COLORS["LINE"]
        line.line.color.rgb = self.COLORS["LINE"]
        line.line.width = Pt(1.2)

        return line

    def _draw_line(self, slide, x1, y1, x2, y2):
        line = slide.shapes.add_connector(
            MSO_CONNECTOR_TYPE.STRAIGHT,
            int(x1),
            int(y1),
            int(x2),
            int(y2)
        )

        line.line.fill.solid()
        line.line.fill.fore_color.rgb = self.COLORS["LINE"]
        line.line.color.rgb = self.COLORS["LINE"]
        line.line.width = Pt(1.2)

        return line

    def _add_footer(self, slide):
        left = Cm(5.57)
        top = Cm(17.24)
        width = Cm(22.80)
        height = Cm(1.54)

        footer_shape = slide.shapes.add_textbox(left, top, width, height)
        tf = footer_shape.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = (
            "This document aims to support the business groups and corporate functions "
            "in Nokia subject to necessary legal procedures and approvals. Nothing herein "
            "should be deemed to indicate that any final decision has been made which "
            "otherwise may require information and/or consultation with relevant employee "
            "representative body/ies, where applicable."
        )
        p.font.size = Pt(10.7)
        p.font.name = "Nokia Pure Text Light"
        p.font.color.rgb = RGBColor(128, 128, 128)
        p.alignment = PP_ALIGN.LEFT

    def _draw_box(
        self,
        slide,
        x,
        y,
        box_data: BoxModel,
        width=Cm(6.93),
        height=Cm(1.33)
    ):

        CHARS_PER_LINE = 40

        # calculating lines for title
        title_len = len(box_data.title or "")
        title_lines = max(1, -(-title_len // CHARS_PER_LINE)) 

        # calculating lines for subtitle
        sub_len = len(box_data.subtitle or "")
        sub_lines = max(1, -(-sub_len // CHARS_PER_LINE))

        total_lines = title_lines + sub_lines

        if total_lines > 2:
            # base padding + height per line (approx. 0.45 cm per text line)
            calculated_height = Cm(0.4) + Cm(0.45 * total_lines)
            # ensure it never shrinks below the standard minimum height
            height = max(height, calculated_height)

        shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            x,
            y,
            width,
            height
        )

        tf = shape.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE

        if box_data.is_changed:
            shape.line.color.rgb = self.COLORS["HIGHLIGHT"]
            shape.line.width = Pt(2.5)
        else:
            shape.line.fill.background()

        shape.fill.solid()

        if box_data.box_type == "manager":
            shape.fill.fore_color.rgb = self.COLORS["HEAD"]
        elif box_data.box_type == "assistant":
            shape.fill.fore_color.rgb = self.COLORS["ASSISTANT"]
        elif box_data.box_type == "dotted":
            shape.fill.fore_color.rgb = self.COLORS["DOTTED"]
        else:
            shape.fill.fore_color.rgb = self.COLORS["UNIT"]

        tf.margin_left = Cm(0.25)
        tf.margin_right = Cm(0.15)
        tf.margin_top = Cm(0.05)
        tf.margin_bottom = Cm(0.05)

        p1 = tf.paragraphs[0]
        p1.text = box_data.title
        p1.font.name = "Nokia Pure Headline"
        p1.alignment = PP_ALIGN.LEFT
        p1.font.bold = True
        p1.font.size = Pt(12)

        if box_data.box_type in ["manager", "assistant", "dotted"]:
            p1.font.color.rgb = RGBColor(255, 255, 255)
        else:
            p1.font.color.rgb = RGBColor(0, 0, 0)

        p2 = tf.add_paragraph()
        p2.text = box_data.subtitle
        p2.font.name = "Nokia Pure Headline"
        p2.font.size = Pt(12)
        p2.font.color.rgb = p1.font.color.rgb

        return shape

    def _set_internal_hyperlink(self, shape, target_slide):
        """
        Attach a click action to ``shape`` that jumps to ``target_slide``
        inside the same presentation (PowerPoint "Hyperlink to > Slide").
        """
        # create a relationship from this slide's part to the target slide part
        slide_part = shape.part
        rId = slide_part.relate_to(
            target_slide.part,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
        )

        # add the click action (hlinkClick) to the shape's non-visual props
        cNvPr = shape._element._nvXxPr.cNvPr
        ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
        r_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

        # remove any pre-existing hlinkClick to stay idempotent
        existing = cNvPr.find(f"{{{ns}}}hlinkClick")
        if existing is not None:
            cNvPr.remove(existing)

        hlink = cNvPr.makeelement(f"{{{ns}}}hlinkClick", {})
        hlink.set(f"{{{r_ns}}}id", rId)
        hlink.set("action", "ppaction://hlinksldjump")
        cNvPr.append(hlink)

    def _generate_filename(self, output_name):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if output_name:
            clean_name = output_name.replace(".pptx", "")
            return f"{clean_name}_{timestamp}.pptx"

        return f"presentation_{timestamp}.pptx"

    def _build_file_url(self, filename):
        return f"{self.base_url}/{filename}"