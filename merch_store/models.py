from django.db import models, transaction
from django.contrib.auth.models import User

ITEMS = {
    "t-shirt": 80,
    "cup": 20,
    "book": 50,
    "pen": 10,
    "powerbank": 200,
    "hoody": 300,
    "umbrella": 200,
    "socks": 10,
    "wallet": 50,
    "pink-hoody": 500,
}


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet", primary_key=True)
    balance = models.PositiveIntegerField(default=1000)


class Transaction(models.Model):
    sender = models.ForeignKey(User, on_delete=models.PROTECT, related_name="sent_transactions")
    receiver = models.ForeignKey(User, on_delete=models.PROTECT, related_name="received_transactions")
    amount = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    @transaction.atomic
    def save(self, *args, **kwargs):

        if self.amount < 0:
            raise ValueError("Невозможно отправить отрицательное количество")

        if self.sender == self.receiver:
            raise ValueError("Невозможно отправить самому себе")

        sender_wallet = Wallet.objects.select_for_update().get(user=self.sender)
        receiver_wallet = Wallet.objects.select_for_update().get(user=self.receiver)

        if sender_wallet.balance < self.amount:
            raise ValueError("Недостаточно средств на балансе отправителя")

        sender_wallet.balance -= self.amount
        receiver_wallet.balance += self.amount

        sender_wallet.save()
        receiver_wallet.save()

        super().save(*args, **kwargs)


class Purchase(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='purchases'
    )
    item_name = models.CharField(max_length=100)
    item_price = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.item_name not in ITEMS:
            raise ValueError(f"Неизвестный товар: {self.item_name}")
        if ITEMS[self.item_name] != self.item_price:
            raise ValueError("Несоответствие цены товара")

        wallet = Wallet.objects.select_for_update().get(user=self.user)

        if wallet.balance < self.item_price:
            raise ValueError("Недостаточно средств для покупки")

        wallet.balance -= self.item_price
        wallet.save()

        super().save(*args, **kwargs)
