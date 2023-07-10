# AUTHOR: VIBHA PATIL
# THIS IS MY CODE TO PARSE IMAGE/PDF TO JSON FORMAT CONTAINING PRODUCT DETAILS
# note: I used processor version: pretrained-invoice-v1.2-2022-02-18
#       I think it worked better on doing trial and error
# THINGS TO DO: 
# 1) process json file into csv with the entities required
# THOUGHTS:
# 1) change processor version if required

# CHANGED THE METHOD OF PROCESSING OF RESPONSE TO GET PRODUCT DETAILS DIRECTLY

import os
import json
from google.cloud import documentai_v1 as documentai
from google.cloud.documentai_v1 import types
from google.cloud import storage

def parser(file_path):
    # Read the input file
    with open(file_path, "rb") as file:
        image_content = file.read()

    # Set up your Google Cloud project credentials and configuration
    project_id = "<project id>"  #google project id
    location = "us"  # e.g., "us" or "eu"
    processor_id = "<processor id>"   # id of created processor
    processor_version_id = 'pretrained-invoice-v1.2-2022-02-18'   #v1.2 works better imo- Vibha
    # The full resource name of the processor version
    processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}/processorVersions/{processor_version_id}"
    field_mask = "text,entities"  # Optional. The fields to return in the Document object.
    

    # Refer to https://cloud.google.com/document-ai/docs/file-types for supported file types
    # Determine the file type based on the file extension
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension == ".pdf":
        mime_type = "application/pdf"
    elif file_extension in [".jpeg", ".jpg", ".png"]:
        mime_type = "image/jpeg"  # Change the mime type for image files as per Document AI requirements
    else:
        print("Unsupported file format.")
        return


    raw_document = documentai.RawDocument(content=image_content, mime_type=mime_type)
    # Configure the process request
    request = documentai.ProcessRequest(
        name=processor_name, raw_document=raw_document, field_mask=field_mask
    )

    result = client.process_document(request=request)

    # For a full list of Document object attributes, please reference this page:
    # https://cloud.google.com/python/docs/reference/documentai/latest/google.cloud.documentai_v1.types.Document
    document = result.document
    entities = document.entities
    text = document.text

    # Store the extracted entities and text in a dictionary
    extracted_data = {
        "Invoice Date": None,
        "Vendor Name": None,
        "Vendor GST": None,
        "Products": [],
        "Total Order Value": None,
        "Total Tax": None,
        "Net Amount before tax": None
    }

    for entity in entities:
        entity_type = entity.type_
        mention_text = entity.mention_text

        if entity_type == "invoice_date":
            extracted_data["Invoice Date"] = mention_text
        elif entity_type == "supplier_name":
            extracted_data["Vendor Name"] = mention_text
        elif entity_type == "supplier_tax_id":
            extracted_data["Vendor GST"] = mention_text
        elif entity_type == "line_item":
            line_item_properties = entity.properties
            product = {}
            for prop in line_item_properties:
                prop_type = prop.type_
                prop_mention_text = prop.mention_text

                if prop_type == "line_item/description":
                    product["Product"] = prop_mention_text
                elif prop_type == "line_item/quantity":
                    product["Quantity"] = prop_mention_text
                elif prop_type == "line_item/unit_price":
                    product["Unit Price"] = prop_mention_text
                elif prop_type == "line_item/amount":
                    product["Amount"] = prop_mention_text

                if product not in extracted_data["Products"]:  #to prevent repeated instances
                        extracted_data["Products"].append(product)

        elif entity_type == "total_amount":
            extracted_data["Total Order Value"] = mention_text   
        elif entity_type == 'total_tax_amount':
            extracted_data["Total Tax"] = mention_text
        elif entity_type == 'net_amount':
            extracted_data["Net Amount before tax"] = mention_text
    # Store the extracted entities in a JSON file
    output_file = "output.json"
    with open(output_file, "w") as file:
        json.dump(extracted_data, file, indent=4)
    print(f"Extracted entities stored in {output_file}")


#authorizing client credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=r"<C:\path to\.apikeyjson>"   #api key

client = documentai.DocumentProcessorServiceClient()

file_path = r"<file path>"
parser(file_path)
