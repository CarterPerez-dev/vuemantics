"""
ⒸAngelaMos | 2026
Standard HTTP response definitions for OpenAPI documentation
"""

from typing import Any

from .error_schemas import ErrorDetail


AUTH_401: dict[int | str,
               dict[str,
                    Any]] = {
                        401: {
                            "model": ErrorDetail,
                            "description": "Authentication failed"
                        },
                    }

FORBIDDEN_403: dict[int | str,
                    dict[str,
                         Any]] = {
                             403: {
                                 "model": ErrorDetail,
                                 "description": "Permission denied"
                             },
                         }

NOT_FOUND_404: dict[int | str,
                    dict[str,
                         Any]] = {
                             404: {
                                 "model": ErrorDetail,
                                 "description": "Resource not found"
                             },
                         }

CONFLICT_409: dict[int | str,
                   dict[str,
                        Any]] = {
                            409: {
                                "model": ErrorDetail,
                                "description": "Resource conflict"
                            },
                        }

FILE_TOO_LARGE_413: dict[int | str,
                         dict[str,
                              Any]] = {
                                  413: {
                                      "model": ErrorDetail,
                                      "description": "File too large"
                                  },
                              }

UNSUPPORTED_MEDIA_415: dict[int | str,
                            dict[str,
                                 Any]] = {
                                     415: {
                                         "model":
                                         ErrorDetail,
                                         "description":
                                         "Unsupported media type"
                                     },
                                 }

VALIDATION_422: dict[int | str,
                     dict[str,
                          Any]] = {
                              422: {
                                  "model": ErrorDetail,
                                  "description": "Validation error"
                              },
                          }

RATE_LIMIT_420: dict[int | str,
                     dict[str,
                          Any]] = {
                              420: {
                                  "model": ErrorDetail,
                                  "description": "Calm down a little.."
                              },
                          }

SERVER_ERROR_500: dict[int | str,
                       dict[str,
                            Any]] = {
                                500: {
                                    "model": ErrorDetail,
                                    "description": "Internal server error"
                                },
                            }

SERVICE_UNAVAILABLE_503: dict[int | str,
                              dict[str,
                                   Any]] = {
                                       503: {
                                           "model": ErrorDetail,
                                           "description":
                                           "Service unavailable"
                                       },
                                   }
