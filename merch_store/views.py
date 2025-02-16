from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from .models import Wallet, Transaction, Purchase, ITEMS


class Auth(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'errors': 'Необходимо указать имя пользователя и пароль'},
                            status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(username=username).first()

        if user is None:
            try:
                User.objects.create_user(username=username, password=password)
            except Exception as e:
                return Response({'errors': f'Ошибка при создании пользователя: {str(e)}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'errors': 'Неверный пароль'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken.for_user(user)
        except Exception as e:
            return Response({'errors': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'token': str(refresh.access_token)}, status=status.HTTP_200_OK)


class Info(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            wallet = Wallet.objects.get(user=request.user)
            purchases = Purchase.objects.filter(user=request.user)
            transactions_received = Transaction.objects.filter(receiver=request.user)
            transactions_sent = Transaction.objects.filter(sender=request.user)

            inventory = []
            for item_name in ITEMS.keys():
                count = purchases.filter(item_name=item_name).count()
                if count > 0:
                    inventory.append({'type': item_name, 'quantity': count})

            coin_history = {
                'received': [{'fromUser': t.sender.username, 'amount': t.amount} for t in transactions_received],
                'sent': [{'toUser': t.receiver.username, 'amount': t.amount} for t in transactions_sent]
            }

            return Response({
                'coins': wallet.balance,
                'inventory': inventory,
                'coinHistory': coin_history
            }, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({'errors': 'Кошелек не найден'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'errors': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BuyItem(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, item):
        try:
            if item not in ITEMS:
                return Response({'errors': 'Товар не найден'}, status=status.HTTP_400_BAD_REQUEST)

            purchase = Purchase(user=request.user, item_name=item, item_price=ITEMS[item])
            purchase.save()

            return Response({'message': f'Товар {item} успешно куплен'}, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({'errors': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as vale:
            return Response({'errors': str(vale)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'errors': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendCoin(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            to_user = request.data.get('to_user')
            amount = request.data.get('amount')
            if not to_user or not amount:
                return Response({'errors': 'Неверный запрос'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                receiver = User.objects.get(username=to_user)
            except User.DoesNotExist:
                return Response({'errors': 'Получатель не найден'}, status=status.HTTP_400_BAD_REQUEST)
            transaction = Transaction(sender=request.user, receiver=receiver, amount=amount)
            transaction.save()
            return Response({'message': 'Монеты успешно отправлены'}, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({'errors': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as vale:
            return Response({'errors': str(vale)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'errors': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
