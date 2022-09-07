from django.db.models import Lookup


class GistDistance(Lookup):
    lookup_name = "distance"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return "%s <-> %s" % (lhs, rhs), params
