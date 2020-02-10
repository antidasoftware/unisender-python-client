# UniSender Python client


Python open source client for [UniSender API](https://www.unisender.com/ru/support/api/api/)

### Features
- Client for low-level access
- SimpleClient to quickly start mailing

### Requirements
- Python >= 3.6
- requests

### Installation

pip install git+git://github.com/antidasoftware/unisender-python-client.git


### Basic usage

Create an account in the [service](https://www.unisender.com) and get the API key in your account settings.


```python
from unisender import Client

cl = Client(
    api_key="your_api_key",
    platform="example",
    lang="ru"
)
```
##### Client configuration

- **base_url** [str] - API URL (default: "https://api.unisender.com")
- **lang** [str] - API messages language, available: "ru", "en", "it" (default: "en")
- **format** [str] - API response format, only "json" (default: "json")
- **api_key*** [str] - UniSender account API key
- **platform*** [str] - API tracking marker (any string)

##### API Methods call example

See details about called methods in the [API docs](https://www.unisender.com/ru/support/api/api)

```python
# create contacts fields
cl.create_field(name='username', type='string')

# import contacts to API
response = cl.import_contacts(
    field_names=['email', 'name'],
    data=[
        ['example1@gmail.com', 'John Lennon'],
        ['example2@gmail.com', 'Paul McCartney']
    ]
)
```

### Advanced usage

For fast mailing use SimpleClient:

```python
from unisender import SimpleClient
from datetime import datetime, timedelta

cl = SimpleClient(
    api_key="your_api_key",
    platform="example",
    lang="ru"
)
recipients = [
    {'email': 'example_3@gmail.com', 'name': 'Dave Guard'},
    {'email': 'example_4@mail.ru', 'name': 'Bon Shane'},
    {'email': 'example_5@yandex.ru', 'name': 'Nick Reynolds'},
]
```
SimpleClient provide **create_email_campaign** method for quick start mailing.
Method return boolean "True" value if campaign created successfully (else "False").

There are three mailing modes:

1. Send custom HTML-email message:
```python
time_now = datetime.now() + timedelta(hours=2)

success = cl.create_email_campaign(
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

```
2. Send email message from UniSender custom template:

```python
time_delay = datetime.now() + timedelta(hours=2)

success = cl.create_email_campaign(
    email_type='template',
    email_data={
        "sender_name": 'John Lenon',
        "sender_email": 'example_1@gmail.com',
        "template_id": 4185485
    },
    recipients=recipients,
    start_time=time_delay,
)
```
3. Send email message from UniSender system template:

``` python
fixed_time = datetime.strptime('2020-02-07 17:00', '%Y-%m-%d %H:%M')

success = cl.create_email_campaign(
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
```
- **email_type** [str] - one of "html", "template" or "system_template"
- **email_data*** [dict] - email message data. See more about email data in ["createEmailMessage" docs](https://www.unisender.com/ru/support/api/messages/createemailmessage/)
- **recipints*** [list] - each list item must be represented by a dictionary with the same set of keys. Dictionary keys can be used in a email template.
- **start_time** [datetime] - mailing start time
- **timezone** [str] - time zone that indicates propagation time. Available only "UTC" (default: time zone from your account settings)
