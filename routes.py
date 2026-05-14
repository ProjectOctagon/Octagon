from flask import Blueprint, request, jsonify

from request_models import GeneratePptRequest
from response_models import GeneratePptResponse


def create_generation_blueprint():
    generation_bp = Blueprint('generation', __name__)

    @generation_bp.route("/api/generate", methods=['POST'])
    def generate_ppt():
        try:
            body = request.get_json()
            
            if body is None:
                response = GeneratePptResponse(
                    success=False,
                    message = "Request body is missing or not in JSON format"
                )
                return jsonify(response.__dict__), 400

            if "org_id" not in body or not body["org_id"]:
                response = GeneratePptResponse(
                success = False,
                message = "org_id is required and cannot be empty"
                )
                return jsonify(response.__dict__), 400


            generate_request = GeneratePptRequest(
                org_id = body["org_id"],
                include_externals = body.get("include_externals", False),
                include_trainees = body.get("include_trainees", False),
                template_name = body.get("template_name", "default"),
                output_name = body.get("output_name")
            )

            generated_file = generation_service.generate(generate_request)

            response = GeneratePptResponse(
                success = True, 
                file_ult = generated_file.file_url,
                message = "PPT generated successfully"
            )

            return jsonify(response.__dict__), 200

        except ValueError as error:
            response = GeneratePptResponse(
                success = False, 
                message = str(error)
            )

            return jsonify(response.__dict__), 400

        except Exception as error:
            response = GeneratePptResponse(
                success = False, 
                message = "An unexpected error occurred: " + str(error)
            )

            return jsonify(response.__dict__), 500
        
    return generation_bp

