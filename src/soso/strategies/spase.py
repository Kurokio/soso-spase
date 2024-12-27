"""The SPASE strategy module."""

from lxml import etree
from soso.interface import StrategyInterface
from soso.utilities import (
    delete_null_values,
)
from typing import Union, List, Dict
import re

# pylint: disable=duplicate-code


class SPASE(StrategyInterface):
    """Define the conversion strategy for SPASE (Space Physics Archive Search
    and Extract).

    Attributes:
        file: The path to the metadata file. This should be an XML file in
            SPASE format.
        schema_version: The version of the SPASE schema used in the metadata
            file.
        kwargs: Additional keyword arguments for handling unmappable
            properties. See the Notes section below for details.

    Notes:
        Some properties of this metadata standard don't directly map to SOSO.
        However, these properties can still be included by inputting the
        information as `kwargs`. Keys should match the property name, and
        values should be the desired value. For a deeper understanding of each
        SOSO property, refer to the `SOSO guidelines
        <https://github.com/ESIPFed/science-on-schema.org/blob/master/guides/Dataset.md>`_.

        Below are unmappable properties for this strategy:
            - [includedInDataCatalog]
            - [version]
    """

    def __init__(self, file: str, **kwargs: dict):
        """Initialize the strategy."""
        file = str(file)  # incase file is a Path object
        if not file.endswith(".xml"):  # file should be XML
            raise ValueError(file + " must be an XML file.")
        super().__init__(metadata=etree.parse(file))
        self.file = file
        self.schema_version = get_schema_version(self.metadata)
        self.namespaces = {"spase": "http://www.spase-group.org/data/schema"}
        self.kwargs = kwargs
        self.root = self.metadata.getroot()

    def get_id(self) -> str:
        # Mapping: schema:identifier = spase:ResourceID
        desiredTag = self.root[1].tag.split("}")
        SPASE_Location = ".//spase:" + f"{desiredTag[1]}/spase:ResourceHeader/spase:ResourceID"
        dataset_id = self.metadata.findtext(
            SPASE_Location, namespaces=self.namespaces
        )
        return delete_null_values(dataset_id)

    def get_name(self) -> str:
        # Mapping: schema:description = spase:ResourceHeader/spase:ResourceName
        desiredTag = self.root[1].tag.split("}")
        SPASE_Location = ".//spase:" + f"{desiredTag[1]}/spase:ResourceHeader/spase:ResourceName"
        name = self.metadata.findtext(
            SPASE_Location,
            namespaces=self.namespaces,
        )
        return delete_null_values(name)

    def get_description(self) -> str:
        # Mapping: schema:description = spase:ResourceHeader/spase:Description
        desiredTag = self.root[1].tag.split("}")
        SPASE_Location = ".//spase:" + f"{desiredTag[1]}/spase:ResourceHeader/spase:Description"
        description = self.metadata.findtext(
            SPASE_Location,
            namespaces=self.namespaces,
        )
        return delete_null_values(description)

    def get_url(self) -> str:
        # Mapping: schema:url = spase:ResourceHeader/spase:DOI (or https://hpde.io landing page, if no DOI)
        desiredTag = self.root[1].tag.split("}")
        SPASE_Location = ".//spase:" + f"{desiredTag[1]}/spase:ResourceHeader/spase:DOI"
        url = self.metadata.findtext(
            SPASE_Location,
            namespaces=self.namespaces,
        )
        if delete_null_values(url) is None:
            desiredTag = self.root[1].tag.split("}")
            SPASE_Location = ".//spase:" + f"{desiredTag[1]}/spase:ResourceID"
            url = self.metadata.findtext(
                SPASE_Location, namespaces=self.namespaces
            ).replace("spase://", "https://hpde.io/")
        return delete_null_values(url)

    def get_same_as(self) -> None:
        same_as = None
        return delete_null_values(same_as)

    def get_version(self) -> None:
        version = None
        return delete_null_values(version)

    # commented out partial code that was put on hold due to licenses being added to SPASE soon
    def get_is_accessible_for_free(self) -> bool:
        """schema:description: spase:AccessInformation/AccessRights"""
        is_accessible_for_free = None
        # local vars needed
        #access = ""

        # iterate thru to find AccessInfo
        #for child in self.root[1]:
        #    if access == "Open":
        #        break
        #    if child.tag.endswith("AccessInformation"):
        #        targetChild = child
                # iterate thru to find AccessRights
        #        for child in targetChild:
        #            if child.tag.endswith("AccessRights"):
        #                access = child.text 
        #if access == "Open":
        #    is_accessible_for_free = True
        #else:
        #    is_accessible_for_free = False
        return delete_null_values(is_accessible_for_free)

    def get_keywords(self) -> Union[str, None]:
        # Mapping: schema:keywords = spase:ResourceHeader/spase:Keyword
        keywords = []
        for child in self.root[1].iter(tag=etree.Element):
                if child.tag.endswith("Keyword"):
                    keywords.append(child.text)
        if keywords == []:
            keywords = None
        else:
            keywords = str(keywords).replace("[", "").replace("]", "")
        return delete_null_values(keywords)

    def get_identifier(self) -> Union[tuple, None]:
        # Mapping: schema:identifier = spase:ResourceHeader/spase:DOI (or https://hpde.io landing page, if no DOI)
        # Each item is: {@id: URL, @type: schema:PropertyValue, propertyID: URI for identifier scheme, value: identifier value, url: URL}
        # Uses identifier scheme URI, provided at: https://github.com/ESIPFed/science-on-schema.org/blob/main/guides/Dataset.md#identifier
        url = self.get_url()
        # if SPASE record has a DOI
        if "doi" in url:
            temp = url.split("/")
            value = "doi:" + "/".join(temp[3:])
            identifier = {"@id": f"{url}",
                        "@type" : "PropertyValue",
                        "propertyID": "https://registry.identifiers.org/registry/doi",
                        "value": f"{value}",
                        "url": f"{url}"}
        # if SPASE record only has landing page instead
        else:
            identifier = url
        return identifier

    def get_citation(self) -> Union[str, None]:
        # Mapping: schema:citation = spase:ResourceHeader/spase:PublicationInfo/spase:Authors
        # AND spase:ResourceHeader/spase:PublicationInfo/spase:PublicationDate
        # AND spase:ResourceHeader/spase:PublicationInfo/spase:PublishedBy
        # AND spase:ResourceHeader/spase:PublicationInfo/spase:Title
        # AND spase:ResourceHeader/spase:DOI

        # local vars needed
        authorTemp = ""
        author = []
        pubDate = ""
        pub = ""
        dataset = ""
        i = 0

        authorTemp, authorRole, pubDate, pub, dataset = get_authors(self.metadata)
        authorStr = str(authorTemp)
        authorStr = authorStr.replace("[", "").replace("]","")
        authorStr = authorStr.replace("'","")
        authorStr = authorStr.replace(" and ", " ")
        # if author is not empty
        if authorTemp:
            # if author was pulled from ContactID
            if "Person/" in authorStr:
                # if multiple found, split them and iterate thru one by one
                if len(authorTemp) > 1:
                    for person in authorTemp:
                        path, sep, authorStr = person.partition("Person/")
                        givenName, sep, familyName = authorStr.partition(".")
                        #print(givenName)
                        #print(familyName)
                        #print(authorStr)
                        # if name has initial(s) already
                        if ("." in familyName):
                            initial, sep, familyName = familyName.partition(".")
                            givenName = givenName[0] + ". " + initial + "."
                        else:
                            givenName = givenName[0] + "."
                        # add commas to separate each name until last name in list
                        if (i < (len(authorTemp) - 1)):
                            author += [familyName + ", " + givenName]
                        else:
                            author += ["& " + familyName + ", " + givenName]
                        i += 1
                    # reformat author string
                    author = str(author).replace("[", "").replace("]","")
                    author = author.replace("'","")
                # if only one Contact found
                else:
                    path, sep, authorTemp = authorStr.partition("Person/")
                    #print(authorTemp)
                    givenName, sep, familyName = authorTemp.partition(".")
                    # if name has initial(s) already
                    if ("." in familyName):
                        initial, sep, familyName = familyName.partition(".")
                        givenName = givenName[0] + ". " + initial + "."
                    else:
                        givenName = givenName[0] + "."
                    author = familyName + ", " + givenName
            # case when in PubInfo but only one author
            elif ";" not in authorStr:
                # in case there are multiple w/o ;
                if "., " in authorStr:
                    authorStr = authorStr.replace(".,", "..,")
                    authorTemp = authorStr.split("., ")
                    if "and " in authorTemp[-1]:
                        authorTemp[-1].replace("and ", "& ")
                    else:
                        authorTemp[-1] = "& " + authorTemp[-1]
                    author = str(authorTemp).replace("[", "").replace("]","")
                    author = author.replace("'","")
                else:
                    familyName, sep, givenName = authorStr.partition(", ")
                    # if name has initial(s) already
                    if ("," in givenName):
                        givenName, sep, initial = givenName.partition(", ")
                        givenName = givenName[0] + ". " + initial
                    else:
                        givenName = givenName[0] + "."
                    author = familyName + ", " + givenName
            # handle case when multiple authors pulled from PubInfo
            else:
                authorTemp = authorStr.split("; ")
                #print(authorTemp)
                authorStr = ""
                for each in authorTemp:
                    eachTemp = str(each).replace("[", "").replace("]","")
                    #print(eachTemp)
                    if (", " in eachTemp) or ("." in eachTemp):
                        if ", " in eachTemp:
                            familyName, sep, givenName = eachTemp.partition(", ")
                        else:
                            givenName, sep, familyName = eachTemp.partition(".")
                    #print(familyName)
                    #print(givenName)
                    # if name has initial(s) already
                    if ("." in familyName):
                        initial, sep, familyName = familyName.partition(".")
                        givenName = givenName[0] + ". " + initial + "."                    
                    elif ("," in givenName):
                        givenName, sep, initial = givenName.partition(", ")
                        givenName = givenName[0] + ". " + initial
                    else:
                        givenName = givenName[0] + "."
                    if authorTemp.index(each) == (len(authorTemp)-1):
                        familyName = "& " + familyName
                    else:
                        givenName += ", "
                    authorStr += familyName + ", " + givenName
                author = authorStr
        # no author was found
        else:
            author = ""
        # assign backup values if not found in desired locations
        if pub == '':
            # TODO: ask if this process should be used to find backup pub
            #for child in self.root[1].iter(tag=etree.Element):
                #if child.tag.endswith("AccessInformation"):
                    #targetChild = child
                    # iterate thru children to locate RepositoryID
                    #for child in targetChild:
                        #if child.tag.endswith("RepositoryID"):
                            # use partition to split text by Repository/
                            #    and assign only the text after it to pub
                            #(before, sep, after) = child.text.partition("Repo" +
                                                                        #"sitory/")
                            #pub = after
            if pub == '':
                pub = "NASA Heliophysics Digital Resource Library"
        if pubDate == "":
            # iterate thru to find ResourceHeader
            for child in self.root[1].iter(tag=etree.Element):
                if child.tag.endswith("ResourceHeader"):
                    targetChild = child
                    # iterate thru to find ReleaseDate (temp pubYr)
                    for child in targetChild:
                        if child.tag.endswith("ReleaseDate"):
                            pubDate = child.text[:4]
        DOI = self.get_url()
        if dataset:
            citation = f"{author} ({pubDate}). {dataset}. {pub}. {DOI}"
        else:
            citation = f"{author} ({pubDate}). {pub}. {DOI}"
        return delete_null_values(citation)

    def get_variable_measured(self) -> Union[List[Dict], None]:
        # Mapping: schema:variable_measured = /spase:Parameters/spase:Name, Description, Units, ValidMin, ValidMax
        # Each object is:
        #   {"@type": schema:PropertyValue, "name": Name, "description": Description, "unitText": Units,
        #       "minValue": ValidMin, "maxValue": ValidMax}
        # Following schema:PropertyValue found at: https://github.com/ESIPFed/science-on-schema.org/blob/main/guides/Dataset.md#variables
        variable_measured = []
        for child in self.root[1].iter(tag=etree.Element):
            if child.tag.endswith("Parameter"):
                targetChild = child
                for child in targetChild:
                    if child.tag.endswith("Name"):
                        paramName = child.text
                    elif child.tag.endswith("Description"):
                        paramDesc = child.text
                    elif child.tag.endswith("Units"):
                        unit = child.text
                    elif child.tag.endswith("ValidMin"):
                        minVal = child.text
                    elif child.tag.endswith("ValidMax"):
                        maxVal = child.text
                variable_measured.append({"@type": "PropertyValue", 
                                        "name": f"{paramName}",
                                        "description": f"{paramDesc}",
                                        "unitText": f"{unit}",
                                        "minValue": f"{minVal}",
                                        "maxValue": f"{maxVal}"})
        return delete_null_values(variable_measured)

    def get_included_in_data_catalog(self) -> None:
        included_in_data_catalog = None
        return delete_null_values(included_in_data_catalog)

    def get_subject_of(self) -> None:
        encoding_format = None
        return delete_null_values(encoding_format)

    def get_distribution(self) -> Union[List[Dict], None]:
        # Mapping: schema:distribution = /spase:AccessInformation/spase:AccessURL/spase:URL
        # AND /spase:AccessInformation/spase:Format
        # Each object is:
        #   {"@type": schema:DataDownload, "contentURL": URL, "encodingFormat": Format}
        # Following schema:DataDownload found at: https://github.com/ESIPFed/science-on-schema.org/blob/main/guides/Dataset.md#accessing-data-through-a-service-endpoint
        distribution = []
        dataDownloads, potentialActions = get_accessURLs(self)
        for k, v in dataDownloads.items():
            distribution.append({"@type": "DataDownload",
                                "contentUrl": f"{k}",
                                "encodingFormat": f"{v}"})
        for k, v in potentialActions.items():
            v = str(v).replace("[", "").replace("]", "")
            encoder, sep, prodKeys = v.partition(",")
            distribution.append({"@type": "DataDownload",
                                "contentUrl": f"{k}",
                                "encodingFormat": f"{encoder}"})
        return delete_null_values(distribution)

    def get_potential_action(self) -> Union[List[Dict], None]:
        potential_action = {}
        dataDownloads, potentialActions = get_accessURLs(self)
        for k, v in dataDownloads.items():
            # Unfinished, have to figure out what to put here
            potential_action.append({"@type": "SearchAction",
                                "target": {"@type": "EntryPoint",
                                            "contentType": "",
                                            "urlTemplate": "",
                                            "description": "",
                                            "httpMethod": ""}
                                })
        return delete_null_values(potential_action)

    def get_date_created(self) -> None:
        date_created = None
        return delete_null_values(date_created)

    def get_date_modified(self) -> None:
        date_modified = None
        return delete_null_values(date_modified)

    def get_date_published(self) -> None:
        date_published = None
        return delete_null_values(date_published)

    def get_expires(self) -> None:
        expires = None
        return delete_null_values(expires)

    def get_temporal_coverage(self) -> Union[Dict, None]:
        # Mapping: schema:temporal_coverage = spase:TemporalDescription/spase:TimeSpan/*
        # Each object is:
        #   {"@context": schema.org, "@type": schema:Dataset, name: ResourceName, temporalCoverage: StartDate and StopDate|RelativeStopDate}
        # Using format as defined in: https://github.com/ESIPFed/science-on-schema.org/blob/main/guides/Dataset.md#temporal-coverage
        ResourceName = self.get_name()
        desiredTag = self.root[1].tag.split("}")
        SPASE_Location = ".//spase:" + f"{desiredTag[1]}/spase:TemporalDescription/spase:TimeSpan/spase:StartDate"
        start = self.metadata.findtext(
            SPASE_Location,
            namespaces=self.namespaces,
        )
        temporal_coverage = {"@context": "https://schema.org/",
                            "@type": "schema:Dataset",
                            "name": f"{ResourceName}",
                            "temporalCoverage": f"{start}"}
        return delete_null_values(temporal_coverage)

    def get_spatial_coverage(self) -> Union[List[Dict], None]:
        # Mapping: schema:spatial_coverage = list of spase:NumericalData/spase:ObservedRegion/*
        # Each object is:
        #   {"@type": schema:Place, "@id": URI}
        # Using URIs, as defined in: https://github.com/polyneme/topst-spase-rdf-tools/blob/main/data/spase.owl
        spatial_coverage = []
        desiredTag = self.root[1].tag.split("}")
        SPASE_Location = ".//spase:" + f"{desiredTag[1]}/spase:ObservedRegion"
        for item in self.metadata.findall(
            SPASE_Location,
            namespaces=self.namespaces,
        ):
            spatial_coverage.append(
                {
                    "@type": "schema:Place",
                    "identifier": f"http://www.spase-group.org/data/schema/{item.text.replace('.', '_').upper()}",
                    "alternateName": item.text,
                }
            )
        return delete_null_values(spatial_coverage)

    def get_creator(self) -> Union[List, None]:
        # Mapping: schema:creator = spase:ResourceHeader/spase:PublicationInfo/spase:Authors 
        # OR schema:creator = spase:ResourceHeader/spase:Contact/spase:PersonID
        # Each item is:
        #   {@type: Role, roleName: Contact Role, creator: {@type: Person, name: Author Name, givenName: First Name, familyName: Last Name}}
        # Using schema:Creator as defined in: https://github.com/ESIPFed/science-on-schema.org/blob/main/guides/Dataset.md#roles-of-people
        author, authorRole, pubDate, pub, dataset = get_authors(self.metadata)
        authorStr = str(author).replace("[", "").replace("]","")
        creator = []
        multiple = False
        # if creators were found in Contact/PersonID
        if "Person/" in authorStr:
            # if multiple found, split them and iterate thru one by one
            if "'," in authorStr:
                multiple = True
            for person in author:
                if multiple:
                    # keep track of position so roles will match
                    index = author.index(person)
                else:
                    index = 0
                path, sep, authorStr = person.partition("Person/")
                # get rid of extra quotations
                authorStr = authorStr.replace("'","")
                givenName, sep, familyName = authorStr.partition(".")
                # if name has initial(s)
                if ("." in familyName):
                    initial, sep, familyName = familyName.partition(".")
                    givenName = givenName + ' ' + initial + '.'
                authorStr = givenName + " " + familyName
                authorStr = authorStr.replace("\"", "")
                creator.append({"@type": "Role", 
                                "roleName": f"{authorRole[index]}",
                                "creator": {"@type": "Person",
                                            "name": f"{authorStr}",
                                            "givenName": f"{givenName}",
                                            "familyName": f"{familyName}"}
                                            })
        # if all creators were found in PublicationInfo/Authors
        else:
            # if there are multiple authors
            if (";" in authorStr) or (".," in authorStr):
                if (";" in authorStr):
                    author = authorStr.split("; ")
                else:
                    author = authorStr.split("., ")
                # iterate over each person in author string
                for person in author:
                    # get rid of extra quotations
                    person = person.replace("'","")
                    # if first name is abbreviated
                    if (not person.endswith(".")):
                        # if initial doesnt have a period, add one
                        if (re.search(r"[A-Z][.][A-Z]", person) is not None):
                            #print(re.search(r"[A-Z][.][A-Z]", person))
                            person += "."
                    # remove 'and' from name
                    if "and " in person:
                        person = person.replace("and ", "")
                    if authorRole == ["Author"]:
                        familyName, sep, givenName = person.partition(", ")
                        creator.append({"@type": "Role", 
                                        "roleName": f"{authorRole[0]}",
                                        "creator": {"@type": "Person",
                                                    "name": f"{person}",
                                                    "givenName": f"{givenName}",
                                                    "familyName": f"{familyName}"}
                                                    })
            # if there is only one author listed
            else:
                # get rid of extra quotations
                person = authorStr.replace("'","")
                if authorRole == ["Author"]:
                    familyName, sep, givenName = person.partition(",")
                    creator.append({"@type": "Role", 
                                    "roleName": f"{authorRole[0]}",
                                    "creator": {"@type": "Person",
                                                "name": f"{person}",
                                                "givenName": f"{givenName}",
                                                "familyName": f"{familyName}"}
                                                })
        return delete_null_values(creator)

    def get_contributor(self) -> None:
        contributor = None
        return delete_null_values(contributor)

    def get_provider(self) -> None:
        provider = None
        return delete_null_values(provider)

    def get_publisher(self) -> None:
        publisher = None
        return delete_null_values(publisher)

    def get_funding(self) -> None:
        funding = None
        return delete_null_values(funding)

    def get_license(self) -> None:
        license_url = None
        return license_url

    def get_was_revision_of(self) -> None:
        was_revision_of = None
        return delete_null_values(was_revision_of)

    def get_was_derived_from(self) -> None:
        was_derived_from = None
        return delete_null_values(was_derived_from)

    def get_is_based_on(self) -> None:
        is_based_on = None
        return delete_null_values(is_based_on)

    def get_was_generated_by(self) -> None:
        was_generated_by = None
        return delete_null_values(was_generated_by)


# Below are utility functions for the SPASE strategy.


def get_schema_version(metadata: etree.ElementTree) -> str:
    """
    :param metadata:    The SPASE metadata object as an XML tree.

    :returns:   The version of the SPASE schema used in the metadata record.
    """
    schema_version = metadata.findtext(
        "{http://www.spase-group.org/data/schema}Version"
    )
    return schema_version

def get_authors(metadata: etree.ElementTree) -> tuple:
    """
    :param metadata:    The SPASE metadata object as an XML tree.
    
    :returns: The highest priority authors found within the SPASE record as a list
                as well as a list of their roles, the publication date, publisher,
                and the title of the publication.
    """
    # local vars needed
    author = []
    authorRole = []
    pubDate = ""
    pub = ""
    dataset = ""
    PI_child = None
    priority = False
    root = metadata.getroot()
    # holds role values that are not considered for author var
    UnapprovedAuthors = ["MetadataContact", "ArchiveSpecialist",
                        "HostContact", "Publisher", "User"]

    # iterate thru to find ResourceHeader
    for child in root[1].iter(tag=etree.Element):
        if child.tag.endswith("ResourceHeader"):
            targetChild = child
            # iterate thru to find PublicationInfo
            for child in targetChild:
                if child.tag.endswith("PublicationInfo"):
                    PI_child = child
                elif child.tag.endswith("Contact"):
                    C_Child = child
                    # iterate thru Contact to find PersonID and Role
                    for child in C_Child:
                        # find PersonID
                        if child.tag.endswith("PersonID"):
                            # store PersonID
                            PersonID = child.text
                        # find Role
                        elif child.tag.endswith("Role"):
                            # backup author
                            if ("PrincipalInvestigator" or "PI") in child.text:
                                # if a lesser priority author found
                                #     first, overwrite author lists
                                if not priority and author:
                                    author = [PersonID]
                                    authorRole = [child.text]
                                else:
                                    author.append(PersonID)
                                    authorRole.append(child.text)
                                # mark that highest priority backup author was found
                                priority = True
                            # backup publisher
                            elif child.text == "Publisher":
                                pub = child.text
    if PI_child is not None:
        for child in PI_child:
            # collect preferred author
            if child.tag.endswith("Authors"):
                author = [child.text]
                authorRole = ["Author"]
            elif child.tag.endswith("PublicationDate"):
                pubDate = child.text
                pubDate = pubDate[:4]
            # collect preferred publisher
            elif child.tag.endswith("PublishedBy"):
                pub = child.text
            # collect preferred dataset
            elif child.tag.endswith("Title"):
                dataset = child.text
    return author, authorRole, pubDate, pub, dataset

def getPaths(entry, paths) -> list:
    """Takes the absolute path of a SPASE record directory to be walked
    to extract all SPASE records present. Returns these paths using the
    list parameter paths, which holds the absolute paths generated by
    the function.

    :param entry: A string of the absolute path of the SPASE record directory
                    to be searched/walked to find all SPASE records within.
    :type entry: String
    :param paths: A list to hold absolute paths of all SPASE records found
                    within the given directory
    :type paths: list
    :return: A list containing the absolute paths of all SPASE records found
                within the given directory.
    :rtype: list
    """
    import os
    if os.path.exists(entry):
        for root, dirs, files in os.walk(entry):
            if files:
                for file in files:
                    paths.append(root + "/" + file)
    else:
        print(entry + " does not exist")
    return paths

def get_accessURLs(metadata: etree.ElementTree) -> tuple:
    """
    :param metadata:    The SPASE metadata object as an XML tree.
    
    :returns: The AccessURLs found in the SPASE record, separated into two dictionaries,
                dataDownloads and potentialActions, depending on if they have a product key
                associated with them or not.
    """
    dataDownloads = {}
    potentialActions = {}
    AccessURLs = {}
    root = metadata.getroot()
    # iterate thru children to locate Access Information
    for child in root[1].iter(tag=etree.Element):
        if child.tag.endswith("AccessInformation"):
            targetChild = child
            # iterate thru children to locate AccessURL and Format
            for child in targetChild:
                if child.tag.endswith("Format"):
                    encoder = child.text
                elif child.tag.endswith("AccessURL"):
                    targetChild = child
                    # iterate thru children to locate URL
                    for child in targetChild:
                        if child.tag.endswith("URL"):
                            url = child.text
                            # provide "NULL" value in case no keys are found
                            AccessURLs[url] = []
                        # check if URL has a product key
                        elif child.tag.endswith("ProductKey"):
                            prodKey = child.text
                            # if only one prodKey exists
                            if AccessURLs[url] == []:
                                AccessURLs[url] = [prodKey]
                            # if multiple prodKeys exist
                            else:
                                AccessURLs[url] += [prodKey]
                    # continue to check for additional AccessURLs
                    continue
            # continue to check for additional Access Informations
            continue
    for k, v in AccessURLs.items():
        # if URL has no prodKeys at all, add to the dataDownloads dictionary
        if not v:
            dataDownloads[k] = encoder
        # if URL has prodKeys, add to the potentialActions dictionary
        else:
            potentialActions[k] = [encoder, v]
    return dataDownloads, potentialActions

#TODO: add docstring
def main(folder, parameterDesired = False, printFlag = True) -> None:
    # list that holds SPASE records already checked
    searched = []

    SPASE_paths = []
    noCreators = []

    # obtains all filepaths to all SPASE records found in given directory
    SPASE_paths = getPaths(folder, SPASE_paths)
    print("You entered " + folder)
    if len(SPASE_paths) == 0:
        print("No records found. Returning.")
    else:
        print("The number of records is " + str(len(SPASE_paths)))
        # iterate through all SPASE records
        # Note: starting at record 24 in ACE/EPAM folder, end of author string is formatted wrong with "and first last" instead of "and last, first" (SPASE issue)
        # Successfully passed for all 129 records in NumericalData/ACE/EPAM folder and all 187 in DisplayData
        # In DisplayData, records 130, 167-70 has authors formatted wrong
        # DisplayData: record 70 is ex w multiple contacts, ACE has ex's w multiple authors
        for r, record in enumerate(SPASE_paths):
            if record not in searched:
                # scrape metadata for each record
                statusMessage = f"Extracting metadata from record {r+1}"
                statusMessage += f" of {len(SPASE_paths)}"
                print(statusMessage)
                print(record)
                testSpase = SPASE(record)

                #print(testSpase.get_is_accessible_for_free())
                keywords = testSpase.get_keywords()
                citation = testSpase.get_citation()
                identifier = testSpase.get_identifier()
                creator = testSpase.get_creator()
                variable_measured = testSpase.get_variable_measured()

                if printFlag:
                    if keywords is None:
                        print("No keywords found")
                    else:
                        print(keywords)
                    print(citation)
                    print(identifier)
                    if creator is not None:
                        for each in creator:
                            print(each)
                    else:
                        print("No creators were found according to the priority rules")
                        # TODO: once testing is done add export for records who lack desired creators
                        # append ResourceID and ResourceHeader of the record for exporting to spreadsheet
                        #noCreators.append()
                if parameterDesired:
                    if variable_measured is not None:
                        for variable in variable_measured:
                            print(variable)
                print("Metadata extraction completed")
                print()

                # add record to searched
                searched.append(record)

# test directories
#folder = "C:/Users/zboqu/NASA Internship/NASA/DisplayData"
#folder = "C:/Users/zboqu/NASA Internship/NASA/NumericalData/ACE/EPAM"
#folder = "C:/Users/zboqu/NASA Internship/NASA/NumericalData/Cassini/MAG"
folder = "C:/Users/zboqu/NASA Internship/NASA/NumericalData/MMS/4/HotPlasmaCompositionAnalyzer/Burst/Level2/Ion"
main(folder)