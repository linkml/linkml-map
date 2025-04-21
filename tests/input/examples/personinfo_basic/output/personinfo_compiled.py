
NULL = None





def derive_Container(
        source_object: src.Container
    ) -> tgt.Container:
    # assign slots
    persons = source_object.persons
    organizations = source_object.organizations

    return tgt.Container(
        agents=[ derive_Agent(x) for x in source_object.persons ],
    )



def derive_Agent(
        source_object: src.Person
    ) -> tgt.Agent:
    # assign slots
    primary_email = source_object.primary_email
    secondary_email = source_object.secondary_email
    birth_date = source_object.birth_date
    age_in_years = source_object.age_in_years
    gender = source_object.gender
    current_address = source_object.current_address
    has_employment_history = source_object.has_employment_history
    has_familial_relationships = source_object.has_familial_relationships
    has_medical_history = source_object.has_medical_history
    has_important_life_events = source_object.has_important_life_events
    aliases = source_object.aliases
    id = source_object.id
    name = source_object.name
    description = source_object.description
    image = source_object.image

    def gen_driving_since(src):
        target = None
        d_test = [x.important_event_date for x in src.has_important_life_events if str(x.event_name) == "PASSED_DRIVING_TEST"]
        if len(d_test):
            target = d_test[0]
        return target


    def gen_first_known_event(src):
        target = None
        if src.has_important_life_events:
          target = src.has_important_life_events[0].important_event_date
        return target


    def gen_death_date(src):
        target = None
        death_dates = [x.important_event_date for x in src.has_important_life_events if str(x.event_name) == "DEATH"]
        if len(death_dates):
          target = death_dates[0]
        return target


    return tgt.Agent(
        id=source_object.id,
        label=source_object.name,
        age=str(age_in_years) + ' years',
        primary_email=source_object.primary_email,
        secondary_email=NULL,
        gender=None,
        driving_since=gen_driving_since(source_object),
        first_known_event=gen_first_known_event(source_object),
        death_date=gen_death_date(source_object),
        current_address=source_object.current_address,
        has_familial_relationships=[ derive_FamilialRelationship(x) for x in source_object.has_familial_relationships ],
    )



def derive_Address(
        source_object: src.Address
    ) -> tgt.Address:
    # assign slots
    street = source_object.street
    city = source_object.city
    postal_code = source_object.postal_code

    return tgt.Address(
        address_of='foo',
        street=source_object.street,
        city=source_object.city,
    )



def derive_FamilialRelationship(
        source_object: src.FamilialRelationship
    ) -> tgt.FamilialRelationship:
    # assign slots
    type = source_object.type
    started_at_time = source_object.started_at_time
    ended_at_time = source_object.ended_at_time
    related_to = source_object.related_to

    return tgt.FamilialRelationship(
        type=source_object.type,
        related_to=source_object.related_to,
    )