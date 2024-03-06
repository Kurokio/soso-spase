"""Configure the test suite."""
import socket
from urllib.parse import urlparse
import pytest
from soso.strategies.eml import EML
from soso.utilities import get_example_metadata_file_path


@pytest.fixture
def strategy_names():
    """Return the names of available strategies."""
    return ["eml"]


@pytest.fixture(params=[EML])
def strategy_instance(request):
    """Return the strategy instances."""
    if request.param is EML:
        res = request.param(file=get_example_metadata_file_path("EML"))
    return res


@pytest.fixture
def soso_properties():
    """Return the names of SOSO properties."""
    return [
        "@context",
        "@type",
        "name",
        "description",
        "url",
        "sameAs",
        "version",
        "isAccessibleForFree",
        "keywords",
        "identifier",
        "citation",
        "variableMeasured",
        "includedInDataCatalog",
        "subjectOf",
        "distribution",
        "potentialAction",
        "dateCreated",
        "dateModified",
        "datePublished",
        "expires",
        "temporalCoverage",
        "spatialCoverage",
        "creator",
        "contributor",
        "provider",
        "publisher",
        "funding",
        "license",
        "wasRevisionOf",
        "wasDerivedFrom",
        "isBasedOn",
        "wasGeneratedBy",
    ]


@pytest.fixture
def interface_methods():
    """Return the names of strategy methods."""
    res = [
        "get_name",
        "get_description",
        "get_url",
        "get_same_as",
        "get_version",
        "get_is_accessible_for_free",
        "get_keywords",
        "get_identifier",
        "get_citation",
        "get_variable_measured",
        "get_included_in_data_catalog",
        "get_subject_of",
        "get_distribution",
        "get_potential_action",
        "get_date_created",
        "get_date_modified",
        "get_date_published",
        "get_expires",
        "get_temporal_coverage",
        "get_spatial_coverage",
        "get_creator",
        "get_contributor",
        "get_provider",
        "get_publisher",
        "get_funding",
        "get_license",
        "get_was_revision_of",
        "get_was_derived_from",
        "get_is_based_on",
        "get_was_generated_by",
    ]
    return res


def pytest_configure(config):
    """A marker for tests that require internet connection."""
    config.addinivalue_line(
        "markers", "internet_required: mark test as requiring internet " + "connection"
    )


@pytest.fixture(scope="session")
def internet_connection():
    """Check if there is an internet connection."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False


def is_url(url):
    """Check if a string is a URL."""
    try:
        res = urlparse(url)
        return all([res.scheme, res.netloc])
    except ValueError:
        return False


def is_property_type(results, expected_types):
    """
    Parameters
    ----------
    results : Any
        The results of a strategy method to check.
    expected_types : List
        The expected types, as a list of strings. See below for the currently
        supported types.

    Returns
    -------
    bool
        True if the result is one of the expected types.

    Notes
    -----
    Expected types are one or more of:

    - schema:Text
    - schema:URL
    - schema:Number
    - schema:Boolean
    - schema:DefinedTerm
    - schema:PropertyValue
    - schema:DataCatalog
    - schema:DataDownload
    - time:ProperInterval
    - time:Instant
    - schema:Place
    - schema:Person
    - schema:Organization
    - schema:MonetaryGrant
    - @id
    - provone:Execution

    where schema, time, and provone are the namespaces of https://schema.org/,
    http://www.w3.org/2006/time#, and
    http://purl.dataone.org/provone/2015/01/15/ontology# respectively.

    When type matching, the namespace prefix of an expected type is not used.
    Only the suffix is used.
    """
    # pylint: disable=R0912
    # Prepare the results and expected_types for iteration
    if isinstance(results, dict) and results.get("@list") is not None:
        results = results.get("@list")  # Flatten @list to facilitate checking
    if not isinstance(results, list):  # Convert to list for iteration
        results = [results]
    if not isinstance(expected_types, list):  # Convert to list for iteration
        expected_types = [expected_types]
    # Check that the results are at least one of the expected types
    outputs = []
    for result in results:
        is_expected_type = []
        for expected_type in expected_types:
            if expected_type == "schema:Text":
                is_expected_type.append(isinstance(result, str))
            elif expected_type == "schema:URL":
                is_expected_type.append(is_url(result))
            elif expected_type == "schema:Number":
                is_expected_type.append(isinstance(result, (int, float)))
            elif expected_type == "schema:Boolean":
                is_expected_type.append(isinstance(result, bool))
            elif expected_type in ["schema:Date", "schema:DateTime"]:
                is_expected_type.append(isinstance(result, str))
            elif expected_type == "@id":
                is_expected_type.append(is_url(result.get("@id")))
            elif isinstance(result, dict):  # schema:Thing or @id
                if result.get("@type") is not None:
                    suffix = expected_type.split(":")[1]
                    is_type = suffix in result.get("@type")
                    is_expected_type.append(is_type)
            else:
                is_expected_type.append(False)
        outputs.append(any(is_expected_type))
    return any(outputs)
