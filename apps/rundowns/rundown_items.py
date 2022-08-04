import superdesk

from typing import Dict

from . import privileges, types

from apps.archive.common import ITEM_DUPLICATE
from superdesk.metadata.item import metadata_schema


class RundownItemsResource(superdesk.Resource):
    schema = {
        "title": metadata_schema["headline"],
        "item_type": superdesk.Resource.not_analyzed_field(required=True),
        "content": metadata_schema["body_html"],
        "duration": {
            "type": "number",
        },
        "planned_duration": {
            "type": "number",
        },
        "operation": superdesk.Resource.not_analyzed_field(),
        "original_id": superdesk.Resource.not_analyzed_field(),
        "show_part": superdesk.Resource.not_analyzed_field(),
        "live_sound": superdesk.Resource.not_analyzed_field(),
        "guests": superdesk.Resource.not_analyzed_field(),
        "additional_notes": superdesk.Resource.not_analyzed_field(),
        "live_captions": superdesk.Resource.not_analyzed_field(),
        "last_sentence": superdesk.Resource.not_analyzed_field(),
    }

    datasource = {
        "search_backend": "elastic",
    }

    versioning = True
    privileges = {"POST": privileges.RUNDOWNS, "PATCH": privileges.RUNDOWNS, "PUT": privileges.RUNDOWNS}


class RundownItemsService(superdesk.Service):
    def duplicate_ref(self, ref: types.IRef) -> types.IRef:
        item = self.find_one(req=None, _id=ref["_id"])
        copy = self.copy_item(item)
        self.post([copy])
        new_ref: types.IRef = {
            "_id": copy["_id"],
            "start_time": ref["start_time"],
        }
        return new_ref

    def copy_item(self, item: Dict):
        copy = {k: v for k, v in item.items() if k[0] != "_"}

        copy["original_id"] = item["_id"]
        copy["operation"] = ITEM_DUPLICATE
        return copy


items_service = RundownItemsService()
