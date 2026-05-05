from models import Person, Organization

class DataAccessLayer:
    @staticmethod
    def get_org_by_id(org_id):
        return Organization.objects(org_id=org_id, isDeleted=False).first()

    @staticmethod
    def get_sub_organizations(parent_id):
        return list(Organization.objects(parent=parent_id, isDeleted=False))

    @staticmethod
    def get_people_by_ids(personnel_numbers):
        if not personnel_numbers:
            return []
        return list(Person.objects(PERSONNEL_NUMBER__in=personnel_numbers))

    @staticmethod
    def get_org_with_hierarchy(org_id):
        root_org = Organization.objects(org_id=org_id, isDeleted=False).first()
        if not root_org:
            return []
        descendants = Organization.objects(ancestors=org_id, isDeleted=False)
        return [root_org] + list(descendants)
