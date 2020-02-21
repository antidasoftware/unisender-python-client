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

1. Create an account in the [service](https://www.unisender.com) and get the API key in your account settings.

2. Import and configure client:

- **base_url** [str] - API URL (default: "https://api.unisender.com")
- **lang** [str] - API messages language, available: "ru", "en", "it" (default: "en")
- **format** [str] - API response format, only "json" (default: "json")
- **api_key*** [str] - UniSender account API key
- **platform*** [str] - API tracking marker (any string)

Example configuration:
```python
from unisender import Client

cl = Client(
    api_key="your_api_key",
    platform="example",
    lang="ru"
)
```
3. Email authentication (for production)

Create SPF, DKIM records for your domain, see [instruction](https://www.unisender.com/ru/support/about/email-autentifikaciya/).

4. Client usage:

Client allow use any [API methods](https://www.unisender.com/ru/support/api/api), for example "create_field" and "import_contacts":

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


For start mailing your need a complete a set of API requests:
1. Create list;
2. Create fields;
3. Import contacts;
4. Create email message;
5. Create campaign.

It is not comfortable. To simplify this procedure, use "SimpleClient" and next methods:
- **create_email_campaign** - send one email message;
- **create_email_campaigns** - send a lot of email messages.

Example configuration:

```python
from unisender import SimpleClient
from datetime import datetime, timedelta

cl = SimpleClient(
    api_key="your_api_key",
    platform="example",
    lang="ru"
)
```

#### create_email_campaign

Attributes:
- **recipients*** [list] - each list item must be represented by a dictionary with the same set of keys. Dictionary keys can be used in a email template;
- **email_data*** [dict] - represent fields for "create_email_message" API-method. See the [method documentation](https://www.unisender.com/ru/support/api/messages/createemailmessage/) for a list of valid parameters. Parameter "list_id" is set automatically;
- **campaign_data** [dict] - represent fields for "create_campaign" API-method. See the [method documentation](https://www.unisender.com/ru/support/api/messages/createcampaign/) for a list of valid parameters. Parameter "message_id" is set automatically;

Return value [int] - created campaign id. 

Examples:

1. Send custom email message (with body as HTML) now:
```python
client.create_email_campaign(
    recipients = [
        {'email': 'example_3@gmail.com', 'name': 'Dave Guard'},
        {'email': 'example_4@mail.ru', 'name': 'Bon Shane'},
        {'email': 'example_5@yandex.ru', 'name': 'Nick Reynolds'}
    ],
    email_data={
        "subject": 'Email subject',
        "sender_name": 'John Lenon',
        "sender_email": 'example_1@gmail.com',
        "body": '<html>...</html>',
        "categories": ['First', 'Second']
    }
)
```
2. Send delayed email message (from UniSender custom email template):

```python
start_time = datetime.now() + timedelta(hours=2)

client.create_email_campaign(
    recipients = [
        {'email': 'example_3@gmail.com', 'name': 'Dave Guard'},
        {'email': 'example_4@mail.ru', 'name': 'Bon Shane'},
        {'email': 'example_5@yandex.ru', 'name': 'Nick Reynolds'}
    ],
    email_data={
        "sender_name": 'John Lenon',
        "sender_email": 'example_1@gmail.com',
         "template_id": 4185485
    },
    campaign_data={
        "start_time": start_time
    }
)
```
3. Send delayed email message (from UniSender system template) with UTC time zone:

``` python
start_time = datetime.now() + timedelta(hours=2)

client.create_email_campaign(
    recipients = [
        {'email': 'example_3@gmail.com', 'name': 'Dave Guard'},
        {'email': 'example_4@mail.ru', 'name': 'Bon Shane'},
        {'email': 'example_5@yandex.ru', 'name': 'Nick Reynolds'}
    ],
    email_data={
        "sender_name": 'John Lenon',
        "sender_email": 'example_1@gmail.com',
        "system_template_id": 54485
    },
    campaign_data={
        start_time=start_time,
        timezone='UTC'
    }
)
```

#### create_email_campaigns

Attributes:
- **recipients*** [list] - each list item must be represented by a dictionary with the same set of keys. Dictionary keys can be used in a email template;
- **campaigns** [list] - each list item must be represented by next dictionary:
    ```python
    {
        "email_data": {
            "subject": 'Email subject', 
            "body": '<html>...</html>',
            "text_body": "My message text",
            "categories": ["first", "second"],
            # ... or any allowed parameter from "create_email_message" method documentation
        },
        "campaign_data": {
            "start_time": time_delay_4,
            "track_links": 1,
            "track_read": 1,
            "timezone": "UTC"
            # ... or any allowed parameter from "create_campaign" method documentation
        }
    }
    ```

- **default_email_data** [dict] - represent default fields for campaigns. See the [method documentation](https://www.unisender.com/ru/support/api/messages/createemailmessage/) for a list of valid parameters. Parameter "list_id" is set automatically;
- **default_campaign_data** [dict] - represent default fields for campaigns. See the [method documentation](https://www.unisender.com/ru/support/api/messages/createcampaign/) for a list of valid parameters. Parameter "message_id" is set automatically.

Return value [list] - created campaigns ids. 

Example:
```python
from datetime import datetime, timedelta
from unisender import SimpleClient

cl = SimpleClient(
    api_key="your_api_key",
    platform="example",
    lang="ru"
)

time_delay_1 = datetime.now() + timedelta(hours=1)
time_delay_4 = datetime.now() + timedelta(hours=4)

# Send many delayed email messages (from UniSender custom template):

client.create_email_campaigns(
    recipients=[
        {'email': 'example_3@gmail.com', 'name': 'Dave Guard'},
        {'email': 'example_4@mail.ru', 'name': 'Bon Shane'},
        {'email': 'example_5@yandex.ru', 'name': 'Nick Reynolds'},
    ],
    campaigns=[
        # First campaign starts now from HTML-message
        {
            "email_data": {
                "subject": 'Email subject',
                "body": '<html>...</html>',
            }
        },
        # Second campaign starts after 1 hours from HTML-message
        {
            "email_data": {
                "subject": 'Email subject',
                "body": '<html>...</html>',
            },
            "campaign_data": {
                "start_time": time_delay_1
            }
        },
        # Third campaign starts after 4 hours from UniSender email template
        {
            "email_data": {
                "template_id": 3140875
            },
            "campaign_data": {
                "start_time": time_delay_4
            }
        }
    ],
    default_email_data={
        "sender_name": sender_name,
        "sender_email": sender_email
    },
    default_campaign_data={
        "timezone": 'UTC',
    }
)
```