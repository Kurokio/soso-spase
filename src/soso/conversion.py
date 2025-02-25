from soso.main import convert
from pprint import pprint
from soso.strategies.spase import (get_temporal, get_instrument, get_observatory,
                                   get_alternate_name, get_is_related_to, get_is_part_of,
                                   getPaths, SPASE)
import json

def main(folder) -> None:
    # list that holds SPASE records already checked
    searched = []

    SPASE_paths = []

    # obtains all filepaths to all SPASE records found in given directory
    SPASE_paths = getPaths(folder, SPASE_paths)
    #print("You entered " + folder)
    if len(SPASE_paths) == 0:
        print("No records found. Returning.")
    else:
        #print("The number of records is " + str(len(SPASE_paths)))
        # iterate through all SPASE records
        # Note: starting at record 24 in ACE/EPAM folder, end of author string is formatted wrong with "and first last" instead of "and last, first" (SPASE issue)
        # Successfully passed for all 129 records in NumericalData/ACE/EPAM folder and all 187 in DisplayData
        # In DisplayData, records 130, 167-70 has authors formatted wrong
        # DisplayData: record 70 is ex w multiple contacts, ACE has ex's w multiple authors
        # ReleaseDate is not most recent at this dataset (causes dateModified to be incorrect): C:/Users/zboquet/NASA/DisplayData\SDO\AIA\SSC
        #   And some here too: C:/Users/zboquet/NASA/DisplayData\STEREO-A\SECCHI\, C:/Users/zboquet/NASA/DisplayData\STEREO-B\SECCHI
        #                       C:/Users/zboquet/NASA/NumericalData\Cluster-Rumba\WBD\BM2
        # DD: #134 is ex w a LOT of observatory entries thanks to multiple instruments
        # record NASA/DisplayData\OBSPM/H-ALPHA.xml has broken instrumentID link
        # record NASA/DisplayData/UCLA/Global-MHD-code/mS1-Vx/PT10S.xml has extra spacing in PubInfo/Authors
        for r, record in enumerate(SPASE_paths):
            if record not in searched:
                # scrape metadata for each record
                statusMessage = f"Extracting metadata from record {r+1}"
                statusMessage += f" of {len(SPASE_paths)}"
                print(statusMessage)
                print(record)
                print()
                testSpase = SPASE(record)
                temporal = get_temporal(testSpase.metadata, testSpase.namespaces)
                instrument = get_instrument(testSpase.metadata, record)
                observatory = get_observatory(testSpase.metadata, record)
                alternate_name = get_alternate_name(testSpase.metadata)
                inLanguage = "en"
                is_related_to = get_is_related_to(testSpase.metadata)
                is_part_of = get_is_part_of(testSpase.metadata)
                #print(measurement_type)
                # add record to searched
                searched.append(record)

                kwargs = {"temporal": temporal,
                            "instrument": instrument,
                            "observatory": observatory,
                            "alternateName": alternate_name,
                            "inLanguage": inLanguage,
                            "isRelatedTo": is_related_to,
                            "isPartOf": is_part_of}
                r = convert(file = record, strategy='SPASE')
                dict = json.loads(r)
                finalDict = dict | kwargs
                pprint(finalDict)
                #print(json.dumps(finalDict, indent=3))

def main2(file) -> None:
    print(file)
    print()
    testSpase = SPASE(file)
    temporal = get_temporal(testSpase.metadata, testSpase.namespaces)
    instrument = get_instrument(testSpase.metadata, file)
    """instrument = [{'@type': 'IndividualProduct',
                 'identifier': 'spase://SMWG/Instrument/MMS/4/FIELDS/FGM',
                 'name': 'MMS 4 FIELDS Suite, Fluxgate Magnetometer (FGM) '
                         'Instrument',
                 'url': ['https://www.nasa.gov/mission_pages/mms/spacecraft/mms-instruments.html']},
                {'@type': 'IndividualProduct',
                 'identifier': 'spase://SMWG/Instrument/MMS/4/HotPlasmaCompositionAnalyzer',
                 'name': 'MMS 4 Hot Plasma Composition Analyzer (HPCA) '
                         'Instrument',
                 'url': ['https://www.nasa.gov/mission_pages/mms/spacecraft/mms-instruments.html']}]"""
    observatory = get_observatory(testSpase.metadata, file)
    """observatory = [{'@id': 'spase://SMWG/Observatory/MMS',
                  '@type': 'ResearchProject',
                  'name': 'MMS',
                  'url': ['https://mms.gsfc.nasa.gov/']},
                 {'@id': 'spase://SMWG/Observatory/MMS/4',
                  '@type': 'ResearchProject',
                  'name': 'MMS-4',
                  'url': ['https://mms.gsfc.nasa.gov/']}]"""
    alternate_name = get_alternate_name(testSpase.metadata)
    inLanguage = "en"
    is_related_to = get_is_related_to(testSpase.metadata, file)
    """is_related_to = {'@type': 'CreativeWork',
                    'isRelatedTo': ['spase://NASA/NumericalData/ACE/EPAM/LEFS150/MFSA/SolarWindFrame/Sectored/Proton/Fluxes/PT17M',
                                'spase://NASA/NumericalData/ACE/EPAM/LEFS150/MFSA/SolarWindFrame/Sectored/Proton/Fluxes/P1D']}"""
    is_part_of = get_is_part_of(testSpase.metadata, file)
    """is_part_of = {'@type': 'CreativeWork',
                'isPartOf': 'spase://NASA/NumericalData/Ulysses/COSPIN/HET/Rates/SpinAveraged/PT10M'}"""
    #print(measurement_type)

    kwargs = {"temporal": temporal,
                "instrument": instrument,
                "observatory": observatory,
                "alternateName": alternate_name,
                "inLanguage": inLanguage,
                "isRelatedTo": is_related_to,
                "isPartOf": is_part_of}
    r = convert(file = file, strategy='SPASE')
    dict = json.loads(r)
    dict.update(kwargs)
    out_file = open("./SOSO_Draft.json", "w")
    json.dump(dict, out_file, indent=3, sort_keys=True)
    out_file.close()
    #finalDict = dict | kwargs
    #pprint(finalDict)
file = "C:/Users/zboquet/NASA/NumericalData/MMS/4/HotPlasmaCompositionAnalyzer/Burst/Level2/Ion"
#main(file)
#/PT0.625S.xml"
file = "C:/Users/zboquet/soso-spase/src/soso/data/spase.xml"
main2(file)