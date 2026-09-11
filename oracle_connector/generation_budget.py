"""Separate initial work from the budget reserved for actual visual review."""
PLAN_SECONDS=600
PHOTO_REVIEW_SECONDS=240
BLENDER_SECONDS=900
PHOTO_REBUILD_SECONDS=300


def initial_ai_remaining(spent):return max(0.,PLAN_SECONDS-spent)
def total_ai_limit(has_photos):return PLAN_SECONDS+(PHOTO_REVIEW_SECONDS if has_photos else 0)
def initial_blender_remaining(spent,has_photos):
    return max(0.,BLENDER_SECONDS-(PHOTO_REBUILD_SECONDS if has_photos else 0)-spent)
