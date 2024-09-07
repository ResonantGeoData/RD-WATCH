import logging

import requests
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin

from django.conf import settings

logger = logging.getLogger(__name__)


class RDWatchAccountAdapter(DefaultAccountAdapter):
    def new_user(self, request):
        user = super().new_user(request)
        # Disable all users on creation. Manual user approval is required if
        # not using GitLab OAuth.
        user.is_active = False
        return user


class RDWatchSocialAccountAdapter(DefaultSocialAccountAdapter):
    def new_user(self, request, sociallogin: SocialLogin):
        user = super().new_user(request, sociallogin)
        # Disable all users on initially. GitLab group membership will be checked
        # in `pre_social_login`, where this flag will be set to True if the user
        # is a member of an allowed group.
        user.is_active = False
        return user

    def pre_social_login(self, request, sociallogin: SocialLogin):
        if sociallogin.user.is_active:
            return

        logger.info(f'User {sociallogin.user} is not active, checking if eligible...')

        gitlab_url: str = settings.SOCIALACCOUNT_PROVIDERS['gitlab']['APPS'][0][
            'settings'
        ]['gitlab_url'].rstrip('/')
        resp = requests.get(
            f'{gitlab_url}/oauth/userinfo?access_token={sociallogin.token.token}'
        )

        groups = resp.json().get('groups', [])

        if any(group in settings.ALLOWED_GITLAB_GROUPS for group in groups):
            logger.info(
                f'User {sociallogin.user} is a member of an allowed GitLab group'
            )
            sociallogin.user.is_active = True
            # If this user already exists (i.e., this is a login, not a registration),
            # save it.
            # If this is a new user, we don't want to save it yet as that will occur
            # in another method in the SocialAccountAdapter flow.
            if sociallogin.is_existing:
                sociallogin.user.save()
        else:
            logger.info(
                f'User {sociallogin.user} is not a member of any allowed GitLab group'
            )
