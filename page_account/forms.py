# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class AccountForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('email', 'username')
