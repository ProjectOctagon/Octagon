from typing import List, Optional, Dict


class BusinessLogicService:
    def __init__(self, include_externals: bool = False, include_trainees: bool = False):
        """
        Initializare
        """
        self.include_externals = include_externals
        self.include_trainees = include_trainees

    def process_data(self, raw_orgs: List) -> List[Dict]:
       
        processed_results = []

        # 1. Filtrare Organizatii: isDeleted
        active_orgs = [o for o in raw_orgs if not getattr(o, 'isDeleted', False)]

        for org in active_orgs:
            # Pregatim structura de baza a unitatii
            unit_data = {
                "org_id": org.org_id,
                "name": org.name,
                "is_virtual": getattr(org, 'isVirtual', False),
                "manager": None,
                "employees": []
            }

            # 2. Procesare Oameni din cadrul organizatiei
            people_list = getattr(org, 'people', [])
            if not people_list:
                people_list = []

            for person in people_list:
                # Verificam daca persoana trece de filtrele de business
                if self._should_include_person(person, org):
                    mapped_person = self._map_person(person, org)

                    # Identificam daca este managerul unitatii (Line Manager)
                    if person.PERSONNEL_NUMBER == org.lm_personnel_number:
                        mapped_person["is_head"] = True
                        unit_data["manager"] = mapped_person
                    else:
                        unit_data["employees"].append(mapped_person)

            processed_results.append(unit_data)

        return processed_results

    def _should_include_person(self, person, org) -> bool:
        """
        Aplica regulile de excludere din OctagonExtractDatabaseFields.pdf
        """
        # Managerul este mereu inclus
        is_manager = person.PERSONNEL_NUMBER == org.lm_personnel_number
        if is_manager:
            return True

        # Filtru Headcount: Status '2' sau 'Not in Headcount' se exclude
        if person.HEADCOUNT_STATUS in ["2", "Not in Headcount"]:
            return False

        # Identificare tip angajat din EMPLOYEE_GROUP_TEXT
        group_text = (person.EMPLOYEE_GROUP_TEXT or "").lower()

        # Filtru Externi (external, etl, contractor)
        is_external = any(x in group_text for x in ["external", "etl", "contractor"])
        if is_external and not self.include_externals:
            return False

        # Filtru Trainees (student, trainee, intern)
        is_trainee = any(x in group_text for x in ["student", "trainee", "intern"])
        if is_trainee and not self.include_trainees:
            return False

        return True

    def _map_person(self, person, org) -> Dict:
        """
        Transforma datele brute in format organizat
        """
        # Formatare nume
        if person.FirstName and person.LastName:
            full_name = f"{person.FirstName} {person.LastName}"
        else:
            full_name = person.Name or "Unknown"

        # Formatare Locatie
        loc_parts = [p for p in [person.City, person.Country] if p]
        location = ", ".join(loc_parts) if loc_parts else "N/A"

        is_acting = False
        if person.PERSONNEL_NUMBER == org.lm_personnel_number:
            is_acting = str(getattr(org, 'isActingLM', 'false')).lower() == "true"

        return {
            "full_name": full_name,
            "job_title": person.JOB_TITLE or "N/A",
            "email": person.Email,
            "location": location,
            "personnel_number": person.PERSONNEL_NUMBER,
            "is_acting": is_acting,
            "is_head": False  # Va fi setat in functia principala
        }
