from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Empresa, Usuario
from .permission_policies import PermissionPolicyFactory

class AuthTests(APITestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nome="Empresa Teste",
            cnpj="12.345.678/0001-99",
            email="teste@empresa.com"
        )
        self.user_password = "password123"
        self.user = Usuario.objects.create_user(
            username="testuser",
            password=self.user_password,
            empresa=self.empresa,
            tipo_usuario="gestor"
        )
        self.login_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')

    def test_login_success(self):
        """Testa se o usuário consegue obter o token JWT com credenciais válidas."""
        data = {
            "username": "testuser",
            "password": self.user_password
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_password(self):
        """Testa se o login falha com senha incorreta."""
        data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Testa se o token de acesso pode ser renovado usando o refresh token."""
        login_data = {
            "username": "testuser",
            "password": self.user_password
        }
        login_response = self.client.post(self.login_url, login_data)
        refresh_token = login_response.data['refresh']

        refresh_data = {"refresh": refresh_token}
        response = self.client.post(self.refresh_url, refresh_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

class UserProfileTests(APITestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Alpha", cnpj="111", email="a@a.com")
        self.user = Usuario.objects.create_user(
            username="admin_test", password="123", tipo_usuario="admin"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('usuarios-list')

    def test_create_user_admin(self):
        """Testa se um Admin pode criar novos usuários."""
        data = {
            "username": "novo_tecnico",
            "password": "password123",
            "email": "tec@teste.com",
            "tipo_usuario": "tecnico",
            "empresa": self.empresa.id
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Usuario.objects.filter(username="novo_tecnico").count(), 1)

    def test_update_own_profile(self):
        response = self.client.patch(
            reverse('me'),
            {'first_name': 'Nome atualizado'},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Nome atualizado')

    def test_gestor_cannot_create_an_admin_user(self):
        gestor = Usuario.objects.create_user(
            username='gestor_user_admin',
            password='password123',
            tipo_usuario='gestor',
            empresa=self.empresa,
        )
        self.client.force_authenticate(user=gestor)

        response = self.client.post(self.url, {
            'username': 'forbidden_admin',
            'email': 'forbidden@example.com',
            'tipo_usuario': 'admin',
            'empresa': self.empresa.id,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Usuario.objects.filter(username='forbidden_admin').exists())

    def test_gestor_cannot_create_users_in_another_company(self):
        gestor = Usuario.objects.create_user(
            username='gestor_cross_company',
            password='password123',
            tipo_usuario='gestor',
            empresa=self.empresa,
        )
        outra_empresa = Empresa.objects.create(
            nome='Outra', cnpj='222', email='outra@example.com'
        )
        self.client.force_authenticate(user=gestor)

        response = self.client.post(self.url, {
            'username': 'cross_company_user',
            'email': 'cross@example.com',
            'tipo_usuario': 'tecnico',
            'empresa': outra_empresa.id,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Usuario.objects.filter(username='cross_company_user').exists())

    def test_gestor_cannot_create_or_delete_companies(self):
        gestor = Usuario.objects.create_user(
            username='gestor_company_admin',
            password='password123',
            tipo_usuario='gestor',
            empresa=self.empresa,
        )
        self.client.force_authenticate(user=gestor)

        create_response = self.client.post(reverse('empresas-list'), {
            'nome': 'Empresa indevida',
            'cnpj': '333',
            'email': 'indevida@example.com',
        }, format='json')
        delete_response = self.client.delete(
            reverse('empresas-detail', args=[self.empresa.id])
        )

        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)


class ChangePasswordTests(APITestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            username='password_change_user',
            password='old-password-123',
            tipo_usuario='tecnico',
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('change-password')

    def test_change_password_with_valid_current_password(self):
        response = self.client.post(self.url, {
            'senha_atual': 'old-password-123',
            'nova_senha': 'S0lidPass#2026',
            'confirmar_nova_senha': 'S0lidPass#2026',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('S0lidPass#2026'))

    def test_change_password_rejects_mismatched_confirmation(self):
        response = self.client.post(self.url, {
            'senha_atual': 'old-password-123',
            'nova_senha': 'S0lidPass#2026',
            'confirmar_nova_senha': 'DifferentPass#2026',
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PermissionPolicyFactoryTests(APITestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Empresa Teste", cnpj="99.999.999/0001-99", email="teste@empresa.com")
        self.gestor = Usuario.objects.create_user(
            username="gestor_policy",
            password="123",
            tipo_usuario="gestor",
            empresa=self.empresa,
        )
        self.tecnico = Usuario.objects.create_user(
            username="tecnico_policy",
            password="123",
            tipo_usuario="tecnico",
            empresa=self.empresa,
        )

    def test_factory_selects_gestor_policy(self):
        policy = PermissionPolicyFactory.create('gestor')
        self.assertTrue(policy.can_access(self.gestor, 'POST'))
        self.assertFalse(policy.can_access(self.tecnico, 'POST'))

    def test_factory_keeps_read_only_access_for_authenticated_users(self):
        policy = PermissionPolicyFactory.create('gestor_or_readonly')
        self.assertTrue(policy.can_access(self.tecnico, 'GET'))
        self.assertFalse(policy.can_access(self.tecnico, 'POST'))
