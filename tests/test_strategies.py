"""Test the strategies."""
import pytest
from soso.interface import StrategyInterface
from tests.conftest import is_property_type
from tests.conftest import is_not_null


def test_strategy_inherits_strategy_interface(strategy_instance):
    """Test that each strategy inherits the StrategyInterface class."""
    assert isinstance(strategy_instance, StrategyInterface)


# Each strategy should read a metadata document and store it as an attribute
# for class methods to access.


def test_strategy_reads_metadata(strategy_instance):
    """Test that each strategy reads a metadata document."""
    assert strategy_instance.metadata is not None


# SOSO properties are not universally shared across metadata dialects. In cases
# where a property is not available, the corresponding strategy method will
# return None. Therefore, each method test below first checks if the return
# value is not None before checking the type of the returned value. This
# approach allows for the flexibility of the SOSO guidelines while providing a
# consistent test suite.


def test_get_name_returns_expected_type(strategy_instance):
    """Test that the get_name method returns the expected type."""
    res = strategy_instance.get_name()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:Text"])


def test_get_description_returns_expected_type(strategy_instance):
    """Test that the get_description method returns the expected type."""
    res = strategy_instance.get_description()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:Text"])


def test_get_url_returns_expected_type(strategy_instance):
    """Test that the get_url method returns the expected type."""
    # url doesn't map to EML so use kwargs
    strategy_instance.kwargs = {"url": "https://example.com"}
    res = strategy_instance.get_url()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:URL"])


def test_get_same_as_returns_expected_type(strategy_instance):
    """Test that the get_same_as method returns the expected type."""
    strategy_instance.kwargs = {"sameAs": "https://example.com"}
    res = strategy_instance.get_same_as()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:URL"])


def test_get_version_returns_expected_type(strategy_instance):
    """Test that the get_version method returns the expected type."""
    version_values = ["1.0", 1.0]
    for value in version_values:
        strategy_instance.kwargs = {"version": value}
        res = strategy_instance.get_version()
        assert is_not_null(res)
        assert is_property_type(res, ["schema:Text", "schema:Number"])


def test_get_is_accessible_for_free_returns_expected_type(strategy_instance):
    """Test that the get_is_accessible_for_free method returns the expected
    type."""
    strategy_instance.kwargs = {"isAccessibleForFree": True}
    res = strategy_instance.get_is_accessible_for_free()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:Boolean"])


def test_get_keywords_returns_expected_type(strategy_instance):
    """Test that the get_keywords method returns the expected type."""
    res = strategy_instance.get_keywords()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:Text", "schema:DefinedTerm"])


def test_get_identifier_returns_expected_type(strategy_instance):
    """Test that the get_identifier method returns the expected type."""
    res = strategy_instance.get_identifier()
    assert is_not_null(res)
    assert is_property_type(
        results=res,
        expected_types=["schema:Text", "schema:URL", "schema:PropertyValue"],
    )


@pytest.mark.skipif(strategy_instance="EML", reason="Property not in schema")
def test_get_citation_returns_expected_type(strategy_instance):
    """Test that the get_citation method returns the expected type."""
    res = strategy_instance.get_citation()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:Text", "schema:CreativeWork"])


def test_get_variable_measured_returns_expected_type(strategy_instance):
    """Test that the get_variable_measured method returns the expected type."""
    res = strategy_instance.get_variable_measured()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:PropertyValue"])


def test_get_included_in_data_catalog_returns_expected_type(strategy_instance):
    """Test that the get_included_in_data_catalog method returns the expected
    type."""
    strategy_instance.kwargs = {
        "includedInDataCatalog": {
            "@type": "DataCatalog",
            "name": "Biological Data",
            "description": "A catalog of biological data.",
            "url": "https://www.sample-data-repository.org/collection/biological-data",
        }
    }
    res = strategy_instance.get_included_in_data_catalog()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:DataCatalog"])


def test_get_subject_of_returns_expected_type(strategy_instance):
    """Test that the get_subject_of method returns the expected type."""
    strategy_instance.kwargs = {
        "subjectOf": {
            "@type": "DataDownload",
            "name": "Metadata for dataset",
            "description": "Metadata describing the dataset",
            "encodingFormat": [
                "application/xml",
                "https://metadata.schema/version-1.0.0",
            ],
            "contentURL": "https://example.com/metadata/eml-metadata.xml",
            "dateModified": "2019-06-12T14:44:15Z",
        }
    }
    res = strategy_instance.get_subject_of()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:DataDownload"])


def test_get_distribution_returns_expected_type(strategy_instance):
    """Test that the get_distribution method returns the expected type."""
    res = strategy_instance.get_distribution()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:DataDownload"])


def test_get_potential_action_returns_expected_type(strategy_instance):
    """Test that the get_potential_action method returns the expected type."""
    strategy_instance.kwargs = {
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "contentType": ["application/x-netcdf", "text/tab-separated-values"],
                "urlTemplate": "https://www.sample-data-repository.org/"
                "dataset/1234/download?format={format}&"
                "startDateTime={start}&endDateTime={end}&bounds"
                "={bbox}",
                "description": "Download dataset 1234 based on the requested "
                "format, start/end dates and bounding box",
                "httpMethod": ["GET", "POST"],
            },
            "query-input": [
                {
                    "@type": "PropertyValueSpecification",
                    "valueName": "format",
                    "description": "The desired format requested either "
                    "'application/x-netcdf' or 'text/tab-"
                    "separated-values'",
                    "valueRequired": True,
                    "defaultValue": "application/x-netcdf",
                    "valuePattern": r"(application\/x-netcdf|text\/tab-"
                    "separated-values)",
                },
                {
                    "@type": "PropertyValueSpecification",
                    "valueName": "start",
                    "description": "A UTC ISO DateTime",
                    "valueRequired": False,
                    "valuePattern": "(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0"
                    "[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|"
                    "[01][0-9]):([0-5][0-9]):([0-5][0-9])"
                    "(.[0-9]+)?(Z)?",
                },
                {
                    "@type": "PropertyValueSpecification",
                    "valueName": "end",
                    "description": "A UTC ISO DateTime",
                    "valueRequired": False,
                    "valuePattern": "(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0"
                    "[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|"
                    "[01][0-9]):([0-5][0-9]):([0-5][0-9])"
                    "(.[0-9]+)?(Z)?",
                },
                {
                    "@type": "PropertyValueSpecification",
                    "valueName": "bbox",
                    "description": "Two points in decimal degrees that create "
                    "a bounding box fomatted at 'lon,lat' of "
                    "the lower-left corner and 'lon,lat' of "
                    "the upper-right",
                    "valueRequired": False,
                    "valuePattern": "(-?[0-9]+(.[0-9]+)?),[ ]*(-?[0-9]+(.[0-9]"
                    "+)?)[ ]*(-?[0-9]+(.[0-9]+)?),[ ]*(-?[0-9]"
                    "+(.[0-9]+)?)",
                },
            ],
        }
    }
    res = strategy_instance.get_potential_action()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:SearchAction"])


@pytest.mark.skipif(strategy_instance="EML", reason="Property not in schema")
def test_get_date_created_returns_expected_type(strategy_instance):
    """Test that the get_date_created method returns the expected type."""
    res = strategy_instance.get_date_created()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:Date", "schema:DateTime"])


def test_get_date_modified_returns_expected_type(strategy_instance):
    """Test that the get_date_modified method returns the expected type."""
    res = strategy_instance.get_date_modified()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:Date", "schema:DateTime"])


def test_get_date_published_returns_expected_type(strategy_instance):
    """Test that the get_date_published method returns the expected type."""
    res = strategy_instance.get_date_published()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:Date", "schema:DateTime"])


def test_get_expires_returns_expected_type(strategy_instance):
    """Test that the get_expires method returns the expected type."""
    strategy_instance.kwargs = {"expires": "2019-06-12T14:44:15Z"}
    res = strategy_instance.get_expires()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:Date", "schema:DateTime"])


def test_get_temporal_coverage_returns_expected_type(strategy_instance):
    """Test that the get_temporal_coverage method returns the expected type."""
    res = strategy_instance.get_temporal_coverage()
    assert is_not_null(res)
    assert is_property_type(
        results=res,
        expected_types=[
            "schema:Text",
            "schema:Date",
            "schema:DateTime",
            "time:ProperInterval",
            "time:Instant",
        ],
    )


def test_get_spatial_coverage_returns_expected_type(strategy_instance):
    """Test that the get_spatial_coverage method returns the expected type."""
    res = strategy_instance.get_spatial_coverage()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:Place"])


def test_get_creator_returns_expected_type(strategy_instance):
    """Test that the get_creator method returns the expected type."""
    res = strategy_instance.get_creator()
    assert is_not_null(res)
    assert is_property_type(
        results=res,
        expected_types=["schema:Person", "schema:Organization", "schema:Role"],
    )


@pytest.mark.skipif(strategy_instance="EML", reason="Property not in schema")
def test_get_contributor_returns_expected_type(strategy_instance):
    """Test that the get_contributor method returns the expected type."""
    res = strategy_instance.get_contributor()
    assert is_not_null(res)
    assert is_property_type(
        results=res,
        expected_types=["schema:Person", "schema:Organization", "schema:Role"],
    )


def test_get_provider_returns_expected_type(strategy_instance):
    """Test that the get_provider method returns the expected type."""
    strategy_instance.kwargs = {
        "provider": {"@id": "https://www.sample-data-repository.org"}
    }
    res = strategy_instance.get_provider()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:Organization", "@id"])


def test_get_publisher_returns_expected_type(strategy_instance):
    """Test that the get_publisher method returns the expected type."""
    strategy_instance.kwargs = {
        "publisher": {"@id": "https://www.sample-data-repository.org"}
    }
    res = strategy_instance.get_publisher()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:Organization", "@id"])


def test_get_funding_returns_expected_type(strategy_instance):
    """Test that the get_funding method returns the expected type."""
    res = strategy_instance.get_funding()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:MonetaryGrant"])


def test_get_license_returns_expected_type(strategy_instance):
    """Test that the get_license method returns the expected type."""
    res = strategy_instance.get_license()
    assert is_not_null(res)
    assert is_property_type(res, ["schema:URL"])


@pytest.mark.skipif(strategy_instance="EML", reason="Property not in schema")
def test_get_was_revision_of_returns_expected_type(strategy_instance):
    """Test that the get_was_revision_of method returns the expected type."""
    res = strategy_instance.get_was_revision_of()
    assert is_not_null(res)
    assert is_property_type(res, ["@id"])


@pytest.mark.skipif(strategy_instance="EML", reason="Property not in schema")
def test_get_was_derived_from_returns_expected_type(strategy_instance):
    """Test that the get_was_derived_from method returns the expected type."""
    res = strategy_instance.get_was_derived_from()
    assert is_not_null(res)
    assert is_property_type(res, ["@id"])


@pytest.mark.skipif(strategy_instance="EML", reason="Property not in schema")
def test_get_is_based_on_returns_expected_type(strategy_instance):
    """Test that the get_is_based_on method returns the expected type."""
    res = strategy_instance.get_is_based_on()
    assert is_not_null(res)
    assert is_property_type(res, ["@id"])


def test_get_was_generated_by_returns_expected_type(strategy_instance):
    """Test that the get_was_generated_by method returns the expected type."""
    strategy_instance.kwargs = {
        "wasGeneratedBy": {
            "@id": "https://example.org/executions/execution-42",
            "@type": "provone:Execution",
            "prov:hadPlan": "https://somerepository.org/datasets/10.xxxx/"
            "Dataset-2.v2/process-script.R",
            "prov:used": {"@id": "https://doi.org/10.xxxx/Dataset-1"},
        }
    }
    res = strategy_instance.get_was_generated_by()
    assert is_not_null(res)
    assert is_property_type(res, ["provone:Execution"])
