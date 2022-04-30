from ..util import lazy

class UserPermissions:
    REVIEW_QUALIFIERS = "omgwords-agent.change_qualifier"

    def __init__(self, user):
        self.user = user

    @lazy
    def auth_user(self):
        if (self.user and hasattr(self.user, "website_user")
                and hasattr(self.user.website_user, "auth_user")):
            return self.user.website_user.auth_user

    def review_qualifiers(self):
        return self.auth_user is not None and self.auth_user.has_perm(self.REVIEW_QUALIFIERS)
