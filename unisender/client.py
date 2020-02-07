# -*- coding: utf-8 -*-
import requests
from unisender.utils import to_camel_case


class Client(object):

    """
    This class represents the client for low-level access
    to the `UniSender API <https://www.unisender.com/ru/support/api/api/>`

    .. note::
        Your may call any method registered in `_api_methods`.
        Usage example:
            cl = Client(api_key, platform)
            cl.create_field(name='username', type='string')
            response = cl.import_contacts(
                field_names=['email', 'name'],
                data=[
                    ['example1@gmail.com', 'John Lennon'],
                    ['example2@gmail.com', 'Paul McCartney']
                ]
            )
            assert response.ok and not response.json().get('error')
    """

    DEFAULT_CONF = {
        "base_url": "https://api.unisender.com",
        "lang": "en",
        'format': 'json',
        "api_key": None,
        'platform': None,
    }

    def _get_default_request_data(self) -> dict:

        """ Return default data for API requests """

        return {
            'api_key': self._config['api_key'],
            'platform': self._config['platform'],
            'format': self._config['format']
        }

    def _build_request_data(self, data: dict, extra_key=None) -> dict:

        """
        Add default request data and converts data to unisender request data format

        :param data: dict, request params
        :param extra_key: str, name for list param (for recursive call)
        :return: specific unisender request data format, see below

        .. note::
            Example for `importContacts` method request data:
            data: {
                'field_names': ['email_list_ids', 'name', 'email', 'email_status'],
                'data': [['19941536', 'example_name', 'example@gmail.com', 'active']],
                'overwrite_lists': 1
            }

            return: {
                'api_key':  '****api_key***',
                'platform': 'example_platform',
                'format':   'json',
                'field_names[0]': 'email_list_ids',
                'field_names[1]': 'name',
                'field_names[2]': 'email',
                'field_names[3]': 'email_status',
                'data[0][0]': '19941536',
                'data[0][1]': 'example_name',
                'data[0][2]': 'zakirmalay@gmail.com',
                'data[0][3]': 'active',
                'overwrite_lists': 1
            }

        """
        result = self._get_default_request_data()
        for key, val in data.items():
            _key = f'{extra_key}[{key}]' if isinstance(extra_key, str) else key
            if isinstance(val, dict):
                result.update(self._build_request_data(val, _key))
            elif isinstance(val, list):
                result.update(self._build_request_data(dict(enumerate(val)), _key))
            elif val is not None:
                result[_key] = val
        return result

    def _get_request_url(self, method: str) -> str:

        """
        Build API request url by passed method and config

        :param method: str, snake case API method name
        :return: request url in unisender API format
        """

        return '{base_url}/{lang}/api/{method}'.format(
            base_url=self._config['base_url'],
            lang=self._config['lang'],
            method=to_camel_case(method),
        )

    def after_request(self, response: requests.Response) -> None:

        """ Do something with api response """

        pass

    def _api_request(self, method: str, **kwargs) -> requests.Response:

        """
        Calls the API method by the given name and request data

        :param method: str, snake case API method name
        :param kwargs: dict, request data
        :return: requests.Response, API response obj
        """

        data = self._build_request_data(kwargs)
        url = self._get_request_url(method)
        response = requests.post(url, data)
        self.after_request(response)
        return response

    @property
    def _api_methods(self) -> list:

        """ Return list of allowed unisender api methods """

        return [
            'get_lists', 'create_list', 'update_list', 'delete_list',
            'subscribe', 'exclude', 'unsubscribe',
            'import_contacts', 'export_contacts',
            'get_total_contacts_count', 'get_contact_count', 'get_contact',
            'get_fields', 'create_field', 'update_field', 'delete_field',
            'get_tags', 'delete_tag',
            'create_email_message', 'update_email_message', 'delete_message',
            'send_email', 'send_test_email', 'check_email', 'update_opt_in_email',
            'get_messages', 'get_message', 'list_messages', 'get_checked_email',
            'create_campaign', 'cancel_campaign',
            'create_sms_message', 'send_sms', 'check_sms', 'get_actual_message_version',
            'get_web_version',
            'create_email_template', 'update_email_template', 'delete_template',
            'get_template', 'get_templates', 'list_templates',
            'get_campaign_delivery_stats', 'get_campaign_common_stats', 'get_visited_links',
            'get_campaigns', 'get_campaign_status',
            'validate_sender', 'register', 'check_user_exists', 'get_user_info', 'get_users',
            'transfer_money', 'get_available_tariffs', 'change_tariff', 'set_sender_domain',
        ]

    def __init__(self, api_key: str, platform: str, **kwargs):

        """
        Configures api client

        :param api_key:  str, API key
        :param platform: str, API tracking marker
        :param format:   str, API response format
        :param base_url: str, API server url
        :param lang:     str, API message language, available: ru,en,it
        """

        self._config = self.DEFAULT_CONF
        self._config['api_key'] = api_key
        self._config['platform'] = platform
        self._config.update(kwargs)

    def __getattr__(self, name: str):

        """ Check if attr name in _api_methods, call _api_request function """

        def get(self, **kwargs):
            return self._api_request(method=name, **kwargs)

        if name in self._api_methods:
            return get.__get__(self)
