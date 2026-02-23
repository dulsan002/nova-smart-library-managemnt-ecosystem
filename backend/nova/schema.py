"""
Nova — Root GraphQL Schema
===============================
Composes all bounded-context Query and Mutation classes into
a single schema served at /graphql.
"""

import graphene

from apps.identity.presentation.queries import IdentityQuery
from apps.identity.presentation.mutations import IdentityMutation
from apps.governance.presentation.schema import GovernanceQuery
from apps.catalog.presentation.schema import CatalogQuery, CatalogMutation
from apps.circulation.presentation.schema import (
    CirculationQuery,
    CirculationMutation,
)
from apps.digital_content.presentation.schema import (
    DigitalContentQuery,
    DigitalContentMutation,
)
from apps.engagement.presentation.schema import (
    EngagementQuery,
    EngagementMutation,
)
from apps.intelligence.presentation.schema import (
    IntelligenceQuery,
    IntelligenceMutation,
)
from apps.asset_management.presentation.schema import (
    AssetManagementQuery,
    AssetManagementMutation,
)
from apps.hr.presentation.schema import HRQuery, HRMutation
from apps.common.presentation.settings_schema import SettingsQuery, SettingsMutation


# ---------------------------------------------------------------------------
# Root Query — inherits all bounded-context queries
# ---------------------------------------------------------------------------

class Query(
    IdentityQuery,
    GovernanceQuery,
    CatalogQuery,
    CirculationQuery,
    DigitalContentQuery,
    EngagementQuery,
    IntelligenceQuery,
    AssetManagementQuery,
    HRQuery,
    SettingsQuery,
    graphene.ObjectType,
):
    """
    Root GraphQL Query.

    All bounded-context queries are composed here via multiple
    inheritance. Each context contributes its own resolver methods.
    """
    health = graphene.String(
        description='Simple health check returning "ok".',
    )

    def resolve_health(self, info):
        return 'ok'


# ---------------------------------------------------------------------------
# Root Mutation — inherits all bounded-context mutations
# ---------------------------------------------------------------------------

class Mutation(
    IdentityMutation,
    CatalogMutation,
    CirculationMutation,
    DigitalContentMutation,
    EngagementMutation,
    IntelligenceMutation,
    AssetManagementMutation,
    HRMutation,
    SettingsMutation,
    graphene.ObjectType,
):
    """
    Root GraphQL Mutation.

    All bounded-context mutations are composed here. Governance has
    no mutations — it is append-only via services.
    """
    pass


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

schema = graphene.Schema(query=Query, mutation=Mutation)
