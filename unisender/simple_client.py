# -*- coding: utf-8 -*-
import requests
from copy import deepcopy
from unisender.client import Client
from unisender.utils import get_unique_hash


class SimpleClient(Client):

    """ This class represents the client for simple mailing """

    COMMON_EMAIL_ARGS = []
    REQUIRED_EMAIL_ARGS = {
        'html': ['sender_name', 'sender_email', 'body', 'subject'],
        'template':  ['sender_name', 'sender_email']
    }
    EMAIL_SYSTEM_FIELDS = {
        'delete', 'tags', 'email', 'email_status', 'email_availability', 'email_list_ids',
        'email_subscribe_times', 'email_unsubscribed_list_ids', 'email_excluded_list_ids'
    }
    ERROR_MESSAGES = {
        'email_data_error':       'UniSender client error: Please fill correct "email_data" fields',
        'email_missing_fields':   'UniSender client error: Please fill "email_data" required field(s): %s',
        'email_recipients_empty': 'UniSender client error: The recipient list should not be empty!',
        'request_error':          'UniSender client error: Request failed [status: %s] [URL: %s] Details: %s',
    }

    def _validate_recipients(self, recipients: list) -> None:
        if not recipients:
            raise Exception(self.ERROR_MESSAGES['email_recipients_empty'])

    def _validate_email_data(self, data: dict) -> None:

        """ Checks required fields for `create_email_message` method """

        is_template = any(elem in data.keys() for elem in ['template_id', 'system_template_id'])
        is_html = any(elem in data.keys() for elem in ['text_body', 'body'])
        if is_template:
            email_type = 'template'
        elif is_html:
            email_type = 'html'
        else:
            raise Exception(self.ERROR_MESSAGES["email_data_error"])

        try:
            assert set(self.REQUIRED_EMAIL_ARGS[email_type]) <= set(data.keys())
        except AssertionError:
            fields = set(self.REQUIRED_EMAIL_ARGS[email_type]) - set(data.keys())
            raise Exception(self.ERROR_MESSAGES['email_missing_fields'] % ', '.join(fields))

    def _validate_response(self, response: requests.Response) -> None:

        """ Raise Exception for failed API response """

        if response.status_code == requests.codes.ok:
            error = response.json().get('error')
            if error is not None:
                raise Exception(
                    self.ERROR_MESSAGES['request_error'] % (response.status_code, response.request.url, error)
                )
        else:
            raise Exception(
                self.ERROR_MESSAGES['request_error'] % (response.status_code, response.request.url, 'HTTP error')
            )

    def after_request(self, response: requests.Response) -> None:

        """ Check API response """

        self._validate_response(response)

    def find_list_id(self, title: str):

        """
        Get or create mailing list by the specified unique title

        :param title: str, mailing list unique title
        :return:  mailing list id or None
        """

        result = None
        response = self.get_lists()
        for elem in response.json()['result']:
            if elem['title'] == title:
                result = elem['id']
        return result

    def create_fields(self, field_names: list, field_type: str = 'string') -> None:

        """
        Create API contacts fields if not exist

        :param field_names: list, names of creating fields
        :param field_type: str, field type, one of: string, text, number, date, bool
        """

        response = self.get_fields()
        existing_field_names = self.EMAIL_SYSTEM_FIELDS.copy()
        for api_field in response.json()['result']:
            existing_field_names.add(api_field['name'])

        field_names = set(field_names) - existing_field_names
        for field_name in field_names:
            self.create_field(name=field_name, type=field_type)

    def import_contacts(self, recipients: list, email_list_ids=None) -> requests.Response:

        """
        Import and subscribe recipients list in API

        :param recipients: list, of dictionaries that represents contacts data
        :param email_list_ids: list, ids of the mailing lists to which created contacts will be subscribed
        :return: requests.Response
        """

        def _create_contacts_field_names(recipients: list) -> list:

            """
            Creates `field_names` list from `recipients` for 'create_contacts' method

            :param recipients: list, of dictionaries that represents contacts data
            :return: list contacts data fields names

            .. note::
                Example:
                recipients = [
                    {"name": "John Lennon", "email": "example_1@gmail.com"},
                    {"name": "Paul McCartney", "email": "example2@gmail.com"}
                ]

                return ["name", "email"]
            """

            field_names = set(recipients[0].keys())
            field_names.add('email_status')
            field_names.add('email_list_ids')
            return list(field_names)

        def _create_contacts_data(field_names: list, recipients: list, email_list_ids: list) -> list:

            """
            Converts `recipients` data to format accepted for 'create_contacts' method

            :param field_names: list, represents fields of created contacts
            :param recipients: list, of dictionaries with created contacts data
            :param email_list_ids: list, ids of the lists to which created contacts will be subscribed
            :return: list of lists with contacts data ordered by field_names

            .. note::
                Example:
                recipients = [
                    {"name": "John Lennon", "email": "example_1@gmail.com"},
                    {"name": "Paul McCartney", "email": "example2@gmail.com"}
                ]

                field_names = ["name", "email"]

                return [
                    ["John Lennon", "example_1@gmail.com"],
                    ["Paul McCartney", "example_2@gmail.com"],
                ]
            """

            data = []
            contacts = deepcopy(recipients)
            for contact in contacts:
                contact['email_status'] = 'active'
                contact['email_list_ids'] = ','.join([str(el) for el in email_list_ids])
                data.append([str(contact[key]) for key in field_names])
            return data

        if not email_list_ids:
            email_list_ids = []
        field_names = _create_contacts_field_names(recipients)
        data = _create_contacts_data(field_names, recipients, email_list_ids)
        self.create_fields(field_names)
        return self._api_request(
            method='import_contacts',
            field_names=field_names,
            data=data,
            overwrite_lists=1
        )

    def create_email_message(self, **data) -> requests.Response:

        """
        Create email message with given data

        :param data: dict, email params
        :return: requests.Response

        .. note::
            Convert category list to specific API format:
            from list: ['first', 'second'] to str: 'first, second'
        """

        categories = data.get('categories')
        if categories is not None:
            data['categories'] = ','.join(str(el) for el in categories)
        return self._api_request(method='create_email_message', **data)

    def create_email_campaign(self, recipients: list, email_data: dict, campaign_data=None) -> int:

        """
        Makes a set of API operations for creating email campaign

        :param recipients: list, of dictionaries that represents contacts data
        :param email_data: dict, data for `create_email_message` method
        :param campaign_data: None|dict, data for `create_campaign` method
        :return: int, created campaign id

        .. note::
            Sequence of API operations:
                1. get or create list
                2. create_fields
                3. import_contacts
                4. create_email_message
                5. create_campaign

            Usage example:
            # -----------------
            from datetime import datetime, timedelta
            from unisender import SimpleClient

            client = SimpleClient(api_key, platform="example")
            recipients = [
                {'email': 'example_3@gmail.com', 'name': 'Dave Guard'},
                {'email': 'example_4@mail.ru', 'name': 'Bon Shane'},
                {'email': 'example_5@yandex.ru', 'name': 'Nick Reynolds'},
            ]
            time_delay = datetime.now() + timedelta(hours=2)

            # 1. Send custom email message (with body as HTML) now:

            client.create_email_campaign(
                recipients,
                email_data={
                    "subject":     'Mail subject',
                    "sender_name": 'John Lenon',
                    "sender_email": 'example_1@gmail.com',
                    "body": '<html>...</html>',
                    "categories": ['First', 'Second']
                }
            )

            # 2. Send delayed email message (from UniSender custom template) :

            client.create_email_campaign(
                recipients=recipients,
                email_data={
                    "sender_name": 'John Lenon',
                    "sender_email": 'example_1@gmail.com',
                    "template_id": 4185485
                },
                campaign_data={
                    "start_time": time_delay
                }
            )

            # 3. Send delayed email message (from UniSender system template) with UTC time zone:

            client.create_email_campaign(
                recipients=recipients,
                email_data={
                    "sender_name": 'John Lenon',
                    "sender_email": 'example_1@gmail.com',
                    "system_template_id": 54485
                },
                campaign_data={
                    start_time=time_delay,
                    timezone='UTC'
                }
            )
        """

        self._validate_recipients(recipients)
        self._validate_email_data(email_data)

        recipients_hash = get_unique_hash(recipients)
        list_title = f'mailing_list_{recipients_hash}'
        list_id = self.find_list_id(list_title)
        if list_id is None:
            response = self.create_list(title=list_title)
            list_id = response.json()['result']['id']

        email_data['list_id'] = list_id

        self.import_contacts(recipients, email_list_ids=[list_id])
        response = self.create_email_message(**email_data)

        if campaign_data is None:
            campaign_data = {}
        campaign_data['message_id'] = response.json()['result']['message_id']
        start_time = campaign_data.get('start_time')
        if start_time:
            campaign_data['start_time'] = start_time.strftime("%Y-%m-%d %H:%M")

        response = self._api_request(method='create_campaign', **campaign_data)
        return response.json()['result']['campaign_id']

    def create_many_email_campaigns(self, campaigns: list, recipients: list,
                                    default_email_data=None, default_campaign_data=None):

        """
        Create many email campaigns. Makes a set of calls the "create_email_campaign" method

        :param campaigns: list, see example below
        :param recipients: list of dictionaries, represents contacts data
        :param default_email_data: None|dict, default data for `create_email_message` method
        :param default_campaign_data: None|dict, default data for `create_campaign` method
        :return: list, created campaigns ids

        ..note::

            Usage example:
            # -----------------
            from datetime import datetime, timedelta
            from unisender import SimpleClient

            client = SimpleClient(api_key, platform="example")
            time_delay_1 = datetime.now() + timedelta(hours=1)
            time_delay_4 = datetime.now() + timedelta(hours=4)

            # Send many delayed email messages (from UniSender custom template):

            campaign_ids = client.create_many_email_campaigns(
                default_email_data={
                    "sender_name": sender_name,
                    "sender_email": sender_email
                },
                default_campaign_data={
                    "timezone": 'UTC',
                    "start_time": time_delay_1
                },
                campaigns=[
                    {
                        "email_data": {"template_id": 3140875},
                        "campaign_data": {"start_time": time_delay_4}
                    },
                    {
                        "email_data": {"template_id": 3140875},
                        "campaign_data": {"start_time": time_delay_4}
                    }
                ],
                recipients=[
                    {'email': 'example_3@gmail.com', 'name': 'Dave Guard'},
                    {'email': 'example_4@mail.ru', 'name': 'Bon Shane'},
                    {'email': 'example_5@yandex.ru', 'name': 'Nick Reynolds'},
                ]
            )
        """

        campaign_ids = []
        for campaign_num, campaign in enumerate(campaigns):
            if default_email_data is not None:
                for key, val in default_email_data.keys():
                    campaign['email_data'].setdefault(key, val)
            if default_campaign_data is not None:
                for key, val in default_campaign_data.keys():
                    campaign['campaign_data'].setdefault(key, val)
            try:
                campaign_id = self.create_email_campaign(
                    recipients=recipients,
                    email_data=campaign['email_data'],
                    campaign_data=campaign['campaign_data']
                )
            except Exception as e:
                raise Exception(f'{e}. Campaign number: {campaign_num}')
            else:
                campaign_ids.append(campaign_id)
        return campaign_ids
