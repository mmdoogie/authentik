"""Sync LDAP Users into authentik"""
import ldap3
import ldap3.core.exceptions
from django.core.exceptions import FieldError
from django.db.utils import IntegrityError

from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.sources.ldap.sync.base import LDAP_UNIQUENESS, BaseLDAPSynchronizer
from authentik.sources.ldap.sync.vendor.freeipa import FreeIPA
from authentik.sources.ldap.sync.vendor.ms_ad import MicrosoftActiveDirectory


class UserLDAPSynchronizer(BaseLDAPSynchronizer):
    """Sync LDAP Users into authentik"""

    def sync(self) -> int:
        """Iterate over all LDAP Users and create authentik_core.User instances"""
        if not self._source.sync_users:
            self.message("User syncing is disabled for this Source")
            return -1
        users = self._source.connection.extend.standard.paged_search(
            search_base=self.base_dn_users,
            search_filter=self._source.user_object_filter,
            search_scope=ldap3.SUBTREE,
            attributes=[ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES],
        )
        user_count = 0
        for user in users:
            attributes = user.get("attributes", {})
            user_dn = self._flatten(user.get("entryDN", user.get("dn")))
            if self._source.object_uniqueness_field not in attributes:
                self.message(
                    f"Cannot find uniqueness field in attributes: '{user_dn}",
                    attributes=attributes.keys(),
                    dn=user_dn,
                )
                continue
            uniq = self._flatten(attributes[self._source.object_uniqueness_field])
            try:
                defaults = self.build_user_properties(user_dn, **attributes)
                self._logger.debug("Creating user with attributes", **defaults)
                if "username" not in defaults:
                    raise IntegrityError("Username was not set by propertymappings")
                ak_user, created = self.update_or_create_attributes(
                    User, {f"attributes__{LDAP_UNIQUENESS}": uniq}, defaults
                )
            except (IntegrityError, FieldError) as exc:
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=(
                        f"Failed to create user: {str(exc)} "
                        "To merge new user with existing user, set the user's "
                        f"Attribute '{LDAP_UNIQUENESS}' to '{uniq}'"
                    ),
                    source=self._source,
                    dn=user_dn,
                ).save()
            else:
                self._logger.debug("Synced User", user=ak_user.username, created=created)
                user_count += 1
                MicrosoftActiveDirectory(self._source).sync(attributes, ak_user, created)
                FreeIPA(self._source).sync(attributes, ak_user, created)
        return user_count
