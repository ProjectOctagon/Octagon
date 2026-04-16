from pptx import Presentation
import os
from datetime import datetime


class PptService:
    def __init__(self, template_dir: str, output_dir: str, base_url: str):
        self.template_dir = template_dir # where .pptx templates for generating the slides are stored
        self.output_dir = output_dir # path for saving generated files
        self.base_url = base_url #  used to generate a download link

    def generate_presentation(self, model, template_name: str, output_name: str = None): # model => list of slide definitions, template_name =>.pptx template used to generate slides, output_name => optional filename for generated pptx                                                                                
        template_path = os.path.join(self.template_dir, f"{template_name}.pptx") #loading template for generating the slides

        if not os.path.exists(template_path): #if the template doesn't exist, throws an error
            raise FileNotFoundError(f"Template not found: {template_path}")

        prs = Presentation(template_path)

        # Build slides
        for slide_model in model.slides: #model contains a list of slide definitions;
            slide_type = getattr(slide_model, "type") #get type required for slides and generate appropriate pptx

            if slide_type == "org_chart":  
                self._add_org_chart_slide(prs, slide_model)
            

        # Save file
        filename = self._generate_filename(output_name) 
        output_path = os.path.join(self.output_dir, filename)

        os.makedirs(self.output_dir, exist_ok=True)
        prs.save(output_path)

        return self._build_file_url(filename)

    
    def _add_org_chart_slide(self, prs, slide_model):
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank slide

       #to be implemented...


    
    def _generate_filename(self, output_name): #generates unique file names using timestamp to prevent overwriting existing files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  

        if output_name:
            return f"{output_name}_{timestamp}.pptx" 

        return f"presentation_{timestamp}.pptx" #if user doesn't provide name, it gives it a default one, example: presentation_20260410_153012.pptx

    def _build_file_url(self, filename): 
        return f"{self.base_url}/{filename}"
