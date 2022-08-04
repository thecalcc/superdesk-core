import datetime
import superdesk

from typing import Optional

from superdesk.metadata.item import metadata_schema

from . import privileges, rundown_items, types, templates, shows


class RundownsResource(superdesk.Resource):
    resource_title = "Rundowns"
    schema = {
        "show": superdesk.Resource.rel("shows", required=True),
        "title": metadata_schema["headline"],
        "template": superdesk.Resource.rel("rundown_templates", nullable=True),
        "scheduled_on": {
            "type": "datetime",
            "readonly": True,
            "nullable": True,
        },
        "duration": {
            "type": "number",
            "readonly": True,
        },
        "planned_duration": {
            "type": "number",
        },
        "airtime_time": {
            "type": "string",
        },
        "airtime_date": {
            "type": "string",
        },
        "airtime_datetime": {
            "type": "datetime",
        },
        "items": templates.TemplatesResource.schema["items"].copy(),
    }

    datasource = {
        "search_backend": "elastic",
    }

    versioning = True
    privileges = {"POST": privileges.RUNDOWNS, "PATCH": privileges.RUNDOWNS, "PUT": privileges.RUNDOWNS}


class RundownsService(superdesk.Service):
    def create(self, docs, **kwargs):
        ids = []
        for doc in docs:
            show = shows.shows_service.find_one(req=None, _id=doc["show"])
            assert show is not None, {"show": 1}
            date = datetime.date.fromisoformat(doc["airtime_date"])
            if doc.get("template"):
                template = templates.templates_service.find_one(req=None, _id=doc["template"])
                assert template is not None, {"template": 1}
                rundown = self.create_from_template(template, date)
            else:
                rundown = self.create_from_show(show, date, doc)
            doc.update(rundown)
            assert "_id" in rundown, {"rundown": {"_id": 1}}
            ids.append(rundown["_id"])
        return ids

    def create_from_show(self, show: types.IShow, date: datetime.date, doc: types.IRundown) -> types.IRundown:
        assert "_id" in show, {"show": {"_id": 1}}
        rundown: types.IRundown = {
            "show": show["_id"],
            "title": doc.get("title") or show["title"],
            "planned_duration": doc.get("planned_duration") or show.get("planned_duration") or 0,
            "airtime_date": date.isoformat(),
            "airtime_time": doc.get("airtime_time"),
            "scheduled_on": None,
            "template": None,
            "items": [],
        }

        super().create([rundown])
        return rundown

    def create_from_template(
        self, template: types.ITemplate, date: datetime.date, scheduled_on: Optional[datetime.datetime] = None
    ) -> types.IRundown:
        assert "_id" in template, {"template": {"_id": 1}}
        rundown: types.IRundown = {
            "show": template["show"],
            "airtime_date": date.isoformat(),
            "airtime_time": template.get("airtime_time", ""),
            "title": template.get("title", ""),
            "template": template["_id"],
            "planned_duration": template.get("planned_duration", 0),
            "scheduled_on": scheduled_on or datetime.datetime.utcnow(),
            "items": [],
        }

        if template.get("title_template"):
            title_template = template["title_template"]
            rundown["title"] = " ".join(
                filter(
                    bool,
                    [
                        title_template.get("prefix") or "",
                        title_template.get("separator", " ").strip(),
                        date.strftime(title_template.get("date_format", "%d.%m.%Y")),
                    ],
                )
            )

        if template.get("items"):
            rundown["items"] = [rundown_items.items_service.duplicate_ref(ref) for ref in template["items"]]

        super().create([rundown])
        return rundown


rundowns_service = RundownsService()
