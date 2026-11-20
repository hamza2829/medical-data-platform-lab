from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import UserRole

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'role']
    def get_role(self, user):
        try: return user.role_profile.role
        except UserRole.DoesNotExist: return 'admin' if user.is_superuser else 'researcher'

class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=12)
    role = serializers.ChoiceField(choices=UserRole.Role.choices)
    def validate_password(self, value):
        validate_password(value)
        return value
    def validate_username(self, value):
        if User.objects.filter(username=value).exists(): raise serializers.ValidationError('Username is already in use.')
        return value
    def validate_email(self, value):
        if User.objects.filter(email=value).exists(): raise serializers.ValidationError('Email is already in use.')
        return value
    def create(self, validated_data):
        role = validated_data.pop('role')
        user = User.objects.create_user(**validated_data)
        UserRole.objects.create(user=user, role=role)
        return user

class UserUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    role = serializers.ChoiceField(choices=UserRole.Role.choices, required=False)
    is_active = serializers.BooleanField(required=False)
