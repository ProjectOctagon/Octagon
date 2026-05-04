from models import Person, Organization

class DataAccessLayer:
    @staticmethod
    def get_org_by_id(org_id):
        return Organization.objects(org_id=org_id, isDeleted=False).first()

    @staticmethod
    def get_sub_organizations(parent_id):
        return list(Organization.objects(parent=parent_id, isDeleted=False))

    @staticmethod
    def get_people_in_org(personnel_numbers):
        return list(Person.objects(PERSONNEL_NUMBER__in=personnel_numbers))

    @staticmethod
    def get_org_with_hierarchy(org_id):
        org = Organization.objects(org_id=org_id).first()
        if not org:
            return []
        
        descendants = Organization.objects(ancestors=org_id, isDeleted=False)
        return [org] + list(descendants)
