"""
Created on Oct 1, 2014

@author: fabiomignini
@author: gabrielecastellano
"""
import logging

from service_layer_application_core.exception import RequestValidationError
from jsonschema import validate, ValidationError


class RequestValidator:
    @staticmethod
    def validate(nffg):
        schema = {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "properties": {
                "session": {
                    "type": "object",
                    "properties": {
                        "mac": {
                            "type": "string"
                        }
                    },
                    "additionalProperties": True
                }
            },
            "required": [
                "session"
            ],
            "additionalProperties": False
        }
        try:
            validate(nffg, schema)
        except ValidationError as err:
            logging.info(err.message)
            raise RequestValidationError(err.message)
