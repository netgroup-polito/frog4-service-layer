"""
Created on Oct 1, 2014

@author: fabiomignini
"""
import logging

from service_layer_application_core.exception import RequestValidationError
from json_hyper_schema import Schema, ValidationError


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
        hyper_schema = Schema(schema)
        try:
            hyper_schema.validate(nffg)
        except ValidationError as err:
            logging.info(err.message)
            raise RequestValidationError(err.message)
