from flask import Flask 

from routes import create_generation_blueprint
from generation_service import GenerationService


class MockOrgRepository:
    def get_org_hierarchy(self, org_id):
        return ["mock_org"]


class MockMappingService:
    def build_presentation_model(self, orgs, include_externals, include_trainees):
        return {"mock": "presentation_model"}



class MockPptService:
    def generate_presentation(self, model, template_name, output_name):
        class GeneratedFile:
            file_url = "http://localhost:5000/generated/mock.pptx"

        return GeneratedFile()



def create_app():
    app = Flask(__name__)

    generation_service = GenerationService(
        org_repository = MockOrgRepository(),
        mapping_service = MockMappingService(),
        ppt_service = MockPptService(),
    )

    generation_bp = create_generation_blueprint(generation_service)
    


    app.register_blueprint(generation_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
