"""Functions related to interacting with building permit applications."""
import os
import requests

# pylint: disable=too-few-public-methods
class PermitApplication():
    """Functions related to interacting with building permit forms."""

    @staticmethod
    def get_applications_by_query(
            query_params,
            base_url=None,
            formio_api_key=None,
        ):
        """Given a query parameters, retreive submissions """

        base_url = base_url if base_url else os.environ.get('API_BASE_URL')
        api_key = formio_api_key if formio_api_key else os.environ.get('X_APIKEY')

        headers = {
            'x-apikey': '{}'.format(api_key),
            'Content-Type': 'application/json'
        }

        url = '{base_url}/{submission_endpoint}'.format(
            base_url=base_url,
            submission_endpoint='applications'
        )

        response = requests.get(
            url,
            headers=headers,
            params=query_params
        )
        response.raise_for_status()
        print(response.json())
        return response.json()

    @staticmethod
    def update_status(
            formio_id,
            base_url=None,
            formio_api_key=None
        ):
        """ update actionState based on the status of csv export """

        base_url = base_url if base_url else os.environ.get('API_BASE_URL')
        api_key = formio_api_key if formio_api_key else os.environ.get('X_APIKEY')

        headers = {
            'accept': 'application/json',
            'x-apikey': '{}'.format(api_key),
            'Content-Type': 'application/json'
        }
        payload = '{"actionState" : "Done"}'
        url = '{base_url}/{submission_endpoint}/{id}'.format(
            base_url=base_url,
            submission_endpoint='applications',
            id=formio_id
        )

        response = requests.patch(
            url,
            headers=headers,
            data=payload
        )
        response.raise_for_status()
        return response.json()
