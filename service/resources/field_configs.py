""" Custom field configurations from form.io """
# pylint: disable=too-few-public-methods
class FieldConfigs():
    """ Takes field configs from environment var as JSON. Could also pass in from POST, if do_post is implemented
        Determines which fields need custom formatting.
     """

    # will move this to client side in the POST body when we implement do_post()
    map_field_configs = {'building_use': {'existingBuildingPresentUseOther', 'proposedUseOther', 'newBuildingUseOther'}, \
        'construction_type': {'existingBuildingConstructionType', 'typeOfConstruction', 'newTypeOfConstruction'}, \
        'occupancy_code': {'existingBuildingOccupancyClass', 'newOccupancyClass', 'occupancyClass'}, 'street_suffix_fields': {'projectAddressStreetType'}, \
        'state_fields': {'Page2State', 'ownerState', 'constructionLenderState', 'existingBuildingState', 'constructionLenderState1'}}

    pretty_field_configs = {
        'phone_fields': {'applicantPhoneNumber', 'ownerPhoneNumber'}
    }

    # new construction fields, map them to proposed
    new_proposed_fields = ["newProjectDescription", "newTypeOfConstruction", "newOccupancyClass", "newDwellingUnits", "newOccupancyStories", "newBasements"]

    # addresses that have nested structure
    address_fields = ["ownerAddress", "applicantAddress"]

    missing_fields = ["ownerName", "contractorName", "engineerName", "architectName", "agentName", "attorneyName"]

    # fields that need to be convert to Yes/No instead of True/False
    convert_bool_fields = ["onlyFireDepartmentReview"]

    # fields that need to be relabel
    relabel_fields = {
        "occupancyClass": "proposedOccupancyClass",
        "typeOfConstruction": "proposedTypeOfConstruction"
    }

    pts_fields = ["id", "created", "permitType", "reviewOverTheCounter", "onlyFireDepartmentReview", "applicantType", "applicantFirstName", "buildingPermitApplicationNumber",
                  "applicantLastName", "applicantPhoneNumber", "applicantEmail", "applicantAddress1", "applicantAddress2", "applicantCity", "applicantState",
                  "applicantZipCode", "applicantContractorLicenseNumber", "applicantBTRC", "applicantArchitectLicenseNumber", "applicantEngineerLicenseNumber",
                  "ownerName", "ownerPhoneNumber", "ownerEmail", "ownerAddress1", "ownerAddress2", "ownerCity", "ownerState", "ownerZipCode",
                  "contractorOrganizationName", "contractorName", "contractorEmail", "contractorLicenseNumber",
                  "contractorBTRC", "existingBuildingConstructionType", "existingBuildingDwellingUnits", "existingBuildingOccupancyStories",
                  "existingBuildingBasementsAndCellars", "existingBuildingPresentUseOther", "existingBuildingOccupancyClass",
                  "sitePermitForm38", "sitePermitForm12", "estimatedCostOfProject", "projectDescription", "typeOfConstruction",
                  "proposedDwellingUnits", "proposedOccupancyStories", "proposedBasementsAndCellars", "proposedBasementsAndCellars", "proposedUseOther", "occupancyClass"
                  "electricalWork", "plumbingWork", "deckOrHorizontalExtension", "affordableHousing", "accessoryDwellingUnit", "bluebeamId", "noPlansPermit",
                  "projectAddressNumber", "projectAddressNumberSuffix", "projectAddressStreetName", "projectAddressUnitNumber", "projectAddressStreetType",
                  "projectAddressBlock", "projectAddressLot",
                  "engineerOrganizationName", "engineerName", "engineerEmail", "engineerLicenseNumber",
                  "architectOrganizationName", "architectName", "architectEmail", "architectLicenseNumber",
                  "agentOrganizationName", "agentName", "agentEmail",
                  "attorneyOrganizationName", "attorneyName", "attorneyEmail", "notes", "workersCompSelectboxes", "carrier", "policyNumber"]

    ordered_fields = ["id", "created", "permitType", "reviewOverTheCounter", "onlyFireDepartmentReview", "applicantType", "applicantFirstName",
                      "applicantLastName", "applicantPhoneNumber", "applicantEmail", "applicantCompanyName", "applicantAddress1", "applicantAddress2", "applicantStreetSuffix",
                      "applicantCity", "applicantState", "applicantZipCode", "applicantContractorLicenseNumber", "applicantBTRC",
                      "ownerFirstName", "ownerLastName", "ownerPhoneNumber", "ownerAddress1", "ownerAddress2", "ownerCity", "ownerState", "ownerZipCode",
                      "contractorOrganizationName", "contractorFirstName", "contractorLastName", "contractorEmail", "contractorLicenseNumber",
                      "contractorBTRC", "existingBuildingConstructionType", "existingBuildingDwellingUnits", "existingBuildingOccupancyStories",
                      "existingBuildingBasementsAndCellars",
                      "existingBuildingPresentUseOther", "existingBuildingOccupancyClass", "existingFireRating", "sitePermit", "estimatedCostOfProject",
                      "projectDescription", "proposedTypeOfConstruction", "proposedDwellingUnits", "proposedOccupancyStories", "proposedBasementsAndCellars",
                      "proposedBasementsAndCellars", "proposedUseOther", "proposedFireRating", "proposedOccupancyClass",
                      "electricalWork", "plumbingWork", "deckOrHorizontalExtension", "affordableHousing", "accessoryDwellingUnit", "accessoryDwellingUnit2", "bluebeamId", "noPlansPermit",
                      "projectAddressNumber", "projectAddressNumberSuffix", "projectAddressStreetName", "projectAddressStreetType", "projectAddressUnitNumber",
                      "projectAddressBlock", "projectAddressLot",
                      "engineerOrganizationName", "engineerFirstName", "engineerLastName", "engineerEmail", "engineerLicenseNumber", "engineerPhoneNumber", "engineerAddress1",
                      "engineerAddress2", "engineerCity", "engineerState", "engineerZipCode",
                      "architectOrganizationName", "architectFirstName", "architectLastName", "architectEmail", "architectLicenseNumber", "architectPhoneNumber", "architectAddress1",
                      "architectAddress2", "architectCity", "architectState", "architectZipCode",
                      "agentOrganizationName", "agentFirstName", "agentLastName", "agentEmail", "agentPhoneNumber", "agenttAddress1",
                      "agentAddress2", "agentCity", "agentState", "agentZipCode",
                      "attorneyOrganizationName", "attorneyFirstName", "attorneyLastName", "attorneyEmail", "attorneyPhoneNumber", "attorneyAddress1",
                      "attorneyAddress2", "attorneyCity", "attorneyState", "attorneyZipCode", "notes", "workersCompSelectboxes", "carrier", "policyNumber"]

    @staticmethod
    def get_field_key(value, field_type):
        """ get the key from field_config based on value """
        if field_type == 'map':
            field_configs = FieldConfigs.map_field_configs
        else:
            field_configs = FieldConfigs.pretty_field_configs

        # loop through the Field Config variables to find the key, so value ="buildingPermitApplicationNumber" returns "appnum_fields"
        for field_key, field_value in field_configs.items():
            if value in field_value:
                return field_key
        return None

    @staticmethod
    def is_nested_address_field(field):
        """ check address field is nested """
        return field and field in FieldConfigs.address_fields

    @staticmethod
    def is_missing_field(field):
        """ check which MIS fields are missing """
        return field and field in FieldConfigs.missing_fields

    @staticmethod
    def is_pts_fields(field):
        """ check pts specific fields to be included in the csv export, according to
            https://docs.google.com/spreadsheets/d/1CkGnw8aYxzPwp_CzEGwsmDhqJOATIB3EGp2gsVJtmjc/edit#gid=937406231
        """
        return field and field in FieldConfigs.pts_fields

    @staticmethod
    def is_building_use(field):
        """ check if field is one of building_use field """
        return field and field in FieldConfigs.map_field_configs['building_use']

    @staticmethod
    def get_relabel_fields(field):
        """ relabel field to MIS specified header """
        for field_key, field_value in FieldConfigs.relabel_fields.items():
            if field == field_key:
                return field_value
        return None
