# Coderr Backend

REST API for the Coderr freelancer marketplace, built with Django and Django REST Framework.

Business users publish offers with three pricing tiers (basic, standard, premium). Customer users
book a tier, which creates an order, and can rate the business users they worked with.

This repository contains the backend only. The frontend is a separate Vanilla JS project provided
by the Developer Akademie.

## Requirements

- Python 3.9 or newer
- pip

## Setup

Clone the repository and change into the project folder:

```bash
git clone https://github.com/MarcelHaessler/Codeer.git
cd Codeer
```

Create and activate a virtual environment:

```bash
python3 -m venv env
source env/bin/activate
```

On Windows use `env\Scripts\activate` instead.

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create your `.env` file from the template:

```bash
cp .env.example .env
```

The project refuses to start without a `SECRET_KEY`. Generate one and paste it into `.env`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Create the database:

```bash
python manage.py migrate
```

Create an admin account so you can use the Django admin at `/admin/`:

```bash
python manage.py createsuperuser
```

Start the server:

```bash
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/api/`.

## Connecting the frontend

The frontend expects the backend on `http://127.0.0.1:8000/` — this is configured in the
frontend's `shared/scripts/config.js`. Do not start the backend on a different port unless you
change that file as well.

Open the frontend's `index.html` with the VS Code Live Server extension. CORS is configured for
ports 5500 on both `127.0.0.1` and `localhost`, which is what Live Server uses. If your setup
serves the frontend from a different origin, add it to `CORS_ALLOWED_ORIGINS` in
`core/settings.py`.

The frontend ships with two guest logins in `config.js` (`andrey` and `kevin`). These users do not
exist in a fresh database — either register them through the frontend with the passwords listed in
that file, or change the file to match your own accounts.

## Authentication

The API uses token authentication. Register or log in to receive a token:

```bash
curl -X POST http://127.0.0.1:8000/api/registration/ \
  -H "Content-Type: application/json" \
  -d '{"username":"jdoe","email":"jdoe@example.com","password":"secret123","repeated_password":"secret123","type":"business"}'
```

Send the token with every other request:

```
Authorization: Token <your-token>
```

All endpoints require authentication except registration, login and `base-info`.

## Endpoints

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/api/registration/` | Requires `type`: `customer` or `business` |
| POST | `/api/login/` | |
| GET, PATCH | `/api/profile/<pk>/` | `pk` is the **user id**, not the profile id |
| GET | `/api/profiles/business/` | |
| GET | `/api/profiles/customer/` | |
| GET, POST | `/api/offers/` | POST is restricted to business users |
| GET, PATCH, DELETE | `/api/offers/<id>/` | Restricted to the creator |
| GET | `/api/offerdetails/<id>/` | |
| GET, POST | `/api/orders/` | POST is restricted to customer users |
| GET, PATCH, DELETE | `/api/orders/<id>/` | PATCH by the business user, DELETE by staff only |
| GET | `/api/order-count/<business_user_id>/` | Orders still in progress |
| GET | `/api/completed-order-count/<business_user_id>/` | |
| GET, POST | `/api/reviews/` | POST is restricted to customer users |
| GET, PATCH, DELETE | `/api/reviews/<id>/` | Restricted to the author |
| GET | `/api/base-info/` | Public, no token required |

### Offer list query parameters

`/api/offers/` supports `creator_id`, `min_price`, `max_delivery_time`, `search`, `ordering`
(`updated_at` or `min_price`, prefix with `-` for descending), `page` and `page_size`. The default
page size is 6, matching the frontend.

### Review list query parameters

`/api/reviews/` supports `business_user_id`, `reviewer_id` and `ordering` (`updated_at` or
`rating`, prefix with `-` for descending).

## Things worth knowing

**Profiles are addressed by user id.** `/api/profile/<pk>/` expects the id of the user, not the id
of the profile row. This is what the frontend sends, and the view is configured accordingly.

**A profile is created automatically on registration.** The `type` field sent during registration
is stored on the profile, since Django's built-in user model has no such field. `first_name`,
`last_name` and `email` live on the user model and are read and written through the profile
serializer rather than being duplicated.

**Orders are snapshots.** When a customer books an offer tier, the title, price, revisions,
delivery time, features and offer type are copied into the order. Changing or deleting the offer
afterwards leaves existing orders untouched, so customers keep the terms they agreed to.

**Offers always have exactly three tiers.** Creating an offer requires exactly one `basic`, one
`standard` and one `premium` detail. Updating an offer matches details by their `offer_type`.

**One review per customer and business user.** This is enforced both in the serializer, for a
readable error message, and by a database constraint.

**Uploads.** Profile pictures and offer images are stored under `media/`. In development Django
serves this folder directly; the `media/` folder is not part of this repository.

**Prices are returned as numbers,** not as strings. This is set through
`COERCE_DECIMAL_TO_STRING` in `core/settings.py`.

## Project structure

```
core/            project settings, root URL configuration
auth_app/        registration and login
profile_app/     profile model, profile detail and list endpoints
offers_app/      offer and offer detail models and endpoints
orders_app/      order model, order endpoints and order counts
reviews_app/     review model and endpoints
base_info_app/   aggregated platform statistics, no models
```

Each app keeps its API layer in an `api/` subfolder containing `serializers.py`, `views.py`,
`urls.py` and, where needed, `permissions.py` and `filters.py`.

## Development notes

The database file, the `media/` folder and `.env` are excluded from version control. After
cloning you always start with an empty database and have to create your own `.env`; use
`.env.example` as the template.

Code style is checked with flake8 using the configuration in `.flake8` (max line length 99).
flake8 is a development dependency and is deliberately not listed in `requirements.txt`:

```bash
pip install flake8
flake8 .
```

Every app ships tests covering the happy path as well as the permission and validation rules:

```bash
python manage.py test
```

To measure coverage, install `coverage` (also a development dependency, not listed in
`requirements.txt`) and run:

```bash
pip install coverage
coverage run --source='.' --omit='env/*,*/migrations/*,manage.py,*/tests.py' manage.py test
coverage report
```
