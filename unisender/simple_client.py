# -*- coding: utf-8 -*-
import requests
from datetime import datetime
from copy import deepcopy
from unisender.client import Client
from unisender.utils import get_unique_hash


class SimpleClient(Client):

    """ This class represents the client for simple mailing """

    EMAIL_TYPES = ['html', 'template', 'system_template']
    COMMON_EMAIL_ARGS = ['sender_name', 'sender_email', 'list_id']
    REQUIRED_EMAIL_ARGS = {
        'html': COMMON_EMAIL_ARGS + ['body', 'subject'],
        'template': COMMON_EMAIL_ARGS + ['template_id'],
        'system_template': COMMON_EMAIL_ARGS + ['system_template_id'],
    }
    EMAIL_SYSTEM_FIELDS = {
        'delete', 'tags', 'email', 'email_status', 'email_availability', 'email_list_ids',
        'email_subscribe_times', 'email_unsubscribed_list_ids', 'email_excluded_list_ids'
    }
    ERROR_MESSAGES = {
        'email_missing_fields':   'Please fill "email_data" required field(s): %s',
        'email_recipients_empty': 'The recipient list should not be empty!',
    }

    def after_request(self, response):

        """ Raises HTTPError for failed API request """
        response.raise_for_status()

    def _validate_email_data(self, email_type: EMAIL_TYPES, email_data: dict) -> None:

        """
        Checks required params in `email_data` by given email_type

        :param email_type: str, one of `EMAIL_TYPES`
        :param email_data: dict, data for `create_email_message` method
        """

        try:
            assert set(self.REQUIRED_EMAIL_ARGS[email_type]) <= set(email_data.keys())
        except AssertionError:
            fields = set(self.REQUIRED_EMAIL_ARGS[email_type]) - set(email_data.keys())
            raise Exception(self.ERROR_MESSAGES['email_missing_fields'] % ', '.join(fields))

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

        try:
            assert len(recipients)
        except AssertionError:
            raise Exception(self.ERROR_MESSAGES['email_recipients_empty'])
        else:
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

    def create_email_campaign(self, recipients: list, email_data: dict, email_type: EMAIL_TYPES,
                              start_time: datetime, track_read=1, **kwargs) -> bool:

        """
        Performs a sequence of API operations to creating email campaign

        :param recipients: list, of dictionaries that represents contacts data
        :param email_data: dict, data for `create_email_message` method
        :param email_type: str, one of `EMAIL_TYPES`
        :param start_time: datetime, mailing start time
        :param track_read: bool, track reading a letter
        :param kwargs:     dict, additional campaign params
        :return:

        .. note::
            Sequence of API operations:
                1. create_list
                2. create_fields
                3. import_contacts
                4. create_email_message
                5. create_campaign

            Usage example:
                from datetime import datetime, timedelta

                recipients = [
                    {'email': 'example_3@gmail.com', 'name': 'Dave Guard'},
                    {'email': 'example_4@mail.ru', 'name': 'Bon Shane'},
                    {'email': 'example_5@yandex.ru', 'name': 'Nick Reynolds'},
                ]
                time_now = datetime.now() + timedelta(hours=2)
                time_delay = datetime.now() + timedelta(hours=2)
                fixed_time = datetime.strptime('2020-02-07 17:00', '%Y-%m-%d %H:%M')

                1. Send custom email message with body as HTML:

                    create_email_campaign(
                        email_type='html',
                        email_data={
                            "subject":     'Mail subject',
                            "sender_name": 'John Lenon',
                            "sender_email": 'example_1@gmail.com',
                            "body": '<html>...</html>',
                            "categories": ['First', 'Second']
                        },
                        recipients=recipients,
                        start_time=time_now,
                    )

                2. Send email message from UniSender custom template:

                    create_email_campaign(
                        email_type='template',
                        email_data={
                            "sender_name": 'John Lenon',
                            "sender_email": 'example_1@gmail.com',
                            "template_id": 4185485
                        },
                        recipients=recipients,
                        start_time=time_delay,
                    )


                3. Send email message from UniSender system template:

                    create_email_campaign(
                        email_type='system_template',
                        email_data={
                            "sender_name": 'John Lenon',
                            "sender_email": 'example_1@gmail.com',
                            "system_template_id": 54485
                        },
                        recipients=recipients,
                        start_time=fixed_time,
                        timezone='UTC'
                    )
        """

        recipients_hash = get_unique_hash(recipients)
        list_title = f'mailing_list_{recipients_hash}'
        response = self.create_list(title=list_title)
        if response.json().get('result'):
            list_id = response.json()['result']['id']
        else:
            list_id = self.find_list_id(list_title)
        assert list_id is not None
        email_data['list_id'] = list_id
        self.import_contacts(recipients, email_list_ids=[list_id])
        self._validate_email_data(email_type, email_data)
        response = self.create_email_message(**email_data)
        message_id = response.json()['result']['message_id']
        response = self._api_request(
            method='create_campaign',
            message_id=message_id,
            start_time=start_time.strftime("%Y-%m-%d %H:%M"),
            track_read=track_read,
            **kwargs
        )
        success = response.ok and not response.json().get('error')
        return success
