from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from offers_app.models import Offer, OfferDetail
from profile_app.models import Profile

TEST_PASSWORD = 'testpass123'

DETAIL_TIERS = [
    ('basic', 100, 5, 2),
    ('standard', 200, 7, 5),
    ('premium', 500, 10, -1),
]


def create_user(username, profile_type):
    """Creates a user together with a profile of the given type."""
    user = User.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password=TEST_PASSWORD,
    )
    Profile.objects.create(user=user, type=profile_type)
    return user


def auth_client(user):
    """Returns an API client authenticated as the given user."""
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


def create_offer(user, title='Test Offer'):
    """Creates an offer with the three required pricing tiers."""
    offer = Offer.objects.create(user=user, title=title, description='Test')
    for offer_type, price, days, revisions in DETAIL_TIERS:
        OfferDetail.objects.create(
            offer=offer, title=f'{offer_type} tier', price=price,
            delivery_time_in_days=days, revisions=revisions,
            features=['Feature'], offer_type=offer_type,
        )
    return offer


def tier_payload(offer_type, price=100, days=5, revisions=1):
    """Builds a single detail entry for offer create and update requests."""
    return {
        'title': f'{offer_type} tier',
        'revisions': revisions,
        'delivery_time_in_days': days,
        'price': price,
        'features': ['Feature'],
        'offer_type': offer_type,
    }
