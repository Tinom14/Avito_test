from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from merch_store.models import Wallet
import pytest


@pytest.mark.django_db
def test_user_creation():
    """Тест создания пользователя"""
    user = User.objects.create_user(username='testuser', password='1234')
    assert user.username == 'testuser'
    assert user.check_password('1234') is True


@pytest.mark.django_db
def test_wallet_creation():
    """Тест создания кошелька при создании пользователя"""
    user = User.objects.create_user(username='testuser', password='1234')
    wallet = Wallet.objects.get(user=user)
    assert wallet.balance == 1000


@pytest.mark.django_db
def test_auth():
    """Тест получения JWT токена"""
    User.objects.create_user(username='testuser', password='1234')
    client = APIClient()
    response = client.post('/api/auth/', {'username': 'testuser', 'password': '1234'})
    assert response.status_code == status.HTTP_200_OK
    assert 'token' in response.data


@pytest.mark.django_db
def test_auth_with_JWT():
    """Тест авторизации пользователя через JWT"""
    user = User.objects.create_user(username='testuser', password='1234')
    token = AccessToken.for_user(user)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    response = client.get('/api/info/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_auth_wrong_password():
    """Тест авторизации с неправильным паролем"""
    User.objects.create_user(username='testuser', password='1234')
    client = APIClient()
    response = client.post('/api/auth/', {'username': 'testuser', 'password': 'wrongpass'})
    assert response.status_code == 401
    assert response.data['errors'] == 'Неверный пароль'


@pytest.mark.django_db
def test_auth_register():
    """Тест создания пользователя при первой авторизации"""
    client = APIClient()
    response = client.post('/api/auth/', {'username': 'user', 'password': '1234'})
    assert response.status_code == status.HTTP_200_OK
    assert 'token' in response.data


@pytest.mark.django_db
def test_auth_missing_fields():
    """Тест авторизации без введенных данных"""
    client = APIClient()
    response = client.post('/api/auth/', {}, format='json')
    assert response.status_code == 400
    assert response.data['errors'] == 'Необходимо указать имя пользователя и пароль'


@pytest.mark.django_db
def test_info_unauthorized():
    """Тест авторизации без передачи JWT токена"""
    client = APIClient()
    response = client.get('/api/info/')
    assert response.status_code == 401


@pytest.mark.django_db
def test_info():
    """Тест получения информации о купленных товарах и передачах монет"""
    user = User.objects.create_user(username='info_user', password='1234')

    token = AccessToken.for_user(user)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    response = client.get('/api/info/')

    assert response.status_code == 200
    assert response.data['coins'] == 1000


@pytest.mark.django_db
def test_buy_item():
    """Тест покупки товара"""
    user = User.objects.create_user(username='buyer', password='buyerpass')
    token = AccessToken.for_user(user)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    response = client.get('/api/buy/t-shirt/')

    assert response.status_code == 200
    assert response.data['message'] == 'Товар t-shirt успешно куплен'


@pytest.mark.django_db
def test_buy_item_no_balance():
    """Тест покупки товара при недостаточном балансе"""
    user = User.objects.create_user(username='poor_buyer', password='poorpass')
    Wallet.objects.filter(user=user).update(balance=0)
    token = AccessToken.for_user(user)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    response = client.get('/api/buy/powerbank/')

    assert response.status_code == 400
    assert response.data['errors'] == 'Недостаточно средств для покупки'


@pytest.mark.django_db
def test_buy_not_existing_item():
    """Тест покупки несуществующего товара"""
    user = User.objects.create_user(username='poor_buyer', password='poorpass')
    token = AccessToken.for_user(user)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    response = client.get('/api/buy/power/')

    assert response.status_code == 400
    assert response.data['errors'] == 'Товар не найден'


@pytest.mark.django_db
def test_send_coin():
    """Тест отправки монет"""
    sender = User.objects.create_user(username='s', password='1234')
    User.objects.create_user(username='r', password='1234')

    token = AccessToken.for_user(sender)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    response = client.post('/api/sendCoin/', {'to_user': 'r', 'amount': 100}, format='json')

    assert response.status_code == 200
    assert response.data['message'] == 'Монеты успешно отправлены'


@pytest.mark.django_db
def test_send_coin_no_balance():
    """Тест отправки монет при недостаточном балансе"""
    sender = User.objects.create_user(username='s', password='1234')
    Wallet.objects.filter(user=sender).update(balance=0)
    User.objects.create_user(username='r', password='1234')

    token = AccessToken.for_user(sender)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    response = client.post('/api/sendCoin/', {'to_user': 'r', 'amount': 100}, format='json')

    assert response.status_code == 400
    assert response.data['errors'] == 'Недостаточно средств на балансе отправителя'


@pytest.mark.django_db
def test_send_not_existing_user():
    """Тест отправки монет несуществующему пользователю"""
    sender = User.objects.create_user(username='s', password='1234')

    token = AccessToken.for_user(sender)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    response = client.post('/api/sendCoin/', {'to_user': 'not_existing_user', 'amount': 100}, format='json')

    assert response.status_code == 400
    assert response.data['errors'] == 'Получатель не найден'
