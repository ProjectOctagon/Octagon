from mongoengine import Document, StringField, ListField, BooleanField, IntField, ReferenceField

class Person(Document):
    meta = {'collection': 'people'}
    PERSONNEL_NUMBER = StringField(required=True, unique=True)
    NSN_ID = StringField()
    Name = StringField()
    FirstName = StringField()
    LastName = StringField()
    Email = StringField()
    Country = StringField()
    City = StringField()
    JOB_TITLE = StringField()
    HEADCOUNT_STATUS = StringField()
    STATUS = StringField()
    LineManager = StringField()  
    TeamCode = StringField()

class Organization(Document):
    meta = {'collection': 'organizations'}
    org_id = StringField(required=True, unique=True)
    name = StringField()
    parent = ReferenceField('Organization')
    ancestors = ListField(ReferenceField('Organization'))
    children = ListField(ReferenceField('Organization'))
    people = ListField(ReferenceField('Person'))  
    isDeleted = BooleanField(default=False)
    sap_org_id = StringField()
