"""
Created on Oct 1, 2014

@author: fabiomignini
"""
import requests
import falcon
import json
import jsonschema
import logging

from sqlalchemy.orm.exc import NoResultFound
from service_layer_application_core.user_authentication import UserAuthentication
from service_layer_application_core.exception import SessionNotFound, UnauthorizedRequest, RequestValidationError
from service_layer_application_core.controller import ServiceLayerController
from service_layer_application_core.validate_request import RequestValidator

from json.decoder import JSONDecodeError


class ServiceLayer(object):
    """
    ServiceLayer class that intercept the REST call through the WSGI server
    It allows the user to manage his own graph through a REST web service.
    """

    def on_delete(self, request, response, mac_address=None):
        """
        De-instantiate the NF-FG of the user, or update it by removing a mac rule

        :param request: HTTP GET request containing user credential as headers (X-Auth-User, X-Auth-Pass, X-Auth-Tenant)
        :param response: HTTP response code
        :param mac_address: if specified, only the rule relative to this mac will be erased
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
            # Now, it initialize a new controller instance to handle the request
            controller = ServiceLayerController(user_data)
            controller.delete(mac_address=mac_address)
        except NoResultFound:
            print("EXCEPTION - NoResultFound")
            raise falcon.HTTPNotFound()
        except requests.HTTPError as err:
            logging.exception(err.response.text)
            if err.response.status_code == 401:
                raise falcon.HTTPUnauthorized(json.loads(err.response.text)['error']['title'],
                                              json.loads(err.response.text))
            elif err.response.status_code == 403:
                raise falcon.HTTPForbidden(json.loads(err.response.text)['error']['title'],
                                           json.loads(err.response.text))
            elif err.response.status_code == 404:
                raise falcon.HTTPNotFound()
            raise err
        except jsonschema.ValidationError as err:
            logging.exception(err.message)
            raise falcon.HTTPBadRequest('Bad Request', err.message)
        except ValueError:
            logging.exception("Malformed JSON")
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect.')
        except SessionNotFound as err:
            logging.exception(err.message)
            raise falcon.HTTPNotFound()
        except falcon.HTTPError as err:
            logging.exception("Falcon " + err.title)
            raise
        except UnauthorizedRequest as err:
            raise falcon.HTTPUnauthorized("Authentication error. ", err.message)
        except Exception as err:
            logging.exception(err)
            raise falcon.HTTPInternalServerError('Contact the admin. ', str(err))

    def on_put(self, request, response):
        """
        Create a new session for this user instantiating its NF-FG;
        if the user already have an active session, the old NF-FG will be updated.
        The NF-FG is fetched from the database, and sent to the orchestrator (put).

        :param request: HEADER - user credential (X-Auth-User, X-Auth-Pass, X-Auth-Tenant)
                        BODY - json that contain the MAC address of the user device, and its virtual port as
                        {"session":{"device":{"mac":"fc:4d:e2:56:9f:19", "port":"eth4"}}}
                        or void session if no devices should be attached, like
                        {"session":{}}
        :param response: HTTP response code
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
            logging.debug("Authenticated user: " + user_data.username)
            # Now, it initialize a new controller instance to handle the request
            controller = ServiceLayerController(user_data)
            request_dict = json.loads(request.stream.read().decode())
            # request_dict = json.load(request.stream, 'utf-8')
            RequestValidator.validate(request_dict)
            if 'device' in request_dict['session']:
                controller.put(mac_address=request_dict['session']['device']['mac'])
            else:
                controller.put(mac_address=None)
            response.status = falcon.HTTP_202
        except requests.HTTPError as err:
            logging.exception(err.response.text)
            if err.response.status_code == 401:
                raise falcon.HTTPUnauthorized(json.loads(err.response.text)['error']['title'],
                                              json.loads(err.response.text))
            elif err.response.status_code == 403:
                raise falcon.HTTPForbidden(json.loads(err.response.text)['error']['title'],
                                           json.loads(err.response.text))
            elif err.response.status_code == 404:
                raise falcon.HTTPNotFound()
            else:
                raise falcon.HTTPInternalServerError('Orchestrator Error.', json.loads(err.response.text))
        except JSONDecodeError as err:
            logging.exception(err)
            raise falcon.HTTPBadRequest('Bad Request', str(err))
        except jsonschema.ValidationError as err:
            logging.exception(err.message)
            raise falcon.HTTPBadRequest('Bad Request', err.message)
        except RequestValidationError as err:
            logging.exception(err.message)
            raise falcon.HTTPBadRequest('Bad Request', err.message)
        except ValueError:
            logging.exception("Malformed JSON")
            raise falcon.HTTPInternalServerError("Internal Server Error", "Malformed JSON")
        except falcon.HTTPError as err:
            logging.exception("Falcon " + err.title)
            raise err
        except UnauthorizedRequest as err:
            raise falcon.HTTPUnauthorized("Authentication error. ", err.message)
        except Exception as err:
            logging.exception(err)
            raise falcon.HTTPInternalServerError('Contact the admin. ', str(err))

    def on_get(self, request, response):
        """
        Get the status of the user NF-FG by requesting it to the orchestrator.

        :param request: HTTP GET request containing user credential as headers (X-Auth-User, X-Auth-Pass, X-Auth-Tenant)
        :param response: The status of the NF-FG returned by the orchestrator
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
            logging.debug("Authenticated user: " + user_data.username)
            # Now, it initialize a new controller instance to handle the request
            controller = ServiceLayerController(user_data)
            response.body, response.status = controller.get()
        except ValueError:
            logging.exception("Malformed JSON")
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect.')
        except requests.HTTPError as err:
            logging.exception(err.response.text)
            if err.response.status_code == 401:
                raise falcon.HTTPUnauthorized(json.loads(err.response.text)['error']['title'],
                                              json.loads(err.response.text))
            elif err.response.status_code == 403:
                raise falcon.HTTPForbidden(json.loads(err.response.text)['error']['title'],
                                           json.loads(err.response.text))
            elif err.response.status_code == 404:
                logging.exception("Graph not yet instantiated for this user.")
                raise falcon.HTTPNotFound()
            raise err
        except SessionNotFound:
            raise falcon.HTTPNotFound()
        except falcon.HTTPError as err:
            logging.exception("Falcon " + err.title)
            raise
        except UnauthorizedRequest as err:
            raise falcon.HTTPUnauthorized("Authentication error. ", err.message)
        except Exception as err:
            logging.exception(err)
            raise falcon.HTTPInternalServerError('Contact the admin. ', str(err))
