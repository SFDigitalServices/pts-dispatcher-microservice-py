""" Custom field configurations from form.io """
# pylint: disable=too-few-public-methods
class FieldConfigs():
    """ Takes field configs from environment var as JSON. Could also pass in from POST, if do_post is implemented
        Determines which fields need custom formatting.
     """

    # will move this to client side in the POST body when we implement do_post()
    map_field_configs = {'building_use': {'existingBuildingPresentUse', 'proposedUse', 'newBuildingUse'}, \
        'construction_type': {'existingBuildingConstructionType', 'typeOfConstruction', 'newTypeOfConstruction'}, \
        'occupancy_code': {'existingBuildingOccupancyClass', 'newOccupancyClass', 'occupancyClass'}, 'street_suffix_fields': {'projectAddressStreetType'}, \
        'state_fields': {'Page2State', 'ownerState', 'constructionLenderState', 'existingBuildingState', 'constructionLenderState1'}}

    pretty_field_configs = {
        'phone_fields': {'applicantPhoneNumber', 'ownerPhoneNumber'},
        'appnum_fields': {'buildingPermitApplicationNumber'},
    }

    pts_fields = ["applicantType", "_id", "applicantFirstName", "applicantLastName", "applicantLastName", "applicantPhoneNumber",
        "applicantEmail", "applicantAddress1", "applicantAddress2", "applicantCity", "Page2State", "applicantZipCode", "applicantContractorLicenseNumber",
        "applicantBTRC", "ownerName", "ownerPhoneNumber", "ownerEmail", "ownerAddress1", "ownerAddress2", "ownerCity", "ownerState", "ownerZipCode",
        "agentOrganizationName", "agentEmail", "architectOrganizationName", "architectName", "architectEmail", "architectLicenseNumber", "architectLicenseExpirationDate",
        "attorneyOrganizationName", "attorneyName", "attorneyEmail", "contractorOrganizationName", "contractorName", "contractorEmail", "contractorLicenseNumber",
        "contractorBTRC", "engineerOrganizationName", "engineerName", "engineerEmail", "engineerLicenseNumber", "alterOrConstructDriveway", "useStreetSpace",
        "electricalWork", "plumbingWork", "additionalHeightOrStory", "newCenterLineFrontHeight", "deckOrHorizontalExtension", "changeOfOccupancy", "bluebeamId", 
        "notes", "Project Address Number", "Project Address Number Suffix", "Project Address St Type", "Project Address Unit Number", "Project Address Block",
        "Project Address Lot", "Project Address Zip"]

    form_38_fields = ["existingBuildingDwellingUnits", "existingBuildingDwellingUnits", "existingBuildingOccupancyStories", "existingBuildingBasementsAndCellars",
        "existingBuildingPresentUse", "existingBuildingOccupancyClass", "sitePermitForm38", "estimatedCostOfProject", "projectDescription", "typeOfConstruction",
        "proposedDwellingUnits", "proposedOccupancyStories", "proposedBasementsAndCellars", "proposedBasementsAndCellars", "proposedUse", "occupancyClass"]
    form_12_fields = ["newEstimatedCostOfProject", "newProjectDescription", "newTypeOfConstruction", "newBuildingUse", "newOccupancyClass", "newGroundFloorArea",
        "newBuildingFrontHeight", "newDwellingUnits", "newOccupancyStories", "newBasements", ""]

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
