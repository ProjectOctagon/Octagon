
class GenerationService:
    def __init__(self, org_repository, mapping_service, ppt_service):
        self.org_repository = org_repository
        self.mapping_service = mapping_service
        self.ppt_service = ppt_service


    def generate(self, request):
        orgs = self.org_repository.get_org_hierarchy(request.org_id)

        if not orgs:
            raise ValueError(f"No organization found for org_id= {request.org_id}")


        presenation_model = self.mapping_service.build_presentation_model(
            orgs = orgs,
            include_externals = request.include_externals,
            include_trainees = request.include_trainees,
        )


        generated_file = self.ppt_service.generate_presentation(
            model = presenation_model,
            template_name = request.template_name,
            output_name = request.output_name,
        )


        return generated_file
