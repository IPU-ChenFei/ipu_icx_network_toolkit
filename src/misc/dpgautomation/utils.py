from django_python3_ldap.utils import format_search_filters


def custom_format_search_filters(ldap_fields):
    # add divisioncode and groupcode to filter all users from Intel MODEM & PLATFORM SW
    ldap_fields["intelDivisionCode"] = "130237"
    ldap_fields["intelGroupCode"] = "120092"

    # call the base format callable
    search_filters = format_search_filters(ldap_fields)
    return search_filters